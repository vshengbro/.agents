#!/usr/bin/env python3
"""§17.18 — a publicly exported struct must not expose its fields as `pub`.

A field that is `pub` on a `pub` struct is part of the crate's published
API: a consumer can write `response.status_code` instead of
`response.get_status_code()`. That bypasses the accessor the struct was
designed around, and it freezes the field layout into the API — renaming the
field or changing its type becomes a breaking change instead of a private
refactor.

So a `pub` struct keeps its fields private (or crate-internal) and the
consumer reaches them through the generated `get_*` / `set_*` accessors.

What is KEPT:

  * a struct that is NOT `pub` — `pub(crate)`, `pub(super)` or private. Its
    fields are not reachable from outside the crate anyway, so the rule
    has nothing to say about them.
  * a `pub` struct whose fields are already `pub(crate)`, `pub(super)` or
    private.
  * a tuple struct's positional fields — they are read as `.0`, `.1` and
    the accessor convention does not name them.
  * a unit struct, which has no fields.

A package that ships BOTH a library and a binary has one more case: the
binary is a separate crate from the library, so it is an EXTERNAL consumer
of it. A `pub` struct that the binary reads through its accessors has to
keep those accessors reachable, so its fields stay `pub` as well.

Usage:
    python3 verify_no_pub_field_in_pub_struct.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from verify_fn_body_blank_lines import rust_syntax  # noqa: E402


def load_parser() -> object:
    """The shared parser, loaded the way the gate loads a verifier."""
    path = SCRIPT_DIR / "verify_fn_body_blank_lines.py"
    spec = importlib.util.spec_from_file_location("rsv_shared_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the shared parser: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def struct_visibility(payload: dict) -> dict[str, str]:
    """The visibility of every named struct in the file."""
    result: dict[str, str] = {}
    for entry in payload.get("items", []):
        name = entry[0] if isinstance(entry, (list, tuple)) else entry
        visibility = entry[1] if isinstance(entry, (list, tuple)) and len(entry) > 1 else ""
        if name:
            result[name] = visibility
    return result


def package_of(path: Path) -> Path | None:
    """The package directory a source file belongs to."""
    directory = path.parent
    while directory != directory.parent:
        if (directory / "Cargo.toml").is_file():
            return directory
        directory = directory.parent
    return None


def binary_targets(package: Path) -> list[Path]:
    """The source files of the package's own binary targets.

    A package that ships BOTH a library and a binary has two crates: the
    binary is an EXTERNAL consumer of the library. A `pub` struct that the
    binary reads through its accessors has to keep those accessors
    reachable, so its fields stay `pub` as well.

    The manifest is read with a regex rather than a TOML parser, because the
    Python that runs the gate may predate `tomllib` and the rule must not
    depend on an optional module.
    """
    manifest = package / "Cargo.toml"
    if not manifest.is_file():
        return []
    text = manifest.read_text()
    targets: list[Path] = []
    for section in re.finditer(r"\[\[bin\]\](.*?)(?=\n\[|\Z)", text, re.S):
        body = section.group(1)
        path = re.search(r'^\s*path\s*=\s*"([^"]+)"', body, re.M)
        if path:
            targets.append(package / path.group(1))
    # A package with a `src/main.rs` and no explicit `[[bin]]` ships the
    # binary under the package name.
    if not targets:
        default = package / "src/main.rs"
        if default.is_file():
            targets.append(default)
    return [target for target in targets if target.is_file()]


def binary_consumed_accessors(package: Path) -> set[tuple[str, str]]:
    """The (struct, accessor) pairs a package's own binary target reads.

    A package that ships BOTH a library and a binary has two crates: the
    binary is an EXTERNAL consumer of the library. A `pub` struct that the
    binary reads through its accessors has to keep those accessors
    reachable, so its fields stay `pub` as well.

    The pair carries the struct name as well, because the binary may read
    an accessor of a DIFFERENT struct that happens to share the name. The
    struct is resolved through the TYPE of the binding the accessor is
    called on, because the call site usually names a variable rather than
    the type.
    """
    names: set[tuple[str, str]] = set()
    for target in binary_targets(package):
        try:
            text = target.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        # The type of every binding the binary declares.
        types: dict[str, str] = {}
        for match in re.finditer(
                r"\b(?:let|mut)\s+(?P<variable>[a-z_][A-Za-z0-9_]*)\s*:\s*"
                r"(?P<type>[A-Z][A-Za-z0-9_]*)",
                text):
            types[match.group("variable")] = match.group("type")
        for match in re.finditer(
                r"\b(?P<variable>[a-z_][A-Za-z0-9_]*)\s*\.\s*"
                r"(?P<accessor>get|set|get_mut)_(?P<field>[a-z_][A-Za-z0-9_]*)",
                text):
            struct_name = types.get(match.group("variable"))
            if not struct_name:
                continue
            names.add((struct_name,
                       f"{match.group('accessor')}_{match.group('field')}"))
    return names


def check_file(path: Path) -> list[str]:
    """The findings for one file."""
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    if not text:
        return []
    try:
        payload = rust_syntax(text)
    except RuntimeError:
        return []
    package = package_of(path)
    consumed = binary_consumed_accessors(package) if package else set()
    findings: list[str] = []
    for struct_name, field_name, field_visibility, line in payload.get(
            "pub_struct_fields", []):
        if field_visibility != "pub":
            continue
        if (struct_name, f"get_{field_name}") in consumed or (
                struct_name, f"set_{field_name}") in consumed:
            # The package's own binary target reads this accessor, so the
            # accessor has to stay reachable and the field with it.
            continue
        findings.append(
            f"{path}:{line}: the public struct `{struct_name}` exposes the field "
            f"`{field_name}` as `pub` — a consumer must reach it through the "
            f"generated `get_{field_name}` / `set_{field_name}` accessors"
        )
    return findings


def audit_one(path: Path) -> list[str]:
    """Single-file entry point for `staged_file_gate`.

    Reads exactly the path it is handed and nothing else, so the gate's
    before/after baselines compare.
    """
    return check_file(path)


def iter_rs(root: Path):
    for path in sorted(root.rglob("*.rs")):
        parts = set(path.parts)
        if "target" in parts or ".git" in parts or ".worktrees" in parts:
            continue
        yield path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_pub_field_in_pub_struct.py [ROOT]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    violations: list[str] = []
    files_with_violations = 0
    for path in iter_rs(root):
        found = check_file(path)
        if found:
            violations += found
            files_with_violations += 1

    total = len(violations)
    for finding in violations:
        print(finding)
    print(f"=== pub-field-in-pub-struct (§17.18): {total} violation(s) "
          f"in {files_with_violations} file(s) ===")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
