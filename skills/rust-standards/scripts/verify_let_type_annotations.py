#!/usr/bin/env python3
"""
Verify rust-standards §5.1: ALL `let` bindings MUST have explicit
type annotations (rule 6 / 2026-09-26 third iteration).

User original (2026-09-26 third iteration):
  "let 的类型必须要显示标注 (包含 let _ = )"

This is a strengthening of `verify_explicit_type_annotations.py`
(check 31) which only catches collection constructors without
type annotation.  The new rule is far broader: NO `let` binding
may omit its type.  Specifically:

  ❌  let x = 5;
  ❌  let s = "hello";
  ❌  let v = vec![1, 2, 3];
  ❌  let _ = fs::remove_dir_all(&temp_dir).await;   // user explicit
  ❌  let opt = some_fn();

  ✅  let x: u32 = 5;
  ✅  let s: &str = "hello";
  ✅  let v: Vec<u32> = vec![1, 2, 3];
  ✅  let _: Result<()> = fs::remove_dir_all(&temp_dir).await;
  ✅  let opt: Option<u32> = some_fn();

Exemptions (legitimate cases where type inference is the spec):
  - `let <pat>: binding = (Some::<T>::None | None::<T>)` — explicit
    generic annotation, no need for `:` re-statement.
  - `if let Some(x) = ...` / `while let Some(x) = ...` patterns —
    these are pattern bindings, not `let` statements.
  - Inside `tests/` directory (R14.7 self-contained).
  - `let _ = ...` is **also** banned per user explicit; we
    require `let _: T = ...`.  Rationale: `let _ = expr;`
    hides the return type from the reader and is a frequent
    source of silently dropped Result errors.  Even on discard,
    the type carries signal (the reader knows what shape is
    being discarded).

This script is the broader successor to
`verify_explicit_type_annotations.py` (check 31).  Check 31
remains as a subset-style "collection constructors specifically"
check; this script (check 33) is the comprehensive form.

Exits 0 if clean, 1 if any violation.

Usage:
    python3 verify_let_type_annotations.py [ROOT]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


# Match `let <pat> = <expr>;` where `<pat>` does NOT contain `:`
# (no type annotation).  Pattern captures the binding name.
#
# We must distinguish:
#   let x = ...;           ← violation (no type)
#   let x: u32 = ...;      ← ok (has type)
#   let mut x = ...;       ← violation
#   let mut x: u32 = ...;  ← ok
#   let _ = ...;           ← violation (per user explicit)
#   let _: T = ...;        ← ok
#   let (a, b) = ...;      ← violation (no type) — but tuple
#                             destructuring is uncommon; treat as
#                             violation so users add `: (T, U)`
#   if let Some(x) = ...;  ← NOT a `let` statement (it's a
#                             pattern guard in if/while); regex
#                             must not match.
#
# Regex: starts with `let `, followed by binding name (with optional
# `mut`), then either `: ` (type annotation present) or ` = `
# (no annotation — violation).
LET_NO_ANNOT = re.compile(
    r"^\s*let\s+(?:mut\s+)?"
    r"(?P<pat>(?:\([^)]*\))?(?:_[a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)"
    r"(?:\s*:\s*[^=]+?)?)"  # optional `: type` (non-greedy, must not consume `=`)
    r"\s*=\s*"                # the `=` after binding
)


# `let <name> = move |<params>| { ... }` — a capturing closure binding.
#
# §5.1 asks for an explicit type on every `let`, but a `move` closure's type
# is not nameable in Rust: it captures, so it is never a `fn` pointer and
# there is no syntax that spells the type out. All three "obvious" fixes fail
# to compile (measured 2026-10-01 on euv's `example/src/page/canvas` and
# `ui/src/component/nav`):
#
#   * `Box<dyn FnMut(Event)>`  -> E0507 cannot move out of a value captured
#     in an `FnMut` closure, when the binding is consumed by a macro that
#     wraps it in an inner `move` closure.
#   * `impl FnMut(Event)`      -> E0562 `impl Trait` is not allowed in the
#     type of a variable binding (arguments and return types only).
#   * `fn(..)` pointer / alias -> impossible, the closure captures.
#
# So demanding a type here is unsatisfiable rather than merely discouraged.
# The closure PARAMETERS stay covered by §5.2, which
# `verify_closure_type_annotations.py` checks independently.
#
# A closure WITHOUT `move` can usually be given a `fn(..)` pointer type and is
# therefore still reported — that boundary is deliberate. Verified on
# `macros/src/html/fn.rs`, where a non-`move` closure took
# `let push_merged: fn(&mut HtmlAttrs, ..) = |..| { .. };` cleanly.
MOVE_CLOSURE_BINDING = re.compile(
    r"^\s*let\s+(?:mut\s+)?[a-zA-Z_][a-zA-Z0-9_]*"
    r"(?:\s*:\s*[^=]+?)?"
    r"\s*=\s*move\s*\|"
)


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
    return _drop_git_ignored(files, root)

SKIP_DIR_NAMES = {
    ".git", "target", ".cargo", "node_modules", ".venv", "venv", "dist",
    "build", ".idea", ".vscode", "out",
}


def _drop_git_ignored(files, root):
    """Return only the files git does not ignore (2026-09-28).

    A path listed in a .gitignore is not part of the project: `crate-cli/tmp/`
    holds scratch crates from local runs, and scanning them reported
    violations in files no commit can ever contain.  One batched call.
    """
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
        return files
    if r.returncode not in (0, 1):
        return files
    ignored = {line.strip() for line in r.stdout.splitlines() if line.strip()}
    return [f for f, rel in zip(files, rels) if rel not in ignored]




def _has_type_annotation(pat: str) -> bool:
    """Return True if the binding pattern already has `:` type
    annotation (e.g. `x: u32`, `_: Result<()>`).  `:` inside
    generics like `Option::<u32>` doesn't count; we look for
    `:` followed by space and a type-like character."""
    # Strip the leading optional `mut ` already matched by
    # LET_NO_ANNOT's prefix (we get the post-mut pat).
    if ":" in pat:
        # Find `:` not inside angle brackets (rough heuristic)
        depth = 0
        for i, ch in enumerate(pat):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
            elif ch == ":" and depth == 0:
                # Has explicit type annotation
                rest = pat[i + 1:].lstrip()
                if rest and not rest.startswith("="):
                    return True
                # colon but no real type? treat as no annotation
                return False
    return False


_RAW_OPEN_RE = re.compile(r'r(#*)"')


def _line_mask_state(
    line: str,
    in_block_comment: bool,
    in_raw: str,
    in_str: str,
) -> tuple[bool, bool, str, str]:
    """Scan ONE line left to right, returning (masked, in_block, in_raw, in_str).

    `in_raw` is the raw-string closer (`"` + `#`*h) while inside a raw
    string, else "".  `in_str` is the quote character of an unterminated
    plain string/char literal, else "".

    This is a real character-level state machine rather than a set of
    per-line regex probes.  The earlier regex version derived the
    "does this plain string continue to the next line" answer from
    ``line.split("//", 1)[0]``, which collapses a DOC COMMENT line to
    the empty string: in

        /// `App::mount("#app", ...)`.
        pub const DEFAULT_CODE: &str = r##"use ...

    the `//` at the very start made body == "", the terminator probe
    could never match, `in_str` latched on, and the `r##"` raw string on
    the next line was never recognised.  Everything after that was
    scanned as ordinary Rust, so a `let add_event = ...` living inside
    the user-facing template string was reported as a real §5.1
    violation.  Comments are now skipped structurally, before any
    literal handling, so a quote inside a comment can never desync
    the scanner.
    """
    masked = False
    i = 0
    n = len(line)
    # A line that BEGINS inside a literal is masked even when empty:
    # the blank line 4 of a `r#"..."#` body is still raw-string content.
    if in_raw or in_str:
        masked = True
    while i < n:
        ch = line[i]
        # --- inside a raw string: only the exact closer ends it ---
        if in_raw:
            masked = True
            idx = line.find(in_raw, i)
            if idx < 0:
                return masked, in_block_comment, in_raw, in_str
            i = idx + len(in_raw)
            in_raw = ""
            continue
        # --- inside an unterminated plain string/char: scan to the closer ---
        if in_str:
            masked = True
            j = i
            while j < n:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == in_str:
                    break
                j += 1
            if j >= n:
                return masked, in_block_comment, in_raw, in_str
            in_str = ""
            i = j + 1
            continue
        # --- inside a block comment: only `*/` ends it ---
        if in_block_comment:
            idx = line.find("*/", i)
            if idx < 0:
                return masked, in_block_comment, in_raw, in_str
            in_block_comment = False
            i = idx + 2
            continue
        # --- line comment: the rest of the line is not source ---
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            break
        if ch == "/" and i + 1 < n and line[i + 1] == "*":
            in_block_comment = True
            i += 2
            continue
        # --- raw string opener: r"..", r#"..#, r##"..## ---
        if ch == "r" or (ch == "b" and i + 1 < n and line[i + 1] == "r"):
            j = i + 1 if ch == "r" else i + 2
            m = _RAW_OPEN_RE.match(line, j)
            if m:
                closer = '"' + m.group(1)
                masked = True
                k = m.end()
                idx = line.find(closer, k)
                if idx < 0:
                    return masked, in_block_comment, closer, in_str
                i = idx + len(closer)
                continue
        # --- plain string / char literal ---
        if ch in ('"', "'") or (ch == "b" and i + 1 < n and line[i + 1] in ('"', "'")):
            j = i + 1 if ch == "b" else i
            quote = line[j]
            if quote == "'":
                # `'a` is a lifetime or pivot far more often than a char
                # literal.  Only treat it as a literal when the content is
                # exactly one char (optionally escaped) closed on this line;
                # `impl<'a> Parser<'a> {` must NOT be read as a char.
                if j + 1 < n and line[j + 1] == "\\":
                    k = j + 2
                    while k < n and line[k] != "'":
                        k += 1
                elif j + 2 < n and line[j + 1] not in ("'", "\\") and line[j + 2] == "'":
                    k = j + 2
                else:
                    i = j + 1
                    continue
            else:
                k = j + 1
                while k < n and line[k] != quote:
                    if line[k] == "\\":
                        k += 1
                    k += 1
            if k < n and line[k] == quote:
                masked = True
                i = k + 1
                continue
            # unterminated on this line -> spans to the next line
            masked = True
            return masked, in_block_comment, in_raw, quote
        i += 1
    return masked, in_block_comment, in_raw, in_str


def _string_literal_lines(text: str) -> set[int]:
    """Line numbers that live INSIDE a string/char literal.

    A Rust file can embed a whole second language as a raw string --
    the repo's WGSL shaders under `example/src/page/*/hook/const.rs`
    are `let ball = u_balls.balls[vi / 6u];` inside `r#"..."#`.  That
    is shader source, not a Rust `let` binding, so §5.1 does not apply
    to it.  Scanning those lines produced 104 phantom violations.

    The same applies to user-facing template constants: this repo's
    `application/service/euv_playground/const.rs` ships a whole
    Leptos app as `EUV_PLAYGROUND_DEFAULT_CODE: &str = r##"..."##`,
    complete with its own `fn app()` and `let add_event = ...`.

    Doc comments are NOT masked: they are Rust source position, and the
    doc-format verifier is the one that owns them.  Comments never
    desync the scanner -- see `_line_mask_state`.
    """
    masked: set[int] = set()
    in_block_comment = False
    in_raw = ""
    in_str = ""
    for idx, line in enumerate(text.splitlines(), start=1):
        line_masked, in_block_comment, in_raw, in_str = _line_mask_state(
            line, in_block_comment, in_raw, in_str
        )
        if line_masked:
            masked.add(idx)
    return masked


def _quote_macro_lines(text: str) -> set[int]:
    """Line numbers that live INSIDE a `quote!` / `quote_spanned!` body.

    A proc-macro crate's `quote!` block is the SOURCE TEXT SHIPPED TO THE
    USER'S CRATE, not this crate's own Rust. A binding such as

        let _ = #function_expr(#stream, #context).await;

    interpolates a `syn::Expr` the user supplied, so its type is unknowable
    at expansion time: the hook it calls returns `Status`, not `()`, and the
    only "compliant" annotation `let _: () = ...` fails to compile inside
    every downstream crate that writes such a hook. §5.1 therefore does not
    apply here for the same reason it does not apply to a shader embedded in
    a raw string — the binding is not a binding of this workspace.

    Measured 2026-10-01 on hyperlane/macros: 2 phantom violations that could
    only be "fixed" by changing macro output.
    """
    lines = text.splitlines()
    masked: set[int] = set()
    depth = 0
    for idx, line in enumerate(lines, start=1):
        body = line.split("//", 1)[0]
        if depth > 0:
            masked.add(idx)
            depth += body.count("{") - body.count("}")
            if depth <= 0:
                depth = 0
            continue
        m = re.search(r"\bquote(?:_spanned)?!\s*[({]", body)
        if not m:
            continue
        masked.add(idx)
        if m.group(0).rstrip("! \t(").endswith("(") or body[m.end() - 1] == "(":
            # `quote!(...)` form: balanced by parens, not braces
            depth = 0
            paren = 1
            for ch in body[m.end():]:
                if ch == "(":
                    paren += 1
                elif ch == ")":
                    paren -= 1
            if paren <= 0:
                continue
            depth = 1
            continue
        depth = body.count("{") - body.count("}")
    return masked


def audit_one(path: Path) -> list[str]:
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    violations: list[str] = []
    string_lines = _string_literal_lines(text)
    masked_lines = string_lines | _quote_macro_lines(text)
    for i, line in enumerate(text.splitlines(), start=1):
        if i in masked_lines:
            continue
        # Skip `if let` / `while let` pattern guards
        stripped = line.lstrip()
        if stripped.startswith(("if let ", "while let ", "} else if let ")):
            continue
        # Skip let-chains (Rust 2024 `if let X = ... && let Y = ...`)
        if "&&" in stripped and stripped.startswith("let "):
            continue
        m = LET_NO_ANNOT.match(line)
        if not m:
            continue
        # A `move` closure binding has no nameable type — see
        # MOVE_CLOSURE_BINDING. §5.2 covers its parameters.
        if MOVE_CLOSURE_BINDING.match(line):
            continue
        pat = m.group("pat").strip()
        if _has_type_annotation(pat):
            continue
        violations.append(
            f"{path}:{i}: `let` binding without explicit type annotation "
            f"per §5.1: {line.strip()[:80]!r}"
        )
    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    total = 0
    files_with_v = 0
    for f in _list_rs_files(root):
        if "tests" in f.parts:
            continue
        v = audit_one(f)
        if v:
            files_with_v += 1
            total += len(v)
            for line in v:
                print(line)
    print(f"\n=== let-bindings-explicit-type: "
          f"{total} violation(s) in {files_with_v} file(s) ===")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())