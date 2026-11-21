#!/usr/bin/env python3
"""Verify §9.1 item 10 in committed diff hunks, using the Rust syntax tree.

The shared parser uses syn for syntax and rustc_lexer for literal/comment spans.
Cargo builds it once in the Hermes scratch cache; build/parse failures exit 2.
The original Git scope and entry-point exclusions are intentionally unchanged.
"""
from __future__ import annotations

import re
import subprocess
import sys
import hashlib
import json
import os
import fcntl
from functools import lru_cache
from pathlib import Path

HUNK = re.compile(r'^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@')


PARSER_MANIFEST = '''[workspace]
[package]
name = "rust-standards-parser"
version = "0.0.0"
edition = "2021"
[dependencies]
syn = { version = "2", features = ["full", "visit"] }
proc-macro2 = { version = "1", features = ["span-locations"] }
rustc_lexer = "0.1"
serde_json = "1"
'''

# Reuse the syn Visit/body-span approach from the repository's AST diagnosis.
# rustc_lexer supplies comment/literal spans; no home-grown Rust lexer is used.
PARSER_SOURCE = r'''
use std::{io::{self, Read}, process};
use proc_macro2::Span;
use serde_json::{json, Value};
use syn::{spanned::Spanned, visit::{self, Visit}, Item, UseTree};

#[derive(Default)]
struct Scan {
    bodies: Vec<(usize, usize)>,
    paths: Vec<Value>,
    imports: Vec<Value>,
    type_spans: Vec<Value>,
    items: Vec<Value>,
}
fn segments(path: &syn::Path) -> Vec<String> {
    path.segments.iter().map(|s| s.ident.to_string().trim_start_matches("r#").to_owned()).collect()
}
fn binding(tree: &UseTree, prefix: Vec<String>, out: &mut Vec<Value>, line: usize) {
    match tree {
        UseTree::Path(p) => {
            let mut path = prefix;
            path.push(p.ident.to_string());
            binding(&p.tree, path, out, line);
        }
        UseTree::Group(g) => {
            for item in &g.items { binding(item, prefix.clone(), out, line); }
        }
        UseTree::Name(n) => {
            let mut path = prefix;
            let name = n.ident.to_string();
            if name != "self" { path.push(name); }
            if let Some(short) = path.last() { out.push(json!([line, short, path])); }
        }
        UseTree::Rename(n) => {
            let mut path = prefix;
            path.push(n.ident.to_string());
            out.push(json!([line, n.rename.to_string(), path]));
        }
        UseTree::Glob(_) => {
            // This marks external glob imports but proves no named collision.
            out.push(json!([line, "*", prefix]));
        }
    }
}
impl Scan {
    fn body(&mut self, block: &syn::Block) {
        self.bodies.push((block.brace_token.span.open().start().line,
                          block.brace_token.span.close().end().line));
    }
    fn path(&mut self, path: &syn::Path, span: Span) {
        if path.segments.len() > 1 {
            self.paths.push(json!([span.start().line, span.end().line, segments(path)]));
        }
    }
    fn type_span(&mut self, path: &syn::Path, span: Span) {
        // The column-precise span of a TYPE path, so a fixer can rewrite
        // the path without touching the rest of the line. It is reported
        // under its own key so the existing `paths` consumers keep working.
        if path.segments.len() > 1 {
            self.type_spans.push(json!([
                span.start().line, span.start().column,
                span.end().line, span.end().column,
                segments(path),
            ]));
        }
    }
}
impl<'ast> Visit<'ast> for Scan {
    fn visit_item(&mut self, node: &'ast syn::Item) {
        // The NAME a module declares, so a caller can tell what a glob
        // re-export of that module actually brings into scope.
        let named = match node {
            syn::Item::Struct(i) => Some(i.ident.to_string()),
            syn::Item::Enum(i) => Some(i.ident.to_string()),
            syn::Item::Union(i) => Some(i.ident.to_string()),
            syn::Item::Trait(i) => Some(i.ident.to_string()),
            syn::Item::Type(i) => Some(i.ident.to_string()),
            syn::Item::Mod(i) => Some(i.ident.to_string()),
            _ => None,
        };
        if let Some(name) = named {
            self.items.push(json!([name]));
        }
        visit::visit_item(self, node);
    }
    fn visit_item_fn(&mut self, node: &'ast syn::ItemFn) {
        self.body(&node.block);
        visit::visit_item_fn(self, node);
    }
    fn visit_impl_item_fn(&mut self, node: &'ast syn::ImplItemFn) {
        self.body(&node.block);
        visit::visit_impl_item_fn(self, node);
    }
    fn visit_trait_item_fn(&mut self, node: &'ast syn::TraitItemFn) {
        if let Some(body) = &node.default { self.body(body); }
        visit::visit_trait_item_fn(self, node);
    }
    fn visit_type_path(&mut self, node: &'ast syn::TypePath) {
        self.path(&node.path, node.path.span());
        self.type_span(&node.path, node.path.span());
        visit::visit_type_path(self, node);
    }
    fn visit_trait_bound(&mut self, node: &'ast syn::TraitBound) {
        self.path(&node.path, node.path.span());
        visit::visit_trait_bound(self, node);
    }
    fn visit_item_use(&mut self, node: &'ast syn::ItemUse) {
        binding(&node.tree, vec![], &mut self.imports, node.span().start().line);
        visit::visit_item_use(self, node);
    }
}
fn main() {
    let mut text = String::new();
    io::stdin().read_to_string(&mut text).unwrap();
    let file = match syn::parse_file(&text) {
        Ok(file) => file,
        Err(error) => {
            eprintln!("Rust parse error at line {}: {}", error.span().start().line, error);
            process::exit(2);
        }
    };
    let mut scan = Scan::default();
    scan.visit_file(&file);
    let mut root_imports = vec![];
    for item in &file.items {
        if let Item::Use(node) = item {
            // Conditional/attributed imports cannot prove an unconditional name.
            if node.attrs.is_empty() {
                binding(&node.tree, vec![], &mut root_imports, node.span().start().line);
            }
        }
    }
    let mut protected = vec![];
    let (mut offset, mut line) = (0, 1);
    for token in rustc_lexer::tokenize(&text) {
        let end = offset + token.len;
        let last = line + text[offset..end].bytes().filter(|b| *b == b'\n').count();
        if matches!(token.kind, rustc_lexer::TokenKind::Literal { .. }
                    | rustc_lexer::TokenKind::BlockComment { .. }) {
            protected.push((line, last));
        }
        offset = end;
        line = last;
    }
    println!("{}", json!({"bodies": scan.bodies, "protected": protected,
                         "paths": scan.paths, "imports": scan.imports,
                         "type_spans": scan.type_spans,
                         "items": scan.items,
                         "root_imports": root_imports}));
}
'''


@lru_cache(maxsize=1)
def parser_binary() -> Path:
    """Build the shared real Rust parser outside the audited repository."""
    digest = hashlib.sha256((PARSER_MANIFEST + PARSER_SOURCE).encode()).hexdigest()[:20]
    scratch = Path.home() / '.hermes/cache/scratch'
    directory = scratch / 'rust-standards-parser' / digest
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        (directory / 'src').mkdir(exist_ok=True)
        (directory / 'Cargo.toml').write_text(PARSER_MANIFEST)
        (directory / 'src/main.rs').write_text(PARSER_SOURCE)
        environment = dict(os.environ, TMPDIR=str(scratch),
                           CARGO_TARGET_DIR=str(directory / 'target'))
        metadata = subprocess.run(
            ['cargo', 'metadata', '--no-deps', '--format-version', '1',
             '--manifest-path', str(directory / 'Cargo.toml')],
            capture_output=True, text=True, timeout=120, env=environment)
        if metadata.returncode:
            raise RuntimeError('Rust parser Cargo metadata failed: ' + metadata.stderr.strip())
        configuration = json.loads(metadata.stdout)
        # Cargo's build_directory holds intermediates, not executable artifacts.
        target = Path(configuration['target_directory'])
        executable = 'rust-standards-parser.exe' if os.name == 'nt' else 'rust-standards-parser'
        binary = target / 'debug' / executable
        if not binary.is_file():
            command = ['cargo', 'build', '--quiet', '--manifest-path', str(directory / 'Cargo.toml'),
                       '--target-dir', str(directory / 'target')]
            result = subprocess.run(command, capture_output=True, text=True, timeout=240,
                                    env=environment)
            if result.returncode:
                raise RuntimeError('Rust parser build failed (cargo, syn, rustc_lexer required): '
                                   + result.stderr.strip())
        if not binary.is_file() or binary.stat().st_size == 0:
            raise RuntimeError('Cargo did not produce a nonempty Rust parser at ' + str(binary))
    return binary


@lru_cache(maxsize=128)
def rust_syntax(text: str) -> dict:
    """Fail closed if real Rust parsing is unavailable or rejects the source."""
    try:
        result = subprocess.run([str(parser_binary())], input=text, text=True,
                                capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f'Rust parser unavailable: {error}') from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Rust parser failed')
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError('Invalid Rust parser result') from error


def function_blank_lines(text: str) -> list[int]:
    """Return real blank source lines in fn bodies, excluding literal/comment data."""
    syntax = rust_syntax(text)
    return [number for number, line in enumerate(text.split('\n'), 1)
            if not line.strip()
            and not any(start <= number <= end for start, end in syntax['protected'])
            and any(start < number < end for start, end in syntax['bodies'])]


def _run(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(['git', *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ''
    return r.stdout if r.returncode == 0 else ''


def _try(root: Path, *args: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(['git', *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False, ''
    return r.returncode == 0, r.stdout.strip()


def base_ref(root: Path) -> str:
    ok, url = _try(root, 'config', '--get', 'remote.upstream.url')
    if ok and url:
        ok2, sha = _try(root, 'rev-parse', 'upstream/master')
        if ok2 and sha:
            ok3, mb = _try(root, 'merge-base', 'HEAD', sha)
            if ok3 and mb:
                return mb
    return 'origin/master'


def hunk_ranges(root: Path, base: str, rel: str) -> list[tuple[int, int]]:
    ranges = []
    for line in _run(root, 'diff', base, 'HEAD', '-U0', '--', rel).splitlines():
        match = HUNK.match(line)
        if match:
            start = int(match.group(1))
            length = int(match.group(2)) if match.group(2) else 1
            ranges.append((start, start + length - 1))
    return ranges


def audit_file(root: Path, base: str, rel: str) -> list[str]:
    ranges = hunk_ranges(root, base, rel)
    if not ranges:
        return []
    try:
        text = (root / rel).read_text()
    except FileNotFoundError:
        # Deleted paths in the existing diff scope have no current body to audit.
        return []
    except (OSError, UnicodeDecodeError) as error:
        raise RuntimeError(f'{rel}: cannot read Rust source') from error
    return [f'{rel}:{line}: blank line in fn body (in diff hunk)'
            for line in function_blank_lines(text)
            if any(start <= line <= end for start, end in ranges)]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    if not root.is_dir():
        print(f'error: {root} is not a directory', file=sys.stderr)
        return 2
    base = base_ref(root)
    files = [f for f in _run(root, 'diff', '--name-only', base, 'HEAD', '--', '*.rs').strip().split('\n')
             if f and '/target/' not in f
             and not f.endswith('/lib.rs') and not f.endswith('/build.rs')]
    hits = []
    rel = '<unknown>'
    try:
        for rel in files:
            hits.extend(audit_file(root, base, rel))
    except RuntimeError as error:
        print(f'error: {rel}: {error}', file=sys.stderr)
        return 2
    for hit in hits:
        print(hit)
    print(f'\n=== fn-body-blank-lines (R9.1): {len(hits)} violation(s) '
          f'in {len(files)} file(s) ===')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
