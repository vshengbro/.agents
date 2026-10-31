#!/usr/bin/env python3
"""Self-test for the audit's verdict logic (`audit_rust_standards.run_check`).

Why this exists
---------------
`run_check()` used to decide every check's PASS/FAIL from the subprocess
EXIT CODE.  That is correct for a wrapper template (one that ends with an
explicit `exit "$exit_code"`), because the wrapper forwards its companion
verifier's verdict through the exit status.  It is WRONG for an inline
template — a bare `git diff ... | grep ... | head -20` pipeline — whose
exit status is that of the LAST stage (`head`), i.e. 0 whether it printed
one violation or a thousand.

The consequence was 14 structurally unfailable checks: checks 1-14 of the
audit, covering R11.4 (production unwrap/expect/panic), R14 (#[allow] in
production), R5.1 (implicit Vec::new()), `#[test]`/`#[cfg(test)]` in
production, long-path `use crate::`, inline generic bounds, non-keyword
production filenames, `r#` on a non-keyword file, and the mod.rs
`use super::*;` rules.  A real violation in any of them reported PASS.

The fix routes each template shape to the signal that actually carries
its verdict: exit code for wrappers, stdout for inline templates.

Fixtures assert, for BOTH shapes:
  * a violating template reports FAIL with the hit visible
  * a clean template reports PASS
  * a wrapper that prints a success trailer still reports PASS (the
    regression the exit-code rule was introduced to fix must stay fixed)
  * a wrapper whose companion verifier is missing reports FAIL, not a
    silent pass

Run: python3 self_test_audit_verdict.py
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

_spec = importlib.util.spec_from_file_location(
    "audit_rust_standards", SCRIPT_DIR / "audit_rust_standards.py"
)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

# A wrapper: stdout may carry the verifier's success trailer, the exit
# code carries the verdict.  The `exit "$exit_code"` line is the marker
# that identifies a wrapper template.
WRAPPER_HITS = """cd {target}
echo "src/fn.rs: +1 new violation"
exit_code=1
exit "$exit_code"
"""

WRAPPER_CLEAN = """cd {target}
echo "OK: 3 file(s) checked, no violation"
exit_code=0
exit "$exit_code"
"""

WRAPPER_MISSING = """cd {target}
python3 "{target}/definitely_not_a_real_verifier.py" "{target}"
exit_code=${PIPESTATUS[0]}
if [ "$exit_code" -ne 0 ]; then
    echo "FAIL: verify_missing.py exited $exit_code" >&2
fi
exit "$exit_code"
"""

# An inline template: a `... | head -N` pipeline.  Its exit status is
# `head`'s (always 0) no matter what it printed.
INLINE_HITS = """cd {target}
echo "src/fn.rs: +1 new violation"
"""

INLINE_CLEAN = """cd {target}
true
"""


def run(template: str) -> tuple[str, list[str]]:
    return audit.run_check("probe", template, "/tmp")


def check_index(name: str) -> int:
    """1-based index of a check in the audit's CHECKS list."""
    for index, (check_name, _template) in enumerate(audit.CHECKS, start=1):
        if check_name == name:
            return index
    raise KeyError(name)


def main() -> int:
    failures: list[str] = []

    # --- wrapper shape: exit code is the verdict ---
    name, out = run(WRAPPER_HITS)
    if not out:
        failures.append("wrapper with hits reported PASS (exit-code rule broken)")
    name, out = run(WRAPPER_CLEAN)
    if out:
        failures.append(f"wrapper success trailer counted as hits: {out}")
    name, out = run(WRAPPER_MISSING)
    if not out:
        failures.append("wrapper with a missing verifier reported PASS (vacuous pass)")

    # --- inline shape: stdout is the verdict ---
    name, out = run(INLINE_HITS)
    if not out:
        failures.append(
            "inline template with hits reported PASS — this is the bug the "
            "self-test exists to catch"
        )
    if out and "src/fn.rs" not in out[0]:
        failures.append(f"inline hit lost its detail: {out}")
    name, out = run(INLINE_CLEAN)
    if out:
        failures.append(f"inline clean template reported hits: {out}")

    # --- the shape detector itself ---
    if not audit._is_wrapper_template(WRAPPER_HITS):
        failures.append("wrapper template not detected as a wrapper")
    if audit._is_wrapper_template(INLINE_HITS):
        failures.append("inline template misdetected as a wrapper")

    # --- every template in the real CHECKS list is classified ---
    #     consistently with its own shape: a wrapper must end with the
    #     explicit exit, an inline template must not contain one.
    for check_name, template in audit.CHECKS:
        is_wrapper = audit._is_wrapper_template(template)
        has_exit = 'exit "$exit_code"' in template
        if is_wrapper != has_exit:
            failures.append(f"shape detection disagrees for check {check_name!r}")
        if not is_wrapper and "exit " in template:
            failures.append(
                f"inline check {check_name!r} contains an explicit exit; it "
                "would be classified by the wrong verdict signal"
            )

    # --- every inline template must actually FIRE on a violation ---
    # A correct verdict signal is only half the job: the template itself
    # can still be broken (check 4 once was — `grep -B5` could not reach
    # the file header, and its BRE pattern `^\+` was invalid).  Each
    # inline template is run against a synthetic diff that violates it,
    # and must print something.
    inline_violations = [
        ("#[allow] in production", "+#[allow(dead_code)]\n"),
        ("production unwrap/expect/panic", "+    v.unwrap();\n"),
        ("long-path use crate::xxx in sub-files", "+use crate::x::Y;\n"),
        ("inline generic bounds", "+fn f<Abc: Clone>(v: Abc) {}\n"),
        ("implicit Vec::new() without type", "+    let v = Vec::new();\n"),
    ]
    for check_name, added_line in inline_violations:
        template = dict((n, t) for n, t in audit.CHECKS)[check_name]
        idx = check_index(check_name)
        # The list above is the set of INLINE checks.  A check that has
        # been converted to a wrapper no longer reads a git diff, so the
        # synthetic-diff probe cannot be applied to it — and leaving it in
        # the list made this self-test fail for the wrong reason ("does
        # not read a git diff") instead of catching the real regression.
        # Keep the list honest instead.
        if audit._is_wrapper_template(template):
            failures.append(
                f"check {idx} ({check_name}) is a wrapper but is listed as an "
                "inline check in the non-vacuity probe"
            )
            continue
        # Build a diff stream whose added line sits far from the file
        # header, which is the case the old `grep -B5` template missed.
        diff = (
            "diff --git a/src/probe.rs b/src/probe.rs\n"
            "--- a/src/probe.rs\n"
            "+++ b/src/probe.rs\n"
            "@@ -1,3 +1,20 @@\n"
            " context\n"
            " context\n"
            " context\n"
            " context\n"
            " context\n"
            " context\n"
            " context\n"
            " context\n"
            + added_line
        )
        cmd = template.replace("{{target}}", "/tmp").replace(
            "{{audit_script_dir}}", str(SCRIPT_DIR))
        # Replace the git diff with the synthetic stream.  The pattern
        # must consume the WHOLE command up to the pipe, otherwise the
        # heredoc terminator ends up glued to `| awk` and the filter
        # never runs.  `cat` is used (not `echo`) so the diff arrives
        # verbatim on stdin.
        cmd, count = re.subn(
            r"git diff[^\n]*?(?=\s*\|\s*|\s*$)",
            "cat > /tmp/_audit_selftest_diff <<'DIFF_EOF'\n" + diff + "DIFF_EOF",
            cmd,
            count=1,
        )
        if count == 0 or "DIFF_EOF" not in cmd:
            failures.append(
                f"check {idx} ({check_name}) does not read a git diff; the "
                "non-vacuity assertion could not be applied"
            )
            continue
        # Feed the synthetic diff in through the same path the template
        # uses: replace the git diff invocation with `cat <file>`.
        cmd = cmd.replace(
            "cat > /tmp/_audit_selftest_diff <<'DIFF_EOF'\n" + diff + "DIFF_EOF",
            "cat /tmp/_audit_selftest_diff",
        )
        Path("/tmp/_audit_selftest_diff").write_text(diff)
        proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
        Path("/tmp/_audit_selftest_diff").unlink(missing_ok=True)
        if not proc.stdout.strip():
            failures.append(
                f"check {idx} ({check_name}) printed nothing on a violating "
                "diff — the template itself is broken"
            )
            if proc.stderr.strip():
                failures.append(
                    f"  (stderr: {proc.stderr.strip()[:120]})"
                )

    # --- the real §14.4 wrappers must FIRE on a real violation ------
    # The inline probe above can no longer cover the §14.4 checks: they
    # are wrappers now, and a wrapper reads the TREE, not a diff.  A
    # wrapper is unfailable in exactly the way an inline pipeline used to
    # be — its exit code comes from the companion verifier, so if the
    # verifier is wired wrong (wrong path, wrong argument, a `grep` that
    # swallows everything) the check reports PASS forever.  Probe them
    # against a real fixture directory: a violating production file must
    # make the wrapper FAIL.
    wrapper_fixtures = [
        (
            "#[test] in production",
            "pkg/src/production.rs",
            "pub fn helper() -> usize {\n    1\n}\n\n#[test]\nfn bare_test() {\n"
            "    assert_eq!(helper(), 1);\n}\n",
        ),
        (
            "#[cfg(test)] in production",
            "pkg/src/production.rs",
            "pub fn helper() -> usize {\n    1\n}\n\n#[cfg(test)]\nmod tests {\n"
            "    use super::*;\n\n    #[test]\n    fn inner() {\n"
            "        assert_eq!(helper(), 1);\n    }\n}\n",
        ),
    ]
    with tempfile.TemporaryDirectory() as fixture_tmp:
        for check_name, rel, content in wrapper_fixtures:
            idx = check_index(check_name)
            template = dict((n, t) for n, t in audit.CHECKS)[check_name]
            if not audit._is_wrapper_template(template):
                failures.append(
                    f"check {idx} ({check_name}) was expected to be a wrapper"
                )
                continue
            root = Path(fixture_tmp) / check_name.replace(" ", "_").replace(
                "#", ""
            ).replace("(", "").replace(")", "")
            target_file = root / rel
            target_file.parent.mkdir(parents=True, exist_ok=True)
            (root / "pkg" / "Cargo.toml").write_text(
                '[package]\nname = "pkg"\nversion = "0.1.0"\n'
            )
            target_file.write_text(content)
            cmd = template.replace("{{target}}", str(root)).replace(
                "{{audit_script_dir}}", str(SCRIPT_DIR)
            )
            proc = subprocess.run(
                ["bash", "-c", cmd], capture_output=True, text=True, cwd=str(root)
            )
            if proc.returncode == 0:
                failures.append(
                    f"check {idx} ({check_name}) reported PASS on a violating "
                    f"fixture — the wrapper cannot fail"
                )
            elif not proc.stdout.strip():
                failures.append(
                    f"check {idx} ({check_name}) failed but printed no detail"
                )

    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST OK: audit verdict logic (wrapper=exit code, inline=stdout)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
