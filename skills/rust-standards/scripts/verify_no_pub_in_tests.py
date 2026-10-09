#!/usr/bin/env python3
"""Verify `pub` items inside tests/ directories are actually needed
(§18 tests clause, 2026-10-07 user: "所有的单测都不需要 pub" — narrowed by
the module-boundary evidence, pitfalls §92).

A tests/ tree is a leaf crate, so a `pub` item is vestigial ONLY when its
name never leaves its own file. Two load-bearing patterns make blanket
stripping break the build (both compile-proven on euv 2026-10-07):

  * tests/<sub>/const.rs items: the parent tests/<sub>/mod.rs reaches them
    via `use r#const::*;` — a parent glob-importing from a CHILD module
    needs the child's items to be pub (privacy is top-down).
  * tests/mod.rs `pub use std::{...}` re-exports: a private `use` binding
    is NOT re-exported through `use super::*` globs, so the fn.rs files
    two hops down lose their std imports when pub is stripped.

What remains safely strippable is what this verifier flags: a column-0
`pub`/`pub(crate)` item whose name occurs in NO OTHER file of the same
tests/ tree (per-crate scope: the tests dir under the same Cargo.toml).
Such an item has exactly one reader - its own file - and compiles
identically without the prefix.

Usage:
    python3 verify_no_pub_in_tests.py [ROOT]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB_ITEM_RE = re.compile(
    r"^pub(?:\(crate\))?\s+(?=(?:async\s+|unsafe\s+|extern\s+)*"
    r"(?:fn|const|static|struct|enum|trait|type|mod|use)\b)"
)
NAME_RE = re.compile(
    r"^pub(?:\(crate\))?\s+(?:async\s+|unsafe\s+|extern\s+)*"
    r"(?:fn|const|static|struct|enum|trait|type|mod|use)\s+(?:r#)?([A-Za-z_]\w*)"
)
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
SKIP_DIRS = {"target", ".git", "node_modules"}
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
CHAR_RE = re.compile(r"'(?:\\.|[^'\\])'")


def _blank_literals(line: str) -> str:
    line = STRING_RE.sub('""', line)
    return CHAR_RE.sub("'.'", line)


def _is_tests_file(path: Path) -> bool:
    return path.suffix == ".rs" and "tests" in path.parts


def _tests_tree(path: Path) -> Path | None:
    """The owning tests/ directory: the nearest ancestor named `tests`."""
    for parent in path.parents:
        if parent.name == "tests":
            return parent
    return None


def analyze(root: Path) -> list[str]:
    trees: dict[Path, list[Path]] = {}
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts) or not _is_tests_file(path):
            continue
        tree = _tests_tree(path)
        if tree is not None:
            trees.setdefault(tree, []).append(path)
    violations: list[str] = []
    for tree, files in sorted(trees.items()):
        idents: dict[Path, set[str]] = {}
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            stripped = "\n".join(_blank_literals(l) for l in text.splitlines())
            idents[path] = set(IDENT_RE.findall(stripped))
        for path, own in idents.items():
            others: set[str] = set()
            for other, bag in idents.items():
                if other != path:
                    others |= bag
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(lines, start=1):
                if not PUB_ITEM_RE.match(_blank_literals(line)):
                    continue
                # `pub use` (any pub-marked use) in tests/ is banned outright
                # (2026-10-07 user: "所有单测 tests 目录下的禁止出现 pub use").
                # Plain `use` bindings flow through descendant `use super::*`
                # glob chains (compile-proven on euv-cli, pitfalls §92
                # correction), so the pub prefix is never required.
                if re.match(r"^pub(?:\(crate\)|\(super\))?\s+use\b", line):
                    violations.append(
                        f"{path.relative_to(root)}:{lineno}: pub-marked use is banned in "
                        f"tests/ - plain use reaches descendants through glob chains (§18)"
                    )
                    continue
                m = NAME_RE.match(line)
                name = m.group(1) if m else None
                if name and name not in others:
                    violations.append(
                        f"{path.relative_to(root)}:{lineno}: '{name}' is used only in "
                        f"this file - tests/ items with a single reader never need pub (§18)"
                    )
    return violations


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`."""
    if not _is_tests_file(path) or not path.is_file():
        return []
    root = path.parent
    for parent in [root, *root.parents]:
        if (parent / "Cargo.toml").is_file() and (parent / ".git").exists():
            root = parent
            break
    prefix = str(path.resolve())
    return [v for v in analyze(root) if str((root / v.split(":")[0]).resolve()) == prefix]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_pub_in_tests.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    violations = analyze(root)
    if violations:
        files = len({v.split(":")[0] for v in violations})
        print(f"=== no-pub-in-tests: {len(violations)} violation(s) in {files} file(s) ===")
        for line in violations:
            print(f"  {line}")
        return 1
    print("\n=== no-pub-in-tests: 0 violation(s) in 0 file(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
