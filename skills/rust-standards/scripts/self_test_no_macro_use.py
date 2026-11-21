#!/usr/bin/env python3
"""Two-way self-test for verify_no_macro_use.py (§16.5).

A verifier that cannot fail is not a rule. This proves the verifier reports
a real violation and stays silent on a compliant tree, in both directions.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "verify_no_macro_use.py"

spec = importlib.util.spec_from_file_location("verify_no_macro_use", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

COMPLIANT = """
use proc_macro2::TokenStream;

pub fn handler() -> TokenStream {
    let code: TokenStream = quote! {
        ::hyperlane::Status::Continue
    };
    code
}
"""

VIOLATING_USE = """
use proc_macro2::TokenStream;

pub fn handler() -> TokenStream {
    let code: TokenStream = quote! {
        use ::hyperlane::Status;
        ::hyperlane::Status::Continue
    };
    code
}
"""

VIOLATING_PATH = """
use proc_macro2::TokenStream;

pub fn handler() -> TokenStream {
    let code: TokenStream = quote! {
        hyperlane::Status::Continue
    };
    code
}
"""

# A `macro_rules!` body expands inside the DEFINING crate, so a `use` there is
# that crate's own business, and a crate path (`proc_macro2::Ident`) is fine.
COMPLIANT_RULES = """
use proc_macro2::TokenStream;

macro_rules! impl_it {
    () => {
        pub fn it(item: TokenStream) -> TokenStream {
            let _ = &proc_macro2::Ident::new("x", proc_macro2::Span::call_site());
            item
        }
    };
}
"""

# A `macro_rules!` body expands inside the DEFINING crate, so its paths
# resolve there and need no absolute spelling.
COMPLIANT_RULES_PATH = """
use proc_macro2::TokenStream;

macro_rules! impl_it {
    () => {
        pub fn it(item: TokenStream) -> TokenStream {
            let _ = syn::parse_quote!(fn x() {});
            item
        }
    };
}
"""

# A `use` inside a `macro_rules!` body is that crate's own business.
COMPLIANT_RULES_USE = """
use proc_macro2::TokenStream;

macro_rules! impl_it {
    () => {
        use crate::common::Helper;
        pub fn it(item: TokenStream) -> TokenStream {
            item
        }
    };
}
"""

# `crate::`, `self::` and `super::` name the defining crate's own tree.
COMPLIANT_CRATE_PATH = """
use proc_macro2::TokenStream;

pub fn handler() -> TokenStream {
    let code: TokenStream = quote! {
        crate::common::Helper::new()
    };
    code
}
"""

# A `use` inside a string is prose, not an item.
COMPLIANT_STRING = """
pub fn handler() {
    let text = "use hyperlane::Status;";
}
"""

# A path inside a comment is prose, not a path.
COMPLIANT_COMMENT = """
pub fn handler() {
    // Status::Continue is only mentioned here.
}
"""


def run(source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.rs"
        path.write_text(source)
        return module.check_file(path)


def main() -> int:
    failures: list[str] = []

    cases = [
        ("compliant", COMPLIANT, 0),
        ("violating: use inside quote!", VIOLATING_USE, 1),
        ("violating: bare crate path inside quote!", VIOLATING_PATH, 1),
        ("compliant: macro_rules! body with a crate path", COMPLIANT_RULES, 0),
        ("compliant: macro_rules! body with a bare crate path", COMPLIANT_RULES_PATH, 0),
        ("compliant: macro_rules! body with a use", COMPLIANT_RULES_USE, 0),
        ("compliant: crate:: path inside quote!", COMPLIANT_CRATE_PATH, 0),
        ("compliant: use inside a string literal", COMPLIANT_STRING, 0),
        ("compliant: path inside a comment", COMPLIANT_COMMENT, 0),
    ]
    for name, source, expected in cases:
        found = run(source)
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

    # Mutation check: a verifier whose rule was switched off must make this
    # self-test FAIL, otherwise the self-test proves nothing about the rule
    # being live. With the rule off, the violating case reports nothing, so
    # the case table above would no longer hold.
    original = module.USE_ITEM.pattern
    try:
        module.USE_ITEM = re.compile(r"^\s*NEVER_MATCHES\b")
        if run(VIOLATING_USE):
            print("FAIL  mutation: the `use` ban was switched off but the "
                  "violating case is still reported — the self-test cannot "
                  "tell a live rule from a disabled one")
            return 1
        print("PASS  mutation: switching the `use` ban off silences the "
              "violating case")
    finally:
        module.USE_ITEM = re.compile(original)

    original_path = module.TOKEN_MACRO
    original_rules = module.RULES_MACRO
    try:
        module.TOKEN_MACRO = re.compile(r"\bNEVER_MATCHES\b")
        module.RULES_MACRO = re.compile(r"\bNEVER_MATCHES\b")
        if run(VIOLATING_PATH):
            print("FAIL  mutation: the macro body detection was switched off but "
                  "the violating case is still reported — the self-test cannot "
                  "tell a live rule from a disabled one")
            return 1
        print("PASS  mutation: switching the macro body detection off silences "
              "the violating case")
    finally:
        module.TOKEN_MACRO = original_path
        module.RULES_MACRO = original_rules

    return 0


if __name__ == "__main__":
    sys.exit(main())
