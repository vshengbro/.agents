#!/usr/bin/env python3
"""Forbid hand-writing a constructor when lombok's `New` derive exists for it.

Background (rust-standards §17.17, user-ratified 2026-10-16): if a type has a
`new` function, it must come from `#[derive(New)]` on the struct — not from a
hand-written `fn new(...)`. And `New`'s whole reason for existing is the one
manual constructor cannot do: **`#[new(skip)]` drops a field out of the
signature**, so the ones you do not want to pass get `Default::default()`.
Re-implementing `new` by hand throws that capability away.

    #[derive(Clone, Debug, Data, New)]      <-- correct
    pub struct User { name: String, email: String }

    impl User {
        pub fn new(name: String) -> Self {    // <-- violation: hand-written,
            Self { name, email: String::new() } //    and it forces email too
        }
    }

`New` supports exactly what the manual form is missing:
  - `#[new(skip)]`      — field absent from the signature, `Default::default()`
  - `#[new(pub(crate))]` / `#[new(pub(super))]` / `#[new(private)]`
  - `#[new(with = expr)]` / `#[new(into)]` — per-field conversion

Scope — deliberately narrow, because the honest answer is that most `fn new`
in these repos are NOT this rule's business:

  1. STRUCT items only. `New` is a derive; a derive decorates a type.
  2. The `fn new` must live in an `impl` block for the SAME struct (matched by
     name), and the struct must carry `New` in its derive list. A struct
     WITHOUT `New` is not reported — `New` generates a `new` that returns all
     fields as parameters, which is the wrong shape for enums' variants, for
     unit structs, and for any type whose constructor must validate or
     transform. Those keep hand-written constructors by design.
  3. Hand-written `fn new` that returns `Self` in an `impl` for a `New`-derived
     struct is reported ONCE per impl block, named by the impl target.

What this rule does NOT do: it does not demand `New` on every struct that could
have one. That is a different rule (and a much noisier one — see the reference
§17.17 for the baseline counts). This one catches the case where the macro is
already there and the hand-written duplicate is the reason it is not being used.

Comments, string literals and doc comments never count.
Read-only. Exits non-zero when any violation is present.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {"target", ".git", "node_modules", ".cargo", "dist", "www"}

DERIVE_ATTR_RE = re.compile(r"#\[\s*derive\s*\(")
NEW_DERIVE = "New"
ITEM_KIND_RE = re.compile(r"\b(?:struct|enum|union|trait|fn|impl|mod)\b")
IMPL_TARGET_RE = re.compile(
    r"\bimpl(?:\s*<[^>]*>)?\s+(?:::)?([A-Za-z_][A-Za-z0-9_]*)"
)
FN_NEW_RE = re.compile(r"\bfn\s+new\s*(?:<[^>]*>)?\s*\(")

# `New` derives an all-fields constructor: every field becomes a parameter.
# These shapes cannot use it meaningfully, so a hand-written `new` is correct.
NEW_CANNOT_APPLY = re.compile(
    r"\b(?:struct|enum|union)\s+\w+(?:<[^>]*>)?\s*[;{]"
)


def strip_comments(text: str) -> str:
    """Blank out comments and string/char literal bodies, preserving offsets.

    Offset preservation matters: violations are reported at the original line
    number. Blanking is what keeps prose (`/// see #[derive(..)]` in a doc
    comment, a raw string holding sample code) from being read as code.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        two = text[i : i + 2]
        if two == "//":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif two == "/*":
            depth = 1
            out.append("  ")
            i += 2
            while i < n and depth:
                if text[i : i + 2] == "/*":
                    depth += 1
                    out.append("  ")
                    i += 2
                elif text[i : i + 2] == "*/":
                    depth -= 1
                    out.append("  ")
                    i += 2
                else:
                    out.append("\n" if text[i] == "\n" else " ")
                    i += 1
        elif c in "rb" and re.match(r'r(#*)"', text[i:]):
            m = re.match(r'r(#*)"', text[i:])
            assert m
            hashes = m.group(1)
            end = text.find('"' + hashes, i + m.end())
            end = n if end == -1 else end + 1 + len(hashes)
            for ch in text[i:end]:
                out.append("\n" if ch == "\n" else " ")
            i = end
        elif c == '"':
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    out.append(" ")
                    i += 1
                    if i < n:
                        out.append("\n" if text[i] == "\n" else " ")
                        i += 1
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        elif c == "'" and re.match(r"'(?:\\.|[^\\'])'", text[i:]):
            m = re.match(r"'(?:\\.|[^\\'])'", text[i:])
            assert m
            for ch in m.group(0):
                out.append("\n" if ch == "\n" else " ")
            i += m.end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _derive_names(code: str, open_paren: int) -> tuple[list[str], int]:
    """Read one derive list, starting at its `(`. Returns (names, end)."""
    depth = 0
    i = open_paren
    n = len(code)
    while i < n:
        c = code[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return _split_names(code[open_paren + 1 : i]), i + 1
        i += 1
    return [], n


def _split_names(body: str) -> list[str]:
    """Split a derive list on top-level commas, returning bare macro names.

    Path-qualified derives count by their last segment, which is how a crate
    that re-exports the macros spells them (`lombok_macros::New`).
    """
    names: list[str] = []
    depth = 0
    current = ""
    for ch in body:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            names.append(current)
            current = ""
            continue
        current += ch
    names.append(current)
    out: list[str] = []
    for raw in names:
        name = raw.strip().split("::")[-1].strip()
        if name:
            out.append(name)
    return out


def new_derived_structs(code: str) -> dict[str, int]:
    """Map struct name -> line of its definition, for `New`-derived ones only."""
    found: dict[str, int] = {}
    for match in DERIVE_ATTR_RE.finditer(code):
        names, end = _derive_names(code, match.end() - 1)
        if NEW_DERIVE not in names:
            continue
        tail = code[end : end + 200]
        kind_match = ITEM_KIND_RE.search(tail)
        if kind_match is None or kind_match.group(0) != "struct":
            continue
        name_match = re.search(
            r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", code[end : end + 200]
        )
        if name_match is None:
            continue
        found[name_match.group(1)] = code.count("\n", 0, end) + 1
    return found


def check_text(text: str) -> list[tuple[int, str, str]]:
    """Return [(line_no, struct_name, fn_new_line)] for hand-written `new`."""
    code = strip_comments(text)
    derived = new_derived_structs(code)
    if not derived:
        return []
    hits: list[tuple[int, str, str]] = []
    seen: set[tuple[str, int]] = set()
    for match in IMPL_TARGET_RE.finditer(code):
        target = match.group(1)
        if target not in derived:
            continue
        # Confine the search to this impl block, so a `fn new` belonging to a
        # DIFFERENT type further down the file is not attributed to this one.
        block_start = match.end()
        brace = code.find("{", block_start)
        if brace == -1:
            continue
        depth = 0
        end = len(code)
        i = brace
        while i < len(code):
            if code[i] == "{":
                depth += 1
            elif code[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        for fn in FN_NEW_RE.finditer(code, block_start, end):
            key = (target, fn.start())
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                (
                    code.count("\n", 0, fn.start()) + 1,
                    target,
                    f"struct {target} derives {NEW_DERIVE}",
                )
            )
    return hits


def iter_rust_files(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _message(where: str, name: str) -> str:
    return (
        f"{where}: hand-written `fn new` in `impl {name}` — `struct {name}` "
        f"already derives `{NEW_DERIVE}`; delete the manual constructor and "
        f"use the generated one, marking excluded fields `#[new(skip)]` so "
        f"they are defaulted instead of demanded as parameters "
        f"(rust-standards §17.17)"
    )


def check_file(path: Path) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [
        _message(f"{path}:{line_no}", name)
        for line_no, name, _why in check_text(text)
    ]


def audit_one(path: Path, root: Path | None = None) -> list[str]:
    """Per-file entry point used by `staged_file_gate.py`.

    The gate imports this module and calls `audit_one` directly instead of
    shelling out, so a verifier without it is silently skipped (it returns
    an empty list, which reads as "0 violations"). Keep this name.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    base = Path(root) if root is not None else Path(path).parent
    try:
        rel = Path(path).relative_to(base)
    except ValueError:
        rel = Path(path).name
    return [
        _message(f"{rel}:{line_no}", name)
        for line_no, name, _why in check_text(text)
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify_no_manual_new_fn.py <repo_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = list(iter_rust_files(root))
    violations: list[str] = []
    for path in files:
        violations.extend(check_file(path))

    for line in violations:
        print(line)

    print(f"{len(files)} files checked, {len(violations)} violations")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
