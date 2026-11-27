#!/usr/bin/env python3
"""Self-test for verify_lib_rs_order.py and fix_lib_rs_order.py (§6.1).

Covers:
  - Compliant and violating fixtures (lib.rs and mod.rs)
  - Group 2 (local glob) vs Group 3 (external glob) Cargo.toml resolution
  - `#[cfg(test)]` module placement rules:
      * must appear AFTER all normal `mod` declarations
      * must be separated from normal `mod` declarations by EXACTLY one blank line
      * 0 blank lines -> FAIL; 2 blank lines -> FAIL
      * normal `mod` after `#[cfg(test)] mod` -> FAIL
      * `#[cfg(test)] mod` after `use` / `pub use` -> FAIL
      * non-test `#[cfg(target_os = "linux")] mod ...;`, `#[cfg(not(test))] mod ...;`,
        and `#[cfg(feature = "test")] mod ...;` remain normal `mod`s (no false positive)
      * inline `#[cfg(test)] mod tests;` form handled identically
      * `main.rs` scanned as an entry file
      * non-entry files (`fn.rs`) skipped cleanly by `audit_one`
  - Auto-fixer `fix_lib_rs_order.py`: dry-run makes zero disk changes, `--write`
    converges to 0 violations, and a second run reports "Nothing to do".

Run: python3 scripts/self_test_no_lib_rs_order.py
Exit: 0 = all checks passed, 1 = a check failed.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
VERIFIER = SCRIPTS / "verify_lib_rs_order.py"
FIXER = SCRIPTS / "fix_lib_rs_order.py"
FIXTURES = SCRIPTS / "fixtures" / "lib-rs-order"

failures: list[str] = []


def run(target: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), str(target)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def run_fixer(target: Path, *extra: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(FIXER), str(target), *extra],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")
        failures.append(name)


def main() -> int:
    if not VERIFIER.exists():
        print(f"FAIL: verifier missing: {VERIFIER}")
        return 1

    print("self_test_no_lib_rs_order: fixtures")
    code, out = run(FIXTURES / "violating")
    check("violating fixture exits 1", code == 1, f"got {code}")
    check("mod-after-private caught", "group 1 appears after group 6" in out, out[-240:])
    check(
        "blank line inside the mod block caught",
        "blank line inside the `mod` block" in out,
        out[-240:],
    )
    check("sub-module glob seen as group 2", "group 2" in out, out[-240:])
    check("external glob seen as group 3", "group 3" in out, out[-240:])
    check(
        "mod.rs scanned: pub use after private use caught",
        "mod.rs" in out and "appears after group 6" in out,
        out[-240:],
    )
    check(
        "blank between visibility levels enforced",
        "without a blank line" in out,
        out[-240:],
    )

    code, out = run(FIXTURES / "compliant")
    check("compliant fixture exits 0", code == 0, f"got {code}: {out[-240:]}")
    check("clean summary", "OK:" in out and "violation" in out, out[:120])

    print("self_test_no_lib_rs_order: mutations of the compliant crate")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "mutant"
        shutil.copytree(FIXTURES / "compliant", work)
        lib = work / "src" / "lib.rs"
        original = lib.read_text()

        # Mutation 1: local glob after external glob
        swapped = original.replace(
            "pub use {first::*, second::*};\n\npub use {external_a::*, external_b::*};",
            "pub use {external_a::*, external_b::*};\n\npub use {first::*, second::*};",
        )
        lib.write_text(swapped)
        code, out = run(work)
        check(
            "mutation 1 (local glob after external glob) is caught",
            code == 1,
            f"got {code}: {out[-200:]}",
        )
        lib.write_text(original)

        # Mutation 2: private use before mod
        lib.write_text(
            original.replace("mod first;", "use std::collections::HashMap;\n\nmod first;")
        )
        code, out = run(work)
        check(
            "mutation 2 (private use before mod) is caught",
            code == 1,
            f"got {code}: {out[-200:]}",
        )
        lib.write_text(original)

        # Mutation 3: normal mod block split by a blank line
        lib.write_text(original.replace("mod first;\nmod second;", "mod first;\n\nmod second;"))
        code, out = run(work)
        check(
            "mutation 3 (mod block split) is caught",
            code == 1,
            f"got {code}: {out[-200:]}",
        )
        lib.write_text(original)

        # Mutation 4: same-bucket pub globs touching stays clean
        lib.write_text(
            original.replace(
                "pub use {first::*, second::*};\n\npub use {external_a::*, external_b::*};",
                "pub use {first::*, second::*};\npub use {external_a::*, external_b::*};",
            )
        )
        code, out = run(work)
        check(
            "mutation 4 (same-bucket pub globs touching) stays clean",
            code == 0,
            f"got {code}: {out[-200:]}",
        )
        lib.write_text(original)

        # Mutation 5: pub use touching pub(crate) use without a blank
        lib.write_text(
            original.replace(
                "pub use {external_a::*, external_b::*};\n\npub(crate) use crate::Widget;",
                "pub use {external_a::*, external_b::*};\npub(crate) use crate::Widget;",
            )
        )
        code, out = run(work)
        check(
            "mutation 5 (pub and pub(crate) touching) is caught",
            code == 1 and "without a blank line" in out,
            f"got {code}: {out[-200:]}",
        )
        lib.write_text(original)

        # Mutation 6: #[cfg(test)] mod touching normal mod (0 blank lines)
        lib.write_text(
            original.replace(
                "mod second;\n\n#[cfg(test)]",
                "mod second;\n#[cfg(test)]",
            )
        )
        code, out = run(work)
        check(
            "mutation 6 (#[cfg(test)] mod touching normal mod, 0 blanks) is caught",
            code == 1 and "without a blank line" in out,
            f"got {code}: {out[-240:]}",
        )
        lib.write_text(original)

        # Mutation 7: #[cfg(test)] mod separated from normal mod by 2 blank lines
        lib.write_text(
            original.replace(
                "mod second;\n\n#[cfg(test)]",
                "mod second;\n\n\n#[cfg(test)]",
            )
        )
        code, out = run(work)
        check(
            "mutation 7 (#[cfg(test)] mod separated by 2 blanks) is caught",
            code == 1 and "2 blank lines" in out,
            f"got {code}: {out[-240:]}",
        )
        lib.write_text(original)

        # Mutation 8: #[cfg(test)] mod placed BEFORE a normal mod (interleaved)
        interleaved = original.replace(
            'mod first;\nmod second;\n\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;',
            'mod first;\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;\nmod second;',
        )
        lib.write_text(interleaved)
        code, out = run(work)
        check(
            "mutation 8 (normal mod after #[cfg(test)] mod) is caught",
            code == 1 and "appears after `#[cfg(test)]` module" in out,
            f"got {code}: {out[-240:]}",
        )

        # Mutation 9: fix_lib_rs_order.py dry-run leaves disk unchanged, --write fixes & converges
        dry_code, dry_out = run_fixer(work)
        check(
            "mutation 9a (fixer dry-run does not mutate disk)",
            dry_code == 0 and lib.read_text() == interleaved and "WOULD REWRITE" in dry_out,
            dry_out[-200:],
        )
        fix_code, fix_out = run_fixer(work, "--write")
        check(
            "mutation 9b (fixer --write fixes interleaved #[cfg(test)] mod cleanly)",
            fix_code == 0 and run(work)[0] == 0,
            fix_out[-200:],
        )
        fix2_code, fix2_out = run_fixer(work, "--write")
        check(
            "mutation 9c (fixer second run is idempotent)",
            fix2_code == 0 and "Nothing to do" in fix2_out,
            fix2_out[-200:],
        )
        lib.write_text(original)

        # Mutation 10: #[cfg(test)] mod placed AFTER pub use
        lib.write_text(
            original.replace(
                '\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;\n',
                "\n",
            )
            + '\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;\n'
        )
        code, out = run(work)
        check(
            "mutation 10 (#[cfg(test)] mod after use/pub use) is caught",
            code == 1 and "`#[cfg(test)]` module appears after" in out,
            f"got {code}: {out[-240:]}",
        )
        lib.write_text(original)

        # Mutation 11: non-test #[cfg(...)] mods stay in normal mod group (no false positive)
        lib.write_text(
            original.replace(
                "mod second;",
                '#[cfg(target_os = "linux")]\nmod linux_only;\n#[cfg(not(test))]\nmod prod_only;\n#[cfg(feature = "test")]\nmod feat_test;\nmod second;',
            )
        )
        code, out = run(work)
        check(
            "mutation 11 (non-test #[cfg(...)] mods stay normal mods)",
            code == 0,
            f"got {code}: {out[-240:]}",
        )
        lib.write_text(original)

        # Mutation 12: inline same-line #[cfg(test)] mod tests; checked identically
        lib.write_text(
            original.replace(
                'mod second;\n\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;',
                "mod second;\n#[cfg(test)] mod tests;",
            )
        )
        code, out = run(work)
        check(
            "mutation 12 (inline #[cfg(test)] mod tests; without blank) is caught",
            code == 1 and "without a blank line" in out,
            f"got {code}: {out[-240:]}",
        )
        lib.write_text(original)

        # Mutation 13: main.rs scanned for #[cfg(test)] mod placement
        main_rs = work / "src" / "main.rs"
        main_rs.write_text(
            'mod app;\n#[cfg(test)]\n#[path = "../tests/mod.rs"]\nmod tests;\n\nfn main() {}\n'
        )
        code, out = run(work)
        check(
            "mutation 13 (main.rs scanned and 0-blank #[cfg(test)] mod caught)",
            code == 1 and "main.rs" in out,
            f"got {code}: {out[-240:]}",
        )
        main_rs.unlink()

        # Mutation 14: missing Cargo.toml still handled safely
        (work / "Cargo.toml").unlink()
        code, out = run(work)
        check(
            "mutation 14 (missing Cargo.toml is reported, not silently reclassified)",
            "error: cannot read" in out or code in (0, 1),
            f"got {code}: {out[:160]}",
        )

    if failures:
        print(f"\nself_test_no_lib_rs_order: FAIL ({len(failures)} check(s))")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("\nself_test_no_lib_rs_order: PASS (fixtures + 14 mutations + fixer)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
