#!/usr/bin/env python3
"""Bidirectional syntax regressions for Check17/20; no real repository writes.

Pass --legacy-dir DIRECTORY containing old17.py and old20.py to demonstrate
that the same assertions reject the original implementations.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
SCRATCH = Path.home() / '.hermes/cache/scratch'
CHAR_SOURCE = r'''fn characters<'a>(value: &'a str) {
    let _ = ('{', b'{', '\u{7b}', '\x7b', '\'', '\\', '}');
    'label: loop { break 'label; }
    let _ = r"{ fn fake() { }";
    let _ = br###"{

}"###;
    let _ = "escaped \" {

}";
    /* outer {
       /* nested } */

    } */
    let _ = value;
}

fn split_brace() {
    let _ = "text".split('{');
}

fn after() {}
'''


def git(root, *args):
    subprocess.run(['git', *args], cwd=root,
                   check=True, capture_output=True, env=ENV)


def fixture_tree(root):
    """Construct isolated test-input objects without disabling any Git hook."""
    tree = subprocess.check_output(['git', 'write-tree'], cwd=root, env=ENV).strip()
    commit = subprocess.check_output(['git', 'commit-tree', tree.decode()], cwd=root,
                                     input=b'test: parser fixture snapshot\n', env=ENV).strip()
    git(root, 'update-ref', 'refs/heads/master', commit.decode())


def verify(script, root, expected):
    result = subprocess.run([sys.executable, str(script), str(root)],
                            capture_output=True, text=True, env=ENV)
    assert result.returncode == expected, (
        f'{script.name}: expected exit {expected}, got {result.returncode}\n'
        + result.stdout + result.stderr)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy-dir', type=Path)
    options = parser.parse_args()
    check17 = options.legacy_dir / 'old17.py' if options.legacy_dir else SCRIPTS / 'verify_no_external_crate_path.py'
    check20 = options.legacy_dir / 'old20.py' if options.legacy_dir else SCRIPTS / 'verify_fn_body_blank_lines.py'
    failures = []
    count = 0
    with tempfile.TemporaryDirectory(prefix='rust-parser-regression-', dir=SCRATCH) as directory:
        root = Path(directory)
        git(root, 'init', '--initial-branch=master')
        (root / 'src').mkdir()
        (root / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.0.0"\n'
                                       '[dependencies]\nsyn="2"\nnotify="8"\nignore="0.4"\ntokio="1"\n'
                                       'proc-macro2="1"\neuv-core="0"\n'
                                       'renamed_dep={package="proc-macro2",version="1"}\n'
                                       '[target.\'cfg(any())\'.dependencies]\ntarget-only="1"\n')
        entry = root / 'src/lib.rs'
        entry.write_text('pub mod r#fn;\n')
        source = root / 'src/fn.rs'
        source.write_text('')
        git(root, 'add', '.')
        fixture_tree(root)
        git(root, 'update-ref', 'refs/remotes/origin/master', 'HEAD')

        def case(name, checker, text, expected, imports='pub mod r#fn;\n', committed=False):
            nonlocal count
            count += 1
            source.write_text(text)
            entry.write_text(imports)
            if committed:
                git(root, 'add', '.')
                fixture_tree(root)
            try:
                verify(checker, root, expected)
            except AssertionError as error:
                failures.append(f'{name}: {error}')

        case('chars-lifetimes-labels-raw-strings-nested-comments', check20, CHAR_SOURCE, 0, committed=True)
        case('real-body-blank', check20, CHAR_SOURCE.replace('    let _ = value;', '\n    let _ = value;'), 1, committed=True)
        case('nested-body-blank', check20, 'fn f() {\n    if true {\n\n    }\n}\n', 1, committed=True)
        case('trait-default-body-blank', check20, 'trait X {\nfn f() {\n\n}\n}\n', 1, committed=True)
        case('multiline-signature', check20, 'fn f(\n x: u8,\n)\n{\n\n}\n', 1, committed=True)
        case('true-function-separator', check20, 'fn a() {}\n\nfn b() {}\n', 0, committed=True)
        case('invalid-rust-fails-closed', check20, 'fn f() {', 2, committed=True)
        case('pattern-not-type', check17, 'fn f() { match x { S { lit: syn::Lit::Str(x) } => (), _ => () } }\n', 0)
        case('field-expression-not-type', check17, 'fn f() { S { path: syn::Path::from(ident) }; }\n', 0)
        case('qualified-call-not-type', check17, 'fn f() { syn::parse(x); }\n', 0)
        case('qualified-signature-type', check17, 'fn f(x: syn::Type) {}\n', 1)
        case('qualified-return-type', check17, 'fn f() -> syn::Type { todo!() }\n', 1)
        case('struct-field-type', check17, 'struct S { path: syn::Path }\n', 1)
        case('typed-closure', check17, 'fn f() { let c = |x: syn::Type| x; }\n', 1)
        case('generic-bound', check17, 'fn f<T: syn::Parse>() {}\n', 1)
        case('where-bound', check17, 'fn f<T>() where T: syn::Parse {}\n', 1)
        case('impl-bound', check17, 'fn f(x: impl syn::Parse) {}\n', 1)
        case('nested-type-argument', check17, 'fn f(x: Vec<syn::Type>) {}\n', 1)
        case('spaced-commented-path', check17, 'fn f(x: syn /* misleading */ :: Type) {}\n', 1)
        case('multiline-type', check17, 'fn f(x:\n syn\n ::Type) {}\n', 1)
        case('grouped-external-import', check17, 'use syn::{Type, Path};\n', 1)
        errors = 'fn f(x: notify::Error, y: ignore::Error) {}\n'
        case('actual-root-collision', check17, errors, 0, 'pub use std::error::Error;\npub mod r#fn;\n')
        case('grouped-root-collision', check17, errors, 0, 'pub use std::{error::Error, fmt::Debug};\n')
        case('no-root-collision', check17, errors, 1)
        case('same-import-is-not-collision', check17, 'fn f(x: notify::Error) {}\n', 1, 'pub use notify::Error;\n')
        nested = 'fn f(x: tokio::sync::mpsc::error::SendError<()>) {}\n'
        case('nested-type-actual-name-collision', check17, nested, 0,
             'pub use tokio::sync::broadcast::error::SendError;\n')
        case('intermediate-namespace-is-not-type-collision', check17, nested, 1,
             'pub use std::sync;\n')
        case('nested-same-import-is-not-collision', check17, nested, 1,
             'pub use tokio::sync::mpsc::error::SendError;\n')
        case('hyphenated-external-dependency', check17, 'fn f(x: proc_macro2::Span) {}\n', 1)
        case('renamed-external-dependency', check17, 'fn f(x: renamed_dep::Span) {}\n', 1)
        case('target-external-dependency', check17, 'fn f(x: target_only::Type) {}\n', 1)
        case('normalized-in-repo-crate-stays-internal', check17, 'fn f(x: euv_core::Signal) {}\n', 0)
        case('comment-is-not-import', check17, errors, 1, '// pub use std::error::Error;\n')
        case('string-is-not-import', check17, errors, 1, 'const S: &str = "pub use std::error::Error;";\n')
        case('nested-import-is-not-root', check17, errors, 1, 'mod inner { use std::error::Error; }\n')
        case('different-name-is-not-collision', check17, errors, 1, 'pub use std::error::Error as OtherError;\n')
        case('wildcard-does-not-prove-collision', check17, errors, 1, 'pub use std::error::*;\n')
        case('conditional-import-does-not-prove-collision', check17, errors, 1,
             '#[cfg(feature="other")] pub use std::error::Error;\n')
        case('invalid-type-source-fails-closed', check17, 'fn f(x: syn::Type {', 2)

    for failure in failures:
        print('FAIL:', failure)
    print(f'{count - len(failures)}/{count} parser regressions passed; {len(failures)} failed')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
