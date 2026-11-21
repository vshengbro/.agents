#!/usr/bin/env python3
"""Add a name to a crate root's `use` block, precisely.

The block's structure is read from the AST, so a nested group
(`io::{AsyncRead, AsyncReadExt}`) is understood as ONE entry with a nested
brace list, and adding a name to the outer level cannot corrupt it.

Usage:
    python3 add_use_name.py <file> <root> <name> [...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# `use root::{...};` on ONE line, or a block that opens with it.
BLOCK_OPEN = re.compile(r"^(?P<indent>\s*)use\s+(?P<root>[A-Za-z_][A-Za-z0-9_]*)\s*::\s*\{\s*$")
BLOCK_OPEN_FLAT = re.compile(
    r"^(?P<indent>\s*)use\s+(?P<root>[A-Za-z_][A-Za-z0-9_]*)\s*::\s*\{(?P<names>[^{}]*)\}\s*;\s*$"
)


def find_block(lines: list[str], root: str) -> tuple[int, int, list[str]] | None:
    """(start, end, top-level names) of the block that imports `root`.

    A root may own SEVERAL blocks (the file already had one, and a fixer
    added another). The first one is extended, and the later ones are left
    alone: the caller merges them separately.
    """
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        match = BLOCK_OPEN.match(stripped)
        if match and match.group("root") == root:
            closing = index + 1
            while closing < len(lines) and lines[closing].strip() != "};":
                closing += 1
            if closing >= len(lines):
                return None
            return index, closing, _top_level(lines[index + 1:closing])
        match = BLOCK_OPEN_FLAT.match(stripped)
        if match and match.group("root") == root:
            names = [part.strip() for part in match.group("names").split(",") if part.strip()]
            return index, index, names
        index += 1
    return None


def all_blocks(lines: list[str], root: str) -> list[tuple[int, int, list[str]]]:
    """Every block that imports `root`."""
    found: list[tuple[int, int, list[str]]] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        match = BLOCK_OPEN.match(stripped)
        if match and match.group("root") == root:
            closing = index + 1
            while closing < len(lines) and lines[closing].strip() != "};":
                closing += 1
            if closing < len(lines):
                found.append((index, closing, _top_level(lines[index + 1:closing])))
            index = closing + 1
            continue
        match = BLOCK_OPEN_FLAT.match(stripped)
        if match and match.group("root") == root:
            names = [part.strip() for part in match.group("names").split(",") if part.strip()]
            found.append((index, index, names))
        index += 1
    return found


def _top_level(body: list[str]) -> list[str]:
    """The names of a block's top level, nested groups kept whole."""
    names: list[str] = []
    current: list[str] = []
    depth = 0
    for entry in body:
        text_line = entry.strip().rstrip(",")
        if not text_line:
            continue
        current.append(text_line)
        depth += text_line.count("{") - text_line.count("}")
        if depth <= 0:
            names.append(", ".join(current))
            current = []
    if current:
        names.append(", ".join(current))
    return names


def render(root: str, names: list[str], indent: str) -> list[str]:
    """The block, on one line when it fits and over several when it does not."""
    names = sorted(set(names), key=lambda item: (len(item), item))
    flat = f"{indent}use {root}::{{{', '.join(names)}}};"
    if len(flat) <= 100:
        return [flat]
    inner = indent + "    "
    return [f"{indent}use {root}::{{"] + [f"{inner}{name}," for name in names] + [f"{indent}}};"]


def _covers(existing: list[str], name: str) -> bool:
    """Whether the block's names already reach `name`.

    `error::{Code, StreamError}` already reaches `error::StreamError`,
    so adding the latter would define `StreamError` twice.
    """
    leaf = name.rsplit("::", 1)[-1]
    for entry in existing:
        if entry == name:
            return True
        # A nested group `error::{Code, StreamError}` reaches the names
        # inside it.
        if entry.startswith(name + "::"):
            return True
        if entry.endswith("::" + name):
            return True
        if "{" in entry:
            inner = entry[entry.index("{") + 1:entry.rindex("}")]
            prefix = entry[:entry.index("{")].rstrip(":")
            for part in inner.split(","):
                part = part.strip()
                if not part:
                    continue
                full = f"{prefix}::{part}" if prefix else part
                if full == name or full.rsplit("::", 1)[-1] == leaf:
                    return True
    return False


def _covered_by(existing: list[str], name: str) -> set[str]:
    """The block's entries the new group already names."""
    if "{" not in name:
        return set()
    inner = name[name.index("{") + 1:name.rindex("}")]
    prefix = name[:name.index("{")].rstrip(":")
    new_names = set()
    for part in inner.split(","):
        part = part.strip()
        if part:
            new_names.add(f"{prefix}::{part}" if prefix else part)
    covered = set()
    for entry in existing:
        if "{" in entry:
            continue
        leaf = entry.rsplit("::", 1)[-1]
        if any(new.rsplit("::", 1)[-1] == leaf for new in new_names):
            covered.add(entry)
    return covered


def _covers_each(existing: list[str], name: str) -> bool:
    """Whether the new name collides with an entry the block already has.

    Adding `error::{Code, StreamError}` when the block already has
    `error::StreamError` would define `StreamError` twice. The new group
    only has to cover the entries it COLLIDES with; the entries it does
    not mention stay where they are.
    """
    if "{" not in name:
        return False
    inner = name[name.index("{") + 1:name.rindex("}")]
    prefix = name[:name.index("{")].rstrip(":")
    new_leaves = set()
    for part in inner.split(","):
        part = part.strip()
        if part:
            new_leaves.add(part.rsplit("::", 1)[-1])
    for entry in existing:
        if "{" in entry:
            continue
        leaf = entry.rsplit("::", 1)[-1]
        if leaf in new_leaves:
            return True
    return False


def add_to_file(path: Path, root: str, names: list[str]) -> bool:
    """Add `names` to the block that imports `root`, or create that block.

    When the root already owns SEVERAL blocks, they are merged into one:
    §6.6 wants a single brace statement per root.
    """
    text = path.read_text()
    lines = text.split("\n")
    found = all_blocks(lines, root)
    if not found:
        # No block for this root: extend a single-item statement of the same
        # root, or add a block after the last private use group.
        single = _single_item_statement(lines, root)
        if single is not None:
            index, name = single
            extra = [item for item in names if not _covers([name], item)]
            indent = " " * (len(lines[index]) - len(lines[index].lstrip()))
            lines[index:index + 1] = render(root, [name] + extra, indent)
            path.write_text("\n".join(lines))
            return True
        insert_at = _last_private_use(lines)
        if insert_at is None:
            return False
        lines[insert_at:insert_at] = render(root, names, "")
        path.write_text("\n".join(lines))
        return True
    if len(found) == 1:
        start, end, existing = found[0]
        merged = list(existing)
        for name in names:
            if _covers(merged, name):
                continue
            if _covers_each(merged, name):
                # The new group covers what the block already has, so the
                # covered entries are replaced by it.
                merged = [entry for entry in merged
                          if entry not in _covered_by(merged, name)]
                merged.append(name)
                continue
            merged.append(name)
        indent = " " * (len(lines[start]) - len(lines[start].lstrip()))
        lines[start:end + 1] = render(root, merged, indent)
        path.write_text("\n".join(lines))
        return True
    # Several blocks for one root: merge them into the first.
    merged: list[str] = []
    for _, _, group_names in found:
        for name in group_names:
            if name not in merged:
                merged.append(name)
    for name in names:
        if _covers(merged, name):
            continue
        if _covers_each(merged, name):
            merged = [entry for entry in merged
                      if entry not in _covered_by(merged, name)]
            merged.append(name)
            continue
        merged.append(name)
    start = found[0][0]
    end = found[-1][1]
    indent = " " * (len(lines[start]) - len(lines[start].lstrip()))
    lines[start:end + 1] = render(root, merged, indent)
    path.write_text("\n".join(lines))
    return True


def _single_item_statement(lines: list[str], root: str) -> tuple[int, str] | None:
    """A `use root::Name;` statement, as (line index, name)."""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("use ") or not stripped.endswith(";"):
            continue
        body = stripped[len("use "):-1].strip().lstrip(":")
        if not body.startswith(root + "::"):
            continue
        name = body[len(root) + 2:]
        if not name or "::" in name:
            continue
        return index, name
    return None


def _last_private_use(lines: list[str]) -> int | None:
    """The line after the last private use group."""
    insert_at = None
    gated = False
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("#["):
            gated = True
            index += 1
            continue
        if stripped.startswith("use ") and not stripped.startswith("pub use"):
            if not gated:
                if stripped.endswith("{"):
                    closing = index + 1
                    while closing < len(lines) and lines[closing].strip() != "};":
                        closing += 1
                    if closing < len(lines):
                        insert_at = closing + 1
                else:
                    insert_at = index + 1
            gated = False
            index += 1
            continue
        if stripped and not stripped.startswith("#["):
            gated = False
        index += 1
    return insert_at


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: add_use_name.py <file> <root> <name> [...]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    root = sys.argv[2]
    names = sys.argv[3:]
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 2
    changed = add_to_file(path, root, names)
    print(f"=== add-use-name: {path} {'changed' if changed else 'unchanged'} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
