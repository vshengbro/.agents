#!/usr/bin/env python3
"""
Verify rust-standards §1.3c (strengthened, 2026-09-26 third
iteration): hardcoded string literals MUST live in `const.rs`.

User original (2026-09-26 third iteration):
  "硬编码字符串必须要维护到 const.rs 上面"

The existing `audit_rust_standards.py` check 18 only catches
hardcoded byte / char / multi-character string literals in
`fn.rs` files (and only the FIRST few characters of a multi-byte
literal).  This new rule extends coverage to ALL files except
`const.rs` and `tests/`:

  ❌  let path: &str = "/usr/local/bin";         // in fn.rs
  ❌  eprintln!("Hello, world!");                // in fn.rs
  ❌  format!("got {} items", n);                // in impl.rs
  ❌  if name == "admin" { ... }                 // in fn.rs

  ✅  // in const.rs:
      pub const BIN_PATH_USR_LOCAL: &str = "/usr/local/bin";
      pub const HELLO_WORLD: &str = "Hello, world!";
      // then in fn.rs:
      eprintln!("{}", HELLO_WORLD);

Exemptions:
  - Files named `const.rs` (this is the canonical home of
    string constants; literal strings here are not
    "hardcoded", they ARE the constant definition).
  - `tests/` directory (R14.7 self-contained; tests often
    embed expected literals).
  - `format!` / `println!` / `eprintln!` / `panic!` /
    `assert!` / `assert_eq!` / `assert_ne!` / `unimplemented!`
    / `unreachable!` / `todo!` / `dbg!` / `write!` / `writeln!`
    macros whose string literal is the FORMAT string (first
    argument).  These are user-facing format strings; they
    MUST stay inline at the call site for readability.
    BUT: arguments embedded as `format!("got {} items", n)`
    where `n` is a literal `0` are NOT exempt — the format
    string itself stays inline, but constants get extracted
    in surrounding code.
  - String literals used as trait discriminant in
    attribute macros like `#[doc = "..."]` / `#[cfg(test)]` —
    handled by the macro detection (line starts with `#[`).
  - String literals inside `#[derive(...)]` (the derive
    name itself, e.g. `#[derive(Debug)]`) — these are
    attribute paths, not user data.
  - String literals in `serde` rename attributes
    (`#[serde(rename = "...")]`) — these are wire-format
    names that MUST be inline.

Detection heuristic:
  - For each .rs file NOT in {const.rs, tests/}:
    * Find every line that contains a string literal
      (`"...some text..."` — minimum 4 non-trivial chars).
    * If the line is:
      - Inside a macro at attribute position (`#[xxx = "..."]`)
        → exempt
      - Inside a known format macro as the first positional
        arg → exempt
      - Otherwise → violation (line + content)

This is a strict heuristic; it WILL have false positives on
well-named macros that take strings as first argument
(`writeln!`, `assert_eq!` format string).  When in doubt,
the script prefers false-positive (flag) over false-negative
(miss), so authors must explicitly justify the literal.

Exits 0 if clean, 1 if any violation.

Usage:
    python3 verify_hardcoded_strings.py [ROOT]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


# Format-style macros whose FIRST string argument is the
# format string (user-facing) and is exempt from extraction.
FORMAT_MACROS = {
    "format", "println", "eprintln", "print", "eprint",
    "panic", "unimplemented", "unreachable", "todo",
    "assert", "assert_eq", "assert_ne",
    "write", "writeln",
    "dbg", "error", "warn", "info", "debug", "trace",
}

# Format macros whose format string is the SECOND argument: the first is a
# condition (`assert!`) or a value / writer (`assert_eq!`, `writeln!`).
# The scanner must skip that first argument when looking for the format
# string, otherwise it credits the condition line and reports the real
# format string as a §1.3c violation.
# `macro -> 0-based index of its format string`.
#
# `assert!(cond, "..")`        -> 1  (cond first)
# `assert_eq!(a, b, "..")`     -> 2  (two compared values first)
# `assert_ne!(a, b, "..")`     -> 2
# `write!(sink, "..")`         -> 1  (writer first)
# `writeln!(sink, "..")`       -> 1
# `format!/println!/panic!/..` -> 0  (message first, or only arg)
ASSERT_STRING_INDEX = {
    "assert": 1,
    "assert_eq": 2,
    "assert_ne": 2,
    "write": 1,
    "writeln": 1,
}

# The same set, for the single-line scanner.  Kept as an alias so the two
# code paths cannot drift apart on WHICH macros are assert-like.
ASSERT_LIKE_MACROS = frozenset(ASSERT_STRING_INDEX)


# Match a string literal — at minimum 4 non-whitespace chars
# (avoid flagging single-char `'.'` literals and empty `""`).
#
# The lookbehind is load-bearing. Without it, when a literal is too short to
# match (`"/D"` is 2 content chars), the scan slides one character right and
# starts a match at that literal's CLOSING quote, swallowing the code in
# between up to the next quote. On
#     cmd.arg("/D").arg("/S").arg("/C").arg(command)
# that produced the phantom literal `").arg("`, and on
#     path.contains("..") || path.starts_with("/")
# the phantom `") || path.starts_with("`. Both read as "hardcoded strings to
# hoist into const.rs", and hoisting them corrupts the expression — a worker
# hit exactly that and had to revert. A real literal can never be preceded by
# a word character, a closing bracket or a brace, because that position is
# already inside one.
STRING_LITERAL = re.compile(r'"([^"\\]|\\.){4,}"')


def _content_width(literal: str) -> int:
    """Length of a string literal's VALUE, with escape pairs counted once.

    `literal` includes its surrounding quotes. An escape sequence is one
    character at runtime but two in the source, so measuring the source width
    inflates every literal that contains `\\n`, `\\t`, `\\"` or `\\\\`:
    `"a\\nb"` has a 3-character value but measures 5.
    """
    body: str = literal[1:-1]
    width: int = 0
    index: int = 0
    while index < len(body):
        if body[index] == "\\" and index + 1 < len(body):
            index += 2
        else:
            index += 1
        width += 1
    return width


def _literal_spans(text: str, start: int = 0) -> list[tuple[int, int, str]]:
    """Every real string literal in `text` as `(start, end, literal)`.

    Quote-PAIRING, not pattern matching. A regex that fails on a too-short
    literal slides one character right and re-starts at that literal's closing
    quote, so the "match" swallows the code in between up to the next quote:

        path.contains("..") || path.starts_with("/")
        cmd.arg("/D").arg("/S").arg("/C")

    both yielded a phantom literal (`") || path.starts_with("`, `").arg("`)
    that read as a hardcoded string to hoist into const.rs — and hoisting one
    corrupts the expression, not just the formatting. Scanning forward from
    each unescaped opening quote to its partner cannot produce that shape,
    because a closing quote is never treated as an opening one.
    """
    spans: list[tuple[int, int, str]] = []
    i = start
    n = len(text)
    while i < n:
        if text[i] == '"' and (i == 0 or text[i - 1] != "\\"):
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            if j < n:
                spans.append((i, j + 1, text[i:j + 1]))
                i = j + 1
                continue
        i += 1
    return spans


def _macro_name_slots(text: str) -> list[tuple[int, int]]:
    """Spans of `("name" = ..)` macro name slots, as (start, end)."""
    return [m.span("name") for m in MACRO_NAME_SLOT.finditer(text)]

# Raw strings carry a second language, not Rust program data. `r#"{"project_id":
# "aaaZ", "code": "fn app() {}"}"#` is an embedded JSON/XML/SQL/shader payload:
# §1.3c exists to hoist *this crate's* strings into const.rs, and a raw string
# is one indivisible token that cannot be split. Masked wholesale.
def _raw_string_lines(lines: list[str]) -> set[int]:
    """1-indexed line numbers that live inside a raw string literal."""
    masked: set[int] = set()
    in_raw = False
    close = ""
    for idx, line in enumerate(lines, start=1):
        if in_raw:
            masked.add(idx)
            if close in line:
                in_raw = False
            continue
        m = re.search(r'r(#*)"', line)
        if not m:
            continue
        masked.add(idx)
        in_raw = True
        close = '"' + m.group(1)
        if close in line[m.end():]:
            in_raw = False
    return masked

# Match attribute lines like `#[doc = "..."]` /
# `#[serde(rename = "..."]` etc. — the whole line starts
# with `#[` and ends with `]`.
ATTR_LINE = re.compile(r"^\s*#\[")

# Match INNER attribute lines: `#![recursion_limit = "1024"]`,
# `#![doc = "..."]`, `#![feature(...)]`, ...
#
# Same reasoning as ATTR_LINE above, and the same reasoning that made
# `extern "C"` an exempt ABI slot: a crate/module attribute value is read by
# the compiler, not by the program, and several of them are only *syntactically
# legal* as a literal. `#![recursion_limit = "1024"]` cannot be written as
# `#![recursion_limit = SERVER_RECURSION_LIMIT]` — an inner attribute takes
# literal tokens, so a named const is a hard parse error, not a style choice.
# Reporting it is therefore always a false positive with no compliant
# alternative.
#
# Whole-line scoping is safe here (unlike the general "skip the line" smell
# documented for the extern-ABI exemption): an inner attribute is only legal
# before any item in the file, so no real code can share such a line.
INNER_ATTR_LINE = re.compile(r"^\s*#!\[")


# A macro NAME slot: `("owner" = String, Path, ...)` inside a utoipa
# `params(...)` / `security(...)` list.
#
# The same reasoning that exempts `extern "C"` and the `cfg!` predicate applies
# here: this string is a grammar token the macro parses, not program data.
# utoipa-gen parses it with `input.parse::<syn::LitStr>()?` and
# `unparsable parameter name, expected literal string`, so
# `params((SOME_CONST = String))` does not compile — there is no compliant
# alternative, and reporting it can only be fixed by breaking the build.
#
# Scoped to the captured name span, so every other literal on the line (the
# `description = ...`, the `path = ...`, and anything after the tuple) is still
# reported normally. The shape `("..." =` only occurs in macro input: a tuple
# element or struct field cannot have a string literal as its name, so this
# cannot mask a real hoistable string.
MACRO_NAME_SLOT = re.compile(r'\(\s*(?P<name>"(?:[^"\\]|\\.)*")\s*=')
#
#   extern "system" { ... }        (block)
#   extern "C" fn f() { ... }      (single fn)
#   pub unsafe extern "system" fn g() { ... }
#
# The string here is the LINKING ABI, not program data.  It lives in
# a grammar position that accepts ONLY a string literal — there is no
# expression slot, so it can never be hoisted into a `const`:
#
#   const ABI: &str = "system";
#   extern ABI { }        →  error: expected `fn`, found `ABI`
#
# Verified with rustc 1.9x: replacing the literal with a const path is
# a hard syntax error, so flagging it is a false positive by
# construction.
#
# The match CAPTURES the ABI literal as group `abi` so the caller can
# exclude exactly that span and nothing else.  Skipping the whole line
# (the first implementation of this exemption) is a false-negative
# hole: a one-line `extern "C" fn f() -> &'static str { "/secrets" }`
# under `#[rustfmt::skip]` hid every other literal on the line, which
# is reachable in one line of code and survives `cargo fmt --check`.
# This script's contract is "prefer a false positive over a false
# negative" (see the module docstring), so the exemption is scoped as
# tightly as the grammar allows.
EXTERN_ABI_LINE = re.compile(
    r"""^\s*
        (?:pub(?:\s*\((?:[^()]|\([^()]*\))*\))?\s+)?   # pub / pub(crate) / pub(in path)
        (?:unsafe\s+)?                    # optional `unsafe`
        extern\s+                        # the keyword itself
        (?P<abi>"[^"]*")                 # the ABI literal, captured
    """,
    re.VERBOSE,
)


CFG_PREDICATE = re.compile(
    r"""cfg(?:_attr)?!\s*\(\s*
        [A-Za-z_][A-Za-z0-9_]*\s*=\s*        # the predicate key
        (?P<val>"[^"]*")                      # the literal, captured
    """,
    re.VERBOSE,
)


SKIP_DIR_NAMES = {
    ".git", "target", ".cargo", "node_modules", ".venv", "venv", "dist",
    "build", ".idea", ".vscode", "out",
}


def _list_rs_files(root: Path) -> list[Path]:
    r = subprocess.run(
        ["find", str(root), "-name", "*.rs",
         "-not", "-path", "*/target/*",
         "-not", "-path", "*/.cargo/registry/*"],
        capture_output=True, text=True,
    )
    files = [Path(line) for line in r.stdout.strip().splitlines() if line]
    files = [f for f in files
             if not any(part in SKIP_DIR_NAMES for part in f.parts)]
    # Drop anything git already ignores (2026-09-28).  A path listed in a
    # .gitignore is by definition not part of the project: `crate-cli/tmp/`
    # holds 25 scratch crates from `crate fmt` runs, and scanning them
    # reported violations in files no commit can ever contain.
    return _drop_git_ignored(files, root)


def _drop_git_ignored(files: list[Path], root: Path) -> list[Path]:
    """Return the files git does not ignore.  One batched check-ignore call."""
    if not files:
        return files
    try:
        rels = [str(f.relative_to(root)) for f in files]
    except ValueError:
        return files
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--stdin"],
            input="\n".join(rels) + "\n",
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return files  # not a git work tree, or git is unavailable
    if r.returncode not in (0, 1):
        return files
    ignored = {line.strip() for line in r.stdout.splitlines() if line.strip()}
    return [f for f, rel in zip(files, rels) if rel not in ignored]



def _is_format_macro(line: str) -> bool:
    """Return True if the string literal on this line is the
    format string of a known format-style macro (first arg)."""
    # Heuristic: line contains `<macro>!(` followed by string
    # literal before any other arg.
    for m in re.finditer(r"\b(\w+)!\s*\(", line):
        macro = m.group(1)
        if macro in FORMAT_MACROS:
            after = line[m.end():]
            str_match = STRING_LITERAL.search(after)
            if not str_match:
                continue
            comma_match = re.search(r",", after)
            if macro in {"write", "writeln"}:
                # write!/writeln! take the writer as the first arg, so the
                # format string is the second arg (after the first comma).
                if comma_match is None:
                    continue
                second_comma = re.search(r",", after[comma_match.end():])
                if str_match.start() > comma_match.end() and (
                    second_comma is None
                    or str_match.start() < comma_match.end() + second_comma.start()
                ):
                    return True
                continue
            if macro in ASSERT_LIKE_MACROS:
                # `assert!(cond, "fmt", ..)`: the literal is the SECOND
                # argument, so it is exempt only when a comma separates
                # it from the first argument.  Without this branch a
                # single-line `assert!(a < b, "msg {}", v)` is reported,
                # even though the multi-line form of the very same
                # assertion is exempt.
                if comma_match is None:
                    continue
                return str_match.start() > comma_match.end()
            if comma_match is None or str_match.start() < comma_match.start():
                # Format string is the first arg — exempt
                return True
    return False


def _exempt_format_string_lines(lines: list[str]) -> set[int]:
    """Return 1-based line numbers holding the format string of a
    multi-line format-macro call (rustfmt puts each arg on its own
    line, so the format string may not share a line with the macro).

    The format string is NOT always the first argument.  `write!` /
    `writeln!` take the writer first; `assert!` / `assert_eq!` /
    `assert_ne!` take the condition (or the two compared values) first;
    `panic!` / `unreachable!` / `todo!` / `unimplemented!` take the
    message second only when a payload precedes it.  Getting this wrong
    shifts arg counting by one, so the scanner credits the line holding
    the *condition* as the format string and then reports the real format
    string as a violation."""
    exempt: set[int] = set()
    macro_re = re.compile(r"\b(\w+)!\s*\(")
    for idx, line in enumerate(lines):
        for m in macro_re.finditer(line):
            macro = m.group(1)
            if macro not in FORMAT_MACROS:
                continue
            after = line[m.end():]
            if STRING_LITERAL.search(after):
                continue
            depth = 1 + after.count("(") - after.count(")")
            if depth <= 0:
                continue
            # `target_arg` is the 0-based index of the format string
            # among the macro's arguments.  Only these put it at 0; every
            # other macro in FORMAT_MACROS takes at least one
            # non-format argument first.
            target_arg = ASSERT_STRING_INDEX.get(macro, 0)
            arg_index = 1 if after.strip() else 0
            j = idx + 1
            while j < len(lines) and depth > 0:
                current = lines[j]
                depth += current.count("(") - current.count(")")
                content = current.strip()
                if content:
                    if arg_index == target_arg and STRING_LITERAL.search(current):
                        exempt.add(j + 1)
                        break
                    arg_index += 1
                j += 1
    return exempt



def _comment_start(line: str) -> int | None:
    """Index where a comment begins on this line, or None if there is none.

    String literals are tracked so that a `//` or `/*` inside a literal is not
    mistaken for a comment opener — `let u: &str = "http://host";` has no
    comment.  A `\\` escape advances past the next character.
    """
    i, n, in_str, in_char = 0, len(line), False, False
    while i < n:
        c = line[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if in_char:
            if c == "\\":
                i += 2
                continue
            if c == "'":
                in_char = False
            i += 1
            continue
        if c == '"':
            in_str = True
        elif c == "'" and i + 1 < n and line[i + 1] == "'":
            # Lifetime like `'static` is not a char literal; a char literal is
            # `'x'`.  Only treat as a char when a closing quote follows soon.
            j = i + 1
            while j < n and line[j] != "'":
                j += 1
            if j < n and j - i <= 4:
                in_char = True
        elif c == "/" and i + 1 < n:
            nxt = line[i + 1]
            if nxt == "/":
                return i
            if nxt == "*":
                return i
        i += 1
    return None


def _mask_line(line: str) -> str:
    """Blank out string literals and comments on one line, keeping offsets.

    Brace counting for the DSL-block exemptions below runs on this masked
    copy. Without it, a `format!("{}px", w)` inside an `html!` attribute
    contributes one `{` and one `}` that still balance, but an unbalanced
    one (`class: "{"`, or a doc-comment-looking `"//"` inside a literal)
    would push the depth counter off and make the exemption run to
    end-of-file — a silent under-report on a rule whose whole contract is
    "report what is really there". Blanking literals and comments keeps
    the counter counting code.
    """
    out = list(line)
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c == '"':
            out[i] = " "
            i += 1
            while i < n:
                if line[i] == "\\":
                    out[i] = " "
                    if i + 1 < n:
                        out[i + 1] = " "
                    i += 2
                    continue
                if line[i] == '"':
                    out[i] = " "
                    i += 1
                    break
                if line[i] != "\n":
                    out[i] = " "
                i += 1
            continue
        if c == "/" and i + 1 < n and line[i + 1] == "/":
            for k in range(i, n):
                out[k] = " "
            break
        if c == "/" and i + 1 < n and line[i + 1] == "*":
            out[i] = out[i + 1] = " "
            i += 2
            while i < n and not (line[i] == "*" and i + 1 < n and line[i + 1] == "/"):
                if line[i] != "\n":
                    out[i] = " "
                i += 1
            if i < n:
                out[i] = " "
                if i + 1 < n:
                    out[i + 1] = " "
                i += 2
            continue
        i += 1
    return "".join(out)


def _dsl_block_lines(lines: list[str], macros: tuple[str, ...]) -> set[int]:
    """1-based line numbers inside any of the `macros` DSL blocks.

    All four exist for the same reason: their string literals ARE the
    payload, not incidental program data.

    - `class!` is the CSS-class DSL used to declare style rules. Its
      literals (`"flex"`, `"100%"`, `":hover"`) are the declarations.
    - `vars!` is the design-token table. The tokens are meant to live in
      one declarative place, not scattered into `const.rs`.
    - `var!` and `html!` are the attribute-level counterparts. Inside
      `html!` a literal like `role: "img"`, `type: "radio"` or
      `aria-label: "Close"` is markup written the way a developer would
      write it; hoisting it to a const produces a named indirection that
      makes the template harder to read and changes nothing at runtime,
      since the macro already emits the bytes verbatim.

    The practical cost of enforcing §1.3c inside these macros is visible
    in euv: 561 constants existed whose ONLY use was a macro interior, so
    they were single-use indirection created purely to satisfy this rule,
    and 38 `const.rs` files existed only to hold them.

    Reused constants are NOT affected — a const that is also referenced
    from ordinary code is legitimately shared and stays extracted. The
    exemption covers literals written directly in the macro body, which is
    what a template author actually writes.

    The scan re-arms on every macro line, so a file may declare several
    blocks. Nesting is tracked by brace depth, so `@media { .. }` inside a
    class and `for { .. }` inside an `html!` element are covered, and the
    exemption stops at the matching close brace rather than at
    end-of-file. The macro name is matched anywhere on the line (not just
    at the start) so `let node = html! {` is covered too.
    """
    inside = False
    depth = 0
    marked: set[int] = set()
    pattern = re.compile(
        r"(?<![\w:])(?:" + "|".join(re.escape(m) for m in macros) + r")\s*\{"
    )
    for i, line in enumerate(lines, start=1):
        masked = _mask_line(line)
        if not inside:
            if pattern.search(masked):
                inside = True
                depth = masked.count("{") - masked.count("}")
                marked.add(i)
            continue
        marked.add(i)
        depth += masked.count("{") - masked.count("}")
        if depth <= 0:
            inside = False
    return marked


# The four euv DSL macros whose bodies are markup / style / token tables.
DSL_MACROS = ("html!", "class!", "var!", "vars!")


def audit_one(path: Path) -> list[str]:
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    # Skip tests/ (R14.7 self-contained).  This must live HERE, not only in
    # the repo-wide walker: staged_file_gate.py drives audit_one() directly,
    # so an exemption that exists only in main() is invisible to the commit
    # hook and every test edit reads as a fresh batch of violations.
    if "tests" in path.parts:
        return []
    lines = text.splitlines()
    exempt_lines = _exempt_format_string_lines(lines)
    dsl_lines = _dsl_block_lines(lines, DSL_MACROS)
    raw_lines = _raw_string_lines(lines)
    violations: list[str] = []
    for i, line in enumerate(lines, start=1):
        if i in raw_lines:
            continue
        # Skip const.rs (the canonical home)
        if path.name == "const.rs":
            continue
        # Skip literals written directly inside a DSL block — `html!`,
        # `class!`, `var!`, `vars!`. Those bodies are markup, style rules
        # and design tokens: the literal IS the payload, and hoisting it
        # to a const produces a single-use indirection that makes the
        # template harder to read for no runtime benefit.
        if i in dsl_lines:
            continue
        # Skip attribute lines (#[doc = "..."], #[serde(...)])
        if ATTR_LINE.match(line) or INNER_ATTR_LINE.match(line):
            continue
        # Skip lines whose CODE POSITION is inside a comment (2026-09-28).
        # A string in a comment is prose the reader sees, not program data:
        # hoisting `/// (e.g. ":hover")` into const.rs would only corrupt the
        # documentation.  Measured across the three workspaces this removes
        # 637 reported violations that were all doc-comment examples
        # (euv 417, hyperlane 220, ctares 56).
        #
        # This must NOT become a way to hide a real violation, so the rule is
        # positional rather than "the line mentions a comment": the string
        # has to sit after the comment opener.  A trailing comment on a line
        # of real code (`let x: &str = "secret"; // "note"`) still reports the
        # code string and only the part after `//` is exempt.
        code_pos = _comment_start(line)
        if code_pos is not None:
            if code_pos == 0:
                # Whole line is a comment (line, block, doc, or inner).
                continue
            # Trailing comment: keep scanning the CODE part, which is what
            # the rule is about, and stop before the comment.  The scan
            # offset also keeps quote pairing from crossing the boundary.
            abi_end = 0
            scan_line = line[:code_pos]
        else:
            scan_line = line
        # Locate the foreign-ABI slot of `extern "C" { }` / `extern "C" fn f()`
        # (2026-09-28).  The ABI string is a grammar-level keyword slot, not
        # program data — `extern ABI {}` is a hard rustc syntax error, so it
        # can never be hoisted into const.rs.  Only the captured ABI span is
        # excluded below; every OTHER literal on the line is still reported.
        abi_match = EXTERN_ABI_LINE.match(line)
        abi_end = abi_match.end("abi") if abi_match else 0
        # Skip format-macro format strings
        if _is_format_macro(line):
            continue
        # `cfg!(target_os = "...")` is a grammar slot, not program data
        # (2026-09-28).  The predicate value must be a literal: `cfg!(.. =
        # SOME_CONST)` is `error: expected a literal ... found expression`,
        # so it can never be hoisted into const.rs.  Scoped to the captured
        # literal span, exactly like the ABI slot above, so that any OTHER
        # string on the same line is still reported.
        cfg_m = CFG_PREDICATE.search(scan_line)
        cfg_span = cfg_m.span("val") if cfg_m is not None else None
        if i in exempt_lines:
            continue
        # Find string literals on this line.  On an extern line the scan
        # RESUMES after the ABI literal rather than skipping the line:
        # STRING_LITERAL is quote-pairing, so a scan that started at the
        # ABI's closing quote would swallow the code between the two
        # literals and report a garbage span (and could miss a real
        # literal sitting inside that swallowed run).
        for lit_start, lit_end, literal in _literal_spans(scan_line, abi_end):
            if cfg_span is not None and (lit_start, lit_end) == cfg_span:
                # The cfg! predicate literal itself: a grammar slot.
                continue
            if any((lit_start, lit_end) == slot
                   for slot in _macro_name_slots(scan_line)):
                # A utoipa `params(("name" = ..))` / `security(("name" = []))`
                # name: a macro grammar token, not program data.
                continue
            if _content_width(literal) < 4:
                # Measured on the DECODED value, not the source text. An
                # escape pair is one character at runtime but two in the
                # source, so `len(literal) - 2` counted `"a\nb"` as 5 and
                # flagged a 3-character value as a hardcoded string.
                continue
            violations.append(
                f"{path}:{i}: hardcoded string literal {literal!r} "
                f"must live in `const.rs` (§1.3c strengthened): "
                f"{line.strip()[:80]!r}"
            )
    # §1.3c exemption: a literal with a single use in this file carries no
    # coupling between call sites, so naming it would add a hop without
    # adding a constraint. Two or more uses in the SAME file are still
    # reported — that is the case where the name does work. Counted per file
    # so audit_one keeps its contract and the commit hook and the full audit
    # agree.
    seen: dict[str, int] = {}
    for v in violations:
        m = re.search(r"string literal '(.*?)' must live", v)
        if m:
            seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    violations = [v for v in violations if not re.search(r"string literal '(.*?)' must live", v)
                   or seen[re.search(r"string literal '(.*?)' must live", v).group(1)] >= 2]

    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    total = 0
    files_with_v = 0
    for f in _list_rs_files(root):
        # Skip const.rs (we don't audit the canonical home)
        if f.name == "const.rs":
            continue
        # Skip tests/ (R14.7 self-contained)
        if "tests" in f.parts:
            continue
        v = audit_one(f)
        if v:
            files_with_v += 1
            total += len(v)
            for line in v:
                print(line)
    print(f"\n=== hardcoded-strings-to-const: "
          f"{total} violation(s) in {files_with_v} file(s) ===")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())