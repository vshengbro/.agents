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
  * `macro_rules!` bodies and `quote!` / `quote_spanned!` bodies. The tokens
    inside are *emitted* into the downstream crate that expands the macro, so
    they must stay fully qualified — a root import in the defining crate
    never reaches the expansion site (std-macro-extensions and lombok-macros
    are the live cases, 2026-10-09).

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
#
# The char-literal alternative matches EXACTLY one character or escape:
# with `(?:\\.|[^'\\])*` a lifetime apostrophe (`'a`, `'_`) pairs with the
# next quote far away and blanks real code between them (measured: 27 of 203
# hits on ctares were being silently re-swallowed downstream, 2026-10-09).
# Raw strings need a backreference: content runs until a quote followed by the
# SAME number of `#` (`r#"{"a":1}"#`); without it a JSON fixture's inner quote
# opens a phantom string.
STRING_LITERAL = re.compile(
    r'b?r(#*)"(?:.*?)"\1'  # raw string / raw byte string
    r"|b?\"(?:\\.|[^\"\\])*\""  # normal / byte string
    r"|b?'(?:\\.|[^'\\])'",  # char / byte literal: exactly one char or escape
    re.S,
)


def iter_rs(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _blank_macro_token_bodies(blanked: str) -> str:
    """Blank `macro_rules!` / `quote!` / `quote_spanned!` bodies.

    Runs on text whose string/char literals are ALREADY blanked, so a `quote!`
    mentioned inside a string is invisible here, and braces inside macro-body
    strings no longer exist to disturb the balanced scan.
    """
    spans: list[tuple[int, int]] = []
    pairs = {"(": ")", "{": "}", "[": "]"}
    for m in re.finditer(r"(?:macro_rules!\s*\w+|quote!|quote_spanned!)\s*([({\[])", blanked):
        stack: list[str] = []
        i = m.end(1) - 1
        while i < len(blanked):
            c = blanked[i]
            if c in pairs:
                stack.append(pairs[c])
            elif stack and c == stack[-1]:
                stack.pop()
                if not stack:
                    spans.append((m.end(1) - 1, i + 1))
                    break
            elif c in ")}]":
                break  # malformed: bail without a span
            i += 1
    if not spans:
        return blanked
    chars = list(blanked)
    for s, e in spans:
        for i in range(s, e):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def check_file(path: Path, label: str) -> list[str]:
    """Violations in one file, labelled `label` for the message."""
    if path.name in TOP_LEVEL:
        return []
    text = path.read_text(errors="ignore")
    # Blank string/char literals over the WHOLE file (multi-line strings span
    # lines; per-line blanking flags their interior lines, which the rule
    # exempts). Newlines are preserved so reported line numbers stay exact.
    blanked = STRING_LITERAL.sub(lambda s: re.sub(r"[^\n]", " ", s.group(0)), text)
    blanked = _blank_macro_token_bodies(blanked)
    found: list[str] = []
    for number, (line, line_blank) in enumerate(
        zip(text.splitlines(), blanked.splitlines()), 1
    ):
        if USE_LINE.match(line):
            continue
        code = line_blank.split("//", 1)[0]
        if TRAIT_FMT_RETURN.search(code):
            continue
        for m in QUALIFIED.finditer(code):
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
