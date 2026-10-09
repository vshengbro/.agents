#!/usr/bin/env python3
"""
Comprehensive rust-standards audit script for PR review.

Run from a Rust repo working directory with the diff already applied:
  python3 scripts/audit_rust_standards.py [target_dir]

Default target = current working directory.

Categories checked (each is a single pass; output is grouped by category
so false positives are easy to filter out — see references/audit-pitfalls.md
for the master-pattern exceptions the script cannot statically detect):

 1. non-keyword production files (R1.3)
 2. #[allow] in production (R11.x — explicitly forbidden by user)
 3. production unwrap/expect/panic (R11.4)
 4. #[test] in production (R14.5)
 5. // comments in mod.rs (R2.5)
 6. mod.rs missing trailing use super::* (R6.2)
 7. sub-file first line not use super::* (R6.3)
 8. #[cfg(test)] in production (R14.5)
 9. long-path use crate::xxx in sub-files (R6.3)
10. inline generic bounds (R9.2)
11. r# on non-keyword file (R1.4)
12. implicit Vec::new() without type annotation (R5.1, collection-only)
13. #![cfg(test)] in test fn.rs (R14.2)
14. comments in test files (R14.5, DEPRECATED — see check 28)
15. pure &Foo helper in fn.rs should be impl method (R1.3.1)
16. column-0 decl type mismatch in keyword files (R1.3a, raw-string-aware)
17. sub-file body uses external crate full path (R6.4-pitfall-b)
18. fn.rs hardcoded byte/string literals (R1.3c literal purity, fn.rs-only)
19. fn-body blank lines (R9.1 §9.1 item 10)
20. tests/<sub>/fn.rs non-super use (R14.7)
21. Cargo.toml dep block order (§13.7 round 4)
22. CI workflow forbids version bumps and version writes (§17)
23. keyword file purity + first-line use super::* (§1.3 / §6.3)
24. no impl Trait in fn parameters (§9.2)
25. doc-comment format conformance (§2.1 / §2.2) — REMOVED 2026-09-26, see check 35
26. module imports centralized in lib.rs / mod.rs (§6.1 / §6.3 / §6.4)
27. lib.rs / mod.rs three-stage import order (§6.1)
28. no comments in test files (§14.5)
29. mod.rs `mod` declaration must be bare (§6.2)
30. no `#[allow(...)]` in production (§14)
31. explicit type annotations for let bindings (§5.1, collection-only)
32. no `#[inline]` in cdylib crates (§12)
33. all `let` bindings have explicit type annotation (§5.1, comprehensive)
34. closure parameters have explicit type annotation (§5.2)
35. non-test fn has compliant doc comment (§2.1 / §2.2, authoritative)
36. hardcoded strings live in `const.rs` (§1.3c strengthened)
37. lib.rs `//!` doc block structure (§2.4)

Each check prints either "PASS: N. <category>" or "FAIL: N. <category>: <count>
hits" followed by up to 5 sample lines.

Known false positives — see references/audit-pitfalls.md for the complete
list. The script tries to filter the obvious ones (e.g. tests/ is exempt
for several checks) but cannot statically detect every master-pattern
exception (e.g. master accepts `mod r#signal;` inside `core/src/tests/mod.rs`
per R14.1a; master accepts direct `///` doc comments on `enum.rs` without
`use super::*;` when the enum doesn't reference parent-module symbols).
"""
import subprocess
import sys
import os

DEFAULT_TARGET = '.'

CHECKS = [
    ('non-keyword prod files', '''cd {{target}}
git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -vE "/tests/|/lib\\.rs$|/raw_html\\.rs$|/main\\.rs$|/bin/[^/]+\\.rs$|(^|/)build\\.rs$" | while read f; do
  [ -f "$f" ] || continue
  bn=$(basename "$f")
  case "$bn" in
    const.rs|static.rs|fn.rs|enum.rs|struct.rs|trait.rs|impl.rs|type.rs|mod.rs) ;;
    *) echo "NON-KEYWORD: $f" ;;
  esac
done
'''),
    ('#[allow] in production', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | grep -E "^\\+.*#\\[allow" | head -20
'''),
        ('production unwrap/expect/panic', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | while read line; do
  if [[ "$line" == "+++ b/"* ]]; then
    current_file=$(echo "$line" | sed "s|+++ b/||")
  fi
  # A `+` line whose content is only a comment describes code, it is not
  # code. Prose about a *removed* panic ("the old `x().expect(..)` could
  # panic") was counted as a live panic. Skip comment-only lines before the
  # pattern match, so a real call on a `// code` line is still caught.
  added="${line#+}"
  if [[ "$added" =~ ^[[:space:]]*(//|/\*|\*) ]]; then
    continue
  fi
  if echo "$line" | grep -qE "^\+.*(panic!\(|\.expect\(|\.unwrap\(\))"; then
    if [[ ! "$current_file" == *"/tests/"* ]]; then
      # Per audit-pitfalls #41: `try_X().unwrap()` in `get_X` wrappers
      # is an upstream idiom (panic-on-missing contract is part of the
      # wrapper's documented API). Exempt this specific call pattern.
      if echo "$line" | grep -qE "(try_|[Ss]elf::try_)[a-z0-9_]+\(.*\)\.unwrap\(\)|(try_|[Ss]elf::try_)[a-z0-9_]+\(.*\)\.await\.unwrap\(\)|Regex::new\(.*\)\.expect\("; then
        continue
      fi
      # Per audit-pitfalls #42 (forthcoming): proc-macro crates
      # conventionally panic/expect in macro internals to surface user
      # errors via compiler diagnostics. Exempt macros/ subtrees.
      if [[ "$current_file" == *"macros/"* ]]; then
        continue
      fi
      echo "$current_file: $line"
    fi
  fi
done | head -20
'''),
    ('#[test] in production', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | grep -B5 "^\\+.*#\\[test\\]" | grep "^\\+\\+\\+ b/" | grep -v "/tests/" | head -5
'''),
    ('// comments in mod.rs', '''cd {{target}}
for f in $(git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -E "/mod\\.rs$"); do
  [ -f "$f" ] || continue
  if grep -E "^\\s*//[^/!]" "$f" > /dev/null 2>&1; then
    echo "$f"
  fi
done
'''),
    ('mod.rs missing trailing use super::*', '''cd {{target}}
    for f in $(git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -E "/mod\\.rs$" | grep -v "core/tests/mod.rs\\|cli/tests/mod.rs\\|engine/tests/mod.rs\\|ui/tests/mod.rs\\|type/tests/mod.rs"); do
      [ -f "$f" ] || continue
      last=$(grep -E "^[^[:space:]]" "$f" | tail -1)
      case "$last" in
        "use super::*;"|"pub use super::*;") ;;
        *)
          # Per audit-pitfalls #40: a mod.rs's use super::*; is legitimately
          # unused (and may be omitted) when none of its sub-files use the
          # use super::*; chain to reach parent symbols. This is the
          # leaf-mod exemption matching #21's leaf-sub-file exemption.
          dir=$(dirname "$f")
          has_parent_use=0
          for sf in "$dir"/*.rs; do
            [ -f "$sf" ] || continue
            sbn=$(basename "$sf")
            [ "$sbn" = "mod.rs" ] && continue
            if grep -qE "^use super::\\*;" "$sf" 2>/dev/null; then
              has_parent_use=1
              break
            fi
          done
          if [ "$has_parent_use" -eq 0 ]; then
            continue
          fi
          echo "$f: last=$last"
          ;;
      esac
    done
    '''),
    ('sub-file first line not use super::*', '''cd {{target}}
git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -vE "/(mod|lib|raw_html|main)\\.rs$|/tests/|(^|/)build\\.rs$|/bin/[^/]+\\.rs$" | while read f; do
  [ -f "$f" ] || continue
  # Per audit-pitfalls #5 / #5a, files dedicated to a single keyword
  # (const.rs / static.rs / fn.rs / enum.rs / struct.rs
  # / trait.rs / impl.rs / type.rs) are allowed to open with
  # a /// doc comment when they do not need any parent-module
  # symbol. The audit script now matches by the file's *basename*
  # so that every keyword-only sub-file is exempt from the
  # use super::*; requirement, matching what master accepts.
  bn=$(basename "$f")
  case "$bn" in
    const.rs|static.rs|fn.rs|enum.rs|struct.rs|trait.rs|impl.rs|type.rs) continue ;;
  esac
  first=$(grep -nE "^[^[:space:]/]" "$f" 2>/dev/null | head -1 | cut -d: -f1)
  if [ -z "$first" ]; then continue; fi
  line=$(sed -n "${first}p" "$f")
  if [ "$line" != "use super::*;" ]; then
    echo "$f:$first: $line"
  fi
done
'''),
    ('#[cfg(test)] in production', '''cd {{target}}
git diff -U0 origin/master -- "*.rs" 2>/dev/null | grep -F "#[cfg(test)]" | grep -v "^[+][+][+] b/" | grep "^[+]" | grep -v "^\\+[/!]" | grep -v "^\\+\\s*\\*\\s*#\\[cfg" | head -20
'''),
    ('long-path use crate::xxx in sub-files', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | grep -E "^\\+.*\\buse crate::" | grep -v "/tests/" | head -20
'''),
    ('inline generic bounds', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | grep -E "^\\+.*fn [a-z_]+<[A-Z][a-zA-Z]+:" | grep -v "/tests/" | head -10
'''),
    ('r# on non-keyword file', '''cd {{target}}
git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -E "/(mod)\\.rs$" | while read f; do
  [ -f "$f" ] || continue
  if [[ "$f" == *"/tests/"* ]]; then continue; fi
  grep -oE "mod r#[a-z_]+;" "$f" 2>/dev/null | while read line; do
    name=$(echo "$line" | sed -E "s/mod r#([a-z_]+);/\\1/")
    # Per audit-pitfalls #1 the r# prefix is required for every
    # Rust keyword, including the four keywords that were added
    # after the original nine (RFC 2018 added async / await /
    # try; RFC 3324-era work brought dyn). Master accepts
    # mod r#async; for example-page modules whose path collides
    # with these reserved words.
    case "$name" in
      const|static|fn|enum|struct|trait|impl|type|mod|async|await|try|dyn) ;;
      *) echo "$f: r#$name" ;;
    esac
  done
done
'''),
    ('implicit Vec::new() without type', '''cd {{target}}
git diff origin/master -- "*.rs" 2>/dev/null | grep -E "^\\+.*let [a-z_]+ = Vec::new\\(\\);" | grep -v "/tests/" | head -10
'''),
    ('#![cfg(test)] in test fn.rs', '''cd {{target}}
for f in $(git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -E "/tests/.*/fn\\.rs$"); do
  [ -f "$f" ] || continue
  if grep -q "^#!\\[cfg(test)\\]" "$f"; then
    echo "$f"
  fi
done
'''),
    ('comments in test files (R14.5)', '''cd {{target}}
# Per rust-standards §14.5 (2026-09-12 user clarification):
# tests/ files MUST have zero comments. The test fn name is the
# documentation; assertion messages express the expected behavior.
# This applies to:
#   - file-level //! headers
#   - per-fn /// doc comments
#   - fn-body inline // comments
# Blank lines between #[test] fns are fine; only //-prefixed lines fail.
for f in $(git diff --name-only origin/master -- "*.rs" 2>/dev/null | grep -E "/tests/.*\\.rs$"); do
  [ -f "$f" ] || continue
  hits=$(grep -nE "^\s*//[^/]" "$f" 2>/dev/null)
  if [ -n "$hits" ]; then
    echo "FAIL: $f has comments:"
    echo "$hits" | head -3
  fi
done
'''),
    ('pure &Foo helper in fn.rs should be impl method (R1.3.1)', '''cd {{target}}
# For every fn.rs file touched by the PR, find pub fn / pub(crate) fn declarations
# whose first parameter is &Foo / &mut Foo where Foo is a type declared in the
# same directory's struct.rs / enum.rs. Those should be impl methods, not free fns
# (per references/01-directory-structure.md §1.3.1 rule 1).
#
# Companion script: verify_pure_ref_helper.py.  This used to be an inline
# awk template that had never executed.  Three defects compounded: the
# template carried {{/}} brace escapes meant for str.format() while
# substitute() resolves placeholders with a manual .replace(), so awk
# received a literal {{; its split(types, arr, "\\n") sat in a Python
# triple-quoted string so Python consumed the escape and awk received a
# real newline inside a string literal; and the 3-argument match() it used
# is a GNU awk extension BSD awk does not have.  awk died on every run and,
# because run_check took its verdict from stdout rather than the exit code,
# the check reported PASS the entire time.  A pure-Python scan is portable
# and can be self-tested.
python3 "{{audit_script_dir}}/verify_pure_ref_helper.py" "{{target}}" \\
    | grep -v -E '^=== pure-ref-helper'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_pure_ref_helper.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    ('column-0 decl type mismatch in keyword files (R1.3a, raw-string-aware)', '''cd {{target}}
# Companion script: verify_keyword_file_decl_types.py.
# This check used to be an inline python3 -c template nested inside one
# of this file's Python triple-quoted strings. The OUTER parser consumed
# the inner script's escape sequences, so the inner program raised a
# SyntaxError on every invocation and the check never once reported
# anything. A standalone file has no such nesting and can be self-tested.
# Raw-string aware: shader source embedded in a raw string legitimately
# contains struct and fn lines, and those are skipped.
python3 "{{audit_script_dir}}/verify_keyword_file_decl_types.py" "{{target}}" \\
    | grep -v -E '^=== keyword-file-decl-types'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_keyword_file_decl_types.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    ('sub-file body uses external crate full path (R6.4-pitfall-b)', '''cd {{target}}
# Companion script: verify_no_external_crate_path.py.
# This was an inline python3 - <<'PY' heredoc. A heredoc needs a
# temp file, which restricted sandboxes refuse to create, so the check
# died before it could inspect a single line and reported nothing.
# A standalone file has no such dependency and can be self-tested.
python3 "{{audit_script_dir}}/verify_no_external_crate_path.py" "{{target}}" \\
    | grep -v -E '^=== no-external-crate-path'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_external_crate_path.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    ('fn.rs hardcoded byte/string literals (R1.3c literal purity)', '''cd {{target}}
# Companion script: verify_fn_literal_purity.py.
# This was an inline python3 - <<'PY' heredoc. A heredoc needs a temp
# file, which restricted sandboxes refuse to create, so the check never
# actually ran. A standalone file has no such dependency.
python3 "{{audit_script_dir}}/verify_fn_literal_purity.py" "{{target}}" \\
    | grep -v -E '^=== fn-literal-purity'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_fn_literal_purity.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    ('tests/<sub>/fn.rs non-super use (R14.7)', '''
# Per R14.7: tests/<sub>/fn.rs may contain ONLY use super::*; as a top-level
# use statement. Other imports (std / wasm_bindgen_test / web_sys / ...) must
# be re-exported by the parent tests/<sub>/mod.rs via pub use.
# Wrapper invokes the dedicated verify_test_imports_centralized.sh script.
# {{audit_script_dir}} is substituted at audit-script load time (see main()).
# Filter the inner script's "OK: N file(s) ..." line so it doesn't register
# as a hit; only propagate the violation report + exit status.
cd {{target}}
bash "{{audit_script_dir}}/verify_test_imports_centralized.sh" "{{target}}" \
    | grep -v -E '^OK: [0-9]+ tests/'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_test_imports_centralized.sh exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    ('fn-body blank lines (R9.1 §9.1 item 10)', '''cd {{target}}
# Companion script: verify_fn_body_blank_lines.py.
# This was an inline python3 - <<'PY' heredoc. A heredoc needs a
# temp file, which restricted sandboxes refuse to create, so the check
# died before it could inspect a single line and reported nothing.
# A standalone file has no such dependency and can be self-tested.
python3 "{{audit_script_dir}}/verify_fn_body_blank_lines.py" "{{target}}" \\
    | grep -v -E '^=== fn-body-blank-lines'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_fn_body_blank_lines.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    ('Cargo.toml dep block order (§13.7 round 4)', '''
# Per references/13-dependency.md §13.7 (round 4, 2026-09-26):
#   [dependencies] / [dev-dependencies] / [build-dependencies] /
#   [workspace.dependencies] must be ordered:
#     * LOCAL first (workspace members via [workspace] members or
#       value containing workspace = true / path = "...").
#     * EXACTLY ONE blank line separating local group from third-party
#       group. No blank lines within either group.
#     * Within each group: entry full length ascending (whitespace-
#       agnostic; computed by verify_dep_order.py as
#       len(re.sub(r"\\s+", "", "<entry-joined>"))), ties broken by
#       dep key ASCII lex.
#
# The companion script verify_dep_order.py implements this. Its
# exit code is the only source of truth for pass/fail. We pipe its
# stdout through grep -v to drop the success-path trailer line
# (N files checked, M violations) — that line would otherwise be
# counted as a hit by the audit wrapper. The filter matches ANY count, not
# just 0 violations: a nonzero summary line is still a summary line, and
# counting it inflates the reported hit total by exactly 1.
# The actual violation lines (file paths + actual vs expected) MUST flow
# through unfiltered.
# Repos with no Cargo.toml print "No Cargo.toml files found ..." to
# stderr and exit 2 — also filtered out (not a violation).
cd {{target}}
python3 "{{audit_script_dir}}/verify_dep_order.py" "{{target}}" 2>/dev/null \
    | grep -v -E '^[0-9]+ files checked, [0-9]+ violations?$|^OK: 0 Cargo.toml'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_dep_order.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 21b — §13.7 (round 5, 2026-09-27): the elements INSIDE each
    # dependency's `features = [...]` array follow the same length-first
    # ordering as the entries around them.
    ('Cargo.toml features array order (§13.7 round 5)', '''
# verify_dep_order.py orders dependency ENTRIES within a
# [dependencies]-style block but does not look inside a dependency's
# features = [...] array. §13.7 applies the same key to both:
#
#   * Primary: element length in characters, ascending.
#   * Secondary: element text, ASCII lexicographic ascending.
#
# This is the same (length, key) pair entry_sort_key() returns in
# verify_dep_order.py, so a features array reads in the same visual
# rhythm as the block containing it.
#
# Scope: dependency features arrays only. required-features = [] on a
# [[bin]] target is a different key and is skipped. Arrays containing
# comments are skipped too — re-ordering could silently re-associate a
# comment with a different element.
#
# Summary line filtered for ANY violation count, not just 0 violations:
# run_check counts stdout LINES as hits, so an unfiltered nonzero summary
# line would inflate this check's reported hit total by 1.
cd {{target}}
python3 "{{audit_script_dir}}/verify_features_order.py" "{{target}}" 2>/dev/null \
    | grep -v -E '^[0-9]+ files checked, [0-9]+ violations?$|^No Cargo.toml files found'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_features_order.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 23 — §L (2026-09-27 user 钦定): lombok accessor attributes
    # must not spell out `pub`; the macro already defaults to Public.
    ('no redundant explicit `pub` in lombok accessor attrs (§L)', '''
# lombok_macros::Visibility derives Default = Public
# (lombok-macros/src/visibility/enum.rs). So an accessor attribute with
# NO visibility already generates a pub accessor:
#
#     #[get(pub)]              ->  #[get]              (redundant)
#     #[get(pub, type(copy))]  ->  #[get(type(copy))]  (redundant)
#     #[set(pub)]              ->  #[set]              (redundant)
#     #[get_mut(pub)]          ->  #[get_mut]          (redundant)
#
# Narrowing visibility is a different matter and stays:
#
#     #[get(pub(crate))]  /  #[get_mut(pub(crate))]   — meaningful, kept
#
# The verifier matches a bare pub token (not followed by (), so every
# pub(crate) / pub(super) form passes untouched.
#
# The summary line is filtered for ANY count, not just 0 violations: the
# run_check helper counts stdout LINES as hits, so a trailing
# "N files checked, M violations" line would be counted as an extra violation
# and the audit would report M+1 (verified 2026-09-27: 1 real violation was
# reported as "2 hits"). Only the 0 violations form was filtered before, so
# every FAIL was off by one.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_redundant_accessor_pub.py" "{{target}}" 2>/dev/null \
    | grep -v -E '^[0-9]+ files checked, [0-9]+ violations?$'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_redundant_accessor_pub.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 24 — §L (2026-09-27 user 钦定): a BARE lombok accessor attribute
    # is redundant, because `#[derive(Data)]` already generates the accessor.
    # Sibling of check 22b (which catches the redundant explicit `pub`); this one
    # catches what is left after the `pub` is dropped.
    ('no bare redundant lombok accessor attrs (§L)', '''
# #[derive(Data)] IS Getter + GetterMut + Setter, so a field of a derived
# struct already gets its accessor. A bare attribute restates that default:
#
#     #[derive(Data)]
#     pub struct S {
#         #[get]        // redundant — Data already makes get_name()
#         #[get_mut]    // redundant — Data already makes get_mut_count()
#         #[set]        // redundant — Data already makes set_flag()
#         name: String,
#     }
#
# The attribute is KEPT when it carries information the derive cannot infer:
#
#     #[get(pub(crate))]      — narrows visibility (§17.14 exposure rule)
#     #[get(type(copy))]      — changes the return type
#     #[get(skip)] / #[set(skip)]  — opts the field OUT of generation
#
# A file with no accessor-generating derive is skipped entirely (there the
# attribute would be the only thing creating the accessor, so it is not
# redundant), and comment lines never count.
#
# The summary line is filtered for ANY count, not just 0 violations:
# run_check counts stdout LINES as hits, so a trailing
# "N files checked, M violations" would inflate the audit's count to M+1.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_redundant_accessor_attr.py" "{{target}}" 2>/dev/null \
    | grep -v -E '^[0-9]+ files checked, [0-9]+ violations?$'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_redundant_accessor_attr.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 25 — §17 CI never bumps versions / never writes `version =`
    # (2026-09-26 added). Companion script: verify_ci_no_bump.py.
    ('CI workflow forbids version bumps and version writes (§17)', '''
# Forbid any .github/workflows/*.yml step that bumps a Cargo.toml
# version (cc bump / crate bump with --patch/--minor/.../--release /
# --target-version) or rewrites a version = line via sed -i / perl -pi
# / python3 -c / awk >. Read-only grep ... | sed -E 's/.../.../'
# extraction of $VERSION for tag/commit-message is allowed.
# Allowlist: # ci-allow-version-write: <reason> on the line just
# above the violation exempts it (tight coupling).
cd {{target}}
python3 "{{audit_script_dir}}/verify_ci_no_bump.py" "{{target}}" \
    | grep -v -E '^(OK: [0-9]+ workflow|INFO: no .github/workflows)'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_ci_no_bump.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 23 — §1.3 keyword file purity (R1.3a) + first-line use super::*
    # (2026-09-26 user tightening).  Companion script:
    # verify_keyword_file_purity.py.  Replaces / extends the older
    # column-0 decl check (#16) and adds the first-line + use-centralized
    # checks for keyword files.
    ('keyword file purity + first-line use super::* (§1.3 / §6.3)', '''
# Per rust-standards §1.3 + §6.3 (2026-09-26 user tightening):
#   - Each keyword file (const.rs / static.rs / fn.rs / enum.rs /
#     struct.rs / trait.rs / impl.rs / type.rs / mod.rs) under src/
#     MUST be the only declaration kind it contains.
#   - First non-comment line MUST be use super::*; (the previous
#     exemption allowing direct /// doc comments on enum.rs /
#     struct.rs / type.rs is RETIRED).
#   - No use crate::xxx; / use std::xxx; / use external::xxx;
#     / use super::specific_path; outside the leading super::*.
cd {{target}}
python3 "{{audit_script_dir}}/verify_keyword_file_purity.py" "{{target}}" \\
    | grep -v -E '^=== keyword-file purity:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_keyword_file_purity.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 24 — §9.2 fn parameter style: no `impl Trait` in parameters.
    # (2026-09-26 user tightening).  Companion script:
    # verify_no_impl_trait_params.py.
    ('no impl Trait in fn parameters (§9.2)', '''
# Per rust-standards §9.2: fn parameters must use generic + where
# clause, not impl Trait.  Example:
#   fn parse<T: FromStr>(...)  ❌  inline bound
#   fn parse<T>(...) where T: FromStr  ✅
#   fn f(x: impl AsRef<str>)  ❌  impl param
#   fn f<T>(x: T) where T: AsRef<str>  ✅
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_impl_trait_params.py" "{{target}}" \\
    | grep -v -E '^=== no-impl-trait-fn-params:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_impl_trait_params.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 25 — moved to check 35 (consolidated; see 2026-09-26
    # third iteration).  verify_doc_comment_format.py is the
    # authoritative verifier; previously also wired here as
    # check 25.  Removed to avoid running the same script twice.
    # (2026-09-26 user tightening).

    # check 26 — §6.1 / §6.3 / §6.4 module-imports centralized.
    # (2026-09-26 user tightening).  Companion script:
    # verify_module_imports_centralized.py.  Audits lib.rs (private
    # `use` for std/external must be `pub use`), mod.rs (no // comments
    # + last-line use super::*), and keyword sub-files (only `use
    # super::*;` allowed + no long-path use anywhere).
    ('module imports centralized in lib.rs / mod.rs (§6.1 / §6.3 / §6.4)', '''
cd {{target}}
python3 "{{audit_script_dir}}/verify_module_imports_centralized.py" "{{target}}" \\
    | grep -v -E '^=== module-imports centralized:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_module_imports_centralized.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 27 — §6.1 lib.rs / mod.rs three-stage import order.
    # (2026-09-26 user tightening).  Companion script:
    # verify_lib_rs_order.py.
    ('lib.rs / mod.rs three-stage import order (§6.1)', '''
cd {{target}}
python3 "{{audit_script_dir}}/verify_lib_rs_order.py" "{{target}}" \
    | grep -v -E '^(=== |OK: 0 lib)'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_lib_rs_order.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 28 — §14.5 no comments in test files.  Replaces the older
    # regex-based check 14 (which used `^\s*//[^/]` and accidentally
    # excluded `///`).  Companion script: verify_no_test_comments.py.
    # Catches //, ///, and //! uniformly per round-3 user clarification.
    ('no comments in test files (§14.5)', '''
# Per rust-standards §14.5 (2026-09-12 round 3 user clarification,
# 2026-09-26 strengthening):
#   Tests have ZERO comments — no file-level //!, no per-fn ///,
#   no fn-body //.  Test fn name = documentation; assertion
#   message = expected behavior.  All three forms banned.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_test_comments.py" "{{target}}" \
    | grep -v -E '^=== no-comments-in-tests:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_test_comments.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 29 — §6.2 mod.rs `mod xxx;` MUST be bare (no visibility
    # prefix).  User original (2026-09-26): "mod.rs 的 mod 前面不能
    # 有可见性".  Companion: verify_mod_visibility.py.
    ('mod.rs `mod` declaration must be bare (§6.2)', '''
# Per rust-standards §6.2 (2026-09-26 user iteration): in any
# mod.rs, mod r#xxx; declarations MUST be bare — no pub mod,
# no pub(crate) mod, no pub(super) mod.  The visibility of
# items inside the module is controlled at the declaration site
# of the item itself, not on the mod line.  mod in mod.rs is
# always crate-internal (private to the parent module's
# namespace); the parent re-exports via the middle-stage
# pub use {...}; block if external visibility is needed.
cd {{target}}
python3 "{{audit_script_dir}}/verify_mod_visibility.py" "{{target}}" \
    | grep -v -E '^=== mod.rs mod visibility'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_mod_visibility.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 30 — §14 no #[allow(...)] / #[expect(...)] in production
    # code.  Companion to git-diff-scoped check 2 (PR review).  This
    # script scans the whole tree to catch historical accumulation.
    ('no `#[allow(...)]` in production (§14)', '''
# Per rust-standards rule 14 (user 原话, 2026-09-14): "从根源修复
# warn, 禁止使用 allow 宏".  clippy / rustc warnings must be
# fixed at source, not silenced with attribute macros.  This
# check is the tree-wide version of git-diff-scoped check 2;
# it catches #[allow(...)] accumulated over multiple PRs.
# Exemptions:  (a) #[allow(...)] inside #[cfg(test)] mod tests
# { ... } blocks (test helpers may silence unused warnings);
# (b) tests/ directory entirely (R14.7 self-contained).
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_allow_lints.py" "{{target}}" \
    | grep -v -E '^=== no-allow-lints:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_allow_lints.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 31 — §5.1 explicit type annotations for `let` bindings
    # of collection constructors.  Companion to check 12
    # (which only catches `Vec::new()` without `:` via a simpler
    # regex).  This script is more comprehensive on collection
    # types AND catches `Vec<_>` placeholder annotations.
    ('explicit type annotations for let bindings (§5.1)', '''
# Per rust-standards rule 6 (user 原话, 2026-09-26): "所有变量 /
# 参数 / 返回值必须显式类型".  Common pitfall: let items =
# Vec::new(); leaves the type ambiguous to the reader; must be
# let items: Vec<u32> = Vec::new();.  Same for HashMap /
# HashSet / BTreeMap / BTreeSet / VecDeque / LinkedList /
# BinaryHeap / String / Box / Rc / Arc.  Also catches
# let v: Vec<_> = ...collect(); which defeats the rule by
# leaving the element type implicit.
cd {{target}}
python3 "{{audit_script_dir}}/verify_explicit_type_annotations.py" "{{target}}" \
    | grep -v -E '^=== explicit-type-annotations:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_explicit_type_annotations.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 32 — §12 WASM crates (cdylib) MUST NOT have
    # `#[inline]` / `#[inline(always)]` / `#[inline(never)]`
    # attributes.  User original (2026-09-26): "WASM 项目禁止
    # 所有 inline 注解".  WASM codegen handles inlining itself;
    # manual annotations force wasm-opt to skip functions,
    # enlarging the binary 10-50% without measurable speedup.
    ('no `#[inline]` in cdylib crates (§12)', '''
# Per rust-standards rule 12 (2026-09-26 user clarification):
# "WASM 项目禁止所有 inline 注解".  Detection: find all
# Cargo.toml files with crate-type = ["cdylib", ...] and
# audit their src/ trees for #[inline] / #[inline(always)]
# / #[inline(never)].  Pure rust crates (no cdylib) are
# ignored.  When no cdylib crate exists in the tree, the
# script exits 0 with informational output.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_wasm_inline.py" "{{target}}" \
    | grep -v -E '^=== no-wasm-inline:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_wasm_inline.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 33 — §5.1 all `let` bindings MUST have explicit type
    # annotations.  Companion to check 31 (which only catches
    # collection constructors specifically).  This is the
    # comprehensive form: every `let`, including `let _ = ...`,
    # must declare its type.  User original (2026-09-26 third
    # iteration): "let 的类型必须要显示标注 (包含 let _ = )".
    ('all `let` bindings have explicit type annotation (§5.1)', '''
# Per rust-standards §5.1 (2026-09-26 third iteration, user 原话):
#   "let 的类型必须要显示标注 (包含 let _ = )"
# Every let <name> = <expr>; MUST declare the binding's type via
# let <name>: T = <expr>;.  Bare let x = 5; is forbidden.
# Likewise let _ = expr; is forbidden; use let _: T = expr;.
# Companion script: verify_let_type_annotations.py.
# Exempts: tests/ (R14.7 self-contained), if let / while let
# pattern guards, Rust 2024 let-chains (the regex won't match).
cd {{target}}
python3 "{{audit_script_dir}}/verify_let_type_annotations.py" "{{target}}" \
    | grep -v -E '^=== let-bindings-explicit-type:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_let_type_annotations.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 34 — §5.2 closure parameters MUST have explicit type
    # annotations.  User original (2026-09-26 third iteration):
    #   "闭包参数需要显示标注"
    # `|x| x * 2` is forbidden; use `|x: u32| x * 2`.  Exempts:
    # `||` (empty), `|..|` (rest), `|(a, b): &(T, U)|` (tuple
    # destructure with type annotation on whole tuple).
    ('closure parameters have explicit type annotation (§5.2)', '''
# Per rust-standards §5.2 (2026-09-26 third iteration, user 原话):
#   "闭包参数需要显示标注"
# Every closure parameter must have explicit : T annotation.
# |x| x + 1 is forbidden; use |x: u32| -> u32 { x + 1 }.
# Companion script: verify_closure_type_annotations.py.
# Exempts: tests/, empty ||, rest |..|, ref patterns
# |&x: &T|, tuple destructuring with type (pat): T.
cd {{target}}
python3 "{{audit_script_dir}}/verify_closure_type_annotations.py" "{{target}}" \
    | grep -v -E '^=== closure-params-explicit-type:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_closure_type_annotations.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 35 — §2.1 non-test fn / impl MUST have `///` doc
    # comment with proper Layer 1+2+3 format.  User original
    # (2026-09-26 third iteration): "非单侧的 fn 必须要符合格式
    # 的文档注释".  Tests are exempt (R14.5 forbids all comments
    # in test files; thus no doc-comment there either).
    ('non-test fn has compliant doc comment (§2.1 / §2.2)', '''
# Per rust-standards §2.1 + §2.2 (2026-09-26 third iteration,
# user 原话): "非单侧的 fn 必须要符合格式的文档注释".
#   Layer 1 (existence): every non-test fn / impl method needs
#     at least one /// line above it.
#   Layer 2 (completeness): every fn with non-self params OR
#     non-() return must have # Arguments / # Returns section.
#   Layer 3 (format): the doc-comment template structure is
#     exactly # Arguments + - Type - description /
#     # Returns + - Type: description.
# Tests are exempt (R14.5 says test files have ZERO comments).
# Companion script: verify_doc_comment_format.py (already
# existed pre-this-round, but is now wired as the §2.1/§2.2
# authoritative verifier — check 25).  This check 35 is the
# EXPLICIT strengthened entry per user iteration.
cd {{target}}
python3 "{{audit_script_dir}}/verify_doc_comment_format.py" "{{target}}" \
    | grep -v -E '^=== doc-comment format:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_doc_comment_format.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 36 — §1.3c strengthened (2026-09-26 third iteration):
    # hardcoded string literals (≥ 4 non-trivial chars) MUST live
    # in `const.rs`.  User original: "硬编码字符串必须要维护到
    # const.rs".  Exempts: const.rs itself, tests/, attribute
    # lines (`#[doc = "..."]` / `#[serde(rename = "...")]`),
    # format-macro format strings (`println!("...")`).
    ('hardcoded strings live in `const.rs` (§1.3c)', '''
# Per rust-standards §1.3c strengthened (2026-09-26 third
# iteration, user 原话): "硬编码字符串必须要维护到 const.rs".
# Every hardcoded string literal (≥ 4 non-trivial chars) in any
# non-const file MUST live in const.rs as a pub const.  This
# is the comprehensive form of the existing check 18 (which
# only covers fn.rs byte/char/multi-char literals).  Companion
# script: verify_hardcoded_strings.py.  Exempts: const.rs
# itself (canonical home), tests/ (R14.7 self-contained), attr
# lines (#[doc = "..."], #[serde(rename = "...")]), and format
# macro format strings (println!("...")).
cd {{target}}
python3 "{{audit_script_dir}}/verify_hardcoded_strings.py" "{{target}}" \
    | grep -v -E '^=== hardcoded-strings-to-const:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_hardcoded_strings.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 37 — §2.4 lib.rs MUST have leading `//!` doc block
    # (2026-09-26 fifth iteration).  User original: "对于 lib.rs
    # 必须要检查是否存在 //! 注释,注释第一行 //! 后是包名后面
    # 是一行 //! 再后面才是内容".  Mandatory structure:
    #
    #   //! <package_name>
    #   //!
    #   //! <description>
    #
    # Companion script: verify_lib_rs_doc_comment.py reads the
    # nearest Cargo.toml's [package].name to compare against the
    # first `//!` line text.
    ('lib.rs `//!` doc block structure (§2.4)', '''
# Per rust-standards §2.4 (2026-09-26 fifth iteration, user 原话):
#   "对于 lib.rs 必须要检查是否存在 //! 注释,注释第一行 //! 后是
#    包名后面是一行 //! 再后面才是内容"
# Every lib.rs MUST start with the canonical 3-line //! block:
#   1st line: //! <package_name> (text must equal [package].name)
#   2nd line: //! (empty separator)
#   3rd line: //! <description> (content)
# Companion script: verify_lib_rs_doc_comment.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_lib_rs_doc_comment.py" "{{target}}" \
    | grep -v -E '^=== lib.rs-doct-comment:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_lib_rs_doc_comment.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 38 — §6.5 `use ... as ...` import rename forbidden
    # (2026-09-26 user directive).  User original: "类型导入禁止使用
    # as 重命名...如果类型冲突才在使用的地方使用最短可区分的命名
    # 空间".  Any `as <ident>` inside a use statement (any visibility)
    # is a violation; conflicts are resolved by qualifying at the
    # usage site with the shortest distinguishable namespace
    # (e.g. `fmt::Result`, `io::Error`), never by aliasing the import.
    #
    # Companion script: verify_no_import_rename.py tracks use
    # statements including grouped multi-line blocks.
    ('no `as` rename in use statements (§6.5)', '''
# Per rust-standards §6.5 (2026-09-26, user 原话): "类型导入禁止使用
# as 重命名,如果类型冲突才在使用的地方使用最短可区分的命名空间"
# Companion script: verify_no_import_rename.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_import_rename.py" "{{target}}" \
    | grep -v -E '^=== no-import-rename:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_import_rename.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 38 — §17.3 / §17.12 direct `self.field` access forbidden
    # (2026-09-26 user directive).  User original: "禁止通过self直接
    # 操作字段,使用Data宏的get和set".  All production field reads /
    # writes go through Data-macro (or §17.11 hand-written) accessors.
    # Legal self.field positions: accessor bodies (get_*/set_*/
    # try_get_*), Debug/Display impl blocks, #[cfg(test)] / tests/.
    #
    # Companion script: verify_no_self_field_access.py tracks fn /
    # trait-impl / cfg(test) ranges via brace counting.
    ('no direct `self.field` access (§17.3 / §17.12)', '''
# Per rust-standards §17.3 / §17.12 (2026-09-26, user 原话): "禁止通过
# self直接操作字段,使用Data宏的get和set"
# Companion script: verify_no_self_field_access.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_self_field_access.py" "{{target}}" \
    | grep -v -E '^=== no-self-field-access:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_self_field_access.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),

    # check 40 -- 13.8 Cargo.toml top-level section header separation
    # (2026-09-27 user directive).  User original: "Cargo.toml different
    # configuration fields need a blank line between".  Every top-level
    # [section] header in any Cargo.toml MUST be preceded by exactly one
    # blank line if it follows non-section content.  Applies to all cargo
    # sections (package / workspace / workspace.dependencies /
    # dependencies / dev-dependencies / build-dependencies / lib /
    # bin / profile.dev / profile.release / patch.* / etc.).
    # Does NOT apply inside dep blocks (that's section 13.7 round-4).
    #
    # Companion script: verify_section_blanks.py.  Excludes target/,
    # ~/.cargo/registry/, and */tmp/test_*/ (crate-cli fixtures).
    ('Cargo.toml section headers separated by blank line (section 13.8)', '''
# Per rust-standards section 13.8 (2026-09-27, user directive):
# "Cargo.toml different configuration fields need a blank line between".
# Every top-level [section] header in any Cargo.toml MUST be preceded
# by exactly one blank line if it follows non-section content.
# Companion script: verify_section_blanks.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_section_blanks.py" "{{target}}" \
    | grep -v -E '^[0-9]+ files checked, [0-9]+ violations$|^No Cargo.toml'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_section_blanks.py exited $exit_code" >&2
fi
exit "$exit_code"
'''
),
    # check 41 — §6.6 same-root use statements must be aggregated into
    # one brace form (2026-09-27 user directive).  Two or more independent
    # TOP-LEVEL use statements sharing the same root segment (e.g.
    # use std::ffi::c_void; + use std::path::Path;) must be written as
    # use std::{ffi::c_void, path::Path};.
    #
    # Grouping is PER (root, visibility) — this is measured, not assumed.
    # rustfmt 1.9.0-stable reorders but never merges (imports_granularity
    # is nightly-only), and even nightly imports_granularity = "Crate"
    # keeps pub use std::... separate from private use std::..., i.e.
    # a visibility split is intentional re-export semantics, not drift.
    # Cross-visibility pairs are therefore EXEMPT.
    #
    # Other exemptions (all fixture-covered): different roots, glob +
    # non-glob coexistence, fn-body use (§6.4), #[cfg(test)] mod tests,
    # cfg-gated imports (merging would hoist the attribute onto the whole
    # group), rootless brace re-export blocks (§6.1 territory), and
    # same-root pairs separated by another §6.1 stage — §6.1 three-stage
    # order WINS over §6.6 aggregation (check 27 must not regress).
    #
    # Companion script: verify_use_aggregation.py.
    ('same-root `use` statements aggregated into one brace form (§6.6)', '''
# Per rust-standards §6.6 (2026-09-27 user directive): same crate/module
# root imports must be merged into a single brace form.  Grouping is
# per (root, visibility); §6.1 three-stage order takes precedence.
# Companion script: verify_use_aggregation.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_use_aggregation.py" "{{target}}" \
    | grep -v -E '^=== use-aggregation:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_use_aggregation.py exited $exit_code" >&2
fi
exit "$exit_code"
'''
),


    # check 44 (2026-09-28 user directive): "如果 rust 代码文件同级有目录,
    # 需要报错提示代码文件不能和目录在同一级,注意 lib.rs main.rs build.rs
    # mod.rs 这些除外".
    #
    # A keyword file is a LEAF of the module tree: mod r#fn; in mod.rs
    # resolves to <dir>/fn.rs and nothing else.  Once the same directory
    # also owns sub-modules, the reader must decide whether foo.rs
    # belongs to the parent scope or is a namespace peer of foo/ — two
    # conventions for one level of the tree.  The four entry files are
    # exempt precisely because their whole job is to be the parent of
    # sub-modules.
    #
    # ONE violation per offending DIRECTORY (not per file): the fix is
    # structural (move the files into their own sub-module dirs), so N
    # files in one directory = 1 finding to fix, not N.
    #
    # Companion script: verify_no_sibling_dirs.py.
    ('code file cannot share a directory level with sub-directories (§1.3d)', '''
# Per rust-standards §1.3d (2026-09-28 user directive): a directory that
# owns sub-modules must not also own .rs code files, except lib.rs /
# main.rs / build.rs / mod.rs.  Companion script: verify_no_sibling_dirs.py.
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_sibling_dirs.py" "{{target}}" \\
    | grep -v -E '^=== no-sibling-dirs \(§1\.3d\):'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_sibling_dirs.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_no_panicking_borrow.py.
    ('RefCell borrow guard must not be held across a re-entrant call (\u00a7borrow)', '''
# Per user directive 2026-09-30: "safe handling of all borrow failures".
# RefCell::borrow()/borrow_mut() panic when the cell is already borrowed;
# in WASM there is no try/catch, so a re-entrant borrow blanks the page. A
# one-line borrow is already safe and is deliberately not reported -- only a
# guard still in scope at a call that can re-enter is a violation.
# Companion script: verify_no_panicking_borrow.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_panicking_borrow.py" "{{target}}" \\
    | grep -v -E '^=== no-panicking-refcell-borrow:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_panicking_borrow.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_no_panicking_option_getter.py.
    # This one existed but nothing ran it, so a public `get_x()` that unwraps an
    # `Option<T>` the API documents as `None` was invisible to every caller.
    # Two dimensions: the call site (a getter used as if it returned a bare T)
    # and the declaration itself (a bare Option field on a `Data` struct whose
    # inner type is Copy, which is what makes the generated getter unwrap).
    # The declaration side is scoped to Copy inner types on purpose - for a
    # non-Copy inner type lombok already returns the Option, so flagging those
    # would be a false positive. Verified against a fixed tree (0 hits) and
    # against one reverted fix (exactly 1 hit, naming the struct and field).
    ('no panicking lombok getter on an Option field (R11.5)', '''
# Companion script: verify_no_panicking_option_getter.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_panicking_option_getter.py" "{{target}}" \\
    | grep -v -E '^=== panicking-getter-on-Option:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_panicking_option_getter.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_no_qualified_std_path.py
    # A sub-file that writes `std::fs::create_dir_all` has bypassed the
    # top-level import block, so the call does not resolve through the crate
    # root the way §6.1 intends. Scoped to the standard library because that is
    # where the duplicate-import churn is visible; the crate-name half of
    # §6.4 is verify_no_external_crate_path.
    ('no qualified std:: path in a sub-file (R6.3 std)', '''
# Companion script: verify_no_qualified_std_path.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_qualified_std_path.py" "{{target}}" \\
    | grep -v -E '^=== qualified-std-path:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_qualified_std_path.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_pub_group_order.py (+ fix_pub_group_order.py).
    # §18 (2026-10-07 user): inside one const.rs / static.rs every `pub`
    # item precedes any pub(crate)/pub(super)/private item, so the crate's
    # public surface reads as one group at the top of the file.
    ('pub before pub(crate) group order in const.rs/static.rs (§18)', '''
# Companion script: verify_pub_group_order.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_pub_group_order.py" "{{target}}" \\
    | grep -v -E '^=== pub-group-order:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_pub_group_order.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_const_visibility.py (+ fix_const_visibility.py).
    # §18 constants clause (2026-10-07 user, three rounds: "很多 pub 还是可以
    # 优化成 pub(crate),而且尤其是常量"): a `pub const`/`pub static` with zero
    # readers outside its owning crate is not public API - reduce it.
    # Consumers counted: other workspace crates' src, every tests/ dir,
    # examples/, benches/, src/bin/**, and src/main.rs of a lib+bin package
    # (the bin is a separate crate - see the CARGO_TOML incident, pitfalls §91).
    ('constant visibility: pub const/static is forbidden outright (§18, pitfalls §93)', '''
# Companion script: verify_const_visibility.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_const_visibility.py" "{{target}}" \\
    | grep -v -E '^=== const-visibility:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_const_visibility.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
    # Companion script: verify_no_pub_in_tests.py (+ fix_no_pub_in_tests.py).
    # §18 tests clause (2026-10-07 user: "所有的单测都不需要 pub"), NARROWED by
    # compile evidence (pitfalls §92): only single-reader items are flagged -
    # a tests/<sub>/const.rs item globbed by its parent mod.rs and a tests/mod.rs
    # `pub use` re-export are load-bearing, never flagged.
    ('no vestigial pub inside tests/ (§18 tests clause)', '''
# Companion script: verify_no_pub_in_tests.py
cd {{target}}
python3 "{{audit_script_dir}}/verify_no_pub_in_tests.py" "{{target}}" \\
    | grep -v -E '^=== no-pub-in-tests:'
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_no_pub_in_tests.py exited $exit_code" >&2
fi
exit "$exit_code"
'''),
]


def run_check(name, shell_template, target):
    cmd = shell_template.replace('{target}', target)
    r = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, cwd=target)
    # A wrapper propagates its verifier's verdict through the exit code, so
    # rc == 0 means "this check found nothing" no matter what the verifier
    # printed.  Historically the verdict was decided purely by "did stdout
    # print anything", which turned every verifier's own success trailer
    # into a hit: a wrapper whose `grep -v` filter had drifted out of sync
    # with the verifier's summary string reported a permanent, unfixable
    # false positive.  Trusting the exit code removes that whole class of
    # bug instead of chasing each summary string.  The per-wrapper
    # `grep -v` filters stay in place as a second line of defence.
    if r.returncode == 0:
        return name, []
    out = [l for l in r.stdout.strip().split('\n') if l]
    # A check that produces NO stdout can mean two very different things:
    # "scanned everything and found nothing" (a real pass) or "the
    # verifier script does not exist / crashed before printing" (a
    # vacuous pass).  python3 reports a missing file on stderr and
    # exits 2, so r.returncode catches that case — but the FAIL trailer
    # must go to stderr too, or it would be counted as a hit (see
    # pitfalls 45).  Guard on the script name appearing in stderr.
    if not out:
        missing = [
            l for l in r.stderr.split('\n')
            if 'No such file or directory' in l and '.py' in l
        ]
        if missing:
            return name, ['FAIL: companion verifier is missing — ' + missing[0].strip()]
        return name, [
            f'FAIL: check exited {r.returncode} with no stdout — {r.stderr.strip()[:200]}'
        ]
    return name, out


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET
    if not os.path.isdir(target):
        print(f'error: {target} is not a directory', file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(os.path.join(target, '.git')) and not os.path.isdir(os.path.join(target, '..', '.git')):
        print(f'warning: {target} does not appear to be a git repo (git diff may be empty)')

    # Diff-scoped guard. The checks below that call
    # `git diff --name-only origin/master` see an empty window when that
    # ref does not exist (a fork, a shallow clone, a repo with no such remote).
    # git writes the error to stderr and exits non-zero, but nothing here ever
    # looks at it — so those checks report PASS while having scanned no file
    # at all. Fail loudly instead of handing back a green summary that means
    # nothing.
    window = subprocess.run(
        ['git', '-C', target, 'diff', '--name-only', 'origin/master', 'HEAD', '--', '*.rs'],
        capture_output=True, text=True,
    )
    has_rust = False
    for _root, _dirs, files in os.walk(target):
        if 'target' in _root.split(os.sep) or '.git' in _root.split(os.sep):
            continue
        if any(f.endswith('.rs') for f in files):
            has_rust = True
            break
    if window.returncode != 0 and has_rust:
        detail = [
            line for line in (window.stderr or '').strip().splitlines()
            if 'usage:' not in line and not line.startswith(' ') and line.strip()
        ]
        print(
            'FAIL: 0. diff window is empty: `git diff origin/master` failed, '
            'so every diff-scoped check below would pass without reading a file.',
            file=sys.stderr,
        )
        if detail:
            print(f'  git said: {detail[-1]}', file=sys.stderr)
        print(
            '  Fix: fetch the ref (`git fetch origin master`) or point the '
            'audit at a base that exists.', file=sys.stderr,
        )
        return 1

    # Substitutions available in every shell template:
    #   {{target}}            — absolute path of the repo root being audited
    #   {{audit_script_dir}}  — directory holding this audit script (for invoking
    #                            companion scripts like verify_test_imports_centralized.sh)
    audit_script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.abspath(target)
    substitutions = {'target': target, 'audit_script_dir': audit_script_dir}

    def substitute(template: str) -> str:
        for k, v in substitutions.items():
            template = template.replace('{{' + k + '}}', v)
        return template

    results = []
    for i, (name, shell_template) in enumerate(CHECKS, start=1):
        cmd = substitute(shell_template)
        n, out = run_check(name, cmd, target)
        if out:
            results.append((n, 'FAIL', out))
            print(f'FAIL: {i}. {n}: {len(out)} hits')
            for o in out[:5]:
                print(f'  {o}')
        else:
            results.append((n, 'PASS', []))
            print(f'PASS: {i}. {n}')

    passed = sum(1 for r in results if r[1] == 'PASS')
    print(f'\n=== SUMMARY: {passed}/{len(results)} PASS ===')
    print('See references/audit-pitfalls.md for the false-positive list')
    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    sys.exit(main())