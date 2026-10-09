#!/usr/bin/env python3
"""Verify visibility group order inside `const.rs` / `static.rs` (§18).

Rule (2026-10-07): within one `const.rs` / `static.rs`, every `pub` item
comes before any reduced-visibility item. Reading top to bottom the
visibility rank must be non-increasing:

    pub  (rank 2)  ->  pub(crate) / pub(super)  (rank 1)  ->  private  (rank 0)

A `pub const` sitting after a `pub(crate) const` forces the reader to
hunt for the crate's public surface in two places; group the public API
at the top of the file instead.

Scope: files literally named `const.rs` or `static.rs`. Other keyword
files have their own ordering rules (fn.rs / impl.rs are not flat
declaration lists, so a group rule does not apply mechanically there).

An item is a column-0 `const` / `static` declaration; its doc comments
and attributes travel with it. Order inside one visibility group is NOT
checked here - the (name_len, name_lex) convention for new insertions
stays a prose convention, this script only guards the group boundary.

Usage:
    python3 verify_pub_group_order.py [ROOT]

Companion fixer: fix_pub_group_order.py (stable partition, dry-run default).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ITEM_RE = re.compile(
    r"^(?P<vis>pub(?:\((?:crate|super)\))?\s+)?(?P<kind>const|static)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*:"
)
PREFIX_LINE = re.compile(r"^\s*(///|#\[|//(?![!/]))")
TARGET_NAMES = {"const.rs", "static.rs"}
SKIP_DIRS = {"target", ".git"}

# A raw-string opener: r#" / r##" / br#" ... The closer is `"` + the same
# number of `#`. Raw strings may span lines (HTML templates in cli const
# files), so the span scanner below tracks them as a state rather than
# masking per line.
RAW_OPEN = re.compile(r"b?r(#*)\"")


def _find_span_end(lines: list[str], start: int) -> int:
    """Return the index of the line that terminates the item opened at `start`.

    Char-level scanner with three literal states (raw string, normal
    string, char literal) plus `//` line comments, so brackets inside an
    `r#"..."#` HTML template or a `"{"` literal never touch the depth
    count. -1 when the declaration never terminates.
    """
    depth = 0
    raw_hashes: int | None = None
    i = start
    n = len(lines)
    while i < n:
        line = lines[i]
        j = 0
        size = len(line)
        while j < size:
            ch = line[j]
            if raw_hashes is not None:
                if ch == '"' and line[j + 1 : j + 1 + raw_hashes] == "#" * raw_hashes:
                    j += 1 + raw_hashes
                    raw_hashes = None
                    continue
                j += 1
                continue
            m = RAW_OPEN.match(line, j)
            if m:
                raw_hashes = len(m.group(1))
                j = m.end()
                continue
            if ch == '"':
                j += 1
                while j < size:
                    if line[j] == "\\":
                        j += 2
                        continue
                    if line[j] == '"':
                        j += 1
                        break
                    j += 1
                continue
            if ch == "'":
                k = j + 1
                while k < size:
                    if line[k] == "\\":
                        k += 2
                        continue
                    if line[k] == "'":
                        break
                    k += 1
                if k < size and k - j <= 4:
                    j = k + 1
                    continue
                j += 1
                continue
            if ch == "/" and j + 1 < size and line[j + 1] == "/":
                break
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            j += 1
        if raw_hashes is None and depth <= 0 and line.rstrip().endswith(";"):
            return i
        i += 1
    return -1


class Item:
    __slots__ = ("vis", "kind", "name", "rank", "decl_line", "start", "end")

    def __init__(self, vis, kind, name, rank, decl_line, start, end):
        self.vis = vis
        self.kind = kind
        self.name = name
        self.rank = rank
        self.decl_line = decl_line  # 1-indexed line of the declaration
        self.start = start          # 0-indexed first line of prefix block
        self.end = end              # 0-indexed last line of the item span


def _rank(vis: str | None) -> int:
    if vis is None:
        return 0
    return 2 if vis.strip() == "pub" else 1


def parse_items(lines: list[str]) -> list[Item] | None:
    """Parse the file into items, or None when the shape is unsafe to read.

    Unsafe = a declaration that never terminates, which a fixer could
    mangle. The verifier simply reports nothing for such a file rather
    than guessing.
    """
    items: list[Item] = []
    i = 0
    n = len(lines)
    while i < n:
        m = ITEM_RE.match(lines[i])
        if not m:
            i += 1
            continue
        end = _find_span_end(lines, i)
        if end == -1:
            return None
        start = i
        k = i - 1
        while k >= 0 and PREFIX_LINE.match(lines[k]):
            start = k
            k -= 1
        items.append(
            Item(
                vis=(m.group("vis") or "").strip() or None,
                kind=m.group("kind"),
                name=m.group("name"),
                rank=_rank(m.group("vis")),
                decl_line=i + 1,
                start=start,
                end=end,
            )
        )
        i = end + 1
    return items


def check_file(path: Path, rel: str) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    items = parse_items(text.splitlines())
    if not items:
        return []
    found: list[str] = []
    ceiling = 2
    for item in items:
        if item.rank > ceiling:
            vis = item.vis or "private"
            found.append(
                f"{rel}:{item.decl_line}: '{vis} {item.kind} {item.name}' "
                f"appears after a reduced-visibility item - keep all pub items "
                f"before pub(crate)/pub(super)/private ones (§18)"
            )
        else:
            ceiling = min(ceiling, item.rank)
    return found


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    Reads exactly the path it is handed and nothing else. Files that are
    not named const.rs / static.rs carry no group-order obligation.
    """
    if path.name not in TARGET_NAMES:
        return []
    return check_file(path, path.name)


def iter_targets(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in TARGET_NAMES:
            yield path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_pub_group_order.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    violations: list[str] = []
    files_with_violations = 0
    for path in iter_targets(root):
        found = check_file(path, str(path.relative_to(root)))
        if found:
            violations += found
            files_with_violations += 1
    total = len(violations)
    if total:
        print(f"=== pub-group-order: {total} violation(s) in {files_with_violations} file(s) ===")
        for line in violations:
            print(f"  {line}")
        return 1
    print("\n=== pub-group-order: 0 violation(s) in 0 file(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
