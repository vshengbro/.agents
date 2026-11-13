#!/usr/bin/env python3
"""Vendor the complete Blender skills tree without changing upstream layout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
URL = "https://github.com/arjun988/blender-skills.git"
PREFIX = "skills/blender-skills/"
SUBPATH = ".claude/skills"


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def inventory(root):
    if not root.is_dir() or root.is_symlink():
        return None
    result = {}
    for path in sorted(root.rglob("*")):
        key = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[key] = ("symlink", os.readlink(path))
        elif path.is_dir():
            result[key] = ("directory",)
        elif path.is_file():
            result[key] = ("file", path.read_bytes())
        else:
            raise ValueError(f"Unsupported file: {path}")
    return result


def skill_name(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    names = re.findall(r"^name:\s*([^\r\n]+)$", match[1], re.M) if match else []
    if len(names) != 1:
        raise ValueError(f"Missing or ambiguous frontmatter name: {path}")
    name = names[0].strip()
    if name[:1] in ("'", '"') and name[-1:] == name[:1]:
        name = name[1:-1]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"Invalid skill name {name!r}: {path}")
    if name != path.parent.name:
        raise ValueError(f"Skill name must match its directory: {path} ({name})")
    return name


def fingerprint(path):
    raw = path.read_bytes()
    return hashlib.sha1(f"SKILL.md\0{len(raw)}\0".encode() + raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--source-dir", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.ref or "\n" in args.ref or "`" in args.ref:
        raise ValueError("Invalid ref")
    source = args.source_dir
    if source is None:
        source = (Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
                  / "agents-sync/blender-skills").resolve()
        if source == ROOT or ROOT in source.parents:
            raise ValueError("Network cache must be outside the repository")
        source.parent.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            subprocess.run(["git", "clone", "--quiet", URL, str(source)], check=True)
        if git(source, "remote", "get-url", "origin") != URL:
            raise ValueError("Cache origin does not match upstream")
        subprocess.run(["git", "-C", str(source), "fetch", "--quiet", "--depth", "1",
                        "origin", args.ref], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "--quiet", "--detach",
                        "FETCH_HEAD"], check=True)
    source = source.resolve()
    commit = git(source, "rev-parse", "HEAD")
    upstream = source / SUBPATH
    if not upstream.is_dir():
        raise ValueError(f"Missing {SUBPATH}: {source}")
    dest = ROOT / PREFIX.rstrip("/")
    if dest.is_symlink():
        raise ValueError("Destination must not be a symlink")
    paths = sorted(upstream.rglob("SKILL.md"))
    if not paths:
        raise ValueError("Upstream contains no skills")
    names = {}
    for path in paths:
        name = skill_name(path)
        if name in names:
            raise ValueError(f"Duplicate upstream skill: {name}")
        names[name] = path.relative_to(upstream)
    for path in (ROOT / "skills").rglob("SKILL.md"):
        if dest in path.parents:
            continue
        # Both registry keys and declared names must remain unique.
        if path.parent.name in names:
            raise ValueError(f"Existing skill collision: {path}")
        text = path.read_text(encoding="utf-8")
        header = re.match(r"\A---\r?\n(.*?)\r?\n---", text, re.S)
        if header:
            found = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", header[1], re.M)
            if found and found[1] in names:
                raise ValueError(f"Existing declared name collision: {path}")
    provenance = dict(source="arjun988/blender-skills", sourceType="github",
                      sourceUrl=URL, ref=args.ref, subpath=SUBPATH, upstreamCommit=commit)
    scratch = Path.home() / ".hermes/cache/scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-sync-", dir=scratch) as temp:
        stage = Path(temp) / "tree"
        # Reject links rather than silently dereferencing files outside the source.
        source_inventory = inventory(upstream)
        if source_inventory is None:
            raise ValueError("Upstream skills root must be a real directory")
        if any(value[0] == "symlink" for value in source_inventory.values()):
            raise ValueError("Upstream symlinks are not supported")
        shutil.copytree(upstream, stage)
        for reserved in ("LICENSE", "UPSTREAM.md"):
            if (stage / reserved).exists():
                raise ValueError(f"Upstream tree uses reserved attribution path: {reserved}")
        if (source / "LICENSE").is_symlink():
            raise ValueError("Upstream LICENSE must not be a symlink")
        shutil.copyfile(source / "LICENSE", stage / "LICENSE")
        (stage / "UPSTREAM.md").write_text(
            "# Upstream provenance\n\n"
            f"Vendored from [arjun988/blender-skills]({URL}), directory `{SUBPATH}/`.\n\n"
            f"- upstream commit: `{commit}`\n- upstream ref: `{args.ref}`\n\n"
            "The complete upstream tree, including shared references, is preserved.\n"
            "The upstream LICENSE is included alongside the skills.\n\n"
            "Refresh with:\n\n```shell\n"
            f"bash scripts/sync-blender-skills.sh --ref {args.ref}\n"
            f"bash scripts/sync-blender-skills.sh --ref {args.ref} --check\n```\n\n"
            "Do not hand-edit this vendored tree; synchronization replaces it.\n",
            encoding="utf-8")
        lock_path = ROOT / ".skill-lock.json"
        original_bytes = lock_path.read_bytes() if lock_path.exists() else None
        lock = json.loads(original_bytes) if original_bytes else {}
        entries = lock.get("skills", {})
        expected_paths = {name: PREFIX + rel.as_posix() for name, rel in names.items()}
        drift = inventory(stage) != inventory(dest)
        if drift:
            print("DRIFT: vendored file set, types, or bytes differ (including attribution)")
        for name, rel in names.items():
            expected = dict(provenance, skillPath=expected_paths[name],
                            skillFolderHash=fingerprint(upstream / rel))
            if any(entries.get(name, {}).get(k) != v for k, v in expected.items()):
                print(f"DRIFT: lock entry {name}")
                drift = True
        if any(entry.get("skillPath", "").startswith(PREFIX) and name not in names
               for name, entry in entries.items()):
            print("DRIFT: orphaned vendored lock entries")
            drift = True
        if args.check:
            if not drift:
                print(f"OK: exact tree and lock provenance match {commit}")
            return int(drift)
        if args.dry_run:
            print(f"Would sync {len(names)} skills at {commit}; drift={drift}")
            return 0
        # Keep a rollback copy outside the repo until the lock update succeeds.
        backup = Path(temp) / "backup"
        existed = dest.exists()
        if existed:
            shutil.copytree(dest, backup, symlinks=True)
        try:
            if existed:
                shutil.rmtree(dest)
            shutil.copytree(stage, dest)
            subprocess.run([sys.executable, str(ROOT / "scripts/update_skill_lock.py"),
                            "--preserve-prefix", "skills/rust-standards/"], check=True)
            updated = json.loads(lock_path.read_text(encoding="utf-8"))
            # This sync owns only its own lock records, not unrelated inventory drift.
            own = {name: updated["skills"][name] for name in names}
            updated["skills"] = {name: entry for name, entry in entries.items()
                                 if not entry.get("skillPath", "").startswith(PREFIX)}
            for name, entry in own.items():
                entry.update(provenance)
                updated["skills"][name] = entry
            lock_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        except BaseException:
            if dest.exists():
                shutil.rmtree(dest)
            if existed:
                shutil.copytree(backup, dest, symlinks=True)
            if original_bytes is None:
                lock_path.unlink(missing_ok=True)
            else:
                lock_path.write_bytes(original_bytes)
            raise
        print(f"Synced {len(names)} skills at {commit}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
