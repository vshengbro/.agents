#!/usr/bin/env python3
"""Two-way self-test for verify_no_pub_field_in_pub_struct.py (§17.18).

A verifier that cannot fail is not a rule. This proves the verifier reports
a real violation and stays silent on a compliant tree, in both directions.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "verify_no_pub_field_in_pub_struct.py"

spec = importlib.util.spec_from_file_location("verify_no_pub_field_in_pub_struct", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

# A public struct with a public field: the violation the rule targets.
VIOLATING = """
#[derive(Clone, Debug)]
pub struct Probe {
    pub name: String,
    pub count: u32,
}
"""

# The same struct with the fields narrowed: compliant.
COMPLIANT = """
#[derive(Clone, Debug)]
pub struct Probe {
    name: String,
    count: u32,
}
"""

# A crate-internal struct: its fields are not reachable from outside the
# crate, so the rule has nothing to say about them.
COMPLIANT_INTERNAL = """
#[derive(Clone, Debug)]
pub(crate) struct Probe {
    pub name: String,
}
"""

# A tuple struct: the fields are positional and have no accessor name.
COMPLIANT_TUPLE = """
#[derive(Clone, Debug)]
pub struct Probe(pub String, pub u32);
"""

# A unit struct: no fields at all.
COMPLIANT_UNIT = """
#[derive(Clone, Debug)]
pub struct Probe;
"""

# A package that ships a library and a binary: the binary is an external
# consumer of the library, so a struct it reads keeps its fields public.
PACKAGE_MAIN = """
use crate::Config;

fn main() {
    let config: Config = Config::default();
    let _name: String = config.get_name();
}
"""


def run(source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.rs"
        path.write_text(source)
        return module.check_file(path)


def run_package() -> list[str]:
    """A package whose binary target reads `Config::get_name`."""
    with tempfile.TemporaryDirectory() as directory:
        package = Path(directory) / "pkg"
        (package / "src").mkdir(parents=True)
        (package / "Cargo.toml").write_text(
            "[package]\nname = \"pkg\"\nversion = \"0.1.0\"\n\n"
            "[[bin]]\nname = \"pkg\"\npath = \"src/main.rs\"\n"
        )
        (package / "src/main.rs").write_text(PACKAGE_MAIN)
        library = package / "src/lib.rs"
        library.write_text(
            "#[derive(Clone, Debug)]\npub struct Config {\n    pub name: String,\n}\n"
        )
        return module.check_file(library)


def main() -> int:
    failures: list[str] = []

    cases = [
        ("violating: a public struct with public fields", VIOLATING, 2),
        ("compliant: the fields are narrowed", COMPLIANT, 0),
        ("compliant: a crate-internal struct", COMPLIANT_INTERNAL, 0),
        ("compliant: a tuple struct", COMPLIANT_TUPLE, 0),
        ("compliant: a unit struct", COMPLIANT_UNIT, 0),
    ]
    for name, source, expected in cases:
        found = run(source)
        if len(found) != expected:
            failures.append(
                f"{name}: expected {expected} finding(s), got {len(found)}: {found}"
            )
            continue
        print(f"PASS  {name}: {len(found)} finding(s)")

    # The package's own binary target reads `Config::get_name`, so the
    # struct it names keeps its fields public.
    package_found = run_package()
    if package_found:
        failures.append(
            f"compliant: the package's binary target reads the struct: "
            f"expected 0 finding(s), got {len(package_found)}: {package_found}"
        )
    else:
        print("PASS  compliant: the package's binary target reads the struct: "
              "0 finding(s)")

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        print(f"\nself-test FAILED: {len(failures)} case(s)")
        return 1
    print("\nself-test PASSED: compliant tree is silent, violating tree is reported")

    # Mutation check: with the rule switched off, the violating case must
    # stop being reported. Otherwise the self-test cannot tell a live rule
    # from a disabled one.
    original = module.check_file
    try:
        module.check_file = lambda path: []
        if run(VIOLATING):
            print("FAIL  mutation: the rule was switched off but the violating "
                  "case is still reported — the self-test cannot tell a live "
                  "rule from a disabled one")
            return 1
        print("PASS  mutation: switching the rule off silences the violating case")
    finally:
        module.check_file = original

    return 0


if __name__ == "__main__":
    sys.exit(main())
