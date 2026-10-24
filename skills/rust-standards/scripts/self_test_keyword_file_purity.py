#!/usr/bin/env python3
"""Self-test for verify_keyword_file_purity.py (§1.3 / §1.4).

The rule under test is the keyword-file purity of the nine keyword file
names plus the §1.4 "not a keyword file name" rejection. The behaviour that
needs proving is the gate contract: `staged_file_gate.py` materialises the
HEAD version of a staged file next to the working file and appends a
`.head-baseline.rs` suffix to that copy. The copy is the SAME file, so the
keyword name of the original decides every name-based rule.

Before the suffix was stripped, the baseline copy was judged by the name
`const.rs.head-baseline.rs`, which is not a keyword name, so the copy
produced a §1.4 name finding instead of the real §1.3 finding. The two
counts were equal (one finding each), so the gate's before/after delta was
zero and the hook answered "0 new violations - commit allowed" while a `fn`
sat in `const.rs`. The rule was invisible for EVERY keyword file of EVERY
repo.

Run: python3 scripts/self_test_keyword_file_purity.py
Exit: 0 = all checks passed, 1 = a check failed.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
VERIFIER = SCRIPTS / "verify_keyword_file_purity.py"
FIXTURES = SCRIPTS / "fixtures" / "keyword-file-purity"

failures: list[str] = []


def run(target: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), str(target)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' - ' + detail) if detail else ''}")
        failures.append(name)


def main() -> int:
    if not VERIFIER.exists():
        print(f"FAIL: verifier missing: {VERIFIER}")
        return 1

    print("self_test_keyword_file_purity: fixtures")
    code, out = run(FIXTURES / "violating")
    check("violating fixture exits 1", code == 1, f"got {code}")
    check(
        "forbidden decl in const.rs is caught",
        "forbidden decl in const.rs file" in out,
        out[-240:],
    )
    check(
        "no phantom file-name finding",
        "is not a keyword file name" not in out,
        out[-240:],
    )

    code, out = run(FIXTURES / "compliant")
    check("compliant fixture exits 0", code == 0, f"got {code}: {out[-240:]}")

    print("self_test_keyword_file_purity: gate baseline copies")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "gate"
        shutil.copytree(FIXTURES / "violating", work)
        (work / "src" / "const.rs").rename(work / "src" / "const.rs.head-baseline.rs")
        code, out = run(work)
        check(
            "baseline copy reports the real violation",
            code == 1 and "forbidden decl in const.rs file" in out,
            f"got {code}: {out[-240:]}",
        )
        check(
            "baseline copy is not judged by its suffixed name",
            "is not a keyword file name" not in out,
            out[-240:],
        )

        shutil.rmtree(work)
        shutil.copytree(FIXTURES / "compliant", work)
        (work / "src" / "const.rs").rename(work / "src" / "const.rs.head-baseline.rs")
        code, out = run(work)
        check(
            "compliant baseline copy stays clean",
            code == 0,
            f"got {code}: {out[-240:]}",
        )

    if failures:
        print(f"\nself_test_keyword_file_purity: FAIL ({len(failures)} check(s))")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("\nself_test_keyword_file_purity: PASS (fixtures + gate baseline copy)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
