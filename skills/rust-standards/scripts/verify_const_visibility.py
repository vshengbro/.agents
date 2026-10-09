#!/usr/bin/env python3
"""Verify constant visibility: a `pub const` / `pub static` with zero readers
outside its owning crate must be `pub(crate)` (§18, constants clause).

Rule (2026-10-07, user: "很多 pub 还是可以优化成 pub crate,而且尤其是常量"):
a constant is part of the crate's public API only when an EXTERNAL consumer
reads it. External consumers are:

  * every OTHER workspace crate's src/ (and build.rs)
  * every tests/ directory in the workspace, including the owning crate's
    own tests/ (integration tests are a separate crate)

Method: extract the whole-token identifier set of the external corpus once
(comments stripped, string/char literals KEPT - a code generator that spells
the constant's name inside an emitted-code string is a real consumer), then
check each `pub const|static NAME` at column 0 against it. Same-named
constants in other crates count as usage (conservative direction: a missed
reduction, never a false positive).

Two finding classes:

  * violation  - zero external readers, at least one reader inside the owning
                 crate. Mechanically fixable: `pub` -> `pub(crate)`.
  * unwired    - zero readers anywhere (in- or outside). Reported separately
                 because reducing triggers dead_code and #[allow] is banned;
                 keep-vs-delete is a human decision (§17.14 introspection
                 clause). Not counted in the exit-code violations.

Usage:
    python3 verify_const_visibility.py [ROOT]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB_CONST_RE = re.compile(r"^pub\s+(?P<kind>const|static)\s+(?P<name>[A-Za-z_]\w*)\b")
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
SKIP_DIRS = {"target", ".git", "node_modules"}

LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _strip_comments(text: str) -> str:
    text = BLOCK_COMMENT.sub("", text)
    return LINE_COMMENT.sub("", text)


def _is_internal(path: Path, crate_root: Path) -> bool:
    """True when `path` compiles into the same crate target as the lib.

    False for every OTHER target of the package - tests/, examples/,
    benches/, src/bin/**, and src/main.rs when src/lib.rs exists (a lib+bin
    package: the bin is an external consumer of the lib's pub surface, and
    reducing the lib's pub item makes it vanish from the bin's glob use).
    """
    try:
        rel = path.relative_to(crate_root)
    except ValueError:
        return False
    if not rel.parts:
        return False
    if rel.parts[0] in ("tests", "examples", "benches"):
        return False
    if rel.parts[0] == "src":
        if len(rel.parts) >= 2 and rel.parts[1] == "bin":
            return False
        if rel == Path("src/main.rs") and (crate_root / "src/lib.rs").is_file():
            return False
    return True


class Crate:
    __slots__ = ("root", "internal_idents", "files")

    def __init__(self, root: Path):
        self.root = root
        self.internal_idents: set[str] = set()
        self.files: list[Path] = []


def _crate_roots(repo: Path) -> list[Path]:
    roots = []
    for manifest in sorted(repo.rglob("Cargo.toml")):
        if any(part in SKIP_DIRS for part in manifest.parts):
            continue
        roots.append(manifest.parent)
    return roots


def _owning_crate(path: Path, crates: list[Path]) -> Path | None:
    best: Path | None = None
    for crate in crates:
        try:
            path.relative_to(crate)
        except ValueError:
            continue
        if best is None or len(crate.parts) > len(best.parts):
            best = crate
    return best


def _iter_rs(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def analyze(repo: Path):
    """Return (violations, unwired) as lists of formatted strings."""
    crates = _crate_roots(repo)
    if not crates:
        return [], []
    texts: dict[Path, str] = {}
    for path in _iter_rs(repo):
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    crate_of: dict[Path, Path | None] = {p: _owning_crate(p, crates) for p in texts}
    per_file_idents: dict[Path, set[str]] = {}
    for path, text in texts.items():
        per_file_idents[path] = set(IDENT_RE.findall(_strip_comments(text)))
    # Internal files of crate C = its .rs files outside C/tests/. A constant's
    # own declaration site never counts as a reader, in- or outside.
    internal_files: dict[Path, set[Path]] = {c: set() for c in crates}
    for path in texts:
        crate = crate_of[path]
        if crate is not None and _is_internal(path, crate):
            internal_files[crate].add(path)
    external_idents: dict[Path, set[str]] = {}
    for crate in crates:
        mine = internal_files[crate]
        bag: set[str] = set()
        for path, idents in per_file_idents.items():
            if path not in mine:
                bag |= idents
        external_idents[crate] = bag
    violations: list[str] = []
    unwired: list[str] = []
    for path, text in texts.items():
        crate = crate_of[path]
        if crate is None or not _is_internal(path, crate):
            continue
        outside = external_idents[crate]
        inside = internal_files[crate]
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = PUB_CONST_RE.match(line)
            if not m:
                continue
            name = m.group("name")
            if name == "fn":
                # `pub const fn name(...)` is a function, not a constant.
                continue
            rel = path.relative_to(repo)
            # Absolute ban (user ruling: 常量是肯定不需要pub的 — tests must not
            # verify constants, and cross-crate consumers hold their own copies
            # or call a fn API). No external-reader exemption remains.
            if name in outside:
                violations.append(
                    f"{rel}:{lineno}: 'pub {m.group('kind')} {name}' is a constant; "
                    f"constants are never pub even with external readers - "
                    f"reduce to pub(crate) and give each consumer its own copy "
                    f"or a fn API (§18, pitfalls §93)"
                )
                continue
            has_internal_reader = any(
                other is not path and name in per_file_idents[other] for other in inside
            )
            if has_internal_reader:
                violations.append(
                    f"{rel}:{lineno}: 'pub {m.group('kind')} {name}' has no readers "
                    f"outside {crate.name} - reduce to pub(crate) (§18)"
                )
            else:
                unwired.append(
                    f"{rel}:{lineno}: 'pub {m.group('kind')} {name}' has no readers "
                    f"anywhere (unwired; keep-vs-delete pending)"
                )
    return violations, unwired


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    The corpus is repo-wide, so this walks up to the nearest ancestor
    containing a workspace Cargo.toml and analyzes the file within it.
    """
    if path.suffix != ".rs" or not path.is_file():
        return []
    repo = path.resolve().parent
    for parent in [repo, *repo.parents]:
        if (parent / "Cargo.toml").is_file() and (parent / ".git").exists():
            repo = parent
            break
    else:
        return []
    violations, _unwired = analyze(repo)
    prefix = str(path.resolve().relative_to(repo))
    return [v for v in violations if v.startswith(prefix + ":")]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_const_visibility.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    violations, unwired = analyze(root)
    if unwired:
        # Report-only class goes to stderr: stdout carries violations only,
        # so audit wrappers can count lines without filtering two classes.
        print(
            f"=== const-visibility-unwired: {len(unwired)} item(s) "
            f"(report-only, keep-vs-delete pending) ===",
            file=sys.stderr,
        )
        for line in unwired[:20]:
            print(f"  {line}", file=sys.stderr)
        if len(unwired) > 20:
            print(
                f"  ... and {len(unwired) - 20} more "
                f"(constant-table crates list every export here by design)",
                file=sys.stderr,
            )
    if violations:
        files = len({v.split(":")[0] for v in violations})
        print(f"=== const-visibility: {len(violations)} violation(s) in {files} file(s) ===")
        for line in violations:
            print(f"  {line}")
        return 1
    print("\n=== const-visibility: 0 violation(s) in 0 file(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
