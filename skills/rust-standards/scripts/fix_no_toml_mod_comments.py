#!/usr/bin/env python3
"""§2.5 auto-fixer: strip every comment from TOML files and mod.rs files.

Removes `#` comments (TOML) and `//` / `///` / `//!` / `/* ... */` comments
(mod.rs), using the scanners from `verify_no_toml_mod_comments.py` — one
parser, two consumers, so the fixer and the verifier can never drift apart
(see SKILL.md "新增 audit check 的硬性流程").

Per file:
  - a comment-only line (nothing before the comment but whitespace) is
    dropped entirely;
  - a trailing comment is cut and the surviving code is rstripped;
  - a multi-line block comment drops its middle lines and joins the
    surviving prefix/suffix of the first/last line.

What this fixer deliberately does NOT do: normalise blank lines or section
separators left behind by a deleted comment. That is fix_dep_order.py's job
(TOML §13.7.2 / multi-blank-run) and verify_lib_rs_order.py's job (mod.rs
§6.1 stage blanks); rust_pre_commit.py Phase 1 runs this fixer BEFORE
fix_dep_order.py so the loop converges.

Contract:
  - default DRY-RUN: lists the files it would rewrite, writes nothing;
  - `--write`: applies, then re-verifies every rewritten file with the
    verifier (0 findings or exit 1); second run prints "Nothing to do"
    (idempotent);
  - `--files a b c`: restrict to those paths (rust_pre_commit.py change
    scoping); omit for whole-repo scope.

Usage:
    python3 fix_no_toml_mod_comments.py <repo-root> [--write] [--files ...]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_no_toml_mod_comments",
        _SCRIPT_DIR / "verify_no_toml_mod_comments.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load verify_no_toml_mod_comments.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verifier = _load_verifier()


def _line_offsets(text: str) -> list[int]:
    """Offset of each line's first character (0-indexed lines)."""
    offsets = [0]
    for index, char in enumerate(text):
        if char == "\n":
            offsets.append(index + 1)
    return offsets


def strip_comments(text: str, scope: str) -> tuple[str, int]:
    """Remove every comment span from `text`. Returns (new_text, n_spans)."""
    spans = (
        verifier.find_rust_comments(text)
        if scope == "rust"
        else verifier.find_toml_comments(text)
    )
    if not spans:
        return text, 0
    offsets = _line_offsets(text)
    lines = text.split("\n")
    # per 0-indexed line: list of (col_start, col_end) covered by comments
    covered: dict[int, list[tuple[int, int]]] = {}
    for start, end, start_line in spans:
        # end is exclusive and never includes the trailing newline
        first = start_line - 1
        last = first
        while last + 1 < len(offsets) and offsets[last + 1] <= end:
            last += 1
        for lineno in range(first, last + 1):
            line_start = offsets[lineno]
            line_end = offsets[lineno + 1] - 1 if lineno + 1 < len(offsets) else len(text)
            col_start = max(start, line_start) - line_start
            col_end = min(end, line_end) - line_start
            covered.setdefault(lineno, []).append((col_start, col_end))
    out_lines: list[str] = []
    for lineno, line in enumerate(lines):
        segments = covered.get(lineno)
        if not segments:
            out_lines.append(line)
            continue
        rebuilt = ""
        cursor = 0
        for col_start, col_end in sorted(segments):
            rebuilt += line[cursor:col_start]
            cursor = col_end
        rebuilt += line[cursor:]
        if not rebuilt.strip():
            continue  # comment-only line: drop it entirely
        out_lines.append(rebuilt.rstrip())
    new_text = "\n".join(out_lines)
    return new_text, len(spans)


def plan_changes(
    root: Path, *, write: bool, only: set[Path] | None
) -> tuple[int, list[str]]:
    rewrites = 0
    log: list[str] = []
    for path in verifier.list_target_files(root):
        if only is not None and path.resolve() not in only:
            continue
        scope = verifier.scope_of(path)
        if scope is None:
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        new_text, n_spans = strip_comments(text, scope)
        if new_text == text:
            continue
        rewrites += 1
        log.append(f"  {path}: -{n_spans} comment(s)")
        if write:
            path.write_text(new_text)
            # re-verify: the verifier must see zero findings on what we wrote
            remaining = verifier.audit_one(path)
            if remaining:
                log.append(f"  ! re-verify FAILED for {path}: {remaining[0]}")
                return -1, log
    return rewrites, log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repo root to scan (default: cwd).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply rewrites in-place. Default is dry-run.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Restrict the rewrite to these paths. Omit for whole-repo scope.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    only = None
    if args.files:
        # Tolerate a space-joined single element as well as real argv
        # elements: callers that build argv by joining paths into one
        # string would otherwise resolve one bogus composite path and
        # silently fix nothing.
        only = {
            Path(piece).resolve()
            for item in args.files
            for piece in item.split()
            if piece
        }

    rewrites, log = plan_changes(root, write=args.write, only=only)

    if rewrites < 0:
        print("=== fix_toml_mod_comments: re-verify FAILED ===")
        for line in log:
            print(line)
        return 1
    if rewrites == 0:
        print("Nothing to do (no comments in TOML / mod.rs files)")
        return 0

    print(
        f"=== fix_toml_mod_comments: {rewrites} file(s) "
        f"{'written' if args.write else 'to rewrite'} ==="
    )
    for line in log:
        print(line)
    if not args.write:
        print("(dry-run; pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
