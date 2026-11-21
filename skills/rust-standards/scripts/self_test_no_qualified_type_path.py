#!/usr/bin/env python3
"""Two-way self-test for verify_no_qualified_type_path.py (§6.7).

A verifier that cannot fail is not a rule. This proves the verifier reports
a real violation and stays silent on a compliant tree, in both directions.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "verify_no_qualified_type_path.py"

spec = importlib.util.spec_from_file_location("verify_no_qualified_type_path", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

# The crate root binds `h2::Error` already, so the annotation may spell the
# bare name.
COMPLIANT_BOUND = """
use h2::Error;

pub fn make() -> Error {
    unimplemented!()
}
"""

# The root binds nothing, and the annotation spells the full path.
VIOLATING = """
pub fn make() -> h2::Error {
    unimplemented!()
}
"""

# The root binds the leaf to a DIFFERENT item, so the bare name would be
# ambiguous and the path has to stay.
COMPLIANT_CONFLICT = """
use std::io::Error;

pub fn make() -> h2::Error {
    unimplemented!()
}
"""

# An associated item names a VARIANT of the type before it, not a type of
# its own, so the rule does not apply to it.
COMPLIANT_ASSOCIATED = """
pub fn make() -> io::ErrorKind::NotFound {
    unimplemented!()
}
"""

# A std path is governed by the root's own std imports (§6.3). The root
# binds the module `io`, so `io::Error` already spells an in-scope name.
COMPLIANT_STD = """
pub fn make() -> io::Error {
    unimplemented!()
}
"""


def run(source: str, root_source: str, external: set[str]) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        crate = base / "crate"
        (crate / "src").mkdir(parents=True)
        (crate / "Cargo.toml").write_text(
            "[package]\nname = \"sample\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n"
            "[dependencies]\n" + "".join(f"{name} = \"1\"\n" for name in sorted(external))
        )
        root_file = crate / "src/lib.rs"
        root_file.write_text(root_source)
        target = crate / "src/fn.rs"
        target.write_text(source)
        bindings = module.root_bindings(root_file)
        return module.check_file(target, root_file, external, bindings)


def main() -> int:
    failures: list[str] = []

    cases = [
        ("compliant: the root already binds the item",
         COMPLIANT_BOUND, "use h2::Error;\n", {"h2"}, 0),
        ("violating: the annotation spells the full path",
         VIOLATING, "", {"h2"}, 1),
        ("compliant: the root binds the leaf to another item",
         COMPLIANT_CONFLICT, "use std::io::Error;\n", {"h2"}, 0),
        ("compliant: an associated item",
         COMPLIANT_ASSOCIATED, "", {"io"}, 0),
        ("compliant: a std path",
         COMPLIANT_STD, "use std::io;\n", {"io"}, 0),
    ]
    for name, source, root_source, external, expected in cases:
        found = run(source, root_source, external)
        if len(found) != expected:
            failures.append(
                f"{name}: expected {expected} finding(s), got {len(found)}: {found}"
            )
            continue
        print(f"PASS  {name}: {len(found)} finding(s)")

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
        module.check_file = lambda path, root_file, external, bindings: []
        if run(VIOLATING, "", {"h2"}):
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
