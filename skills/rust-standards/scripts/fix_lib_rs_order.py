#!/usr/bin/env python3
"""Auto-fixer for §6.1 `#[cfg(test)]` module placement in lib.rs / mod.rs / main.rs.

Re-imports parsing and `#[cfg(test)]` detection logic from `verify_lib_rs_order.py`
so verifier and fixer share a single source of truth.

Behaviour:
  - Default mode is dry-run (prints candidate files without touching disk).
  - Pass `--write` to rewrite files in place and re-verify each file with
    `verify_lib_rs_order.audit_one`.
  - Pass `--files ...` to restrict fixes to specific repo-relative or absolute paths.
  - Moves every top-level `#[cfg(test)] mod ...;` block (with all attached outer
    attributes such as `#[path = "..."]`) to immediately after the last normal
    `mod ...;` block, separated by EXACTLY one blank line, and ensures one blank
    line separates the `#[cfg(test)]` module block from following declarations.

Exit code: 0 = clean or all targeted fixes verified clean, 1 = remaining violations,
2 = usage error.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from verify_lib_rs_order import (  # noqa: E402
    ENTRY_FILENAMES,
    MOD_DECL,
    audit_one,
    is_cfg_test_attr,
    list_entry_files,
    split_leading_outer_attrs,
)


def _extract_mod_blocks(lines: list[str]) -> tuple[list[tuple[int, int, bool]], bool]:
    """Return list of `(start_idx, end_idx_exclusive, is_cfg_test)` for top-level `mod xxx;` blocks."""
    blocks: list[tuple[int, int, bool]] = []
    pending_start: int | None = None
    pending_attrs: list[str] = []
    attr_depth = 0
    brace_depth = 0
    n = len(lines)

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue
        if attr_depth > 0:
            pending_attrs.append(stripped)
            attr_depth += stripped.count("[") - stripped.count("]")
            if attr_depth < 0:
                attr_depth = 0
            continue
        if brace_depth > 0:
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth < 0:
                brace_depth = 0
            continue
        if stripped.startswith("#!["):
            pending_start = None
            pending_attrs = []
            continue

        inline_attrs, remainder, open_depth = split_leading_outer_attrs(stripped)
        if inline_attrs:
            if pending_start is None:
                pending_start = i
            pending_attrs.extend(inline_attrs)
            if open_depth > 0:
                attr_depth = open_depth
                continue
            if not remainder:
                continue
            decl_text = remainder
            start_line = pending_start
            attr_blob = "\n".join(pending_attrs)
            pending_start = None
            pending_attrs = []
        else:
            decl_text = stripped
            start_line = pending_start if pending_start is not None else i
            attr_blob = "\n".join(pending_attrs)
            pending_start = None
            pending_attrs = []

        brace_depth += stripped.count("{") - stripped.count("}")
        if brace_depth < 0:
            brace_depth = 0

        if MOD_DECL.match(decl_text):
            blocks.append((start_line, i + 1, bool(attr_blob) and is_cfg_test_attr(attr_blob)))

    has_cfg_test = any(flag for _, _, flag in blocks)
    return blocks, has_cfg_test


def plan_rewrite(text: str) -> str:
    """Return rewritten file content placing `#[cfg(test)]` modules after normal `mod`s with 1 blank line."""
    trailing_newline = text.endswith("\n")
    lines = text.splitlines()
    blocks, has_cfg_test = _extract_mod_blocks(lines)
    if not has_cfg_test:
        return text

    normal_blocks = [b for b in blocks if not b[2]]
    test_blocks = [b for b in blocks if b[2]]

    # Capture lines for every #[cfg(test)] mod block verbatim.
    test_chunks: list[list[str]] = [lines[s:e] for s, e, _ in test_blocks]

    # Mark lines belonging to #[cfg(test)] mod blocks (and surplus surrounding blanks) for removal.
    remove_mask = [False] * len(lines)
    for s, e, _ in test_blocks:
        for k in range(s, e):
            remove_mask[k] = True

    remaining: list[str] = []
    normal_end_in_remaining: int | None = None
    last_normal_orig_end = max((e for _, e, _ in normal_blocks), default=None)

    i = 0
    while i < len(lines):
        if remove_mask[i]:
            i += 1
            continue
        remaining.append(lines[i])
        if last_normal_orig_end is not None and i + 1 == last_normal_orig_end:
            normal_end_in_remaining = len(remaining)
        i += 1

    # Collapse any double blank lines that removal created around the original spot.
    cleaned: list[str] = []
    adjusted_insert: int | None = None
    for idx, line in enumerate(remaining):
        if (
            not line.strip()
            and cleaned
            and not cleaned[-1].strip()
        ):
            if normal_end_in_remaining is not None and idx + 1 == normal_end_in_remaining:
                adjusted_insert = len(cleaned)
            continue
        cleaned.append(line)
        if normal_end_in_remaining is not None and idx + 1 == normal_end_in_remaining:
            adjusted_insert = len(cleaned)

    # Flatten test blocks touching each other (no internal blank lines).
    test_lines: list[str] = []
    for chunk in test_chunks:
        test_lines.extend(chunk)

    if adjusted_insert is not None:
        head = cleaned[:adjusted_insert]
        tail = cleaned[adjusted_insert:]
        # Strip leading blanks from tail so we control exact spacing cleanly.
        while tail and not tail[0].strip():
            tail.pop(0)
        rebuilt: list[str] = list(head)
        rebuilt.append("")
        rebuilt.extend(test_lines)
        if tail:
            rebuilt.append("")
            rebuilt.extend(tail)
    else:
        # No normal `mod` declarations exist: place after leading `//!` doc block.
        insert_at = 0
        while insert_at < len(cleaned) and (
            cleaned[insert_at].lstrip().startswith("//!")
            or cleaned[insert_at].lstrip().startswith("#![")
            or not cleaned[insert_at].strip()
        ):
            insert_at += 1
        head = cleaned[:insert_at]
        tail = cleaned[insert_at:]
        while head and not head[-1].strip():
            head.pop()
        while tail and not tail[0].strip():
            tail.pop(0)
        rebuilt = list(head)
        if rebuilt:
            rebuilt.append("")
        rebuilt.extend(test_lines)
        if tail:
            rebuilt.append("")
            rebuilt.extend(tail)

    result = "\n".join(rebuilt)
    if trailing_newline:
        result += "\n"
    return result


def process_file(path: Path, *, write: bool = False) -> tuple[bool, list[str]]:
    if path.name not in ENTRY_FILENAMES or not path.is_file():
        return False, []
    original = path.read_text(encoding="utf-8")
    updated = plan_rewrite(original)
    if updated == original:
        return False, audit_one(path)
    if write:
        path.write_text(updated, encoding="utf-8")
        return True, audit_one(path)
    return True, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix §6.1 #[cfg(test)] mod placement.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root directory")
    parser.add_argument("--write", action="store_true", help="Write rewrites to disk")
    parser.add_argument("--files", nargs="*", default=None, help="Optional subset of files")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    if args.files:
        targets = []
        for raw in args.files:
            p = Path(raw)
            if not p.is_absolute():
                p = root / p
            if p.name in ENTRY_FILENAMES and p.is_file():
                targets.append(p)
    else:
        targets = list_entry_files(root)

    changed_count = 0
    remaining_violations: list[str] = []
    for path in targets:
        changed, violations = process_file(path, write=args.write)
        if changed:
            changed_count += 1
            mode = "REWRITTEN" if args.write else "WOULD REWRITE"
            print(f"{mode}: {path}")
        remaining_violations.extend(violations)

    if not args.write:
        if changed_count == 0:
            print("Nothing to do (dry-run)")
        else:
            print(f"{changed_count} file(s) would be rewritten (pass --write to apply)")
        return 0

    for v in remaining_violations:
        print(v)
    if remaining_violations:
        print(f"\nFAIL: {len(remaining_violations)} violation(s) remain after rewrite")
        return 1
    if changed_count == 0:
        print("Nothing to do")
    else:
        print(f"OK: rewrote {changed_count} file(s); 0 violations remain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
