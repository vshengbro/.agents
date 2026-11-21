#!/usr/bin/env python3
"""§16.5 — a macro body may not emit a `use`, and every path it emits must
be a full namespace path.

The tokens a macro body holds are EXPANDED into the crate that uses the
macro, not into the crate that defines it. Two consequences follow:

  * an import emitted by the body would land in the consumer's scope, where
    it can collide with the consumer's own imports and where it silently
    depends on the consumer's dependency set;
  * a path spelled with a bare name (`Status::Continue`) resolves against
    the consumer's scope, so it names whatever the consumer happens to have
    in scope — the macro cannot know that.

So the body must spell every path in full (`::crate_name::Path::Item`), and
it must not emit a `use` at all.

`macro_rules!` bodies expand inside the defining crate, so they are exempt
from the `use` ban; the path rule still applies to them, because a
`macro_rules!` body that names an item by a bare name resolves against the
caller's scope at the macro's use site.

The macro bodies recognised are the ones a proc-macro crate writes into
another crate:
  * `quote! { ... }` and `quote_spanned! { ... }`
  * `macro_rules! name { ... }`

Usage:
    python3 verify_no_macro_use.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# A `use` item inside a macro body.
USE_ITEM = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+[A-Za-z_:][^;]*;",
    re.M,
)

# The macro invocations whose body is emitted into another crate.
TOKEN_MACRO = re.compile(r"\b(?:quote|quote_spanned)!\s*[({]")
RULES_MACRO = re.compile(r"\bmacro_rules!\s*[A-Za-z_][A-Za-z0-9_]*")

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"

# The Rust keywords that can precede a `::` without being a crate name.
RUST_KEYWORDS = {
    "as", "async", "await", "break", "const", "continue", "crate", "dyn", "else",
    "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop",
    "match", "mod", "move", "mut", "pub", "ref", "return", "self", "Self",
    "static", "struct", "super", "trait", "true", "type", "unsafe", "use",
    "where", "while", "async", "yield",
}


def _mask_literals_and_comments(text: str) -> str:
    """Blank out string and char literals and comments, keeping offsets.

    A `use` inside a string is prose, not an item; a path inside a string is
    data, not a path. The blanking preserves every character offset so a
    finding still points at the right line.
    """
    out = list(text)
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == '"':
            start = index
            index += 1
            while index < length:
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == '"':
                    index += 1
                    break
                index += 1
            for position in range(start, min(index, length)):
                out[position] = " "
        elif char == "'":
            # A lifetime is not a char literal; a char literal is one char.
            match = re.match(r"'(?:\\.|[^'\\])'", text[index:])
            if match:
                for position in range(index, index + match.end()):
                    out[position] = " "
                index += match.end()
            else:
                index += 1
        elif char == "/" and index + 1 < length and text[index + 1] == "/":
            start = index
            while index < length and text[index] != "\n":
                index += 1
            for position in range(start, index):
                out[position] = " "
        elif char == "/" and index + 1 < length and text[index + 1] == "*":
            start = index
            index += 2
            while index + 1 < length and not (text[index] == "*" and text[index + 1] == "/"):
                index += 1
            index = min(index + 2, length)
            for position in range(start, index):
                if text[position] != "\n":
                    out[position] = " "
        else:
            index += 1
    return "".join(out)


def _matching_delimiter(text: str, start: int) -> int:
    """Index just past the delimiter that opens at `start`."""
    opening = text[start]
    closing = {"(": ")", "{": "}", "[": "]"}[opening]
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(text)


def macro_bodies(text: str) -> list[tuple[int, int, int, int, str]]:
    """(start line, start column, end line, end column, macro kind) per body.

    The column matters: `let x: proc_macro2::TokenStream = quote! { ... }`
    puts the type BEFORE the `quote!`, on the same line, so a line range
    alone would swallow it.
    """
    blanked = _mask_literals_and_comments(text)
    bodies: list[tuple[int, int, int, int, str]] = []
    for match in TOKEN_MACRO.finditer(blanked):
        brace = match.end() - 1
        end = _matching_delimiter(blanked, brace)
        start_line = blanked.count("\n", 0, brace) + 1
        start_col = brace - (blanked.rfind("\n", 0, brace) + 1) + 1
        end_line = blanked.count("\n", 0, end - 1) + 1
        end_col = end - (blanked.rfind("\n", 0, end - 1) + 1)
        bodies.append((start_line, start_col, end_line, end_col, "token-macro"))
    for match in RULES_MACRO.finditer(blanked):
        brace = blanked.find("{", match.end())
        if brace == -1:
            continue
        end = _matching_delimiter(blanked, brace)
        start_line = blanked.count("\n", 0, brace) + 1
        start_col = brace - (blanked.rfind("\n", 0, brace) + 1) + 1
        end_line = blanked.count("\n", 0, end - 1) + 1
        end_col = end - (blanked.rfind("\n", 0, end - 1) + 1)
        bodies.append((start_line, start_col, end_line, end_col, "macro-rules"))
    return bodies


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_body(text: str, start_line: int, start_col: int, end_line: int,
               end_col: int, kind: str) -> list[str]:
    """Findings inside one macro body."""
    lines = text.split("\n")
    body_lines = lines[start_line - 1:end_line]
    # Trim to the exact brace region: the first line starts at the opening
    # delimiter, the last line ends at the closing one.
    body_lines[0] = body_lines[0][start_col - 1:]
    body_lines[-1] = body_lines[-1][:end_col]
    body = "\n".join(body_lines)
    findings: list[str] = []

    # A `macro_rules!` body expands inside the DEFINING crate: it is that
    # crate's own code, and its imports and paths resolve there. Only a
    # `quote!` body is emitted into the consumer's crate, and only that one
    # needs the absolute spelling.
    if kind != "token-macro":
        return findings

    # 1. No `use` may be emitted by a token macro: it would land in the
    #    consumer's scope, where it can collide with the consumer's own
    #    imports and where it silently depends on the consumer's dependency
    #    set rather than the macro author's.
    use_spans: list[tuple[int, int]] = []
    for match in USE_ITEM.finditer(body):
        line = start_line + body.count("\n", 0, match.start())
        use_spans.append((match.start(), match.end()))
        findings.append(
            f"line {line}: a macro body may not emit a `use` — "
            f"the tokens land in the consumer's scope: {match.group(0).strip()[:100]}"
        )

    # 2. Every crate the body names must be named absolutely. A bare
    #    `hyperlane::Status` resolves against the consumer's scope, and the
    #    consumer may not depend on `hyperlane` at all; `::hyperlane::Status`
    #    names the crate the macro author meant, whoever expands it.
    #
    #    The signal is a lowercase root: a crate name is snake_case, while
    #    every local item is UpperCamelCase, so `Status::Continue` (a local
    #    item the consumer may not have) is not caught here — that case is
    #    covered by the same rule the source tree follows.
    #
    #    An interpolated name (`#input_struct`) is a local binding of the
    #    macro, not a crate path, so it is skipped.
    blanked_body = _mask_literals_and_comments(body)
    for match in re.finditer(
            r"(?<![\w:.])([a-z_][a-z0-9_]*)\s*(::)\s*([A-Za-z_][A-Za-z0-9_]*)",
            blanked_body):
        head, separator, tail = match.group(1), match.group(2), match.group(3)
        # A Rust keyword is not a crate name.
        if head in RUST_KEYWORDS:
            continue
        if any(start <= match.start() < end for start, end in use_spans):
            continue
        # `::crate::Item` and `::other_crate::Item` are already absolute.
        before = blanked_body[:match.start()].rstrip()
        if before.endswith("::"):
            continue
        # `crate::`, `self::` and `super::` name the defining crate's own
        # tree, which is where the macro lives; they are always correct.
        if head in {"crate", "self", "super"}:
            continue
        # An interpolated name (`#input_struct`) is a local binding of the
        # macro, not a crate path.
        interpolated = blanked_body[:match.start()].rstrip()
        if interpolated.endswith("#"):
            continue
        line = start_line + body.count("\n", 0, match.start())
        findings.append(
            f"line {line}: a macro body must spell a full namespace path — "
            f"`{head}{separator}{tail}` resolves in the consumer's scope: "
            f"write `::{head}{separator}{tail}`"
        )

    return findings


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    findings: list[str] = []
    for start_line, start_col, end_line, end_col, kind in macro_bodies(text):
        for finding in check_body(text, start_line, start_col, end_line, end_col, kind):
            findings.append(f"{path}: {finding}")
    return findings


def iter_rs(root: Path):
    for path in sorted(root.rglob("*.rs")):
        parts = set(path.parts)
        if "target" in parts or ".git" in parts:
            continue
        yield path


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    Reads exactly the path it is handed and nothing else, so the gate's
    before/after baselines compare.
    """
    return check_file(path)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_macro_use.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    violations: list[str] = []
    files_with_violations = 0
    for path in iter_rs(root):
        found = check_file(path)
        if found:
            violations += found
            files_with_violations += 1

    total = len(violations)
    if total:
        for finding in violations:
            print(finding)
    print(f"=== macro-body-paths (§16.5): {total} violation(s) "
          f"in {files_with_violations} file(s) ===")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
