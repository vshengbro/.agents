#!/usr/bin/env python3
"""Staged-file rust-standards gate: block NEW violations only, never legacy debt.

Why this exists
---------------
`~/.git-hooks/pre-commit` has always been broken, for two independent
reasons:

  1. ARGUMENT-TYPE BUG — the hook invoked the verifiers with a FILE path
     (`python3 verify_*.py "$REPO_ROOT/$f"`), but every `verify_*.py` ends
     its `main()` with `if not root.is_dir(): return 2`. Passing a file
     therefore always failed, so EVERY commit touching a `.rs` file was
     blocked regardless of content. Verified 2026-09-27: all four
     file-level verifiers exit non-zero on a file argument, and no `.rs`
     commit had ever succeeded on ctares since the hook was installed.

  2. NO BASELINE COMPARISON — the hook counted violations in the working
     tree. A file that already carried historical violations
     (e.g. `lombok-macros/src/generate/fn.rs` had 48 pre-existing
     doc-comment findings) was blocked even when the staged diff
     introduced nothing. That directly contradicts the hook's own
     documented intent: "block NEW violations, not legacy debt".

This gate fixes both. For every staged `.rs` file it compares the
violation count in the working tree against the same file at HEAD, and
reports only the DELTA.

Usage
-----
    python3 staged_file_gate.py <repo-root> [--staged | --file PATH ...]

Exit codes
----------
    0 — no new violations (commit allowed)
    1 — new violations introduced by the staged changes (commit blocked)
    2 — usage / environment error (not a git repo, scripts missing, ...)

Design notes
------------
- Verifiers are imported as modules and driven through their `audit_one()`
  entry point rather than re-implemented, so there is exactly one parser
  per rule. Importing also sidesteps the argv contract entirely.
- HEAD content is materialised next to the working file (same name plus a
  `.head-baseline` suffix) so path-relative logic keeps working —
  `verify_lib_rs_doc_comment._read_package_name()` walks up to the nearest
  Cargo.toml to resolve `[package].name`, which a temp file in the scratch
  dir would break. The suffix does not match `*.rs` or `lib.rs`, so it is
  invisible to the verifiers' own `find` patterns, and it is removed in a
  `finally` block.
- `verify_lib_rs_doc_comment` is only meaningful for `lib.rs`; running it
  on any other file name is meaningless work, so it is skipped.
- Files are checked in a `multiprocessing.Pool`: the per-file work (25+
  CPU-bound verifier passes, twice — worktree and HEAD baseline) is
  embarrassingly parallel, and a mega-commit of several hundred files
  otherwise takes >10 minutes serially. Verdicts and report order are
  identical to the serial loop (`Pool.map` preserves input order, and the
  JOBS=1 path runs the very same worker function). Override the worker
  count with STAGED_FILE_GATE_JOBS; 1 forces the serial path.
- The staged `git diff --name-status` listing is computed ONCE per run and
  the HEAD contents of every rename/split source are prefetched ONCE —
  the serial version re-ran two full diff listings plus the source fetches
  for EVERY file, which dominated the runtime on large commits.
"""

from __future__ import annotations

import importlib.util
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

# The baseline temp file must keep a `.rs` suffix: every verifier entry point
# starts with `if path.suffix != ".rs" ... return []` (see
# verify_const_visibility.audit_one), so a temp named `foo.rs.head-baseline`
# silently audits to ZERO findings and every legacy violation in the touched
# file is then reported as "introduced by this commit" -- the exact
# legacy-debt blindness this gate exists to avoid. Insert the marker BEFORE the
# extension so the basename still parses as Rust.
SUFFIX = ".head-baseline.rs"

# Minimum Jaccard overlap for a staged new file to be treated as a split of
# a staged-deleted source. Conservative on purpose: a wrong pairing would hide
# real violations, an absent pairing only over-reports (which is safer).
SPLIT_MIN_OVERLAP = 0.30

# verifier module name -> human label
VERIFIERS = {
    "verify_doc_comment_format": "doc-comment §2.1/§2.2",
    "verify_hardcoded_strings": "hardcoded strings §1.3c",
    "verify_no_import_rename": "import rename §6.5",
    "verify_use_aggregation": "use aggregation §6.6",
    "verify_no_self_field_access": "self.field access §17.3/§17.12",
    "verify_lib_rs_doc_comment": "lib.rs //! block §2.4",
    "verify_no_redundant_accessor_attr": "bare accessor attr §L",
    "verify_no_sibling_dirs": "code file beside sub-dirs §1.3d (only lib/main/build/mod exempt)",
    "verify_no_panicking_borrow": "RefCell borrow guard held across re-entrant call §borrow",
    "verify_no_impl_trait_params": "impl Trait in fn parameters §9.2",
    "verify_no_test_comments": "comments in test files §14.5",
    "verify_ci_no_bump": "CI version bump / version write §17",
    "verify_module_imports_centralized": "module imports centralized §6.1/§6.3/§6.4",
    "verify_lib_rs_order": "lib.rs import group order §6.1",
    # §1.3 / §1.4. Was missing here, which is why cli/src/build/inline.rs
    # survived every commit: the audit script ran the check and the
    # pre-commit hook did not. A rule enforced in one caller and not the
    # other is not a rule. Covers both the filename (§1.4) and the
    # declaration-purity / use-centralization rules (§1.3) already
    # implemented inside the same script.
    "verify_keyword_file_purity": "keyword file purity §1.3 / non-keyword filename §1.4",
    # R11.4. Also previously audit-only: the rule existed as an inline shell
    # pipeline over `git diff origin/master HEAD`, with no per-file script for
    # the gate to drive, so the hook could not enforce it. Same gap as §1.4.
    "verify_no_production_panic": "production panic!/expect/unwrap R11.4",
    # R11.5. Same gap as §1.4 and R11.4 above: the rule ran in the audit
    # but had no entry here, so a panicking lombok getter on a public
    # `Option<Copy>` field would have been committed without the hook
    # noticing. A rule enforced in one caller and not the other is not a
    # rule.
    "verify_no_panicking_option_getter": "panicking lombok getter on Option field R11.5",
    # §12. Found by cross-referencing every audit CHECKS template against this
    # whitelist rather than fixing the verifiers the audit happened to name.
    # This one exposes `audit_one` and acts on `.rs`, so registration is real
    # coverage: verified 0 on the clean tree and 1 with an `#[inline]`
    # planted in engine/src/lib.rs. The other audit-only rules (dep order,
    # section blanks, fn-body blank lines, ...) do not qualify — they either
    # lack `audit_one` or are Cargo.toml rules the gate never reaches.
    "verify_no_wasm_inline": "no #[inline] in a wasm crate §12",
    # These five were audit-only until now. Found by cross-referencing every
    # audit CHECKS template against this whitelist: a rule the audit runs but
    # the hook does not is not enforced at commit time, it is only found by
    # whoever remembers to run the full gate. Each one below exposes
    # `audit_one(path)` and operates on `.rs`, so registration is real
    # coverage rather than a silent no-op -- both conditions were verified
    # before adding them here.
    "verify_mod_visibility": "mod.rs mod declaration must be bare 6.2",
    "verify_no_allow_lints": "#[allow(...)] in production 14",
    "verify_explicit_type_annotations": "explicit type annotations for let bindings 5.1",
    "verify_let_type_annotations": "all let bindings have explicit type annotation 5.1",
    "verify_closure_type_annotations": "closure parameters have explicit type annotation 5.2",
    # Added 2026-10-02. The rule ran in the audit but had no `audit_one` and
    # no entry here, so every `std::fs::create_dir_all(...)` written into a
    # sub-file passed the hook silently -- the same gap as §1.4 and R11.4.
    # Found by planting `std::fs::read` in a test file and watching the gate
    # report 0 while the script on its own reported 1. `audit_one` reads only
    # the path it is handed, so the gate's before/after baselines compare.
    "verify_no_qualified_std_path": "qualified std:: path in a sub-file (hoist to lib.rs / outermost mod.rs)",
    # Added 2026-10-07 (§18). `audit_one` gates on the file name, so only a
    # staged const.rs / static.rs can trip it; the self-test proves the
    # adapter returns findings on a violating file and [] on fn.rs.
    "verify_pub_group_order": "pub items grouped before pub(crate)/private in const.rs/static.rs §18",
    "verify_const_visibility": "pub const/static needs an external reader §18",
    "verify_no_pub_in_tests": "single-reader tests/ items never need pub §18",
}

# Verifiers that only make sense for a specific file name.
FILE_SCOPED = {"verify_lib_rs_doc_comment": "lib.rs"}


def die(message: str, code: int = 2) -> int:
    print(f"staged_file_gate: {message}", file=sys.stderr)
    return code


def load_verifier(scripts_dir: Path, name: str):
    """Import a verifier module by path, so argv/CLI is bypassed entirely."""
    path = scripts_dir / f"{name}.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"rsv_{name}", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as error:  # noqa: BLE001 - a broken verifier must not
        return f"  ! cannot import {name}.py: {error}"
    return module


def audit(module, path: Path, warnings: list[str]) -> list[str]:
    """Run a verifier's per-file check, tolerating a missing entry point."""
    if path is None:
        return []
    audit_one = getattr(module, "audit_one", None)
    if audit_one is None:
        return []
    try:
        return list(audit_one(path))
    except Exception as error:  # noqa: BLE001
        warnings.append(f"  ! {module.__name__}.audit_one failed: {error}")
        return []


def git(repo_root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def parse_staged_listing(listing: str) -> tuple[dict[str, str], list[str]]:
    """Parse one `git diff --cached --name-status -M` listing.

    Returns (renames, sources): renames maps a staged rename's NEW path to
    its OLD path; sources is the de-duplicated, order-preserving list of
    OLD paths from D and R entries (the split-baseline candidates). The
    serial version derived the same two structures by re-running the full
    listing per file; one parse feeds every file.
    """
    renames: dict[str, str] = {}
    sources: list[str] = []
    seen: set[str] = set()
    for line in listing.splitlines():
        parts = line.split("\t")
        status = parts[0][:1] if parts else ""
        if status == "R" and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]
            # Git never emits two renames to the same new path; first wins.
            renames.setdefault(new_path, old_path)
            if old_path not in seen:
                seen.add(old_path)
                sources.append(old_path)
        elif status == "D" and len(parts) >= 2:
            old_path = parts[1]
            if old_path not in seen:
                seen.add(old_path)
                sources.append(old_path)
    return renames, sources


def split_baseline(ctx: dict, rel: str) -> str | None:
    """Best-effort HEAD baseline for a file created by SPLITTING another file.

    A staged move is often recorded as `D old` + `N x A new` rather than a
    rename, because one source file was split into several targets (e.g.
    §1.3d restructuring `class/fn.rs` into `class/{display,page,shell}/fn.rs`).
    Git cannot pair those, so every new path gets baseline `None` and the
    whole pre-existing debt in the split source is reported as
    "introduced by this commit" — the exact legacy-debt blindness the gate
    exists to prevent.

    Resolution is deliberately conservative: a candidate source is accepted
    ONLY when the same-directory sibling rule plus a real content overlap
    both hold, and the accepted baseline is the source's HEAD text. The
    caller still diffs violation COUNTS against it, so genuinely new
    violations in the new file are still caught; the fallback merely stops
    inherited debt from being double-counted as new.

    Returns None (i.e. "treat as a new file") whenever the pairing is
    ambiguous, which keeps the gate strict in the doubtful case.
    """
    repo_root: Path = ctx["repo_root"]
    target = repo_root / rel
    if not target.is_file():
        return None

    # A split may move code in either direction:
    #   class/fn.rs          -> class/page/fn.rs   (into a NEW subdir)
    #   renderer/impl.rs     -> renderer/canvas/impl.rs (into a NEW subdir)
    # so the source is usually the target's PARENT dir, not its own dir.
    # Accept the source when either directory contains the other.
    try:
        target_dir = str(target.parent.relative_to(repo_root))
    except ValueError:
        return None
    if target_dir in {".", ""}:
        target_dir = ""

    current_lines = set(_content_lines(target.read_text(errors="replace")))
    if not current_lines:
        return None

    head_cache: dict[str, str] = ctx["head_cache"]
    best: tuple[float, str] | None = None
    for old_path in ctx["sources"]:
        if not _same_or_nested_dir(old_path, target_dir):
            continue
        content = head_cache.get(old_path)
        if not content:
            continue
        old_lines = set(_content_lines(content))
        if not old_lines:
            continue
        # Jaccard overlap: how much of the new file existed in the source.
        overlap = len(current_lines & old_lines) / len(current_lines)
        if overlap < SPLIT_MIN_OVERLAP:
            continue
        if best is None or overlap > best[0]:
            best = (overlap, content)

    if best is None:
        return None
    return best[1]


def _same_or_nested_dir(old_path: str, target_dir: str) -> bool:
    """True when the deleted file's directory and the target directory nest.

    Covers both split directions: a file split out into a new sub-directory
    (source is the parent) and one split down from a parent (source is an
    ancestor). Sibling dirs are excluded: unrelated code should not be
    used as a baseline.
    """
    old_dir = str(Path(old_path).parent)
    if old_dir in {".", ""}:
        old_dir = ""
    if old_dir == target_dir:
        return True
    if not old_dir or not target_dir:
        return False
    return old_dir.startswith(target_dir + "/") or target_dir.startswith(old_dir + "/")


def _content_lines(text: str) -> list[str]:
    """Significant lines only, so reindentation alone is not an overlap."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("//")
    ]


def materialise(target: Path, text: str) -> Path:
    """Write `text` beside `target` so path-relative logic still resolves."""
    tmp = target.with_name(target.name + SUFFIX)
    tmp.write_text(text)
    return tmp


def baseline_for(ctx: dict, rel: str) -> str | None:
    """File content at HEAD, or None when the file is new / untracked.

    A staged rename makes `HEAD:<newpath>` fail even though the file is not
    new: the content lives at the OLD path in HEAD. Without this lookup the
    baseline is `None`, `before` becomes `[]`, and every pre-existing
    violation in the renamed file is counted as "introduced by this commit"
    — which is exactly the legacy-debt blindness the gate exists to avoid.
    """
    repo_root: Path = ctx["repo_root"]
    code, out = git(repo_root, "show", f"HEAD:{rel}")
    split = split_baseline(ctx, rel)
    if code == 0 and out is not None:
        if split is None:
            return out
        # Union baseline. A file that was MODIFIED may still have received
        # code from a sibling that this commit deleted (the §1.3d move case:
        # `class/display/fn.rs` existed in HEAD but was only a partial file,
        # and the rest arrived from the deleted `class/fn.rs`). Baselining
        # against the partial HEAD copy alone makes the moved-in debt look
        # brand new. Concatenating the sources gives the gate the full
        # pre-commit content set; the caller still diffs per-verifier
        # violation COUNTS, so real new findings are still reported.
        return out + "\n" + split
    old_path = ctx["renames"].get(rel)
    if old_path is not None:
        # A failed prefetch (missing entry) maps to None, exactly like the
        # serial version's `git show` failure path.
        return ctx["head_cache"].get(old_path)
    return split


# ---------------------------------------------------------------------------
# Worker plumbing — one module load per PROCESS, then files map over the pool.
# ---------------------------------------------------------------------------

_CTX: dict = {}


def _init_worker(ctx: dict) -> None:
    """Pool initializer: load verifiers once per worker, stash shared state."""
    global _CTX
    modules: dict[str, object] = {}
    load_errors: list[str] = []
    for name in VERIFIERS:
        if ctx["only"] and name not in ctx["only"]:
            continue
        module = load_verifier(ctx["scripts_dir"], name)
        if isinstance(module, str):
            load_errors.append(module)
        elif module is not None:
            modules[name] = module
    _CTX = {**ctx, "modules": modules, "load_errors": load_errors}


def _check_file(rel: str) -> tuple[list[str], int, list[str]]:
    """Run every verifier on one staged file; return (report, delta, warnings).

    Side-effect free apart from the per-file baseline temp (unique name,
    removed in `finally`), so it is safe to run in a worker process.
    """
    ctx = _CTX
    warnings: list[str] = []
    report: list[str] = []
    repo_root: Path = ctx["repo_root"]
    working = repo_root / rel
    if not working.is_file():
        report.append(f"    - {rel}: staged but missing from worktree, skipped")
        return report, 0, warnings

    baseline = baseline_for(ctx, rel)
    baseline_path: Path | None = None
    if baseline is not None:
        try:
            baseline_path = materialise(working, baseline)
        except OSError as error:
            warnings.append(f"  ! cannot stage baseline for {rel}: {error}")
            baseline_path = None

    total_new = 0
    for name, module in ctx["modules"].items():
        required_name = FILE_SCOPED.get(name)
        if required_name and working.name != required_name:
            continue
        before = audit(module, baseline_path, warnings) if baseline_path else []
        after = audit(module, working, warnings)
        if len(after) > len(before):
            delta = len(after) - len(before)
            total_new += delta
            report.append(
                f"    - {rel}: +{delta} new ({name} — {VERIFIERS[name]})"
            )
    return report, total_new, warnings


def parse_args(argv: list[str]) -> tuple[Path, list[str]]:
    args = argv[1:]
    if not args:
        raise ValueError("usage: staged_file_gate.py <repo-root> [--staged | --file PATH ...]")
    root = Path(args[0]).resolve()
    files: list[str] = []
    rest = args[1:]
    if "--file" in rest:
        index = rest.index("--file")
        files = rest[index + 1 :]
    else:
        code, out = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        if code != 0:
            raise ValueError("not a git repository, or git failed")
        files = [line for line in out.splitlines() if line.strip()]
    return root, files


def _jobs(file_count: int) -> int:
    """Worker count: STAGED_FILE_GATE_JOBS wins, else one per core, capped."""
    raw = os.environ.get("STAGED_FILE_GATE_JOBS", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return min(value, file_count)
        except ValueError:
            pass
    return min(file_count, os.cpu_count() or 4)


def main() -> int:
    try:
        repo_root, staged = parse_args(sys.argv)
    except ValueError as error:
        return die(str(error))

    if not repo_root.is_dir():
        return die(f"{repo_root} is not a directory")

    scripts_dir: Path | None = None
    for candidate in (
        Path.home() / ".agents/skills/rust-standards/scripts",
        Path.home() / ".hermes/skills/rust-standards/scripts",
    ):
        if (candidate / "verify_doc_comment_format.py").is_file():
            scripts_dir = candidate
            break
    if scripts_dir is None:
        return die("rust-standards skill scripts not found")

    rs_files = [f for f in dict.fromkeys(staged) if f.endswith(".rs")]
    if not rs_files:
        print("staged_file_gate: no staged .rs files, nothing to check")
        return 0

    # Fixture support: run a subset of the gate's verifiers so one rule's
    # fixture is not masked by another rule's findings.  Unset in normal
    # use, so the gate always runs the full set.
    only = {
        part.strip()
        for part in os.environ.get("STAGED_FILE_GATE_ONLY_VERIFIERS", "").split(",")
        if part.strip()
    }

    # Load every verifier once in the parent as well: import failures are
    # reported exactly once (not once per worker), and a fully broken
    # scripts dir dies here instead of inside a pool worker.
    usable = 0
    for name in VERIFIERS:
        if only and name not in only:
            continue
        module = load_verifier(scripts_dir, name)
        if isinstance(module, str):
            print(module, file=sys.stderr)
        elif module is not None:
            usable += 1
    if usable == 0:
        return die("no verifier could be imported")

    # One staged listing for the whole run; the serial version re-ran it
    # (twice!) per file. Rename map + split candidates come from the same
    # text, and every source's HEAD content is prefetched once.
    code, listing = git(
        repo_root, "diff", "--cached", "--name-status", "--find-renames", "-M"
    )
    renames: dict[str, str] = {}
    sources: list[str] = []
    if code == 0:
        renames, sources = parse_staged_listing(listing)

    head_cache: dict[str, str] = {}
    for old_path in sources:
        found, content = git(repo_root, "show", f"HEAD:{old_path}")
        if found == 0 and content:
            head_cache[old_path] = content

    ctx = {
        "repo_root": repo_root,
        "scripts_dir": scripts_dir,
        "renames": renames,
        "sources": sources,
        "head_cache": head_cache,
        "only": only,
    }

    print("============================================================")
    print("staged_file_gate: new-violation gate (staged vs HEAD)")
    print(f"  repo:    {repo_root}")
    print(f"  scripts: {scripts_dir}")
    print(f"  .rs files: {len(rs_files)}")
    print("============================================================")

    jobs = _jobs(len(rs_files))
    results: list[tuple[list[str], int, list[str]]]

    # Baseline temps survive for the whole run now: a worker no longer
    # unlinks its own baseline, because repo-wide verifiers (e.g.
    # verify_no_panicking_option_getter rglob the tree once per file) would
    # otherwise read a sibling worker's baseline in the exact window between
    # materialise and unlink and crash with ENOENT — nondeterministically.
    # Any stale temp from a previously killed run is swept up front, and
    # every temp this run may have created is removed at the end, whichever
    # path (pool, serial fallback, exception) produced it.
    for stale in repo_root.rglob(f"*{SUFFIX}"):
        if "/target/" not in str(stale):
            try:
                stale.unlink()
            except OSError:
                pass
    try:
        if jobs <= 1:
            _init_worker(ctx)
            results = [_check_file(rel) for rel in rs_files]
        else:
            try:
                with multiprocessing.Pool(
                    processes=jobs,
                    initializer=_init_worker,
                    initargs=(ctx,),
                ) as pool:
                    chunksize = max(1, len(rs_files) // (jobs * 4))
                    # map preserves input order, so the report is byte-identical
                    # to the serial loop's.
                    results = pool.map(_check_file, rs_files, chunksize)
            except Exception as error:  # noqa: BLE001 - a pool failure must not
                print(  # block the commit; fall back to the serial path
                    f"  ! worker pool unavailable ({error}), running serially",
                    file=sys.stderr,
                )
                _init_worker(ctx)
                results = [_check_file(rel) for rel in rs_files]
    finally:
        for rel in rs_files:
            target = repo_root / rel
            tmp = target.with_name(target.name + SUFFIX)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    total_new = 0
    report: list[str] = []
    warnings: list[str] = []
    for lines, delta, file_warnings in results:
        report.extend(lines)
        total_new += delta
        warnings.extend(file_warnings)
    for line in dict.fromkeys(warnings):
        print(line, file=sys.stderr)

    if total_new == 0:
        print("\n  0 new violations — commit allowed")
        print("  (legacy violations in touched files are NOT counted)")
        print("============================================================")
        return 0

    print(f"\n  {total_new} NEW violation(s) introduced by staged changes:")
    for line in report:
        print(line)
    print("")
    print("============================================================")
    print("staged_file_gate: FAIL — commit BLOCKED")
    print("============================================================")
    return 1


if __name__ == "__main__":
    sys.exit(main())
