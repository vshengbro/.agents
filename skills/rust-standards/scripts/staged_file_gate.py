#!/usr/bin/env python3
"""Compare staged Rust/TOML findings against HEAD in isolated complete trees.

Only new per-verifier finding counts block a commit. The index is captured
once with write-tree; neither verifier inputs nor context come from the user's
working tree. All temporary files live under TMPDIR, never beside user sources.
Missing verifiers and import, execution, or snapshot errors fail closed.
"""
from __future__ import annotations

import importlib.util
import multiprocessing
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SPLIT_MIN_OVERLAP = 0.30
GIT_LOCAL_ENV = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_GRAFT_FILE", "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
    "GIT_SHALLOW_FILE", "GIT_IMPLICIT_WORK_TREE",
}
VERIFIERS = {
    "verify_doc_comment_format": "doc-comment §2.1/§2.2",
    "verify_hardcoded_strings": "hardcoded strings §1.3c",
    "verify_no_import_rename": "import rename §6.5",
    "verify_use_aggregation": "use aggregation §6.6",
    # §16.5 (2026-11-21 user 钦定). The tokens a macro body holds are
    # EXPANDED into the crate that USES the macro, so an import emitted by
    # the body lands in the consumer's scope and a bare path resolves
    # against the consumer's scope. A `quote!` body must therefore spell
    # every crate absolutely and must not emit a `use`. `audit_one` reads
    # only the path it is handed, so the gate's before/after baselines
    # compare.
    "verify_no_macro_use": "macro body full namespace paths, no `use` §16.5",
    # §6.7 (2026-11-21 user 钦定). A type annotation names the TYPE, not
    # the crate's module layout: the import belongs at the crate root and
    # the annotation spells the bare name. When two crates offer a type of
    # the same name the nearest different level of each path is imported
    # instead, because §6.5 forbids renaming an import with `as`.
    # `audit_one` reads only the path it is handed, so the gate's
    # before/after baselines compare.
    "verify_no_qualified_type_path": "qualified type path in a type annotation §6.7",
    "verify_no_self_field_access": "self.field access §17.3/§17.12",
    "verify_lib_rs_doc_comment": "lib.rs //! block §2.4",
    "verify_no_redundant_accessor_attr": "bare accessor attr §L",
    # §17.16 + §17.16.1 (2026-10-14 / 2026-10-18 user 钦定). `Data` IS
    # `Getter + GetterMut + Setter` — lombok's own
    # `inner_lombok_data(input, true, true, true)` — so spelling out all three
    # is one derive too many; and conversely a `Data` struct whose every
    # field skips both `get_mut` and `set` generates no mutator at all and
    # should be `Getter`. Registered in the audit and here together; a rule
    # enforced in only one caller is not a rule.
    "verify_no_redundant_accessor_derive": "accessor derive shape: Getter+GetterMut+Setter spelled out instead of Data / Data with no mutator instead of Getter §17.16/§17.16.1",
    # §17.17 (2026-10-16 user 钦定). If a type has a `new`, it comes from
    # `#[derive(New)]` — whose whole advantage is `#[new(skip)]` dropping a
    # field out of the signature and defaulting it, which a hand-written
    # `fn new` cannot express. Registered in the audit and here together;
    # a rule enforced in only one caller is not a rule. Scoped to structs
    # that ALREADY derive `New`, so constructors which validate or transform
    # (and cannot use `New`) are untouched.
    "verify_no_manual_new_fn": "hand-written fn new on a New-derived struct §17.17",
    # §17.8.1 + §17.14 (2026-10-13). Both rules previously existed as
    # prose only — the audit did not run them and this gate did not
    # either, so nothing caught them. Registered in both callers so a
    # staged .rs edit cannot introduce either.
    "verify_lombok_accessor_contract": "lombok type(copy) on primitives + visibility narrowing §17.8.1/§17.14",
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
    # §2.5 (2026-10-09, absolute): zero comments in every *.toml and every
    # mod.rs. The only verifier that accepts `.toml` files, which is why
    # TOML_AWARE exists: the gate now lets staged .toml through the pipeline
    # but every other verifier still sees .rs only.
    "verify_no_toml_mod_comments": "no comments in *.toml / mod.rs §2.5",
    # §14.4. The audit's check 8 was the only enforcement of "no inline
    # `#[cfg(test)] mod tests { ... }` in a production file", and it was
    # diff-scoped: a violation already sitting in a production file was
    # never reported, and an unrelated edit to that file left it in place
    # while the check stayed silent.  Found by planting an inline test
    # block and watching the gate report 0 while the audit check could
    # not see it either.  `audit_one` reads only the path it is handed,
    # so the gate's before/after baselines compare.
    "verify_no_inline_cfg_test": "inline #[cfg(test)] mod tests in a production file §14.4",
    # §14.4, the OTHER half of the same rule.  The audit's check 4 was the
    # only enforcement of "no bare `#[test]` in a production file", and it
    # was an inline shell pipeline over `git diff origin/master HEAD`: it
    # only ever saw the lines the branch ADDS, so a violation already
    # sitting in a production file was never reported and an unrelated edit
    # to that file left it in place while the check stayed silent.  Same
    # gap as §1.4 and R11.4, and the hook could not run the rule at all
    # because it had no per-file script to drive.  `audit_one` reads only
    # the path it is handed, so the gate's before/after baselines compare.
    # The verifier skips test attributes that live inside an inline
    # `#[cfg(test)] mod { }` block, because that shape is owned by
    # `verify_no_inline_cfg_test` above — one mistake, one finding.
    "verify_no_test_in_production": "bare #[test] in a production file §14.4",
}

# Verifiers that only make sense for a specific file name.
FILE_SCOPED = {"verify_lib_rs_doc_comment": "lib.rs"}

# Verifiers that accept staged `.toml` files in addition to `.rs`. Every
# other verifier assumes Rust content, so a staged Cargo.toml must never
# reach their audit_one.
TOML_AWARE = {"verify_no_toml_mod_comments"}



def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def load_verifier(scripts: Path, name: str):
    path = scripts / f"{name}.py"
    if not path.is_file():
        raise RuntimeError(f"required verifier missing: {path}")
    spec = importlib.util.spec_from_file_location(f"rsv_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException as error:
        raise RuntimeError(f"cannot import required verifier {path}: {error}") from error
    if not callable(getattr(module, "audit_one", None)):
        raise RuntimeError(f"required audit_one missing: {path}")
    return module


def audit(module, path: Path | None) -> list:
    if path is None or not path.is_file():
        return []
    try:
        return list(module.audit_one(path))
    except BaseException as error:
        raise RuntimeError(f"{module.__name__}.audit_one failed on {path}: {error}") from error


def entries(repo: Path, tree: str) -> list:
    result = []
    for record in git(repo, "ls-tree", "-r", "-z", tree).split(b"\0"):
        if record:
            header, relative = record.split(b"\t", 1)
            mode, kind, oid = header.split()
            result.append((os.fsdecode(relative), mode, kind, oid))
    return result


def materialise(repo: Path, tree: str, destination: Path) -> None:
    """Copy every tracked blob, including verifier configuration and context."""
    destination.mkdir()
    # Keep metadata and the index private; share only immutable object reads.
    # An empty index changes ls-files/check-ignore and silently drops context.
    clean_env = {key: value for key, value in os.environ.items() if key not in GIT_LOCAL_ENV}
    subprocess.run(["git", "-C", str(destination), "init", "--quiet", "--template="],
                   env=clean_env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    objects = Path(os.fsdecode(git(repo, "rev-parse", "--git-path", "objects")).strip())
    if not objects.is_absolute():
        objects = repo / objects
    (destination / ".git/objects/info/alternates").write_text(str(objects.resolve()) + "\n")
    subprocess.run(["git", "-C", str(destination), "read-tree", tree],
                   env=clean_env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    source_head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", "HEAD"],
                                 check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if source_head.returncode == 0:
        subprocess.run(["git", "-C", str(destination), "update-ref", "HEAD", source_head.stdout.decode().strip()],
                       env=clean_env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif source_head.returncode != 1:
        raise RuntimeError("cannot resolve snapshot HEAD")
    records = entries(repo, tree)
    for relative, mode, kind, oid in records:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or any(part.casefold() == ".git" for part in path.parts):
            raise RuntimeError(f"unsafe tree path: {relative!r}")
    blobs = [entry for entry in records if entry[2] == b"blob"]
    request = b"".join(oid + b"\n" for _, _, _, oid in blobs)
    data = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                          input=request, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout
    offset = 0
    links = []
    for relative, mode, kind, oid in blobs:
        path = Path(relative)
        end = data.index(b"\n", offset)
        found, found_kind, length = data[offset:end].split()
        if found != oid or found_kind != kind:
            raise RuntimeError(f"invalid blob response: {relative!r}")
        size = int(length)
        content = data[end + 1:end + 1 + size]
        offset = end + size + 2
        if len(content) != size:
            raise RuntimeError(f"truncated blob: {relative!r}")
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write ordinary files before creating any links, so writes can never
        # follow a tree-controlled link. Validate chains only once all exist.
        if mode == b"120000":
            link = os.fsdecode(content)
            lexical = Path(os.path.abspath(target.parent / link))
            if (not link or Path(link).is_absolute() or
                    any(part.casefold() == ".git" for part in Path(link).parts) or
                    not lexical.is_relative_to(destination.resolve())):
                raise RuntimeError(f"unsafe symlink target: {relative!r}")
            links.append((target, link))
            continue
        if mode not in (b"100644", b"100755"):
            raise RuntimeError(f"unsupported blob mode: {mode!r} {relative!r}")
        target.write_bytes(content)
        target.chmod(0o755 if mode == b"100755" else 0o644)
    for relative, mode, kind, oid in records:
        if kind == b"commit":
            (destination / relative).mkdir(parents=True, exist_ok=True)
    for target, link in links:
        target.symlink_to(link)
    root = destination.resolve()
    for target, link in links:
        try:
            resolved = target.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise RuntimeError(f"broken or cyclic symlink: {target.relative_to(root)!s}") from error
        if (not resolved.is_relative_to(root) or
                any(part.casefold() == ".git" for part in resolved.relative_to(root).parts)):
            raise RuntimeError(f"unsafe symlink chain: {target.relative_to(root)!s}")


def changes(repo: Path, head: str, index: str) -> tuple[list[str], dict[str, str], list[str]]:
    fields = git(repo, "diff-tree", "--no-commit-id", "-r", "--name-status", "-z",
                 "--find-renames", head, index).split(b"\0")
    selected, renames, sources = [], {}, []
    iterator = iter(fields)
    for status in iterator:
        if not status:
            continue
        old = os.fsdecode(next(iterator))
        action = status[:1]
        new = os.fsdecode(next(iterator)) if action in (b"R", b"C") else old
        if action == b"R":
            renames[new] = old
            sources.append(old)
        elif action == b"D":
            sources.append(old)
        if action in (b"A", b"C", b"M", b"R", b"T") and new.endswith((".rs", ".toml")):
            if not new.startswith("target/"):
                selected.append(new)
    return selected, renames, list(dict.fromkeys(sources))


def _content_lines(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("//")}


def _same_or_nested_dir(old_path: str, target_dir: str) -> bool:
    old_dir = str(Path(old_path).parent)
    return (old_dir == target_dir or
            (old_dir != "." and target_dir != "." and
             (old_dir.startswith(target_dir + "/") or target_dir.startswith(old_dir + "/"))))


def baseline_paths(ctx: dict, rel: str) -> list[Path]:
    """Preserve rename/split debt, always auditing original HEAD paths/context."""
    head, staged = ctx["head"], ctx["index"]
    own = head / ctx["renames"].get(rel, rel)
    result = [own] if own.is_file() else []
    current = _content_lines(staged / rel)
    best = None
    for source in ctx["sources"]:
        path = head / source
        if path in result or not path.is_file() or path.suffix != Path(rel).suffix:
            continue
        if not _same_or_nested_dir(source, str(Path(rel).parent)):
            continue
        overlap = len(current & _content_lines(path)) / len(current) if current else 0
        if overlap >= SPLIT_MIN_OVERLAP and (best is None or overlap > best[0]):
            best = overlap, path
    if best is not None:
        result.append(best[1])
    return result


_CTX = {}


def _init_worker(ctx: dict) -> None:
    global _CTX
    for key in GIT_LOCAL_ENV:
        os.environ.pop(key, None)
    _CTX = {**ctx, "modules": {}}


def _check_file(rel: str) -> tuple[int, list[str]]:
    ctx = _CTX
    if not ctx["modules"]:
        ctx["modules"] = {name: load_verifier(ctx["scripts"], name) for name in ctx["names"]}
    target = ctx["index"] / rel
    if not target.is_file():
        raise RuntimeError(f"selected path absent from index snapshot: {rel!r}")
    baselines = baseline_paths(ctx, rel)
    count, report = 0, []
    for name, module in ctx["modules"].items():
        if rel.endswith(".toml") and name not in TOML_AWARE:
            continue
        required = FILE_SCOPED.get(name)
        if required and target.name != required:
            continue
        before = sum(len(audit(module, p)) for p in baselines
                     if not required or p.name == required)
        after = len(audit(module, target))
        delta = max(0, after - before)
        count += delta
        if delta:
            report.append(f"  {rel}: +{delta} new ({name} — {VERIFIERS[name]})")
    return count, report


def main() -> int:
    if len(sys.argv) < 2:
        raise ValueError("usage: staged_file_gate.py <repo-root> [--staged | --file PATH ...]")
    repo = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    if args and args[0] not in ("--staged", "--file"):
        raise ValueError("unknown arguments")
    # Resolve helpers beside this executable, so isolated installations and
    # regression copies exercise exactly the selected verifier dependencies.
    scripts = Path(__file__).resolve().parent
    index_path = Path(os.fsdecode(git(repo, "rev-parse", "--git-path", "index")).strip())
    if not index_path.is_absolute():
        index_path = repo / index_path
    with tempfile.TemporaryDirectory(prefix="staged-index-copy-", dir=os.environ.get("TMPDIR")) as copied:
        private_index = Path(copied) / "index"
        private_index.write_bytes(index_path.read_bytes())
        index = subprocess.run(["git", "-C", str(repo), "write-tree"],
                               env={**os.environ, "GIT_INDEX_FILE": str(private_index)},
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()
    probe = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", "HEAD"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if probe.returncode == 0:
        head = probe.stdout.decode().strip()
    elif probe.returncode == 1 and not git(repo, "symbolic-ref", "-q", "HEAD").strip() == b"":
        head = subprocess.run(["git", "-C", str(repo), "hash-object", "-t", "tree", "-w", "--stdin"],
                              input=b"", check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    else:
        raise RuntimeError("cannot resolve HEAD")
    selected, renames, sources = changes(repo, head, index)
    if args and args[0] == "--file":
        requested = set(args[1:])
        selected = [rel for rel in selected if rel in requested]
    if not selected:
        print("staged_file_gate: no staged .rs/.toml files, nothing to check")
        return 0
    only = {part.strip() for part in os.environ.get("STAGED_FILE_GATE_ONLY_VERIFIERS", "").split(",") if part.strip()}
    unknown = only - VERIFIERS.keys()
    if unknown:
        raise RuntimeError(f"unknown required verifiers: {sorted(unknown)}")
    names = [name for name in VERIFIERS if not only or name in only]
    # Validate every required helper in the parent before starting workers.
    for name in names:
        load_verifier(scripts, name)
    with tempfile.TemporaryDirectory(prefix="staged-rust-context-", dir=os.environ.get("TMPDIR")) as temporary:
        root = Path(temporary)
        baseline, staged = root / "head", root / "index"
        materialise(repo, head, baseline)
        materialise(repo, index, staged)
        ctx = dict(head=baseline, index=staged, scripts=scripts, names=names, renames=renames, sources=sources)
        jobs = min(len(selected), int(os.environ.get("STAGED_FILE_GATE_JOBS", os.cpu_count() or 4)))
        if jobs <= 1:
            _init_worker(ctx)
            results = [_check_file(rel) for rel in selected]
        else:
            with multiprocessing.Pool(processes=jobs, initializer=_init_worker, initargs=(ctx,)) as pool:
                results = pool.map(_check_file, selected)
    count = sum(item[0] for item in results)
    for _, report in results:
        for line in report:
            print(line)
    print(f"staged_file_gate: {len(selected)} staged .rs/.toml files; {count} new violations (index vs HEAD)")
    return 1 if count else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"staged_file_gate: ERROR — commit BLOCKED: {error}", file=sys.stderr)
        sys.exit(2)
