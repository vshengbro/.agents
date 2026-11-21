#!/usr/bin/env python3
"""Narrow the public fields of hyperlane's public structs to crate-internal.

§17.18: a `pub` field on a `pub` struct is part of the published API. The
field becomes `pub(crate)`, and the lombok attributes that generate its
accessors are narrowed to match, because §17.14 says an accessor defaults
to `pub` and a `pub(crate)` field without a narrowing attribute silently
widens the field.

Usage:
    python3 fix_no_pub_field_in_pub_struct.py [ROOT] [--write]
Default is dry run; --write rewrites the files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path("/Users/vshengbro/.agents/skills/rust-standards/scripts")
sys.path.insert(0, str(SCRIPT_DIR))

from verify_fn_body_blank_lines import rust_syntax  # noqa: E402

# A field declaration: `pub name: Type,` — the type may hold commas
# (a generic argument list), so the type runs to the LAST comma before the
# line ends.
FIELD = re.compile(
    r"^(?P<indent>\s*)pub\s+(?P<name>[a-z_][A-Za-z0-9_]*)\s*:\s*(?P<type>.+),\s*$"
)
# The lombok attributes that generate an accessor for a field. The argument
# list may hold a nested call (`type(copy)`), so it is matched with a
# balanced scan rather than `[^)]*`.
ACCESSOR_ATTR = re.compile(
    r"^\s*#\[(?P<kind>get|get_mut|set)(?P<args>\((?:[^()]|\([^()]*\))*\))?\]\s*$"
)
# The derive that generates each accessor.
ACCESSOR_DERIVE = {
    "get": {"Getter", "Data"},
    "get_mut": {"GetterMut", "Data"},
    "set": {"Setter", "Data"},
}


def accessor_kinds(payload: dict, struct_name: str) -> set[str]:
    """The accessor kinds a struct's derive actually generates.

    A `#[set(...)]` attribute on a struct that derives only `Getter` is an
    unknown helper attribute and the crate does not compile, so the fixer
    may only add an attribute the derive can consume.
    """
    for entry in payload.get("struct_derives", []):
        if entry[0] != struct_name:
            continue
        derives = {item.strip() for item in entry[1]}
        return {
            kind for kind, sources in ACCESSOR_DERIVE.items()
            if derives & sources
        }
    return set()


def public_fields(text: str) -> list[tuple[str, str, int]]:
    """(struct, field, line) of every public field of a public struct."""
    payload = rust_syntax(text)
    result = []
    for struct_name, field_name, visibility, line in payload.get("pub_struct_fields", []):
        if visibility == "pub":
            result.append((struct_name, field_name, line))
    return result


def binary_consumed_accessors(package: Path) -> set[tuple[str, str]]:
    """The accessor names a package's own binary target reads.

    A package that ships BOTH a library and a binary has two crates: the
    binary is an EXTERNAL consumer of the library. A `pub` struct that the
    binary reads through its accessors has to keep those accessors
    reachable, so its fields stay `pub` as well.
    """
    manifest = package / "Cargo.toml"
    if not manifest.is_file():
        return set()
    text = manifest.read_text()
    targets: list[Path] = []
    for section in re.finditer(r"\[\[bin\]\](.*?)(?=\n\[|\Z)", text, re.S):
        body = section.group(1)
        path = re.search(r'^\s*path\s*=\s*"([^"]+)"', body, re.M)
        if path:
            targets.append(package / path.group(1))
    if not targets:
        default = package / "src/main.rs"
        if default.is_file():
            targets.append(default)
    names: set[str] = set()
    for target in targets:
        if not target.is_file():
            continue
        try:
            source = target.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        types: dict[str, str] = {}
        for match in re.finditer(
                r"\b(?:let|mut)\s+(?P<variable>[a-z_][A-Za-z0-9_]*)\s*:\s*"
                r"(?P<type>[A-Z][A-Za-z0-9_]*)",
                source):
            types[match.group("variable")] = match.group("type")
        for match in re.finditer(
                r"\b(?P<variable>[a-z_][A-Za-z0-9_]*)\s*\.\s*"
                r"(?P<accessor>get|set|get_mut)_(?P<field>[a-z_][A-Za-z0-9_]*)",
                source):
            struct_name = types.get(match.group("variable"))
            if not struct_name:
                continue
            names.add((struct_name,
                       f"{match.group('accessor')}_{match.group('field')}"))
    return names


def package_of(path: Path) -> Path | None:
    """The package directory a source file belongs to."""
    directory = path.parent
    while directory != directory.parent:
        if (directory / "Cargo.toml").is_file():
            return directory
        directory = directory.parent
    return None


def narrow_file(path: Path) -> tuple[int, list[str]]:
    """Narrow the file's public fields and their accessor attributes."""
    text = path.read_text()
    entries = public_fields(text)
    if not entries:
        return 0, []
    payload = rust_syntax(text)
    package = package_of(path)
    consumed = binary_consumed_accessors(package) if package else set()
    lines = text.split("\n")
    changed = 0
    names = []
    # The fields are processed from the bottom up, so an insertion never
    # shifts the line numbers of a field that has not been handled yet.
    for struct_name, field_name, line in sorted(entries, key=lambda entry: -entry[2]):
        index = line - 1
        if index >= len(lines):
            continue
        match = FIELD.match(lines[index])
        if not match or match.group("name") != field_name:
            continue
        if (struct_name, f"get_{field_name}") in consumed or (
                struct_name, f"set_{field_name}") in consumed:
            # The package's own binary target reads this accessor, so the
            # accessor has to stay reachable and the field with it.
            continue
        indent = match.group("indent")
        kinds_available = accessor_kinds(payload, struct_name)
        # Walk back over the field's attributes, narrowing each accessor
        # attribute so the generated method matches the field. A doc comment
        # may sit between the attributes and the field, so it is stepped
        # over.
        attributes = []
        cursor = index - 1
        while cursor >= 0:
            stripped = lines[cursor].strip()
            if stripped.startswith("///") or stripped.startswith("//"):
                cursor -= 1
                continue
            attribute = ACCESSOR_ATTR.match(lines[cursor])
            if not attribute:
                break
            attributes.append(cursor)
            cursor -= 1
        kinds = set()
        for position in attributes:
            kind = ACCESSOR_ATTR.match(lines[position]).group("kind")
            arguments = ACCESSOR_ATTR.match(lines[position]).group("args")
            inner = arguments[1:-1] if arguments else ""
            kinds.add(kind)
            if "pub(crate)" in inner:
                continue
            # The accessor stays PUBLIC: §17.18 makes it the consumer's
            # entry point, so its visibility must not be narrowed. The
            # attribute keeps whatever configuration it carries and its
            # visibility slot is dropped.
            remaining = [item.strip() for item in inner.split(",")
                         if item.strip() and not item.strip().startswith("pub")]
            if remaining:
                lines[position] = f"{indent}#[{kind}({', '.join(remaining)})]"
            else:
                # The attribute carried nothing but a visibility, so it
                # goes away entirely: a bare `#[get]` is forbidden
                # (§17.14.2) and the default accessor is already `pub`.
                lines[position] = None
        # A field with NO accessor attribute still gets one from the
        # derive, and that accessor defaults to `pub`. Nothing has to be
        # added: the default accessor is exactly what §17.18 wants.
        additions = []
        lines[index:index] = additions
        index += len(additions)
        lines[index] = f"{indent}pub(crate) {field_name}: {match.group('type')},"
        changed += 1
        names.append(field_name)
    # An attribute that carried nothing but a visibility is removed, so the
    # placeholders it left behind go away too.
    lines = [line for line in lines if line is not None]
    if changed:
        path.write_text("\n".join(lines))
    return changed, names


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    if len(args) != 1:
        print("usage: fix_no_pub_field_in_pub_struct.py [ROOT] [--write]",
          file=sys.stderr)
        return 2
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    total = 0
    for path in sorted(root.rglob("*.rs")):
        parts = set(path.parts)
        if "target" in parts or ".git" in parts:
            continue
        try:
            entries = public_fields(path.read_text())
        except (OSError, RuntimeError):
            continue
        if not entries:
            continue
        if write:
            changed, names = narrow_file(path)
        else:
            changed = len(entries)
            names = [entry[1] for entry in entries]
        total += changed
        print(f"  {path.relative_to(root)}: {changed} field(s) -> {names}")

    print(f"=== pub-field-narrowing: {total} field(s) "
          f"({'written' if write else 'dry run'}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
