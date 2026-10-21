#!/usr/bin/env python3
"""Self-test for doc_comment_audit.py — the §2 doc fixer must never write into tests/.

Root and member integration-test trees forbid comments under section 14.5.
That includes helper functions and impl blocks without test attributes. The
production documentation fixer must leave these trees unchanged while still
detecting and fixing missing documentation in production code. Both direct
entry points and CLI scope selection must preserve this ownership contract.

Cases (each must hold; a failure names the case, not just "self-test failed"):

  1 direct_entries_never_write_tests    audit_one()/fix_one() on every tests file
  2 cli_whole_repo_scan_never_writes_tests   whole-repo `git ls-files` sweep
  3 cli_explicit_files_never_writes_tests    explicit `--files` of tests paths
  4 cli_explicit_empty_files_is_empty_scope `--files` with no path == no scope
  5 check_then_fix_then_noop              --check fails -> fix -> --check 0 -> noop
  6 near_miss_names_not_exempt           src/test_utils.rs, src/contests.rs
  7 raw_string_payload_untouched         `//` + `fn` inside r#"..."# unchanged
  8 cfg_test_module_still_exempt         in-file `#[cfg(test)]` unchanged
  9 no_comments_in_tests_rule_intact     §14.5 still bites; loop converges

Run:  python3 self_test_doc_comment_audit.py

Env:
  DOC_COMMENT_AUDIT_TOOL   path to the tool under test. Defaults to the
                           `doc_comment_audit.py` sitting next to this file;
                           point it at a pre-fix copy to reproduce the red run.

Exit 0 = self-test passed, 1 = self-test failed.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = Path(os.environ.get("DOC_COMMENT_AUDIT_TOOL") or (HERE / "doc_comment_audit.py"))
NO_TEST_COMMENTS = HERE / "verify_no_test_comments.py"

# Fixtures live in the hermes scratch dir, never in .agents and never in a
# repo's own fixtures/ tree: an intentionally non-compliant fixture must not be
# reachable by another audit.
SCRATCH = Path(os.environ.get("HERMES_SCRATCH") or (Path.home() / ".hermes/cache/scratch"))


# ---------- fixtures --------------------------------------------------------

# Production source: bare impl block, undocumented fn with params + return, and
# a `#[cfg(test)]` module whose helper must stay undocumented.
PROD_LIB = """//! Production crate root.

pub struct Probe {
    pub hits: u8,
}

impl Probe {
    pub fn new(hits: u8) -> Self {
        Self { hits }
    }
}

pub fn untagged(hits: u8) -> u8 {
    hits
}

#[cfg(test)]
mod tests {
    use super::*;

    fn helper_without_attr() -> u8 {
        3
    }

    #[test]
    fn counts() {
        assert_eq!(helper_without_attr(), 3);
    }
}
"""

# Production files whose *names* merely look test-ish. §2 applies: an exemption
# keyed on a substring would silently drop these.
NEAR_MISS = """pub struct Probe {
    pub hits: u8,
}

pub fn build_probe(hits: u8) -> u8 {
    hits
}

impl Probe {
    pub fn hits(&self) -> u8 {
        self.hits
    }
}
"""

# Production file carrying a WGSL-shaped raw string. The `fn` and `//` inside it
# are shader payload, not Rust — see the RAW STRING SAFETY note in the tool.
RAW_STRING_CONST = '''pub const SHADER: &str = r#"
fn vs_main(vert: Vertex) -> Vertex {
    // shader payload: this fn and this comment are not Rust
    return vert;
}
"#;

pub fn upload(bytes: &[u8]) -> usize {
    bytes.len()
}
'''

# Workspace integration test: trait impl, inherent impl, bare trait + impl,
# helper fn, `#[test]` fn. Byte-for-byte the shape that got 1069 injected lines.
ROOT_TEST_IMPL = """use std::sync::Arc;

use crate::server::ServerHook;

pub struct ProbeMiddleware {
    inner: Arc<u8>,
}

impl ServerHook for ProbeMiddleware {
    fn new(inner: Arc<u8>) -> Self {
        Self { inner }
    }

    fn peek(&self) -> u8 {
        *self.inner
    }
}

impl ProbeMiddleware {
    fn build(inner: Arc<u8>) -> Self {
        Self { inner }
    }
}

fn start_server_with(port: u16) -> Arc<u8> {
    Arc::new(port as u8)
}

trait Extra {
    fn help(&self) -> u8;
}

impl Extra for ProbeMiddleware {
    fn help(&self) -> u8 {
        7
    }
}

#[test]
fn peeks() {
    assert_eq!(ProbeMiddleware::build(Arc::new(2)).peek(), 2);
}
"""

# Deep helper module inside the same root tests tree.
ROOT_TEST_DEEP = """fn helper_deep(alpha: u16) -> u16 {
    alpha
}

struct Local;

impl Local {
    fn inner(&self) -> u16 {
        1
    }
}
"""

# Member-crate tests tree, four levels deep.
MEMBER_TEST_DEEP = """fn deep_helper(alpha: u16) -> u16 {
    alpha
}

struct Local;

impl Local {
    fn inner(&self) -> u16 {
        1
    }
}

impl Default for Local {
    fn default() -> Self {
        Self
    }
}
"""

# The file the self-test deliberately leaves commented, to prove §14.5 is not
# weakened by the fixer's new exemption. Only verify_no_test_comments.py may
# ever complain about this one.
MEMBER_TEST_COMMENTED = """// this comment must still be a §14.5 violation
fn annotated() -> u8 {
    1
}
"""

MEMBER_SRC_LIB = """pub struct Widget {
    pub size: u8,
}

impl Widget {
    pub fn new(size: u8) -> Self {
        Self { size }
    }
}
"""

# A fn whose doc block sits ABOVE two attributes — the shape idiomatic Rust
# produces and the shape the fixer used to break. The doc block must survive
# a fix pass untouched, and the fn must not be reported as undocumented.
#
# The bug: the fixer walked up from the fn, stopped at the INNERMOST attribute
# and looked at the line above it. With two attributes that line is the other
# attribute, not the doc block, so the fn read as undocumented and the fixer
# inserted a one-line doc BETWEEN the two attributes. The next scan then read
# that stray one-liner as the fn's whole doc block — hiding the real one and
# making the fn look like it lacked `# Arguments` / `# Returns`.
MULTI_ATTR_DOC = """//! Crate root.

use std::sync::Arc;

use crate::server::ServerHook;

/// Middleware that records a probe.
pub struct ProbeMiddleware {
    inner: Arc<u8>,
}

/// Implements [`ServerHook`] for [`ProbeMiddleware`].
impl ServerHook for ProbeMiddleware {
    /// Handles one request.
    ///
    /// # Arguments
    ///
    /// - `&mut Context` - The request context.
    ///
    /// # Returns
    ///
    /// - `Status` - The status to answer with.
    #[prologue_macros(is_get_method)]
    #[instrument_trace]
    async fn handle(self, ctx: &mut Context) -> Status {
        Status::Continue
    }
}
"""

TEST_FILES = [
    "core/tests/protocol/middleware/impl.rs",
    "core/tests/helper/deep/fn.rs",
    "crates/member/tests/a/b/c/d/impl.rs",
]

# (repo-relative path, content) for every file the self-test writes.
LAYOUT = [
    ("core/src/lib.rs", PROD_LIB),
    ("core/src/test_utils.rs", NEAR_MISS),
    ("core/src/contests.rs", NEAR_MISS),
    ("crates/member/src/lib.rs", MEMBER_SRC_LIB),
    ("core/tests/protocol/middleware/impl.rs", ROOT_TEST_IMPL),
    ("core/tests/helper/deep/fn.rs", ROOT_TEST_DEEP),
    ("crates/member/tests/a/b/c/d/impl.rs", MEMBER_TEST_DEEP),
]


# ---------- harness ---------------------------------------------------------


class SelfTest:
    """Collects per-case failures; the report names the failing case."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passed: list[str] = []
        self.cases: list[str] = []

    def case(self, name: str):
        def wrap(fn):
            self.cases.append(name)
            before = len(self.failures)
            try:
                fn(self)
            except Exception as exc:  # a crash is a failure, not a stack trace
                self.failures.append(f"{name}: raised {exc!r}")
            if len(self.failures) == before:
                self.passed.append(name)
            return fn

        return wrap

    def fail(self, name: str, message: str) -> None:
        self.failures.append(f"{name}: {message}")


def load_tool():
    spec = importlib.util.spec_from_file_location("doc_comment_audit_under_test", str(TOOL))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tool at {TOOL}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_repo(root: Path) -> None:
    """Write the fixture tree and stage it (whole-repo scope reads `git ls-files`)."""
    for rel, body in LAYOUT:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )


def run_no_test_comments(root: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(NO_TEST_COMMENTS), str(root)],
        capture_output=True,
        text=True,
        env=env,
    )


def snapshot(root: Path, rels: list[str]) -> dict[str, str]:
    return {rel: (root / rel).read_text() for rel in rels}


def main() -> int:
    if not TOOL.is_file():
        print(f"tool not found: {TOOL}", file=sys.stderr)
        return 2
    SCRATCH.mkdir(parents=True, exist_ok=True)
    st = SelfTest()
    tool = load_tool()
    prod_files = [
        "core/src/lib.rs",
        "core/src/test_utils.rs",
        "core/src/contests.rs",
        "crates/member/src/lib.rs",
    ]

    # ------------------------------------------------------------------ case 1
    @st.case("direct_entries_never_write_tests")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_direct_", dir=SCRATCH))
        try:
            build_repo(tmp)
            before = snapshot(tmp, TEST_FILES)
            for rel in TEST_FILES:
                path = tmp / rel
                counts = tool.fix_one(str(path))
                if counts != (0, 0):
                    st.fail("direct_entries_never_write_tests", f"fix_one({rel}) reported {counts}")
                violations = tool.audit_one(str(path))
                if violations:
                    st.fail(
                        "direct_entries_never_write_tests",
                        f"audit_one({rel}) still demands docs: {dict(violations)}",
                    )
            after = snapshot(tmp, TEST_FILES)
            for rel in TEST_FILES:
                if before[rel] != after[rel]:
                    st.fail(
                        "direct_entries_never_write_tests",
                        f"{rel} was rewritten by the direct entry point",
                    )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 2
    @st.case("cli_whole_repo_scan_never_writes_tests")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_whole_", dir=SCRATCH))
        try:
            build_repo(tmp)
            (tmp / "core/src/const.rs").write_text(RAW_STRING_CONST)
            subprocess.run(["git", "add", "-A"], cwd=tmp, check=True, capture_output=True)
            before = snapshot(tmp, TEST_FILES)
            proc = run_cli(["--root", str(tmp)], tmp)
            if proc.returncode != 0:
                st.fail("cli_whole_repo_scan_never_writes_tests", f"rc={proc.returncode}: {proc.stderr[:300]}")
            after = snapshot(tmp, TEST_FILES)
            for rel in TEST_FILES:
                if before[rel] != after[rel]:
                    st.fail(
                        "cli_whole_repo_scan_never_writes_tests",
                        f"{rel} was rewritten by the whole-repo sweep",
                    )
            # The sweep must still do its real job on production code.
            lib = (tmp / "core/src/lib.rs").read_text()
            if "/// Implements the `untagged` operation on" not in lib:
                st.fail("cli_whole_repo_scan_never_writes_tests", "production fn in core/src/lib.rs went undocumented")
            if "/// Inherent implementation of [`Probe`]." not in lib:
                st.fail("cli_whole_repo_scan_never_writes_tests", "production impl block in core/src/lib.rs went undocumented")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 3
    @st.case("cli_explicit_files_never_writes_tests")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_files_", dir=SCRATCH))
        try:
            build_repo(tmp)
            before_all = snapshot(tmp, TEST_FILES + prod_files)
            proc = run_cli(["--root", str(tmp), "--files", *TEST_FILES], tmp)
            if proc.returncode != 0:
                st.fail("cli_explicit_files_never_writes_tests", f"rc={proc.returncode}: {proc.stderr[:300]}")
            after_all = snapshot(tmp, TEST_FILES + prod_files)
            for rel in TEST_FILES:
                if before_all[rel] != after_all[rel]:
                    st.fail("cli_explicit_files_never_writes_tests", f"{rel} was rewritten via --files")
            # Scoped to tests only: production files outside the scope stay put.
            for rel in prod_files:
                if rel in before_all and before_all[rel] != after_all[rel]:
                    st.fail("cli_explicit_files_never_writes_tests", f"{rel} changed outside the --files scope")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 4
    @st.case("cli_explicit_empty_files_is_empty_scope")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_empty_", dir=SCRATCH))
        try:
            build_repo(tmp)
            before = snapshot(tmp, prod_files + ["core/src/lib.rs"])
            proc = run_cli(["--root", str(tmp), "--files"], tmp)
            if proc.returncode != 0:
                st.fail("cli_explicit_empty_files_is_empty_scope", f"rc={proc.returncode}: {proc.stderr[:300]}")
            after = snapshot(tmp, prod_files + ["core/src/lib.rs"])
            for rel, body in before.items():
                if body != after[rel]:
                    st.fail(
                        "cli_explicit_empty_files_is_empty_scope",
                        f"--files with no path fell back to a whole-repo sweep and touched {rel}",
                    )
            check = run_cli(["--root", str(tmp), "--check", "--files"], tmp)
            if check.returncode != 0:
                st.fail(
                    "cli_explicit_empty_files_is_empty_scope",
                    f"--check --files with no path scanned the repo: rc={check.returncode}",
                )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 5
    @st.case("check_then_fix_then_noop")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_cycle_", dir=SCRATCH))
        try:
            build_repo(tmp)
            first = run_cli(["--root", str(tmp), "--check"], tmp)
            if first.returncode != 1:
                st.fail("check_then_fix_then_noop", f"first --check rc={first.returncode}, want 1")
            for needle in ("untagged", "build_probe", "new"):
                if needle not in first.stdout:
                    st.fail("check_then_fix_then_noop", f"--check did not report `{needle}`")
            for rel in TEST_FILES:
                if rel in first.stdout:
                    st.fail("check_then_fix_then_noop", f"--check demanded docs in a tests file: {rel}")

            fixed = run_cli(["--root", str(tmp)], tmp)
            if fixed.returncode != 0:
                st.fail("check_then_fix_then_noop", f"fix rc={fixed.returncode}: {fixed.stderr[:300]}")
            second = run_cli(["--root", str(tmp), "--check"], tmp)
            if second.returncode != 0:
                st.fail(
                    "check_then_fix_then_noop",
                    f"--check still failing after the fix: rc={second.returncode}\n{second.stdout[-800:]}",
                )
            stable = snapshot(tmp, ["core/src/lib.rs", "core/src/test_utils.rs", "crates/member/src/lib.rs"])
            again = run_cli(["--root", str(tmp)], tmp)
            if again.returncode != 0:
                st.fail("check_then_fix_then_noop", f"second fix rc={again.returncode}")
            now = snapshot(tmp, ["core/src/lib.rs", "core/src/test_utils.rs", "crates/member/src/lib.rs"])
            for rel in stable:
                if stable[rel] != now[rel]:
                    st.fail("check_then_fix_then_noop", f"second run was not a no-op for {rel}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 6
    @st.case("near_miss_names_not_exempt")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_nearmiss_", dir=SCRATCH))
        try:
            build_repo(tmp)
            for rel in ("core/src/test_utils.rs", "core/src/contests.rs"):
                # --check first: a near-miss name must still be IN scope.
                check = run_cli(["--root", str(tmp), "--check", "--files", rel], tmp)
                if check.returncode != 1:
                    st.fail(
                        "near_miss_names_not_exempt",
                        f"{rel}: --check rc={check.returncode}, want 1 (file was treated as out of scope)",
                    )
                proc = run_cli(["--root", str(tmp), "--files", rel], tmp)
                if proc.returncode != 0:
                    st.fail("near_miss_names_not_exempt", f"{rel}: rc={proc.returncode}")
                body = (tmp / rel).read_text()
                if body == NEAR_MISS:
                    st.fail("near_miss_names_not_exempt", f"{rel} was treated as a test file and left undocumented")
                for needle in (
                    "/// Inherent implementation of [`Probe`].",
                    "/// Body of the `build_probe` free function.",
                ):
                    if needle not in body:
                        st.fail("near_miss_names_not_exempt", f"{rel}: {needle!r} missing after the fix")
                after = run_cli(["--root", str(tmp), "--check", "--files", rel], tmp)
                if after.returncode != 0:
                    st.fail("near_miss_names_not_exempt", f"{rel}: --check rc={after.returncode} after the fix, want 0")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 7
    @st.case("raw_string_payload_untouched")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_rawstr_", dir=SCRATCH))
        try:
            build_repo(tmp)
            (tmp / "core/src/const.rs").write_text(RAW_STRING_CONST)
            proc = run_cli(["--root", str(tmp), "--files", "core/src/const.rs"], tmp)
            if proc.returncode != 0:
                st.fail("raw_string_payload_untouched", f"rc={proc.returncode}: {proc.stderr[:300]}")
            body = (tmp / "core/src/const.rs").read_text()
            payload = RAW_STRING_CONST.split('r#"')[1].split('"#')[0]
            if payload not in body:
                st.fail("raw_string_payload_untouched", "shader payload inside r#\"...\"# was modified")
            for line in body.splitlines():
                if line.startswith("///") and "vs_main" in line:
                    st.fail("raw_string_payload_untouched", f"doc comment injected into shader source: {line!r}")
            # ...while the real Rust fn next to it still gets documented.
            if "/// Body of the `upload` free function." not in body:
                st.fail("raw_string_payload_untouched", "production fn next to the raw string lost its doc")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 8
    @st.case("cfg_test_module_still_exempt")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_cfgtest_", dir=SCRATCH))
        try:
            build_repo(tmp)
            proc = run_cli(["--root", str(tmp), "--files", "core/src/lib.rs"], tmp)
            if proc.returncode != 0:
                st.fail("cfg_test_module_still_exempt", f"fix rc={proc.returncode}: {proc.stderr[:300]}")
            body = (tmp / "core/src/lib.rs").read_text()
            lines = body.splitlines()
            for i, line in enumerate(lines):
                if "fn helper_without_attr" in line:
                    prev = [ln for ln in lines[max(0, i - 3):i]]
                    if any(ln.strip().startswith("///") for ln in prev):
                        st.fail("cfg_test_module_still_exempt", "documented a fn inside a #[cfg(test)] module")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------ case 9
    @st.case("no_comments_in_tests_rule_intact")
    def _(st) -> None:
        if not NO_TEST_COMMENTS.is_file():
            st.fail("no_comments_in_tests_rule_intact", f"missing companion verifier {NO_TEST_COMMENTS}")
            return
        tmp = Path(tempfile.mkdtemp(prefix="docfix_rule_", dir=SCRATCH))
        try:
            build_repo(tmp)
            # (a) the fixer over three Phase1↔Phase2 rounds must not manufacture
            #     §14.5 violations — this is the 1069-hit loop, reproduced small.
            for _ in range(3):
                proc = run_cli(["--root", str(tmp)], tmp)
                if proc.returncode != 0:
                    st.fail("no_comments_in_tests_rule_intact", f"fix rc={proc.returncode}: {proc.stderr[:300]}")
            audit = run_no_test_comments(tmp)
            if audit.returncode != 0:
                st.fail(
                    "no_comments_in_tests_rule_intact",
                    "fixer output is rejected by §14.5; loop cannot converge:\n"
                    + audit.stdout[-800:],
                )
            # (b) §14.5 itself is untouched: a comment in a member tests file
            #     is still a violation, after the fixer exemption was added.
            commented = tmp / "crates/member/tests/a/b/c/d/commented.rs"
            commented.write_text(MEMBER_TEST_COMMENTED)
            b = run_no_test_comments(tmp)
            if b.returncode != 1 or "commented.rs" not in b.stdout:
                st.fail(
                    "no_comments_in_tests_rule_intact",
                    f"§14.5 stopped flagging a commented member test file: rc={b.returncode}",
                )
            check = run_cli(["--root", str(tmp), "--check"], tmp)
            if check.returncode != 0:
                st.fail(
                    "no_comments_in_tests_rule_intact",
                    f"--check demanded docs for a file that §14.5 forbids commenting: rc={check.returncode}\n"
                    + check.stdout[-500:],
                )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ----------------------------------------------------------------- case 10
    @st.case("multi_attribute_doc_block_survives")
    def _(st) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="docfix_multiattr_", dir=SCRATCH))
        try:
            build_repo(tmp)
            target = tmp / "core/src/multi.rs"
            target.write_text(MULTI_ATTR_DOC)
            before = target.read_text()
            # (a) The fixer must not touch a file whose only fn is documented
            #     above two attributes.
            counts = tool.fix_one(str(target))
            if counts != (0, 0):
                st.fail(
                    "multi_attribute_doc_block_survives",
                    f"fix_one rewrote a documented fn: {counts}",
                )
            after = target.read_text()
            if before != after:
                st.fail(
                    "multi_attribute_doc_block_survives",
                    "the fixer modified a file whose fn was already documented:\n"
                    + "\n".join(
                        f"  - {line}"
                        for line in __import__("difflib").unified_diff(
                            before.splitlines(), after.splitlines(), lineterm=""
                        )
                    ),
                )
            # (b) The audit must not report the fn as undocumented, nor as
            #     missing its `# Arguments` / `# Returns` sections.
            violations = tool.audit_one(str(target))
            if violations:
                st.fail(
                    "multi_attribute_doc_block_survives",
                    f"audit_one reports a documented fn as violating: {dict(violations)}",
                )
            # (c) A doc block must never be planted BETWEEN two attributes.
            lines = after.splitlines()
            for i, line in enumerate(lines):
                if not line.strip().startswith("///"):
                    continue
                if i + 1 >= len(lines):
                    continue
                if not lines[i + 1].strip().startswith("#["):
                    continue
                # The line below the doc must be an attribute AND the line
                # above it must be one too — a doc above the OUTERMOST
                # attribute is the correct shape, a doc between two
                # attributes is the corrupted one.
                if i == 0:
                    continue
                if not lines[i - 1].strip().startswith("#["):
                    continue
                st.fail(
                    "multi_attribute_doc_block_survives",
                    f"a doc comment was planted between two attributes: {line!r}",
                )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"tool under test: {TOOL}")
    if st.failures:
        print("SELF-TEST FAIL:")
        for failure in st.failures:
            print(f"  - {failure}")
        print(f"\n{len(st.passed)}/{len(st.cases)} cases passed; {len(st.failures)} assertion failures")
        return 1
    for name in st.passed:
        print(f"  PASS  {name}")
    print(f"\nSELF-TEST OK: doc_comment_audit scope ({len(st.passed)}/{len(st.cases)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
