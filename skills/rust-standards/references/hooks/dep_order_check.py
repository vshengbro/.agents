#!/usr/bin/env python3
"""The staged dependency-order check of the global pre-commit hook.

Extracted verbatim from the hook's here-document so that the check can run
wherever bash cannot create a here-document temporary file. The hook calls:

    python3 ~/.git-hooks/dep_order_check.py <repo-root> <scripts-dir>

Exit 0 when no staged TOML file gains dependency-order violations, 1 when one
does, and 2 when the check itself could not run.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def git(*arguments):
    return subprocess.run(
        ["git", *arguments], cwd=repo, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def manifest(path):
    return Path(path).name == "Cargo.toml" or path in selected


def write_tree(destination, entries):
    for relative, mode, object_id in entries:
        if not manifest(relative):
            continue
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"invalid manifest path: {relative!r}")
        if mode not in (b"100644", b"100755"):
            raise RuntimeError(f"unsupported manifest mode {mode!r}: {relative}")
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("cat-file", "blob", object_id.decode("ascii")))


def local_names(path, view):
    text = path.read_text()
    members = verifier.re.search(r"members\s*=\s*\[(.*?)\]", text, verifier.re.S)
    if members:
        for member in verifier.re.findall(r'"([^\"]+)"', members.group(1)):
            target = (path.parent / member / "Cargo.toml").resolve()
            if not target.is_relative_to(view):
                raise RuntimeError(f"workspace member outside staged repository: {member}")
    return verifier.read_local_crate_names(path)


def findings(view):
    files = sorted(verifier.find_cargo_tomls(view), key=lambda p: (len(p.parts), str(p)))
    for path in files:
        local_names(path, view)
    result = {}
    for relative in selected:
        path = view / relative
        if path.exists():
            names = verifier.local_crate_names_for_manifest(path, view)
            result[relative] = verifier.check_file_v2(path, names) + verifier.check_cross_section_blanks(path)
        else:
            result[relative] = []
    return result


try:
    repo = Path(sys.argv[1]).resolve()
    scripts = Path(sys.argv[2])
    spec = importlib.util.spec_from_file_location("hook_dep_order", scripts / "verify_dep_order.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load canonical dependency-order verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    selected = sorted(
        os.fsdecode(path) for path in git(
            "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z", "--",
            ":(exclude)target/*", ":(exclude)*.lock",
        ).split(b"\0") if path and path.endswith(b".toml")
    )
    if not selected:
        raise RuntimeError("staged TOML selection changed; retry the commit")
    index_entries = []
    for record in git("ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        header, relative = record.split(b"\t", 1)
        mode, object_id, stage = header.split()
        path = os.fsdecode(relative)
        if manifest(path) and stage != b"0":
            raise RuntimeError(f"unmerged manifest in index: {path}")
        index_entries.append((path, mode, object_id))
    if not set(selected).issubset({entry[0] for entry in index_entries}):
        raise RuntimeError("staged TOML path missing from index snapshot")
    head_probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    head_entries = []
    if head_probe.returncode == 0:
        head = head_probe.stdout.decode("ascii").strip()
        for record in git("ls-tree", "-r", "-z", head).split(b"\0"):
            if record:
                header, relative = record.split(b"\t", 1)
                mode, kind, object_id = header.split()
                head_entries.append((os.fsdecode(relative), mode, object_id))
    with tempfile.TemporaryDirectory(prefix="dep-order-context-", dir=os.environ.get("TMPDIR")) as temporary:
        root = Path(temporary).resolve()
        baseline, staged = root / "head", root / "index"
        baseline.mkdir()
        staged.mkdir()
        write_tree(baseline, head_entries)
        write_tree(staged, index_entries)
        old, new = findings(baseline), findings(staged)
        blocked = []
        for relative in selected:
            if len(new[relative]) > len(old[relative]):
                blocked.append(relative)
                print(f"dep-order {relative}: {len(old[relative])} -> {len(new[relative])} violations")
                for diagnostic in new[relative]:
                    print(diagnostic.replace(str(staged) + os.sep, ""))
        print(f"dep-order gate: {len(selected)} staged TOML file(s), full HEAD/index context, {len(blocked)} blocked")
        sys.exit(1 if blocked else 0)
except Exception as error:
    affected = ", ".join(selected) if "selected" in globals() else "selection unavailable"
    print(f"dep-order gate error: {error}; staged TOML: {affected}", file=sys.stderr)
    sys.exit(2)
