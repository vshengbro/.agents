#!/usr/bin/env python3
"""§6.7 auto-fixer — hoist qualified type paths to the crate root.

A type annotation should name the type, not the crate's module layout:

    // before
    let x: h2::Error = ...;
    // after (lib.rs gains `use h2::Error;`)
    let x: Error = ...;

When two crates offer a type of the SAME name, the bare name cannot serve
both and §6.5 forbids renaming an import with `as`. The fixer then
imports the nearest DIFFERENT level of each path, so the use site keeps
just enough of the path to tell them apart:

    // lib.rs gains `use {h2::server, quinn};`
    let a: server::Connection = ...;   // h2::server::Connection
    let b: quinn::Connection = ...;    // quinn::Connection

The fixer is conservative: it only rewrites a path when the result is
unambiguous, it never touches a path the root already binds, and it never
introduces an `as` rename.

Usage:
    python3 fix_no_qualified_type_path.py [ROOT] [--write]
Default is dry-run; --write rewrites the files.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from verify_fn_body_blank_lines import rust_syntax  # noqa: E402
from add_use_name import add_to_file as add_use_name  # noqa: E402
from verify_no_qualified_type_path import (  # noqa: E402
    RUST_KEYWORDS,
    STDLIB,
    crate_of,
    crate_root_file,
    import_owner,
    in_repo_crates,
    owner_declared,
    public_names,
    leaf_of,
    parse_cargo_toml,
    root_bindings,
)


def type_spans(text: str) -> list[tuple[int, int, int, int, tuple[str, ...]]]:
    """Every type path with its exact span."""
    syntax = rust_syntax(text)
    result = []
    for start_line, start_col, end_line, end_col, parts in syntax.get("type_spans", []):
        result.append((start_line, start_col, end_line, end_col, tuple(parts)))
    return result


def is_associated_item(path: tuple[str, ...]) -> bool:
    """`Type::Variant` names a variant, not a type of its own."""
    return len(path) >= 3 and path[-2][0].isupper() and path[-1][0].isupper()


def collect_candidates(path: Path, external: set[str],
                      bindings: dict[str, set[tuple[str, ...]]],
                      own: set[str] | None = None,
                      declared: set[str] | None = None) -> list[dict]:
    """The paths one file spells that the owner could import instead."""
    own = own or set()
    declared = declared or set()
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    if not text:
        return []
    try:
        syntax = rust_syntax(text)
    except RuntimeError:
        return []
    macros = [tuple(m) for m in syntax.get("macro_spans", [])]

    candidates: list[dict] = []
    for start_line, start_col, end_line, end_col, type_path in type_spans(text):
        if len(type_path) < 2:
            continue
        root = type_path[0]
        if root in STDLIB or root in RUST_KEYWORDS:
            continue
        if root not in external:
            continue
        if is_associated_item(type_path):
            continue
        leaf = leaf_of(type_path)
        if leaf in bindings:
            # The root binds this leaf already, either to the same item or
            # to another one. Either way the bare name is not available.
            continue
        if root in bindings:
            # The root binds the path's own root as a module.
            continue
        if leaf in own:
            # The crate's own public API binds the leaf, so the bare name
            # would collide with it.
            continue
        if leaf in declared:
            # The import owner declares the leaf itself.
            continue
        if any(ms <= start_line <= me for ms, me in macros):
            continue
        candidates.append({
            "file": path, "line": start_line, "col": start_col,
            "end_line": end_line, "end_col": end_col,
            "path": type_path,
        })
    return candidates


def plan_owner(sources: list[Path], external: set[str],
               bindings: dict[str, set[tuple[str, ...]]],
               own: set[str] | None = None,
               declared: set[str] | None = None) -> list[dict]:
    """The rewrites for every file of one owner, and the imports they need.

    The conflict groups are computed over the WHOLE owner, not per file:
    two crates may offer the same type name in two different files, and
    the bare name still cannot serve both.
    """
    candidates: list[dict] = []
    for source in sources:
        candidates += collect_candidates(source, external, bindings, own, declared)
    if not candidates:
        return []

    # Group by leaf so the conflicting leaves can be shortened together.
    by_leaf: dict[str, list[dict]] = defaultdict(list)
    for candidate in candidates:
        by_leaf[leaf_of(candidate["path"])].append(candidate)

    rewrites: list[dict] = []
    imports: dict[str, str] = {}
    for leaf, group in by_leaf.items():
        paths = sorted({candidate["path"] for candidate in group})
        if len(paths) == 1:
            # No conflict: import the type itself, the use site says the
            # bare leaf.
            imports[leaf] = "::".join(paths[0])
            for candidate in group:
                rewrites.append({**candidate, "use_site": leaf})
            continue
        # Conflict: the bare leaf cannot serve both, and §6.5 forbids
        # renaming an import with `as`. The way out is to import the
        # nearest level of each path that tells them apart, so the use
        # site keeps just enough of the path to say which one it means.
        #
        #     h2::client::SendRequest  vs  h3::client::SendRequest
        #     -> use {h2::client, h3::client};
        #     -> the use site keeps the crate, so the two stay apart
        #
        # The prefix has to start at the crate, because that is the level
        # the two paths actually differ at.
        for candidate in group:
            others = [p for p in paths if p != candidate["path"]]
            keep = 1
            for path in others:
                shared = 0
                while shared < min(keep, len(path)) and candidate["path"][shared] == path[shared]:
                    shared += 1
                keep = max(keep, shared + 1)
            prefix = candidate["path"][:keep]
            # The prefix must be unique inside the group.
            while any(
                other[:len(prefix)] == prefix and other != candidate["path"]
                for other in others
            ):
                keep += 1
                prefix = candidate["path"][:keep]
            name = prefix[-1]
            imports[name] = "::".join(prefix)
            # The use site keeps the whole path from the crate down, so the
            # two crates stay distinguishable.
            use_site = "::".join(candidate["path"])
            rewrites.append({**candidate, "use_site": use_site})
    return [{"rewrites": rewrites, "imports": imports}]


def apply_plan(plan: list[dict]) -> int:
    """Rewrite every file the plan touches, in place."""
    by_file: dict[Path, list[dict]] = defaultdict(list)
    for entry in plan:
        for rewrite in entry["rewrites"]:
            by_file[rewrite["file"]].append(rewrite)
    applied = 0
    for source, rewrites in by_file.items():
        try:
            text = source.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.split("\n")
        edits: list[tuple[int, int, int, int, str, str]] = []
        for rewrite in rewrites:
            old = "::".join(rewrite["path"])
            new = rewrite["use_site"]
            edits.append((rewrite["line"], rewrite["col"], rewrite["end_line"],
                          rewrite["end_col"], old, new))
        edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
        for start_line, start_col, end_line, end_col, old, new in edits:
            if start_line == end_line:
                line = lines[start_line - 1]
                seg = line[start_col:end_col]
                if not seg.startswith(old):
                    raise RuntimeError(
                        f"{source}:{start_line} expected {old!r} got {seg!r}")
                lines[start_line - 1] = line[:start_col] + new + seg[len(old):] + line[end_col:]
            else:
                head = lines[start_line - 1][:start_col]
                tail = lines[end_line - 1][end_col:]
                middle = lines[start_line:end_line - 1]
                lines[start_line - 1:end_line] = [head + new + tail] + middle
        source.write_text("\n".join(lines))
        applied += len(edits)
    return applied


def add_imports(root_file: Path, imports: dict[str, str]) -> bool:
    """Add the hoisted imports to the crate root.

    Each name goes into the brace block that already holds its ROOT, so
    §6.6 keeps one brace statement per root. The block's structure is read
    from the AST, so a nested group (`io::{AsyncRead, AsyncReadExt}`) is
    understood as one entry and adding a name to the outer level cannot
    corrupt it.

    The insertion point is never a `#[cfg(...)]`-gated group: an import
    that only one platform has would not compile on the other one.
    """
    if not imports:
        return False
    # Group the new names by their root. The dict is keyed by the item's
    # bare name, so two entries can share a root (`h2` the crate itself and
    # `h2::RecvStream` the type); they must land in ONE block.
    by_root: dict[str, list[str]] = {}
    crate_roots: set[str] = set()
    for _, import_path in imports.items():
        segments = import_path.lstrip(":").split("::")
        root = segments[0]
        name = "::".join(segments[1:])
        if not name:
            # The CRATE itself is imported: that is what a conflict group
            # needs (`use h2;` alongside `use h3;`).
            crate_roots.add(root)
            continue
        names = by_root.setdefault(root, [])
        if name not in names:
            names.append(name)
    changed = False
    for root, names in sorted(by_root.items()):
        # The crate itself is the root, never a name inside its own block.
        block_names = [name for name in names if name != root]
        if block_names:
            if add_use_name(root_file, root, block_names):
                changed = True
    for root in sorted(crate_roots):
        # The crate is imported on its own: it goes beside the other use
        # groups, because a crate cannot be a name inside its own block.
        if _add_root_import(root_file, root):
            changed = True
    return changed


def _add_root_import(root_file: Path, root: str) -> bool:
    """Import a crate by itself (`use h2;`) next to the other use groups."""
    text = root_file.read_text()
    lines = text.split("\\n")
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
    if insert_at is None:
        return False
    statement = f"use {root};"
    if statement in text:
        return False
    lines[insert_at:insert_at] = [statement]
    root_file.write_text("\\n".join(lines))
    return True


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    if len(args) != 1:
        print("usage: fix_no_qualified_type_path.py [ROOT] [--write]",
              file=sys.stderr)
        return 2
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    in_repo = in_repo_crates(root)
    changed_files = 0
    total_rewrites = 0
    for manifest in sorted(root.rglob("Cargo.toml")):
        parts = set(manifest.parts)
        if "target" in parts or ".worktrees" in parts:
            continue
        crate = manifest.parent
        if crate_root_file(crate) is None:
            continue
        external = parse_cargo_toml(manifest) - in_repo
        if not external:
            continue
        # Group the crate's files by the file that owns their imports. A
        # crate owns the files under its own `src/` and `tests/`; the
        # workspace members are separate crates.
        owners: dict[Path, list[Path]] = defaultdict(list)
        for source in sorted((crate / "src").rglob("*.rs")):
            if "target" in set(source.parts):
                continue
            owner = import_owner(source, crate)
            if owner is None:
                continue
            owners[owner].append(source)
        tests_dir = crate / "tests"
        if tests_dir.is_dir():
            for source in sorted(tests_dir.rglob("*.rs")):
                owner = import_owner(source, crate)
                if owner is None:
                    continue
                owners[owner].append(source)
        for owner, sources in owners.items():
            bindings = root_bindings(owner)
            own = public_names(crate, root)
            declared = owner_declared(owner)
            owner_imports: dict[str, str] = {}
            plan = plan_owner(sources, external, bindings, own, declared)
            if not plan:
                continue
            for entry in plan:
                owner_imports.update(entry["imports"])
                total_rewrites += len(entry["rewrites"])
            if write:
                apply_plan(plan)
            changed_files += 1
            if write and owner_imports:
                add_imports(owner, owner_imports)
                print(f"  {owner}: added {len(owner_imports)} import(s)")
            elif owner_imports:
                names = ", ".join(sorted(owner_imports.values()))
                print(f"  {owner}: would add {len(owner_imports)} import(s): {names}")

    print(f"=== qualified-type-path fixer: {changed_files} file(s), "
          f"{total_rewrites} rewrite(s) "
          f"({'written' if write else 'dry run'}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
