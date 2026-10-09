#!/usr/bin/env python3
"""Self-test for verify_no_qualified_std_path.py + fix_no_qualified_std_path.py.

Run:  python3 scripts/self_test_no_qualified_std_path.py

Coverage (every case is a file written into a scratch crate tree):
  1. plain consumed path -> 1 hit; `use` line -> 0 hits; top-level lib.rs exempt
  2. string / char literal masking, incl. multi-line strings whose interior
     line spells `std::...` (whole-file blanking, not per-line)
  3. lifetime/char trap: `SplitN<'_, char>` on the line must not swallow a
     real hit, and a hit after `'a ... '-'` still registers
  4. raw string with embedded quotes (`r#"{"a":1}"#`) must not swallow later
     hits (backreference-delimited scan)
  5. macro-token exemption: `macro_rules!` / `quote!` bodies are emitted
     downstream, not consumed -> 0 hits
  6. fixer: rewrites sites, writes the root import, demotes colliding leaves
     (`std::io::Error` next to `std::error::Error` -> `io::Error` + `use
     std::io;`), converges to 0 findings, idempotent on a second run

Exits 0 when every assertion holds, 1 otherwise.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / "verify_no_qualified_std_path.py"
FIXER = HERE / "fix_no_qualified_std_path.py"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok: {name}")
    else:
        FAILURES.append(f"{name} {detail}")
        print(f"  FAIL: {name} {detail}")


def run(script: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )
    return r.returncode, r.stdout + r.stderr


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def make_crate(tmp: Path, files: dict[str, str]) -> Path:
    crate = tmp / "demo"
    write(crate, "Cargo.toml", '[package]\nname = "demo"\nversion = "0.1.0"\n')
    write(crate, "src/lib.rs", "mod thing;\n")
    for rel, text in files.items():
        write(crate, rel, text)
    return crate


def hits_of(output: str) -> int:
    for line in output.splitlines():
        if "violation(s) in" in line:
            tokens = line.replace("===", " ").split()
            return int(tokens[tokens.index("violation(s)") - 1])
    return -1


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="qstd-selftest-"))
    try:
        # 1. plain hit, use-line, top-level exemption
        crate = make_crate(
            tmp,
            {
                "src/thing/fn.rs": "pub fn f(p: &str) -> usize {\n    std::fs::read(p).unwrap().len()\n}\n",
                "src/thing/other_fn.rs": "use std::fs;\n\npub fn g() {}\n",
                "src/thing/mod.rs": "mod r#fn;\n",
            },
        )
        write(crate, "src/lib.rs", "mod thing;\n\npub fn top() -> std::fs::Metadata {\n    todo!()\n}\n")
        _, out = run(VERIFIER, str(crate))
        check("plain hit + use-line + top-level", hits_of(out) == 1, out)

        # 2. literals incl. multi-line string interior
        crate2 = make_crate(
            tmp / "c2",
            {
                "src/thing/fn.rs": (
                    'pub fn f() {\n    let s = "std::fs::read";\n'
                    "    let m = \"line1\nstd::collections::HashMap::new()\nline3\";\n"
                    "    let c = '\'';\n    std::thread::sleep(std::time::Duration::from_secs(1));\n}\n"
                ),
            },
        )
        _, out = run(VERIFIER, str(crate2))
        check("string/multi-line masking keeps code hits", hits_of(out) == 2, out)

        # 3. lifetime + char trap
        crate3 = make_crate(
            tmp / "c3",
            {
                "src/thing/fn.rs": (
                    "pub fn f(p: &str) {\n"
                    "    let mut it: std::str::SplitN<'_, char> = p.splitn(2, '-');\n"
                    "    let _ = it.next();\n}\n"
                ),
            },
        )
        _, out = run(VERIFIER, str(crate3))
        check("lifetime+char trap", hits_of(out) == 1, out)

        # 4. raw string with quotes before a real hit
        crate4 = make_crate(
            tmp / "c4",
            {
                "src/thing/fn.rs": (
                    'pub fn f() {\n    let j = r#"{"a":1}"#;\n'
                    "    std::io::stdout();\n}\n"
                ),
            },
        )
        _, out = run(VERIFIER, str(crate4))
        check("raw-string trap", hits_of(out) == 1, out)

        # 5. macro-token bodies exempt
        crate5 = make_crate(
            tmp / "c5",
            {
                "src/thing/macro.rs": (
                    "#[macro_export]\nmacro_rules! mk {\n"
                    "    () => { std::sync::Arc::new(1) };\n}\n"
                ),
                "src/thing/fn.rs": (
                    "pub fn q() -> proc_macro2::TokenStream {\n"
                    "    quote! { impl std::fmt::Debug for X {} }\n}\n"
                ),
            },
        )
        _, out = run(VERIFIER, str(crate5))
        check("macro-token exemption", hits_of(out) == 0, out)

        # 6. fixer end-to-end incl. dual-Error demotion
        crate6 = make_crate(
            tmp / "c6",
            {
                "src/thing/fn.rs": (
                    "pub fn f() -> Result<(), std::io::Error> { todo!() }\n"
                    "pub fn g() -> Box<dyn std::error::Error> { todo!() }\n"
                ),
            },
        )
        rc, out = run(FIXER, "--write", str(crate6))
        fn_text = (crate6 / "src/thing/fn.rs").read_text()
        lib_text = (crate6 / "src/lib.rs").read_text()
        check(
            "fixer tails",
            "Result<(), io::Error>" in fn_text and "Box<dyn Error>" in fn_text,
            fn_text,
        )
        check(
            "fixer root imports",
            "use std::error::Error;" in lib_text and "use std::io;" in lib_text,
            lib_text,
        )
        _, out = run(VERIFIER, str(crate6))
        check("fixer converges", hits_of(out) == 0, out)
        lib_before = lib_text
        run(FIXER, "--write", str(crate6))
        check(
            "fixer idempotent",
            (crate6 / "src/lib.rs").read_text() == lib_before
            and (crate6 / "src/thing/fn.rs").read_text() == fn_text,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if FAILURES:
        print(f"\nSELF-TEST FAILED: {len(FAILURES)} assertion(s)")
        return 1
    print("\nSELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
