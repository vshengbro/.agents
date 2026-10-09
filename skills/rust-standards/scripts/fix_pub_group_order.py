#!/usr/bin/env python3
"""Reorder `const.rs` / `static.rs` so `pub` items precede reduced visibility (§18).

Companion fixer for verify_pub_group_order.py. The transform is a stable
partition: items keep their relative order inside each visibility group,
only the group blocks move (pub -> pub(crate)/pub(super) -> private).
Each item travels with its doc comments and attributes; blank separators
are regenerated as a single blank line between items.

Safety contract (rust-standards fixer rules):

  * default is --dry-run: report what would change, write NOTHING
  * --write applies, then re-verifies and prints the post-fix count
  * idempotent: a second --write run reports 0 changed
  * a file that does not parse cleanly (unterminated declaration, or
    non-item statement lines between items) is skipped, never guessed at

Usage:
    python3 fix_pub_group_order.py ROOT [--write]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verify_pub_group_order import (
    TARGET_NAMES,
    check_file,
    iter_targets,
    parse_items,
)


def split_blocks(lines: list[str]) -> tuple[list[str], list[list[str]], list[str]] | None:
    """Split into (header, item-blocks, footer).

    header = lines before the first item block (use lines, file-top
    comments) and is kept verbatim. Every item block = prefix comment /
    attribute lines + declaration span. Lines between blocks must be
    blank; anything else makes the file unsafe and returns None.
    """
    items = parse_items(lines)
    if items is None:
        return None
    if not items:
        return (lines, [], [])
    # Gap lines between two items must be blank or `//` section banners.
    # Banners describe the FOLLOWING item ("File names and fallbacks" above
    # its const group), so they travel with that item's block through the
    # partition; anything else (code, use lines, /* */) makes the file
    # unsafe and returns None.
    gap_prefix: list[list[str]] = [[]]
    for prev, nxt in zip(items, items[1:]):
        banner: list[str] = []
        for between in lines[prev.end + 1 : nxt.start]:
            stripped = between.strip()
            if not stripped:
                continue
            if stripped.startswith("//") and not stripped.startswith("//!"):
                banner.append(between)
                continue
            return None
        gap_prefix.append(banner)
    header = lines[: items[0].start]
    for line in header:
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "#[")) or stripped.startswith("use "):
            continue
        return None
    blocks = [
        gap + lines[item.start : item.end + 1]
        for gap, item in zip(gap_prefix, items)
    ]
    footer = lines[items[-1].end + 1 :]
    if any(line.strip() for line in footer):
        return None
    return (header, blocks, footer)


def render(header: list[str], blocks: list[list[str]]) -> str:
    parts: list[str] = []
    head = [l for l in header if l.strip()]
    # A header of pure comment/use lines loses its trailing blanks; the
    # regenerated separator below re-supplies exactly one.
    raw_header = header[:]
    while raw_header and not raw_header[-1].strip():
        raw_header.pop()
    if raw_header:
        parts.append("\n".join(raw_header))
    if head == [] and raw_header:
        parts = ["\n".join(raw_header)]
    parts.extend("\n".join(block) for block in blocks)
    return "\n\n".join(parts) + "\n"


def fix_file(path: Path, *, write: bool) -> bool:
    """Return True when the file needed (or, with write=True, got) a fix."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    lines = text.splitlines()
    split = split_blocks(lines)
    if split is None:
        return False
    header, blocks, _footer = split
    if not blocks:
        return False
    items = parse_items(lines)
    assert items is not None and len(items) == len(blocks)
    order = sorted(range(len(blocks)), key=lambda i: (-items[i].rank, i))
    if order == list(range(len(blocks))):
        return False
    new_text = render(header, [blocks[i] for i in order])
    if new_text == text:
        return False
    if write:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="repo root to scan")
    parser.add_argument("--write", action="store_true", help="apply fixes (default: dry-run)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    changed: list[str] = []
    skipped = 0
    for path in iter_targets(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if split_blocks(text.splitlines()) is None:
            # Only counts as skipped when it actually violates; clean
            # unparseable shapes are none of this fixer's business.
            if check_file(path, str(path.relative_to(root))):
                skipped += 1
            continue
        if fix_file(path, write=args.write):
            changed.append(str(path.relative_to(root)))
    mode = "fixed" if args.write else "would-fix"
    for rel in changed:
        print(f"  {mode}: {rel}")
    print(f"=== pub-group-order-fixer: {len(changed)} file(s) {mode}, {skipped} skipped (unsafe shape) ===")
    if args.write and changed:
        remaining = 0
        for path in iter_targets(root):
            remaining += len(check_file(path, str(path.relative_to(root))))
        print(f"=== pub-group-order-fixer: re-verify {remaining} violation(s) remaining ===")
        return 1 if remaining else 0
    return 1 if (changed and not args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
