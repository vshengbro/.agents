#!/usr/bin/env python3
"""§6.7 — a type annotation must not spell an external crate by its full path.

A type annotation is a place where the type's NAME is what matters, not
where it lives. Writing `let x: h2::Error = ...` says "an error from the
h2 crate" in a form that forces every reader to resolve the path, and it
ties the annotation to the crate's module layout instead of to the type.

The import belongs at the crate root, and the annotation then spells the
bare name:

    // lib.rs
    use h2::Error;
    // the annotation
    let x: Error = ...;

When two crates offer a type of the SAME name, the bare name cannot serve
both, and §6.5 forbids renaming an import with `as`. The way out is to
import the nearest DIFFERENT level of each path, so the use site keeps
enough of the path to tell them apart:

    // lib.rs
    use {h2::server, quinn};
    // the annotations
    let a: server::Connection = ...;   // h2::server::Connection
    let b: quinn::Connection = ...;    // quinn::Connection

The rule applies to the TYPE position of a binding, a parameter, a return
type or a field. It does NOT apply to:

  * an associated item of a type (`io::ErrorKind::NotFound` names a variant
    of `io::ErrorKind`, not a type — importing it is a different question);
  * a path the crate root already binds to the very same item, because
    the bare name is already in scope;
  * a path whose bare name the crate root binds to a DIFFERENT item, since
    the bare name would then be ambiguous;
  * `std::` and `core::` paths in a crate whose root already imports them,
    for the same reason.

Usage:
    python3 verify_no_qualified_type_path.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from verify_fn_body_blank_lines import rust_syntax  # noqa: E402
import rustdoc_exports  # noqa: E402

# Rust keywords are not crate names.
RUST_KEYWORDS = {
    "as", "async", "await", "break", "const", "continue", "crate", "dyn", "else",
    "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop",
    "match", "mod", "move", "mut", "pub", "ref", "return", "self", "Self",
    "static", "struct", "super", "trait", "true", "type", "unsafe", "use",
    "where", "while", "yield",
}

# The crates that are never "external": the standard library and the
# in-repo crates.
STDLIB = {"std", "core", "alloc"}


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args],
                                capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout if result.returncode == 0 else ""


def load_cargo_toml(path: Path) -> dict:
    try:
        tomllib = importlib.import_module("tomllib")
    except ImportError:
        try:
            tomllib = importlib.import_module("tomli")
        except ImportError as error:
            raise RuntimeError("Python <3.11 requires tomli to read Cargo manifests") from error
    with path.open("rb") as handle:
        return tomllib.load(handle)


def parse_cargo_toml(path: Path) -> set[str]:
    """Dependency names of a manifest, in the form a `use` path spells them."""
    if not path.is_file():
        return set()
    try:
        cargo = load_cargo_toml(path)
    except (OSError, RuntimeError):
        return set()
    sections = ("dependencies", "build-dependencies", "dev-dependencies")
    tables = [cargo.get(section, {}) for section in sections]
    tables.append(cargo.get("workspace", {}).get("dependencies", {}))
    names: set[str] = set()
    for table in tables:
        for name in table:
            names.add(name.replace("-", "_"))
    return names


def in_repo_crates(root: Path) -> set[str]:
    """The crates of this repository, by the name a `use` path spells them.

    An in-repo crate is not "external": a path into it is the crate's own
    module tree, which §6.1 governs (a `pub use` of the crate root), not
    §6.7.
    """
    names: set[str] = set()
    for manifest in root.rglob("Cargo.toml"):
        parts = set(manifest.parts)
        if "target" in parts or ".worktrees" in parts:
            continue
        try:
            cargo = load_cargo_toml(manifest)
        except (OSError, RuntimeError):
            continue
        package = cargo.get("package", {}).get("name")
        if package:
            names.add(package.replace("-", "_"))
    return names


def crate_root_file(crate_dir: Path) -> Path | None:
    """The file that owns the crate's imports."""
    manifest = crate_dir / "Cargo.toml"
    if manifest.is_file():
        try:
            cargo = load_cargo_toml(manifest)
        except (OSError, RuntimeError):
            cargo = {}
        library = cargo.get("lib", {})
        if "path" in library:
            candidate = crate_dir / library["path"]
            return candidate if candidate.is_file() else None
        candidate = crate_dir / "src/lib.rs"
        return candidate if candidate.is_file() else None
    candidate = crate_dir / "src/lib.rs"
    return candidate if candidate.is_file() else None


def crate_of(root: Path, path: Path) -> Path | None:
    """The crate directory a file belongs to."""
    directory = path.parent
    while directory != directory.parent:
        if (directory / "Cargo.toml").is_file():
            return directory
        directory = directory.parent
    return None


def root_bindings(root_file: Path) -> dict[str, set[tuple[str, ...]]]:
    """Names the crate root binds, and the paths each name stands for."""
    if not root_file.is_file():
        return {}
    result: dict[str, set[tuple[str, ...]]] = {}
    for _, name, path in rust_syntax(root_file.read_text())["root_imports"]:
        if name == "*":
            continue
        result.setdefault(name, set()).add(tuple(path))
    return result


def leaf_of(path: tuple[str, ...]) -> str:
    return path[-1]


def import_prefix(path: tuple[str, ...]) -> tuple[str, ...]:
    """The path the crate root imports so the use site can spell the leaf.

    `h2::server::Connection` imports `h2::server::Connection`; the use site
    then says `Connection`.
    """
    return path


def distinguishable(paths: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    """Shorten each path to the nearest level that tells the group apart.

    Two paths that share a leaf need more of their path to be told apart.
    The shortest prefix that is unique within the group is enough, and it is
    the "nearest different name" the rule asks for.
    """
    if len(paths) == 1:
        return list(paths)
    result: list[tuple[str, ...]] = []
    for path in paths:
        keep = len(path)
        for other in paths:
            if other is path:
                continue
            shared = 0
            while shared < min(keep, len(other)) and path[shared] == other[shared]:
                shared += 1
            keep = min(keep, shared + 1)
        result.append(path[:keep])
    return result


def type_paths(text: str) -> list[tuple[int, int, tuple[str, ...]]]:
    """Every path in a type position, with its line span."""
    syntax = rust_syntax(text)
    found = []
    for start, end, parts in syntax["paths"]:
        path = tuple(parts)
        if len(path) < 2:
            continue
        found.append((start, end, path))
    return found


def check_file(path: Path, root_file: Path, external: set[str],
               bindings: dict[str, set[tuple[str, ...]]],
               own: set[str] | None = None,
               declared: set[str] | None = None,
               ambiguous: set[str] | None = None) -> list[str]:
    """Findings for one file."""
    own = own or set()
    declared = declared or set()
    ambiguous = ambiguous or set()
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
    lines = text.split("\n")

    findings: list[str] = []
    for start_line, start_col, end_line, end_col, parts in syntax.get("type_spans", []):
        type_path = tuple(parts)
        if len(type_path) < 2:
            continue
        root = type_path[0]
        if root in STDLIB or root in RUST_KEYWORDS:
            continue
        if root not in external:
            continue
        # An associated item (`io::ErrorKind::NotFound`) is not a type: the
        # path names a VARIANT of the type before it. A path whose last two
        # segments are both UpperCamelCase is `Type::Variant`.
        if len(type_path) >= 3 and type_path[-2][0].isupper() and type_path[-1][0].isupper():
            continue
        leaf = leaf_of(type_path)
        bound = bindings.get(leaf)
        if bound:
            if type_path in bound:
                # The owner binds exactly THIS item, so the bare name is in
                # scope and the qualified path at the use site is redundant:
                # that is the violation the rule targets.
                pass
            else:
                # The owner binds the leaf to a DIFFERENT item: the bare
                # name would be ambiguous, so the path has to stay.
                continue
        # The owner binds the path's OWN root as a module (`use std::io;`),
        # so the path already spells a name that is in scope, and it is
        # shorter than the bare leaf would be at every use site.
        if type_path[0] in bindings:
            continue
        # The crate's own public API binds the leaf, so the bare name
        # would collide with it.
        if leaf in own:
            continue
        # The import owner declares the leaf itself.
        if leaf in declared:
            continue
        # Another crate offers a type of the same name, so the bare name
        # cannot serve both: the path stays qualified, and the root
        # imports the crate itself (`use h2;`) so the path still resolves.
        if leaf in ambiguous:
            continue
        # Inside a macro body the tokens are emitted elsewhere; §16.5 owns
        # that ground.
        if any(ms <= start_line <= me for ms, me in macros):
            continue
        findings.append(
            f"{path}:{start_line}: {lines[start_line - 1].strip()[:110]}"
        )
    return findings


def public_names(crate: Path, repo: Path) -> set[str]:
    """The names the crate itself binds in its own scope.

    A crate root re-exports its own modules with `pub use {module::*};`, so
    the crate's own tree binds names that an external crate may also offer.
    Importing the external one bare would collide with them, so the
    external path has to stay.

    The re-export chain is walked to any depth, because a module may
    re-export another module (`config` re-exports `r#struct::*`), and the
    name only becomes visible at the root through that chain.
    """
    names: set[str] = set()
    root_file = crate_root_file(crate)
    if root_file is None:
        return names
    try:
        data = rust_syntax(root_file.read_text())
    except (OSError, RuntimeError):
        return names

    def module_items(module: str) -> set[str]:
        """The names a module declares, following its own re-exports."""
        found: set[str] = set()
        directory = root_file.parent / module
        sources = sorted(directory.rglob("*.rs")) if directory.is_dir() else []
        for source in sources:
            try:
                payload = rust_syntax(source.read_text())
            except (OSError, RuntimeError):
                continue
            for _, name, path in payload.get("root_imports", []):
                if name == "*":
                    # A glob re-export of another module: follow it.
                    if path and path[0] not in {"self", "crate", "super"}:
                        found |= module_items(path[0].replace("r#", ""))
                    continue
                if name[0].isupper():
                    found.add(name)
            # The names the module DECLARES, whether it re-exports them or
            # not: a `pub(crate) type` occupies its name in the crate's
            # own scope just as a `pub struct` does.
            for entry in payload.get("items", []):
                name = entry[0]
                if name and name[0].isupper():
                    found.add(name)
        return found

    for _, name, path in data.get("root_imports", []):
        if name != "*" or not path:
            continue
        head = path[0]
        if head in {"self", "crate", "super"}:
            continue
        if (root_file.parent / head).is_dir():
            names |= module_items(head)
        else:
            # A glob re-export of an EXTERNAL crate: the crate's public
            # items come into this crate's scope under their own names.
            names |= external_exports(head, repo)
    return names


def external_exports(crate: str, repo: Path) -> set[str]:
    """The public names an external crate exports, from its rustdoc JSON.

    The rustdoc payload is the authoritative public API; the sources are
    not read, because a published crate's items live in its own build.
    The payload lives in the audited repository's own `target/doc`.
    """
    stem = crate.replace("-", "_")
    doc = repo / "target/doc" / f"{stem}.json"
    if not doc.is_file():
        return set()
    try:
        payload = json.loads(doc.read_text())
    except (OSError, ValueError):
        return set()
    return rustdoc_exports.crate_root_exports(payload)


def owner_declared(owner: Path) -> set[str]:
    """The names the import owner itself declares.

    An owner that declares `pub(crate) type QuicClientConfig` occupies
    that name in its own scope, so importing another crate's item of the
    same name bare would collide with it.
    """
    names: set[str] = set()
    try:
        payload = rust_syntax(owner.read_text())
    except (OSError, RuntimeError):
        return names
    for entry in payload.get("items", []):
        name = entry[0]
        if name and name[0].isupper():
            names.add(name)
    return names


def import_owner(path: Path, crate: Path) -> Path | None:
    """The file that owns the imports for a source file.

    * a file under `src/` belongs to the crate root (`src/lib.rs`);
    * a file under `tests/` belongs to the tests tree root
      (`tests/mod.rs`), because the tests tree is an independent crate;
    * a file under `src/bin/<name>/` belongs to that binary's entry point
      (`src/bin/<name>/main.rs`), because a binary has no lib.rs.
    """
    try:
        relative = path.relative_to(crate)
    except ValueError:
        return None
    parts = relative.parts
    if parts and parts[0] == "tests":
        candidate = crate / "tests/mod.rs"
        return candidate if candidate.is_file() else None
    if len(parts) >= 3 and parts[0] == "src" and parts[1] == "bin":
        candidate = crate / "src" / "bin" / parts[2] / "main.rs"
        return candidate if candidate.is_file() else None
    candidate = crate_root_file(crate)
    return candidate


def ambiguous_leaves(crate: Path, external: set[str],
                      bindings: dict[str, set[tuple[str, ...]]],
                      own: set[str], declared: set[str]) -> set[str]:
    """The leaves that two different crates offer under the same name.

    A bare name cannot serve both, so the paths that name them stay
    qualified and the root imports the crates themselves.
    """
    leaves: dict[str, set[str]] = {}
    sources = sorted((crate / "src").rglob("*.rs"))
    tests_dir = crate / "tests"
    if tests_dir.is_dir():
        sources += sorted(tests_dir.rglob("*.rs"))
    for source in sources:
        data = rust_syntax(source.read_text())
        for _, _, _, _, parts in data.get("type_spans", []):
            path = tuple(parts)
            if len(path) < 2 or path[0] not in external:
                continue
            if path[0] in STDLIB or path[0] in RUST_KEYWORDS:
                continue
            if len(path) >= 3 and path[-2][0].isupper() and path[-1][0].isupper():
                continue
            leaf = path[-1]
            if leaf in bindings or leaf in own or leaf in declared:
                continue
            leaves.setdefault(leaf, set()).add(path[0])
    return {leaf for leaf, roots in leaves.items() if len(roots) > 1}


def iter_crate_files(root: Path) -> list[tuple]:
    """Every source file with its import owner, its externals, and the
    owner's bindings."""
    grouped: dict[tuple[Path, Path], list[Path]] = {}
    in_repo = in_repo_crates(root)
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
        sources = sorted((crate / "src").rglob("*.rs"))
        tests_dir = crate / "tests"
        if tests_dir.is_dir():
            sources += sorted(tests_dir.rglob("*.rs"))
        for source in sources:
            owner = import_owner(source, crate)
            if owner is None:
                continue
            grouped.setdefault((crate, owner), []).append(source)
    output = []
    for (crate, owner), files in grouped.items():
        external = parse_cargo_toml(crate / "Cargo.toml") - in_repo
        bindings = root_bindings(owner)
        own = public_names(crate, root)
        declared = owner_declared(owner)
        ambiguous = ambiguous_leaves(crate, external, bindings, own, declared)
        for path in files:
            output.append((path, owner, external, bindings, own, declared, ambiguous))
    return output


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    Reads exactly the path it is handed and nothing else, so the gate's
    before/after baselines compare.
    """
    root = find_repo_root(path)
    if root is None:
        return []
    crate = crate_of(root, path)
    if crate is None:
        return []
    root_file = crate_root_file(crate)
    if root_file is None:
        return []
    external = parse_cargo_toml(crate / "Cargo.toml")
    if root is not None:
        external -= in_repo_crates(root)
    bindings = root_bindings(root_file)
    repo = root if root is not None else crate
    own = public_names(crate, repo)
    declared = owner_declared(root_file)
    ambiguous = ambiguous_leaves(crate, external, bindings, own, declared)
    return check_file(path, root_file, external, bindings, own, declared, ambiguous)

def find_repo_root(path: Path) -> Path | None:
    directory = path.parent
    while directory != directory.parent:
        if (directory / ".git").exists() or (directory / "Cargo.toml").is_file():
            return directory
        directory = directory.parent
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_qualified_type_path.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    violations: list[str] = []
    files_with_violations = 0
    try:
        for path, root_file, external, bindings, own, declared, ambiguous in iter_crate_files(root):
            found = check_file(path, root_file, external, bindings, own, declared, ambiguous)
            if found:
                violations += found
                files_with_violations += 1
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    total = len(violations)
    for finding in violations:
        print(finding)
    print(f"=== qualified-type-path (§6.7): {total} violation(s) "
          f"in {files_with_violations} file(s) ===")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
