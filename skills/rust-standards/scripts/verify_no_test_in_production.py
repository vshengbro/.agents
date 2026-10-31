#!/usr/bin/env python3
"""
Verify §14.4: no bare test attribute (`#[test]` and its async / wasm
spellings) in a production file — unit tests live in `<crate>/tests/`.

Why this exists
---------------
`audit_rust_standards.py` check 4 implements this rule as an inline shell
pipeline over `git diff origin/master HEAD`, which means it only ever sees
the lines the branch *adds*.  Two consequences:

  1. The pre-commit hook could not run it at all — `staged_file_gate.py`
     drives per-file verifiers through their `audit_one()` entry point, and
     this rule had no such script.  A rule the audit enforces and the hook
     does not is a rule that does not hold at commit time.
  2. `git diff` sees the DIFF, not the FILE.  A production file that
     already carried a `#[test]` function was never reported, and an
     unrelated edit to that file left the violation in place while the
     check stayed silent.

The sanctioned shape puts the test functions in the crate's `tests/` tree,
so the production file carries only an INCLUDE and no test attribute at
all:

    #[cfg(test)]
    #[path = "../tests/mod.rs"]
    mod tests;

An inline `#[cfg(test)] mod tests { ... }` block in a production file is a
DIFFERENT violation with a different owner: `verify_no_inline_cfg_test.py`
(§14.4) reports the block itself.  This verifier therefore skips the test
attributes that live INSIDE such a block, so one mistake is reported once
instead of twice — the gate counts one finding per mistake, not four.

`#[test]` alone is not enough to bypass this: the async and wasm spellings
mark a test function just as well, and a rule that caught only the literal
`#[test]` would be sidestepped by writing one async test.

Usage:
    python3 verify_no_test_in_production.py [ROOT]
    python3 verify_no_test_in_production.py [ROOT] --file PATH   # gate mode

Exit 0 if clean, 1 if any violation, 2 on usage error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXEMPT_DIRS = {"target", ".cargo", "node_modules"}

# `#[cfg(test)]` (or `#[cfg(all(test, ...))]`) on a line of its own.
CFG_TEST = re.compile(r"^\s*#\s*\[\s*cfg\s*\(\s*(?:all\s*\(\s*)?test\b")

# A module declaration with a BODY: `mod name {`.  The include form ends
# with `;` and is therefore not matched.
MOD_BLOCK = re.compile(
    r"^\s*(?:pub\s*\(\s*crate\s*\)\s*)?mod\s+(?:r#)?[A-Za-z_][A-Za-z0-9_]*\s*\{"
)

# `#[path = "..."]` — the include form's marker.
PATH_ATTR = re.compile(r"^\s*#\s*\[\s*path\s*=")

# The test attributes this rule knows.  `tokio::test` and `async_std::test`
# are the async spellings of `#[test]`; `wasm_bindgen_test` is the wasm one.
TEST_ATTR = re.compile(
    r"#\s*\[\s*"
    r"((?:[A-Za-z_][A-Za-z0-9_]*\s*::\s*)*(?:test|wasm_bindgen_test))"
    r"\s*(?:\([^)]*\))?\s*\]"
)

# The item an attribute governs.  `#[test]` only ever applies to a fn.
FN_ITEM = re.compile(
    r"^\s*(?:pub(?:\s*\([^)]*\))?\s+)?(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?"
    r"(?:extern\s+(?:\"[^\"]*\"|[A-Za-z_][A-Za-z0-9_]*)\s+)?fn\b"
)


def _infer_root(path: Path) -> Path:
    """Nearest ancestor that reads as a crate root.

    The crate root must stay ABOVE any `tests/` component, otherwise a
    test file loses its `tests` segment in `path.relative_to(root)` and
    every test is misread as production code.
    """
    for candidate in [path.parent, *path.parents]:
        if candidate.name == "src":
            return candidate.parent
        if (candidate / "src").is_dir() or (candidate / "Cargo.toml").is_file():
            return candidate
    return path.parent


def _exempt_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    if "tests" in parts:
        return True
    return any(part in EXEMPT_DIRS for part in parts)


def _mask(text: str) -> list[str]:
    """Blank out comments and string literals, keeping the line structure.

    A `#[test]` written inside a doc comment, a block comment or a string
    literal is PROSE about a test, not a test, and reporting it would be a
    false positive.  The masked copy is also what the brace counting below
    reads, so a `{` inside a literal cannot shift the block extent.

    Raw strings (`r"..."`, `r#"..."#`) are handled because they routinely
    carry Rust source as their payload.  Character literals are handled
    too, and they are NOT optional: a literal like `'{'` carries an
    unbalanced brace, and the brace counting below reads the masked copy.
    Without masking it, the inline-block extent runs to end-of-file and
    every `#[test]` after it silently escapes the report.

    A character literal is exactly one character (optionally escaped)
    between quotes.  A LIFETIME (`'a`, `'_`, `'static`) is not, so the
    scanner only treats a quote as a literal opener when a closing quote
    follows immediately — the same rule `verify_no_qualified_std_path.py`
    uses, and for the same reason: a looser rule pairs a lifetime with a
    distant quote and swallows the code in between.
    """
    out: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    block_depth = 0
    while i < n:
        ch = text[i]
        if ch == "\n":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        if block_depth:
            if ch == "/" and i + 1 < n and text[i + 1] == "*":
                block_depth += 1
                buf.append("  ")
                i += 2
                continue
            if ch == "*" and i + 1 < n and text[i + 1] == "/":
                block_depth -= 1
                buf.append("  ")
                i += 2
                continue
            buf.append(" ")
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                buf.append(" ")
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            block_depth = 1
            buf.append("  ")
            i += 2
            continue
        if ch == "r" and i + 1 < n and (text[i + 1] == '"' or text[i + 1] == "#"):
            cursor = i + 1
            hashes = 0
            while cursor < n and text[cursor] == "#":
                hashes += 1
                cursor += 1
            if cursor < n and text[cursor] == '"':
                closing = '"' + "#" * hashes
                end = text.find(closing, cursor + 1)
                stop = n if end < 0 else min(end + len(closing), n)
                while i < stop:
                    if text[i] == "\n":
                        out.append("".join(buf))
                        buf = []
                    else:
                        buf.append(" ")
                    i += 1
                continue
        if ch == "'":
            # A character literal is exactly one character (optionally
            # escaped) between quotes.  A lifetime ('a, '_, 'static) has
            # no closing quote right after the first character, so it is
            # left alone.
            if i + 2 < n and text[i + 1] == "\\":
                end = i + 2
                if end < n and text[end] == "'":
                    buf.append(" ")
                    buf.append(" ")
                    buf.append(" ")
                    i = end + 1
                    continue
            elif i + 2 < n and text[i + 2] == "'" and text[i + 1] != "\\":
                buf.append(" ")
                buf.append(" ")
                buf.append(" ")
                i = i + 3
                continue
        if ch == '"':
            buf.append(" ")
            i += 1
            while i < n and text[i] != "\n":
                if text[i] == "\\" and i + 1 < n:
                    buf.append(" ")
                    buf.append(" ")
                    i += 2
                    continue
                if text[i] == '"':
                    buf.append(" ")
                    i += 1
                    break
                buf.append(" ")
                i += 1
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


def _inline_cfg_test_block_lines(lines: list[str]) -> set[int]:
    """Line indices covered by an inline `#[cfg(test)] mod ... { }` block.

    Those test attributes belong to `verify_no_inline_cfg_test.py`, which
    reports the block itself.  Reporting them here as well would count one
    mistake twice.
    """
    inside: set[int] = set()
    total = len(lines)
    index = 0
    while index < total:
        if not CFG_TEST.match(lines[index]):
            index += 1
            continue
        # The module declaration may be separated from the cfg attribute by
        # `#[path = ...]` (the sanctioned include form) or by other
        # attributes.
        cursor = index + 1
        saw_path_attr = False
        mod_line: str | None = None
        while cursor < total and cursor <= index + 8:
            nxt = lines[cursor]
            stripped = nxt.strip()
            if not stripped:
                cursor += 1
                continue
            if stripped.startswith("#["):
                if PATH_ATTR.match(nxt):
                    saw_path_attr = True
                cursor += 1
                continue
            if stripped.startswith("pub ") or stripped.startswith("//"):
                cursor += 1
                continue
            mod_line = nxt
            break
        if mod_line is None or not MOD_BLOCK.match(mod_line) or saw_path_attr:
            index += 1
            continue
        # Block extent, by brace counting on the masked copy.
        depth = 0
        end = cursor
        for j in range(cursor, total):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0:
                end = j + 1
                break
        else:
            end = total
        for k in range(index, min(end, total)):
            inside.add(k)
        index = max(end, index + 1)
    return inside


def _governs_fn(lines: list[str], index: int, attr_end: int) -> bool:
    """True when the attribute at `index` governs a function item.

    `#[test]` is only meaningful on a fn, so requiring one keeps an
    attribute that merely mentions `test` out of the report.
    """
    rest = lines[index][attr_end:].strip()
    if rest:
        return bool(FN_ITEM.match(rest))
    cursor = index + 1
    while cursor < len(lines) and cursor <= index + 8:
        stripped = lines[cursor].strip()
        if not stripped or stripped.startswith("#["):
            cursor += 1
            continue
        return bool(FN_ITEM.match(stripped))
    return False


def audit_one(path: Path, root: Path | None = None) -> list[str]:
    """Report bare test attributes in one production file."""
    path = Path(path)
    root = Path(root) if root is not None else _infer_root(path)
    if path.suffix != ".rs":
        return []
    if _exempt_path(path, root):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = _mask(text)
    inside_block = _inline_cfg_test_block_lines(lines)
    out: list[str] = []
    for index, line in enumerate(lines):
        if index in inside_block:
            continue
        match = TEST_ATTR.search(line)
        if not match:
            continue
        if not _governs_fn(lines, index, match.end()):
            continue
        name = re.sub(r"\s+", "", match.group(1))
        try:
            location = path.relative_to(root)
        except ValueError:
            location = path
        out.append(
            f"{location}:{index + 1}: bare `#[{name}]` in a production file — "
            "move the test to <crate>/tests/ (§14.4)"
        )
    return out


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(
            "error: usage: verify_no_test_in_production.py [ROOT] [--file PATH]",
            file=sys.stderr,
        )
        return 2
    if "--file" in args:
        root = Path(args[0]).resolve()
        path = Path(args[args.index("--file") + 1]).resolve()
        found = audit_one(path, root)
        for line in found:
            print(line)
        return 1 if found else 0
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    total: list[str] = []
    for path in sorted(root.rglob("*.rs")):
        if any(part in EXEMPT_DIRS for part in path.parts):
            continue
        total += audit_one(path, root)
    for line in total[:20]:
        print(line)
    print(
        f"=== bare #[test] in production (§14.4): {len(total)} violation(s) ==="
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
