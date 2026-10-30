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
import sys
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

    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST OK: audit verdict logic (wrapper=exit code, inline=stdout)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
