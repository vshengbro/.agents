#!/usr/bin/env python3
"""
Verify the top-level import rule for the standard library: a sub-file must not
name a `std::` path directly, because the import belongs in the crate's
`lib.rs` (or, for a test directory that has no lib, in its outermost
`mod.rs`) and reaches the sub-file through `use super::*;`.

    std::fs::create_dir_all(p)   ->  create_dir_all(p), imported in lib.rs
    std::borrow::Cow<'_, str>    ->  Cow<'_, str>

Exempt, with a reason rather than by accident:

  * the crate's own `lib.rs` / `main.rs`, which is where the import lives
  * `use` lines themselves, and comment tails - they name paths, they do not
    consume them
  * the return type of a `Display`/`Debug` impl's `fn fmt`. That signature is
    dictated by the trait, the crate already has its own `FmtResult` type that
    a bare import would shadow, and 6.5 forbids renaming an import with `as`,
    so there is no spelling that satisfies all three constraints at once.
    cli/src/error/impl.rs is the live case.
  * string and char literals. A code generator has to spell the import line
    it writes into the crate it generates, and a test has to spell the import
    line it asserts on; hoisting either into lib.rs removes nothing. The rule
    is about a path the crate *consumes*. engine/src/emit/const.rs and its
    matching assertion in engine/tests/generate/fn.rs are the live case.

Usage:
    python3 verify_no_qualified_std_path.py [ROOT]
"""

import re
import sys
from pathlib import Path

# A `std::` path being *consumed*: a call, an associated item, or a type in a
# position other than the one exempted above.
QUALIFIED = re.compile(r"(?<![\w:])std::[a-z_]\w*(::\w+)+")
USE_LINE = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?use\b")
TRAIT_FMT_RETURN = re.compile(
    # `[\w:]*Formatter` rather than `\w*Formatter`: the parameter is written
    # `&mut std::fmt::Formatter<'_>` BEFORE the fix and `&mut Formatter<'_>`
    # after it.  `\w*` cannot cross the `::`, so the original pattern only
    # ever matched the already-shortened spelling -- i.e. the exemption was
    # unreachable for exactly the state it exists to excuse, and every
    # `fn fmt` signature was reported until the parameter was shortened,
    # which the rule itself asks for.  Chicken-and-egg.
    r"fn\s+fmt\s*\(\s*&\s*self\s*,\s*\w+\s*:\s*&\s*mut\s+[\w:]*Formatter\s*<'_\s*>\s*\)"
    r"\s*->\s*std::fmt::Result"
)
TOP_LEVEL = {"lib.rs", "main.rs", "build.rs"}
SKIP_DIRS = {"target", ".git"}

# A string or char literal, raw or not. A `std::` path *inside* one is text the
# crate emits, not a path it consumes: a code generator that writes
# `use std::rc::Rc;` into the crate it generates has to spell it somewhere,
# and hoisting it into lib.rs would not remove it. This is the same category
# as the `fn fmt` exemption above - the rule is about *consuming* a path.
STRING_LITERAL = re.compile(
    r"r?#*\"(?:\\.|[^\"\\])*\"#*|r?'(?:\\.|[^'\\])*'",
    re.S,
)


def iter_rs(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def check_file(path: Path, label: str) -> list[str]:
    """Violations in one file, labelled `label` for the message."""
    if path.name in TOP_LEVEL:
        return []
    found: list[str] = []
    for number, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        if USE_LINE.match(line):
            continue
        code = line.split("//", 1)[0]
        if TRAIT_FMT_RETURN.search(code):
            continue
        for m in QUALIFIED.finditer(STRING_LITERAL.sub(lambda s: " " * len(s.group(0)), code)):
            found.append(
                f"{label}:{number}: `{m.group(0)}` names the standard library "
                f"directly - import it in the outermost lib.rs / mod.rs"
            )
    return found


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    Reads exactly the path it is handed and nothing else. The gate
    materialises a `<file>.head-baseline` copy for each staged file and
    compares before against after, so a verifier that re-walks the worktree
    would read the same bytes on both sides and always report a delta of 0.
    """
    return check_file(path, path.name)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_qualified_std_path.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    violations: list[str] = []
    files_with_violations = 0
    for path in iter_rs(root):
        found = check_file(path, str(path.relative_to(root)))
        if found:
            violations += found
            files_with_violations += 1

    total = len(violations)
    if total:
        print(f"=== qualified-std-path: {total} violation(s) in {files_with_violations} file(s) ===")
        for line in violations:
            print(f"  {line}")
        return 1
    print(f"\n=== qualified-std-path: 0 violation(s) in 0 file(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
