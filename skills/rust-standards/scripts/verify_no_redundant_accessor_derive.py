#!/usr/bin/env python3
"""Forbid spelling out the Getter + GetterMut + Setter trio.

Background (rust-standards §17.16, user-ratified 2026-10-14): when a struct
needs all three accessor kinds, `Data` IS the trio — one derive instead of
three. From lombok-macros 10.2.4 `src/lib.rs`:

    #[proc_macro_derive(Getter,    attributes(get))]       -> inner_lombok_data(input, true,  false, false)
    #[proc_macro_derive(GetterMut, attributes(get_mut))]  -> inner_lombok_data(input, false, true,  false)
    #[proc_macro_derive(Setter,    attributes(set))]      -> inner_lombok_data(input, false, false, true )
    #[proc_macro_derive(Data,      attributes(get, get_mut, set))]
                                                          -> inner_lombok_data(input, true,  true,  true )

Same generator, same three booleans, and `Data` declares the union of the
three helper attributes, so every `#[get(..)]` / `#[get_mut(..)]` /
`#[set(..)]` on the fields keeps working unchanged:

    #[derive(Clone, CustomDebug, Getter, GetterMut, Setter)]   <-- drop
    #[derive(Clone, CustomDebug, Data)]                        <-- keep

Two of the three are NOT a violation: `Getter + Setter` and
`GetterMut + Setter` have no combined derive, so those stay as they are.

Scoping:
  - struct items only. Enums and unions are rejected by the generator itself
    (`_ => panic!(UNSUPPORTED_DATA_DERIVE)` in `inner_lombok_data`), so no
    compilable code can carry the trio on them.
  - a derive list that ALREADY contains `Data` next to the trio is the same
    redundancy from the other side (and does not compile — duplicate
    methods); the message says to delete the individual derives instead.
  - comments, string literals, and doc comments never count.

Read-only. Exits non-zero when any violation is present.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {"target", ".git", "node_modules", ".cargo", "dist", "www"}

# The trio `Data` replaces, and the derive that replaces it.
TRIO = {"Getter", "GetterMut", "Setter"}
DATA = "Data"

DERIVE_ATTR_RE = re.compile(r"#\[\s*derive\s*\(")
STRUCT_AFTER_RE = re.compile(r"\b(?:struct|enum|union|trait|fn|impl|mod)\b")


def strip_comments(text: str) -> str:
    """Blank out comments and string/char literal bodies, preserving offsets.

    Offset preservation matters: violations are reported at the original
    line number. Blanking is what keeps prose (`/// see #[derive(..)]` in a
    doc comment, a raw string holding sample code) from being read as code.
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
        elif c in "rb" and re.match(r"r(#*)\"", text[i:]):
            m = re.match(r"r(#*)\"", text[i:])
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
    that re-exports the macros spells them (`lombok_macros::Data`).
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


def check_text(text: str) -> list[tuple[int, str, str]]:
    """Return [(line_no, derive_list, item_kind)] for redundant trios."""
    code = strip_comments(text)
    hits: list[tuple[int, str, str]] = []
    for match in DERIVE_ATTR_RE.finditer(code):
        names, end = _derive_names(code, match.end() - 1)
        if not TRIO.issubset(names):
            continue
        # The item the derive list decorates decides whether the trio can
        # even compile: only a struct is supported by the generator.
        tail = code[end : end + 200]
        kind_match = STRUCT_AFTER_RE.search(tail)
        if kind_match is None or kind_match.group(0) != "struct":
            continue
        line_no = code.count("\n", 0, match.start()) + 1
        hits.append((line_no, ", ".join(names), kind_match.group(0)))
    return hits


def iter_rust_files(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _message(where: str, names: list[str]) -> str:
    shown = ", ".join(names)
    if DATA in names:
        return (
            f"{where}: derive list `#[derive({shown})]` already contains "
            f"`{DATA}` — delete the individual `Getter` / `GetterMut` / "
            f"`Setter` entries (rust-standards §17.16)"
        )
    return (
        f"{where}: derive list `#[derive({shown})]` spells out the full "
        f"accessor trio — write `#[derive({DATA})]` instead; it is exactly "
        f"`Getter + GetterMut + Setter` (rust-standards §17.16)"
    )


def check_file(path: Path) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [
        _message(f"{path}:{line_no}", names.split(", "))
        for line_no, names, _kind in check_text(text)
    ]


def audit_one(path: Path, root: Path | None = None) -> list[str]:
    """Per-file entry point used by `staged_file_gate.py`.

    The gate imports this module and calls `audit_one` directly instead of
    shelling out, so a verifier without it is silently skipped (it returns
    an empty list, which reads as "0 violations"). Keep this name.

    The optional `root` gives repo-relative prefixes; the gate calls it with
    a single argument, which falls back to the file's own directory as the
    base and yields the bare file name.
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
        _message(f"{rel}:{line_no}", names.split(", "))
        for line_no, names, _kind in check_text(text)
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify_no_redundant_accessor_derive.py <repo_root>", file=sys.stderr)
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
