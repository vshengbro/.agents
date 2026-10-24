#!/usr/bin/env python3
"""Regression tests for `update_skill_lock.py` and `audit_skills.py`.

Every test uses a throwaway tree under `~/.hermes/cache/scratch` (via
`tempfile.TemporaryDirectory`), never against the real repository. The
`update_skill_lock` module is loaded via `importlib` and its `ROOT` /
`SKILLS_DIR` / `LOCK_PATH` module globals are re-pointed at the fixture;
`sys.argv` is saved and restored around every invocation.

Run:
    PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_update_skill_lock.py
    python3 scripts/test_update_skill_lock.py -v
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS_DIR = Path(__file__).resolve().parent
FIXTURE_ROOT = Path.home() / ".hermes" / "cache" / "scratch"
FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


usl = load_module("_usl_under_test", "update_skill_lock.py")
audit = load_module("_audit_under_test", "audit_skills.py")


@contextlib.contextmanager
def fixture(skills: dict[str, str], lock: dict | None = None):
    """Build `<tmp>/skills/<name>/SKILL.md` plus an optional lock file."""
    with tempfile.TemporaryDirectory(prefix="usl-fixture-", dir=FIXTURE_ROOT) as td:
        root = Path(td)
        sd = root / "skills"
        for rel, body in skills.items():
            p = sd / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        lp = root / ".skill-lock.json"
        if lock is not None:
            lp.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        yield root, sd, lp


class ModuleStateMixin(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = (
            usl.SKILLS_DIR, usl.LOCK_PATH, sys.argv,
            usl.REPO_ROOT,
        )
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        usl.SKILLS_DIR, usl.LOCK_PATH, sys.argv, usl.REPO_ROOT = self._saved

    def run_cli(self, root: Path, skills_dir: Path, lock: Path, *args: str) -> tuple[int, str, str]:
        usl.REPO_ROOT = root
        usl.SKILLS_DIR = skills_dir
        usl.LOCK_PATH = lock
        sys.argv = ["update_skill_lock.py", *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = usl.main()
        return code, out.getvalue(), err.getvalue()


def skill_md(name: str, description: str = "d", body: str = "# T\n") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"


# ---------------------------------------------------------------------------
# update_skill_lock: discovery
# ---------------------------------------------------------------------------
class TestDiscovery(ModuleStateMixin):
    def test_recursive_finds_parent_and_nested_child(self):
        """A category-less parent AND its nested child both get lock entries.

        Regression: the original one-level `skills/*/SKILL.md` glob skipped
        every categorised skill, so `creative/`, `web/` etc. were invisible.
        """
        with fixture({"alpha/SKILL.md": skill_md("alpha"),
                      "rust-standards/SKILL.md": skill_md("rust-standards"),
                      "rust-standards/nested-child/SKILL.md": skill_md("nested-child")}) as (root, sd, lp):
            code, out, _ = self.run_cli(root, sd, lp)
            self.assertEqual(code, 0, out)
            skills = json.loads(lp.read_text())["skills"]
            self.assertEqual(sorted(skills), ["alpha", "nested-child", "rust-standards"])

    def test_nested_child_uses_full_repo_relative_path(self):
        with fixture({"cat/deep/SKILL.md": skill_md("deep")}) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            entry = json.loads(lp.read_text())["skills"]["deep"]
            self.assertEqual(entry["skillPath"], "skills/cat/deep/SKILL.md")

    def test_dot_and_pending_dirs_are_ignored(self):
        with fixture({"real/SKILL.md": skill_md("real"),
                      ".hidden/SKILL.md": skill_md("hidden"),
                      "_pending/SKILL.md": skill_md("pending")}) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            self.assertEqual(sorted(json.loads(lp.read_text())["skills"]), ["real"])


# ---------------------------------------------------------------------------
# update_skill_lock: duplicate names
# ---------------------------------------------------------------------------
class TestDuplicates(ModuleStateMixin):
    def test_duplicate_bare_name_is_rejected_with_exit_2(self):
        with fixture({"cat-a/dup/SKILL.md": skill_md("dup"),
                      "cat-b/dup/SKILL.md": skill_md("dup")}) as (root, sd, lp):
            code, _out, err = self.run_cli(root, sd, lp)
            self.assertEqual(code, 2)
            self.assertIn("duplicate skill name", err)

    def test_duplicate_raises_value_error_internally(self):
        with fixture({"a/x/SKILL.md": skill_md("x"), "b/x/SKILL.md": skill_md("x")}) as (root, sd, lp):
            usl.SKILLS_DIR = sd
            usl.LOCK_PATH = lp
            with self.assertRaises(ValueError):
                usl._build_skills_map({}, ())


# ---------------------------------------------------------------------------
# update_skill_lock: --check / --diff / idempotence
# ---------------------------------------------------------------------------
class TestModes(ModuleStateMixin):
    def _synced(self):
        return fixture({"a/SKILL.md": skill_md("a"), "b/SKILL.md": skill_md("b")})

    def test_update_then_check_exits_zero(self):
        with self._synced() as (root, sd, lp):
            self.run_cli(root, sd, lp)
            code, out, _ = self.run_cli(root, sd, lp, "--check")
            self.assertEqual(code, 0, out)
            self.assertIn("already in sync", out)

    def test_check_exits_one_on_drift(self):
        with self._synced() as (root, sd, lp):
            (sd / "c" / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
            (sd / "c" / "SKILL.md").write_text(skill_md("c"), encoding="utf-8")
            code, out, _ = self.run_cli(root, sd, lp, "--check")
            self.assertEqual(code, 1)
            self.assertIn("would ADD", out)
            self.assertIn("c", out)

    def test_check_detects_content_drift(self):
        with self._synced() as (root, sd, lp):
            self.run_cli(root, sd, lp)
            (sd / "a" / "SKILL.md").write_text(skill_md("a", body="# changed\n"),
                                               encoding="utf-8")
            code, out, _ = self.run_cli(root, sd, lp, "--check")
            self.assertEqual(code, 1)
            self.assertIn("would UPDATE", out)

    def test_check_does_not_write(self):
        with self._synced() as (root, sd, lp):
            self.run_cli(root, sd, lp)
            before = lp.read_bytes()
            (sd / "c").mkdir()
            (sd / "c" / "SKILL.md").write_text(skill_md("c"), encoding="utf-8")
            self.run_cli(root, sd, lp, "--check")
            self.assertEqual(lp.read_bytes(), before)

    def test_diff_does_not_write_and_exits_zero(self):
        with self._synced() as (root, sd, lp):
            self.run_cli(root, sd, lp)
            before = lp.read_bytes()
            (sd / "c").mkdir()
            (sd / "c" / "SKILL.md").write_text(skill_md("c"), encoding="utf-8")
            code, out, _ = self.run_cli(root, sd, lp, "--diff")
            self.assertEqual(code, 0, "--diff previews successfully")
            self.assertIn("would ADD", out)
            self.assertEqual(lp.read_bytes(), before, "--diff must not write")

    def test_update_is_byte_idempotent(self):
        with self._synced() as (root, sd, lp):
            self.run_cli(root, sd, lp)
            first = lp.read_bytes()
            code, out, _ = self.run_cli(root, sd, lp)
            self.assertEqual(code, 0, out)
            self.assertEqual(lp.read_bytes(), first,
                             "second run must not rewrite a byte")
            self.assertIn("already in sync", out)

    def test_update_preserves_installed_at_when_hash_unchanged(self):
        lock = {"version": 3,
                "skills": {"a": {"source": "local", "sourceType": "local",
                                 "skillPath": "skills/a/SKILL.md",
                                 "installedAt": "2020-01-01T00:00:00.000Z",
                                 "updatedAt": "2020-01-01T00:00:00.000Z",
                                 "skillFolderHash": usl._fingerprint(Path("x"))}}}
        # build a real matching lock from a first run, then hand-edit timestamps
        with fixture({"a/SKILL.md": skill_md("a")}) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            data = json.loads(lp.read_text())
            data["skills"]["a"]["installedAt"] = "2019-05-05T00:00:00.000Z"
            data["skills"]["a"]["updatedAt"] = "2019-05-05T00:00:00.000Z"
            lp.write_text(json.dumps(data, indent=2) + "\n")
            self.run_cli(root, sd, lp)
            after = json.loads(lp.read_text())["skills"]["a"]
            self.assertEqual(after["installedAt"], "2019-05-05T00:00:00.000Z")
            self.assertEqual(after["updatedAt"], "2019-05-05T00:00:00.000Z")
        del lock

    def test_top_level_metadata_is_retained(self):
        lock = {"version": 5, "dismissed": ["x"], "lastSelectedAgents": {"a": 1},
                "skills": {}}
        with fixture({"a/SKILL.md": skill_md("a")}, lock) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            out = json.loads(lp.read_text())
            self.assertEqual(out["dismissed"], ["x"])
            self.assertEqual(out["lastSelectedAgents"], {"a": 1})
            self.assertGreaterEqual(out["version"], 5)

    def test_provenance_fields_survive_a_hash_change(self):
        with fixture({"a/SKILL.md": skill_md("a")}) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            data = json.loads(lp.read_text())
            entry = data["skills"]["a"]
            entry.update({"source": "github", "sourceType": "git",
                          "sourceUrl": "https://example.com/o/r", "ref": "v1",
                          "subpath": "s", "version": "1.2.3"})
            lp.write_text(json.dumps(data, indent=2) + "\n")
            (sd / "a" / "SKILL.md").write_text(skill_md("a", body="# edited\n"),
                                               encoding="utf-8")
            self.run_cli(root, sd, lp)
            after = json.loads(lp.read_text())["skills"]["a"]
            self.assertEqual(after["source"], "github")
            self.assertEqual(after["sourceType"], "git")
            self.assertEqual(after["sourceUrl"], "https://example.com/o/r")
            self.assertEqual(after["ref"], "v1")
            self.assertEqual(after["subpath"], "s")
            self.assertEqual(after["version"], "1.2.3")
            self.assertIn("skillFolderHash", after)

    def test_removed_skill_is_dropped_and_version_bumped(self):
        with fixture({"a/SKILL.md": skill_md("a"), "gone/SKILL.md": skill_md("gone")},
                     {"version": 4, "skills": {}}) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            v1 = json.loads(lp.read_text())
            (sd / "gone" / "SKILL.md").unlink()
            (sd / "gone").rmdir()
            self.run_cli(root, sd, lp)
            v2 = json.loads(lp.read_text())
            self.assertNotIn("gone", v2["skills"])
            self.assertEqual(v2["version"], v1["version"] + 1)


# ---------------------------------------------------------------------------
# update_skill_lock: argument handling
# ---------------------------------------------------------------------------
class TestArgs(ModuleStateMixin):
    def test_unknown_flag_exits_2(self):
        with fixture({"a/SKILL.md": skill_md("a")}) as (root, sd, lp):
            saved = sys.argv
            sys.argv = ["update_skill_lock.py", "--nope"]
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    usl.main()
            sys.argv = saved
            self.assertEqual(ctx.exception.code, 2)

    def test_diff_and_check_are_mutually_exclusive(self):
        with fixture({"a/SKILL.md": skill_md("a")}) as (root, sd, lp):
            saved = sys.argv
            sys.argv = ["update_skill_lock.py", "--diff", "--check"]
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    usl.main()
            sys.argv = saved
            self.assertEqual(ctx.exception.code, 2)

    def test_missing_skills_dir_exits_2(self):
        with tempfile.TemporaryDirectory(prefix="usl-fixture-", dir=FIXTURE_ROOT) as td:
            root = Path(td)
            code, _o, err = self.run_cli(root, root / "skills", root / ".skill-lock.json")
            self.assertEqual(code, 2)
            self.assertIn("not found", err)


# ---------------------------------------------------------------------------
# update_skill_lock: --preserve-prefix
# ---------------------------------------------------------------------------
class TestPreservePrefix(ModuleStateMixin):
    def _tree(self):
        return {
            "rust-standards/SKILL.md": skill_md("rust-standards"),
            "rust-standards/child/SKILL.md": skill_md("child"),
            "rust-standards-extra/SKILL.md": skill_md("rust-standards-extra"),
            "other/SKILL.md": skill_md("other"),
        }

    def test_prefix_boundary_excludes_lookalike_sibling(self):
        """`skills/rust-standards/` must NOT capture `rust-standards-extra`."""
        with fixture(self._tree()) as (root, sd, lp):
            usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
            new_map = usl._build_skills_map({}, ("skills/rust-standards/",))
            self.assertIn("rust-standards-extra", new_map,
                          "prefix must be component-bounded, not string-prefixed")
            self.assertIn("other", new_map)

    def test_protected_entries_absent_from_lock_get_no_record(self):
        with fixture(self._tree()) as (root, sd, lp):
            usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
            new_map = usl._build_skills_map({}, ("skills/rust-standards/",))
            self.assertNotIn("rust-standards", new_map)
            self.assertNotIn("child", new_map)

    def test_existing_protected_entry_is_preserved_exactly(self):
        with fixture(self._tree()) as (root, sd, lp):
            usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
            old_entry = {"source": "local", "sourceType": "local",
                         "skillPath": "skills/rust-standards/SKILL.md",
                         "installedAt": "2018-01-01T00:00:00.000Z",
                         "updatedAt": "2018-01-01T00:00:00.000Z",
                         "skillFolderHash": "deadbeef", "customField": [1, 2]}
            new_map = usl._build_skills_map(
                {"skills": {"rust-standards": old_entry}},
                ("skills/rust-standards/",))
            self.assertEqual(new_map["rust-standards"], old_entry)
            self.assertEqual(new_map["rust-standards"]["skillFolderHash"], "deadbeef")

    def test_preserve_prefix_end_to_end_keeps_lock_entry(self):
        with fixture(self._tree()) as (root, sd, lp):
            self.run_cli(root, sd, lp)
            data = json.loads(lp.read_text())
            data["skills"]["rust-standards"]["updatedAt"] = "2018-01-01T00:00:00.000Z"
            lp.write_text(json.dumps(data, indent=2) + "\n")
            (sd / "rust-standards" / "SKILL.md").write_text(
                skill_md("rust-standards", body="# rewritten upstream\n"),
                encoding="utf-8")
            code, _o, _e = self.run_cli(root, sd, lp,
                                        "--preserve-prefix", "skills/rust-standards/")
            self.assertEqual(code, 0)
            after = json.loads(lp.read_text())["skills"]
            self.assertEqual(after["rust-standards"]["updatedAt"],
                             "2018-01-01T00:00:00.000Z")
            # the non-protected skill is still refreshed
            self.assertIn("other", after)

    def test_preserve_prefix_normalises_missing_trailing_slash(self):
        with fixture(self._tree()) as (root, sd, lp):
            usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
            new_map = usl._build_skills_map(
                {"skills": {"rust-standards": {"skillPath": "skills/rust-standards/SKILL.md"}}},
                ("skills/rust-standards",))
            self.assertIn("rust-standards", new_map)
            self.assertEqual(new_map["rust-standards"]["skillPath"],
                             "skills/rust-standards/SKILL.md")


# ---------------------------------------------------------------------------
class TestInventoryEdgeCases(ModuleStateMixin):
    def test_duplicate_name_cannot_hide_behind_preservation(self):
        for locked in (False, True):
            with self.subTest(locked=locked), fixture({
                "a/rust-standards/SKILL.md": skill_md("rust-standards"),
                "rust-standards/SKILL.md": skill_md("rust-standards"),
            }) as (_root, sd, lp):
                usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
                lock = {"skills": {"rust-standards": {"skillPath":
                        "skills/rust-standards/SKILL.md"}}} if locked else {}
                with self.assertRaisesRegex(ValueError, "duplicate skill name"):
                    usl._build_skills_map(lock, ("skills/rust-standards/",))

    def test_same_content_moved_to_category_updates_registered_path(self):
        with fixture({"alpha/SKILL.md": skill_md("alpha")}) as (_root, sd, lp):
            usl.SKILLS_DIR, usl.LOCK_PATH = sd, lp
            before = usl._build_skills_map({})
            destination = sd / "category" / "alpha"
            destination.parent.mkdir()
            (sd / "alpha").rename(destination)
            after = usl._build_skills_map({"skills": before})
            self.assertEqual(after["alpha"]["skillPath"], "skills/category/alpha/SKILL.md")
            self.assertEqual(after["alpha"]["skillFolderHash"], before["alpha"]["skillFolderHash"])
            self.assertEqual(after["alpha"]["installedAt"], before["alpha"]["installedAt"])


# audit_skills
# ---------------------------------------------------------------------------
class TestAuditHelpers(unittest.TestCase):
    def test_slug_matches_protected_incoming_anchor(self):
        """The exact anchor rust-standards/references/14-testing.md links to."""
        got = audit.github_slug("临时验证资源生命周期（硬规则 3 细则）")
        self.assertEqual(got, "临时验证资源生命周期硬规则-3-细则")

    def test_slug_drops_punctuation_and_lowercases(self):
        self.assertEqual(audit.github_slug("Find My (Apple)"), "find-my-apple")
        self.assertEqual(audit.github_slug("Due Time vs Alarm / Early Nudge"),
                         "due-time-vs-alarm--early-nudge")

    def test_duplicate_headings_get_github_suffixes(self):
        headings = [(1, 2, "Setup"), (2, 2, "Setup"), (3, 2, "Setup")]
        self.assertEqual(audit.anchor_set(headings), {"setup", "setup-1", "setup-2"})

    def test_links_inside_fences_are_not_checked(self):
        text = ("---\nname: x\n---\n\n"
                "```sh\n"
                "cat ./definitely-missing-file.md\n"
                "```\n\n"
                "```\nunterminated\n")
        links = audit.iter_links(text)
        self.assertEqual(links, [])
        _h, fences = audit.strip_code_and_scan(text)
        self.assertTrue(any(m.startswith("UNTERMINATED") for _s, _e, m in fences))

    def test_tilde_and_longer_fences_close(self):
        text = "~~~~\ncode ``` not a close\n~~~~\n[ok](./real.md)\n"
        _h, fences = audit.strip_code_and_scan(text)
        self.assertEqual(len(fences), 1)
        self.assertFalse(fences[0][2].startswith("UNTERMINATED"))

    def test_reference_style_links_are_resolved(self):
        text = "See [the docs][d].\n\n[d]: ./references/real.md\n"
        self.assertEqual([u for u, _k in audit.iter_links(text)], ["./references/real.md"])


class TestAuditEndToEnd(unittest.TestCase):
    def _run(self, root: Path, *extra: str) -> tuple[int, dict, str]:
        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["audit_skills.py", "--repo", str(root), "--json",
                    str(root / "out.json"), *extra]
        try:
            with contextlib.redirect_stdout(out):
                code = audit.main()
        finally:
            sys.argv = argv
        payload = json.loads((root / "out.json").read_text())
        return code, payload, out.getvalue()

    def _repo(self, files: dict[str, str], lock: dict | None = None):
        td = tempfile.TemporaryDirectory(prefix="audit-fixture-", dir=FIXTURE_ROOT)
        root = Path(td.name)
        for rel, body in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        if lock is not None:
            (root / ".skill-lock.json").write_text(json.dumps(lock), encoding="utf-8")
        self.addCleanup(td.cleanup)
        return root

    def test_help_exits_zero(self):
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["audit_skills.py", "--help"]
        try:
            with contextlib.redirect_stdout(buf):
                with self.assertRaises(SystemExit) as ctx:
                    audit.main()
        finally:
            sys.argv = argv
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--baseline", buf.getvalue())
        self.assertIn("--protected-prefix", buf.getvalue())

    def test_clean_repo_passes(self):
        root = self._repo({
            "skills/alpha/SKILL.md": skill_md("alpha", "Use when alpha applies."),
            "skills/cat/beta/SKILL.md": skill_md("beta", "Use when beta applies."),
        })
        code, payload, text = self._run(root)
        self.assertEqual(code, 0, text)
        self.assertEqual(payload["failures"], [])
        self.assertEqual(payload["metrics"]["skills_total_now"], 2)

    def test_missing_skills_dir_exits_2(self):
        with tempfile.TemporaryDirectory(prefix="audit-fixture-", dir=FIXTURE_ROOT) as td:
            root = Path(td)
            argv = sys.argv
            sys.argv = ["audit_skills.py", "--repo", str(root), "--quiet"]
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err):
                    code = audit.main()
            finally:
                sys.argv = argv
            self.assertEqual(code, 2)
            self.assertIn("not found", err.getvalue())

    def test_name_must_match_folder(self):
        root = self._repo({
            "skills/alpha/SKILL.md": skill_md("not-alpha", "Use when x."),
        })
        code, payload, _ = self._run(root)
        self.assertEqual(code, 1)
        self.assertTrue(any(f["check"] == "frontmatter.name_matches_folder"
                            for f in payload["failures"]))

    def test_duplicate_global_name_fails(self):
        root = self._repo({
            "skills/one/dup/SKILL.md": skill_md("dup", "Use when x."),
            "skills/two/dup/SKILL.md": skill_md("dup", "Use when x."),
        })
        code, payload, _ = self._run(root)
        self.assertEqual(code, 1)
        self.assertTrue(any(f["check"] == "name.global_unique"
                            for f in payload["failures"]))

    def test_line_budget_skips_protected(self):
        long_body = "\n".join(f"line {i}" for i in range(300))
        files = {
            "skills/fat/SKILL.md": skill_md("fat", "Use when x.", long_body),
            "skills/rust-standards/SKILL.md": skill_md(
                "rust-standards", "Use when x.", long_body),
        }
        root = self._repo(files)
        code, payload, _ = self._run(root, "--protected-prefix", "skills/rust-standards/")
        budget = [f for f in payload["failures"] if f["check"] == "entry.line_budget"]
        self.assertEqual([f["path"] for f in budget], ["skills/fat/SKILL.md"])
        self.assertEqual(code, 1)

    def test_overlong_description_fails(self):
        root = self._repo({"skills/a/SKILL.md": skill_md("a", "x" * 241)})
        code, payload, _ = self._run(root)
        self.assertEqual(code, 1)
        self.assertTrue(any(f["check"] == "description.length"
                            for f in payload["failures"]))

    def test_keyword_dump_description_fails(self):
        root = self._repo({"skills/a/SKILL.md": skill_md(
            "a", " ".join(f"kw{i}" for i in range(80)))})
        _code, payload, _ = self._run(root)
        self.assertTrue(any(f["check"] == "description.keyword_dump"
                            for f in payload["failures"]))

    def test_broken_relative_link_fails(self):
        body = "---\nname: a\ndescription: d\n---\n\n[gone](./nope.md)\n"
        root = self._repo({"skills/a/SKILL.md": body})
        _code, payload, _ = self._run(root)
        self.assertTrue(any(f["check"] == "link.target_missing"
                            for f in payload["failures"]))

    def test_external_and_mailto_links_ignored(self):
        body = ("---\nname: a\ndescription: d\n---\n\n"
                "[x](https://example.com/nope) [y](mailto:a@b.c)\n")
        root = self._repo({"skills/a/SKILL.md": body})
        code, _payload, _ = self._run(root)
        self.assertEqual(code, 0)

    def test_placeholder_link_is_recorded_not_silently_dropped(self):
        body = ("---\nname: a\ndescription: d\n---\n\n"
                "[t](./path/to/file.md) [u](../<name>/SKILL.md)\n")
        root = self._repo({"skills/a/SKILL.md": body})
        code, payload, _ = self._run(root)
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["skipped"]["placeholder_links"]), 2)

    def test_anchor_link_to_missing_heading_fails(self):
        body = ("---\nname: a\ndescription: d\n---\n\n"
                "[x](#nope)\n\n## Real\n")
        root = self._repo({"skills/a/SKILL.md": body})
        _code, payload, _ = self._run(root)
        self.assertTrue(any(f["check"] == "link.anchor_missing"
                            for f in payload["failures"]))

    def test_percent_decoded_unicode_anchor_resolves(self):
        body = ("---\nname: a\ndescription: d\n---\n\n"
                "[x](#%E4%B8%AD%E6%96%87)\n\n## 中文\n")
        root = self._repo({"skills/a/SKILL.md": body})
        code, _payload, _ = self._run(root)
        self.assertEqual(code, 0, "percent-decoded unicode anchor must resolve")

    def test_unterminated_fence_fails(self):
        body = "---\nname: a\ndescription: d\n---\n\n```py\nprint(1)\n"
        root = self._repo({"skills/a/SKILL.md": body})
        _code, payload, _ = self._run(root)
        self.assertTrue(any(f["check"] == "fence.unterminated"
                            for f in payload["failures"]))

    def test_protected_fingerprint_detects_modification(self):
        import hashlib
        body = skill_md("rust-standards", "Use when x.")
        baseline = {
            "files": {"skills/rust-standards/SKILL.md": {
                "sha256": "0" * 64, "bytes": len(body)}},
            "skills": [],
        }
        root = self._repo({"skills/rust-standards/SKILL.md": body,
                           "skills/a/SKILL.md": skill_md("a", "Use when a.")})
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp),
                                      "--protected-prefix", "skills/rust-standards/")
        fp = payload["protected_fingerprint"]
        self.assertFalse(fp["ok"])
        self.assertEqual([m["path"] for m in fp["modified"]],
                         ["skills/rust-standards/SKILL.md"])
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),
                         fp["modified"][0]["actual_sha256"])

    def test_protected_fingerprint_detects_addition_and_deletion(self):
        baseline = {"files": {"skills/rust-standards/gone.md": {"sha256": "0" * 64}},
                   "skills": []}
        root = self._repo({"skills/rust-standards/extra.md": "# extra\n",
                           "skills/a/SKILL.md": skill_md("a", "Use when a.")})
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp),
                                      "--protected-prefix", "skills/rust-standards/")
        fp = payload["protected_fingerprint"]
        self.assertEqual(fp["deleted"], ["skills/rust-standards/gone.md"])
        self.assertEqual(fp["added"], ["skills/rust-standards/extra.md"])
        self.assertFalse(fp["ok"])

    def test_protected_incoming_anchor_must_stay_valid(self):
        """Frozen rust file links into a mutable skill: that anchor must hold."""
        files = {
            "skills/rust-standards/references/14-testing.md":
                "# T\n\nSee [x](../../a/SKILL.md#%E4%B8%AD%E6%96%87)\n",
            "skills/a/SKILL.md": "---\nname: a\ndescription: d\n---\n\n# Other\n",
        }
        root = self._repo(files)
        _code, payload, _ = self._run(root, "--protected-prefix", "skills/rust-standards/")
        self.assertTrue(any(f["check"] == "protected_incoming.anchor_missing"
                            for f in payload["failures"]))

    def test_protected_incoming_link_to_deleted_skill_is_a_failure(self):
        files = {
            "skills/rust-standards/references/t.md":
                "See [x](../../a/SKILL.md#head)\n",
            "skills/other/SKILL.md": skill_md("other", "Use when o."),
        }
        root = self._repo(files)
        _code, payload, _ = self._run(root, "--protected-prefix", "skills/rust-standards/")
        self.assertTrue(any(f["check"] == "protected_incoming.target_missing"
                            for f in payload["failures"]))

    def test_dangling_deleted_skill_reference_detected(self):
        files = {
            "skills/other/SKILL.md":
                "---\nname: other\ndescription: d\n---\n\n"
                "See [old](./gone/SKILL.md) and `gone`.\n",
        }
        baseline = {"files": {}, "skills": [{"path": "skills/gone/SKILL.md",
                                             "name": "gone", "bytes": 1,
                                             "lines": 1, "tree_bytes": 1}]}
        root = self._repo(files)
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp))
        self.assertEqual(payload["metrics"]["deleted_skills"], ["skills/gone/SKILL.md"])
        self.assertTrue(any(f["check"] == "dangling_reference"
                            for f in payload["failures"]))
        hard = payload["dangling_references"]["hard"]
        self.assertTrue(any(h["kind"] == "skill_path" for h in hard), hard)

    def test_surviving_skill_is_not_reported_dangling(self):
        """`skills/live/SKILL.md` existing must silence its own name.

        Guards against matching an arbitrary `.../<name>/SKILL.md` string
        when that skill is still on disk.
        """
        files = {
            "skills/other/SKILL.md":
                "---\nname: other\ndescription: d\n---\n\nSee [live](../live/SKILL.md).\n",
            "skills/live/SKILL.md": skill_md("live", "Use when live."),
        }
        baseline = {"files": {}, "skills": [
            {"path": "skills/live/SKILL.md", "name": "live", "bytes": 1,
             "lines": 1, "tree_bytes": 1}]}
        root = self._repo(files)
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp))
        self.assertEqual(payload["metrics"]["deleted_skills"], [])
        self.assertEqual(payload["dangling_references"]["hard"], [])
        self.assertEqual(payload["dangling_references"]["review"], [])

    def test_repo_with_no_supporting_md_does_not_crash(self):
        """Regression: a repo whose only .md files are SKILL.md.

        A split `if not rec: ... continue / ... supporting_scanned += 1`
        bound the name twice and made the audit raise UnboundLocalError on
        the first supporting file it saw. Keep this test so that shape can
        never come back.
        """
        files = {"skills/a/SKILL.md": skill_md("a", "Use when a.")}
        root = self._repo(files)
        baseline = {"files": {"skills/a/SKILL.md": {"sha256": "0" * 64}},
                    "skills": []}
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        code, payload, text = self._run(root, "--baseline", str(bp))
        self.assertIn("supporting_md_scanned", payload["metrics"])
        self.assertGreaterEqual(payload["metrics"]["supporting_md_scanned"], 0)
        self.assertIsInstance(code, int)

    def test_unchanged_supporting_md_is_skipped_changed_is_checked(self):
        import hashlib
        same = "# Ref\n\n[x](#nope-not-here)\n"
        other = same
        files = {
            "skills/a/SKILL.md": skill_md("a", "Use when a."),
            "skills/a/references/kept.md": same,
            "skills/a/references/edited.md": other,
        }
        root = self._repo(files)
        baseline = {"files": {
            "skills/a/references/kept.md": {
                "sha256": hashlib.sha256(same.encode()).hexdigest(), "bytes": len(same)},
            "skills/a/references/edited.md": {"sha256": "0" * 64, "bytes": len(other)},
        }, "skills": []}
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp))
        m = payload["metrics"]
        self.assertEqual(m["supporting_md_unchanged_skipped"], 1,
                         "the byte-identical file must be skipped")
        self.assertEqual(m["supporting_md_scanned"], 1,
                         "only the changed file is link-checked")
        # the broken anchor in the skipped file is NOT reported…
        anchor_failures = [f for f in payload["failures"]
                           if f["check"] == "link.anchor_missing"
                           and "kept.md" in f["path"]]
        self.assertEqual(anchor_failures, [])
        # …but the one in the changed file IS
        self.assertTrue(any(f["check"] == "link.anchor_missing"
                            and "edited.md" in f["path"]
                            for f in payload["failures"]))

    def test_before_after_metrics_are_reported(self):
        files = {
            "skills/a/SKILL.md": "---\nname: a\ndescription: d\n---\n\n# A\n",
            "skills/b/SKILL.md": "---\nname: b\ndescription: d\n---\n\n# B\n",
            "skills/rust-standards/SKILL.md":
                "---\nname: rust-standards\ndescription: d\n---\n\n# R\n",
        }
        baseline = {"files": {}, "skills": [
            {"path": "skills/a/SKILL.md", "name": "a", "bytes": 50, "lines": 20,
             "tree_bytes": 50},
            {"path": "skills/b/SKILL.md", "name": "b", "bytes": 60, "lines": 30,
             "tree_bytes": 60},
            {"path": "skills/rust-standards/SKILL.md", "name": "rust-standards",
             "bytes": 10, "lines": 5, "tree_bytes": 10},
        ]}
        root = self._repo(files)
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp),
                                      "--protected-prefix", "skills/rust-standards/")
        m = payload["metrics"]
        self.assertEqual(m["mutable_bytes_before"], 110)
        self.assertEqual(m["mutable_lines_before"], 50)
        self.assertEqual(m["mutable_bytes_after"], m["mutable_bytes_after"])
        self.assertEqual(m["protected_skills"], 1)
        self.assertLess(m["mutable_bytes_after"], m["mutable_bytes_before"])
        self.assertGreater(m["mutable_bytes_reduction_pct"], 0)

    def test_nested_tree_metrics_count_each_file_once(self):
        bodies = {"skills/a/SKILL.md": skill_md("a", "Use when a."),
                  "skills/a/child/SKILL.md": skill_md("child", "Use when child.")}
        root = self._repo(bodies)
        baseline = {"files": {p: {"bytes": len(text.encode())}
                               for p, text in bodies.items()},
                    "skills": [{"path": p, "bytes": len(text.encode()), "tree_bytes": 9999}
                               for p, text in bodies.items()]}
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        code, payload, text = self._run(root, "--baseline", str(bp))
        self.assertEqual(code, 0, text)
        expected = sum(len(text.encode()) for text in bodies.values())
        metrics = payload["metrics"]
        self.assertEqual(metrics["mutable_tree_bytes_before"], expected)
        self.assertEqual(metrics["mutable_tree_bytes_after"], expected)
        self.assertEqual(metrics["library_tree_bytes_after"], expected)

    def test_same_length_entry_modification_uses_content_hash(self):
        import hashlib
        old = skill_md("a", "Use when aa.")
        new = skill_md("a", "Use when bb.")
        self.assertEqual(len(old.encode()), len(new.encode()))
        root = self._repo({"skills/a/SKILL.md": new})
        baseline = {"skills": [{"path": "skills/a/SKILL.md", "bytes": len(old.encode())}],
                    "files": {"skills/a/SKILL.md": {"bytes": len(old.encode()),
                              "sha256": hashlib.sha256(old.encode()).hexdigest()}}}
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        code, payload, text = self._run(root, "--baseline", str(bp))
        self.assertEqual(code, 0, text)
        self.assertEqual(payload["metrics"]["modified_skills"], ["skills/a/SKILL.md"])

    def _route_fixture(self, selected="alpha"):
        root = self._repo({"skills/alpha/SKILL.md": skill_md("alpha", "Use when alpha applies."),
                           "skills/beta/SKILL.md": skill_md("beta", "Use when beta applies.")})
        cp, rp = root / "cases.json", root / "selections.json"
        cp.write_text(json.dumps([{"id": "r1", "prompt": "alpha thing happens",
                                   "expected": "alpha"}]))
        rp.write_text(json.dumps([{"id": "r1", "selected": selected}]))
        return root, cp, rp

    def test_route_case_report_declares_it_is_not_live_measurement(self):
        root, cp, rp = self._route_fixture()
        code, payload, text = self._run(root, "--route-cases", str(cp),
                                       "--route-results", str(rp))
        self.assertEqual(code, 0, text)
        rc = payload["route_checks"]
        self.assertFalse(rc["is_live_routing_measurement"])
        self.assertIn("no model was invoked", rc["note"])
        self.assertEqual((rc["cases_total"], rc["cases_passed"]), (1, 1))

    def test_route_missing_results_cannot_pass_vacuously(self):
        root, cp, _rp = self._route_fixture()
        code, payload, _ = self._run(root, "--route-cases", str(cp))
        self.assertEqual(code, 1)
        self.assertEqual(payload["route_checks"]["cases_passed"], 0)

    def test_route_wrong_selection_fails(self):
        root, cp, rp = self._route_fixture("beta")
        code, payload, _ = self._run(root, "--route-cases", str(cp),
                                   "--route-results", str(rp))
        self.assertEqual(code, 1)
        self.assertTrue(any(f["check"] == "route_case.intent_mismatch"
                            for f in payload["failures"]))

    def test_route_duplicate_selection_ids_fail(self):
        root, cp, rp = self._route_fixture()
        rp.write_text(json.dumps([{"id": "r1", "selected": "alpha"}] * 2))
        code, _payload, _ = self._run(root, "--route-cases", str(cp),
                                    "--route-results", str(rp))
        self.assertEqual(code, 1)

    def test_route_empty_cases_fail(self):
        root, cp, rp = self._route_fixture()
        cp.write_text("[]")
        code, _payload, _ = self._run(root, "--route-cases", str(cp),
                                    "--route-results", str(rp))
        self.assertEqual(code, 1)

    def test_description_budget_does_not_require_protected_edits(self):
        root = self._repo({"skills/rust-standards/SKILL.md":
                           skill_md("rust-standards", " ".join(["word"] * 100))})
        _code, payload, _ = self._run(root, "--protected-prefix", "skills/rust-standards/")
        self.assertFalse(any(f["check"].startswith("description.")
                             for f in payload["failures"]))

    def test_protected_incoming_link_without_anchor_cannot_dangle(self):
        root = self._repo({"skills/rust-standards/references/t.md":
                           "See [x](../../a/SKILL.md)\n",
                           "skills/other/SKILL.md": skill_md("other", "Use when o.")})
        _code, payload, _ = self._run(root, "--protected-prefix", "skills/rust-standards/")
        self.assertTrue(any(f["check"] == "protected_incoming.target_missing"
                            for f in payload["failures"]))


# ---------------------------------------------------------------------------
# audit_skills: protected prefix and the vendored-reference link repair
# ---------------------------------------------------------------------------
class TestProtectedPrefixDefaults(unittest.TestCase):
    def _repo(self, files: dict[str, str]) -> Path:
        root = Path(tempfile.mkdtemp(prefix="audit-fixture-", dir=FIXTURE_ROOT))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for rel, body in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        return root

    def _run(self, root: Path, *args: str) -> tuple[int, dict, str]:
        payload_path = root / "audit.json"
        argv = ["audit_skills.py", "--repo", str(root), "--json", str(payload_path),
                *args]
        saved = sys.argv
        sys.argv = argv
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = audit.main()
        finally:
            sys.argv = saved
        payload = json.loads(payload_path.read_text()) if payload_path.exists() else {}
        return code, payload, out.getvalue()

    def test_frozen_rust_subtree_is_protected_without_a_flag(self):
        """The Rust subtree is frozen by design, so its long entry must not
        be judged against the mutable entry budget by default."""
        long_desc = " ".join(["word"] * 100)
        body = ("---\nname: rust-standards\ndescription: "
                f"{long_desc}\n---\n\n" + "\n".join(["# H"] * 200) + "\n")
        root = self._repo({"skills/rust-standards/SKILL.md": body})
        code, payload, text = self._run(root)
        self.assertEqual(code, 0, text)
        self.assertFalse(any(f["check"].startswith("entry.")
                             for f in payload["failures"]))
        self.assertFalse(any(f["check"].startswith("description.")
                             for f in payload["failures"]))

    def test_mutable_entry_outside_the_frozen_subtree_is_still_checked(self):
        """Protecting one subtree must not disable the budget elsewhere."""
        long_desc = " ".join(["word"] * 100)
        body = ("---\nname: other\ndescription: "
                f"{long_desc}\n---\n\n" + "\n".join(["# H"] * 200) + "\n")
        root = self._repo({"skills/other/SKILL.md": body})
        code, payload, text = self._run(root)
        self.assertEqual(code, 1, text)
        self.assertTrue(any(f["check"] == "entry.line_budget"
                            for f in payload["failures"]))

    def test_protected_prefix_without_baseline_compares_nothing(self):
        """Regression: with no baseline the expected file set is empty, so
        every file in the protected tree was reported as newly added."""
        root = self._repo({"skills/rust-standards/SKILL.md":
                           skill_md("rust-standards", "Use when r."),
                           "skills/rust-standards/references/t.md": "# t\n"})
        code, payload, text = self._run(root)
        self.assertEqual(code, 0, text)
        fp = payload["protected_fingerprint"]
        self.assertFalse(fp["compared"])
        self.assertEqual(fp["added"], [])
        self.assertEqual(fp["deleted"], [])
        self.assertTrue(fp["ok"])
        self.assertEqual(fp["on_disk"], 2)
        self.assertFalse(any(f["check"].startswith("protected.")
                             for f in payload["failures"]))

    def test_protected_prefix_with_baseline_still_detects_drift(self):
        """Skipping the comparison must not weaken it when a baseline exists."""
        root = self._repo({"skills/rust-standards/extra.md": "# extra\n",
                           "skills/a/SKILL.md": skill_md("a", "Use when a.")})
        baseline = {"files": {"skills/rust-standards/gone.md": {"sha256": "0" * 64}},
                    "skills": []}
        bp = root / "baseline.json"
        bp.write_text(json.dumps(baseline))
        _code, payload, _ = self._run(root, "--baseline", str(bp))
        fp = payload["protected_fingerprint"]
        self.assertTrue(fp["compared"])
        self.assertEqual(fp["deleted"], ["skills/rust-standards/gone.md"])
        self.assertEqual(fp["added"], ["skills/rust-standards/extra.md"])
        self.assertFalse(fp["ok"])


class TestRewriteReferenceLinks(unittest.TestCase):
    """The vendored copies are flat while upstream is nested, so upstream
    relative links must be re-pointed at the vendored sibling."""

    def setUp(self) -> None:
        self.mod = load_module("_rewrite_under_test", "rewrite_reference_links.py")

    def _mapping(self, tmp: Path) -> Path:
        p = tmp / "mapping"
        p.write_text(
            "skills/euv/references/css-vars.md\t\tsrc/euv/macros/css-vars.md\n"
            "skills/hyperlane/references/hyperlane-broadcast.md\t"
            "src/hyperlane-broadcast/README.md\n",
            encoding="utf-8")
        return p

    def test_vendored_sibling_is_used_when_the_page_is_mapped(self):
        mapping = {"src/euv/macros/css-vars.md":
                   ["skills/euv/references/css-vars.md"]}
        got = self.mod.rewrite_target(
            "../macros/css-vars.md", "src/euv/macros/class.md", mapping,
            "skills/euv/references/class.md", "https://ltpp.vip")
        self.assertEqual(got, "css-vars.md")

    def test_unmapped_page_falls_back_to_its_published_url(self):
        mapping = {"src/euv/macros/css-vars.md":
                   ["skills/euv/references/css-vars.md"]}
        got = self.mod.rewrite_target(
            "../ui/hooks.md", "src/euv/usage-introduction/event.md", mapping,
            "skills/euv/references/event.md", "https://ltpp.vip")
        self.assertEqual(got, "https://ltpp.vip/zh/euv/ui/hooks.html")

    def test_current_upstream_layout_keeps_its_locale(self):
        """Upstream moved from `src/<area>/<page>.md` to
        `docs/<locale>/<area>/<page>.md`; the published URL must not carry
        the layout prefix twice."""
        got = self.mod.site_url("docs/zh/euv/macros/class/class.md",
                                "https://ltpp.vip")
        self.assertEqual(got, "https://ltpp.vip/zh/euv/macros/class/class.html")

    def test_older_upstream_layout_still_resolves(self):
        got = self.mod.site_url("src/euv/usage-introduction/event.md",
                                "https://ltpp.vip")
        self.assertEqual(got, "https://ltpp.vip/zh/euv/usage-introduction/event.html")

    def test_anchor_is_preserved_across_the_rewrite(self):
        mapping = {"src/euv/macros/css-vars.md":
                   ["skills/euv/references/css-vars.md"]}
        got = self.mod.rewrite_target(
            "../macros/css-vars.md#top", "src/euv/macros/class.md", mapping,
            "skills/euv/references/class.md", "https://ltpp.vip")
        self.assertEqual(got, "css-vars.md#top")

    def test_rewriting_twice_changes_nothing(self):
        """The rewriter must be idempotent: a link it already re-pointed at
        a vendored sibling must not be resolved against the upstream tree
        again on the next run."""
        mapping = {"src/euv/macros/computed.md":
                   ["skills/euv/references/computed.md"]}
        once = self.mod.rewrite_target(
            "../macros/computed.md", "src/euv/usage-introduction/reactive.md",
            mapping, "skills/euv/references/reactive.md", "https://ltpp.vip")
        self.assertEqual(once, "computed.md")
        twice = self.mod.rewrite_target(
            once, "src/euv/usage-introduction/reactive.md",
            mapping, "skills/euv/references/reactive.md", "https://ltpp.vip")
        self.assertEqual(twice, once)

    def test_absolute_and_fragment_links_are_left_alone(self):
        mapping = {}
        for target in ("https://example.com/a", "mailto:a@b.c", "#anchor",
                       "/absolute/path"):
            got = self.mod.rewrite_target(
                target, "src/euv/macros/class.md", mapping,
                "skills/euv/references/class.md", "https://ltpp.vip")
            self.assertEqual(got, target)

    def test_link_into_another_skill_keeps_that_skills_copy(self):
        mapping = {"src/hyperlane-broadcast/README.md":
                   ["skills/hyperlane/references/hyperlane-broadcast.md"]}
        got = self.mod.rewrite_target(
            "../../hyperlane-broadcast/README.md",
            "src/hyperlane/usage-introduction/websocket.md", mapping,
            "skills/hyperlane/references/websocket.md", "https://ltpp.vip")
        self.assertEqual(got, "hyperlane-broadcast.md")

    def test_source_vendored_into_two_skills_keeps_the_local_one(self):
        """A page vendored into two skills must link to the copy in the
        skill the reader is already in."""
        mapping = {"src/hyperlane/usage-introduction/websocket.md":
                   ["skills/euv/references/websocket.md",
                    "skills/hyperlane/references/websocket.md"]}
        got = self.mod.rewrite_target(
            "websocket.md", "src/hyperlane/usage-introduction/websocket.md",
            mapping, "skills/hyperlane/references/websocket.md", "https://ltpp.vip")
        self.assertEqual(got, "websocket.md")

    def test_mapping_parser_ignores_comments_and_blank_columns(self):
        with tempfile.TemporaryDirectory(prefix="relink-", dir=FIXTURE_ROOT) as td:
            p = Path(td) / "mapping"
            p.write_text(
                "# a comment\n"
                "\n"
                "skills/euv/references/a.md\t\tsrc/euv/macros/a.md\n"
                "skills/euv/references/b.md\t\tsrc/euv/macros/b.md\t"
                "# manual override: note\n",
                encoding="utf-8")
            parsed = self.mod.load_mapping(p)
            self.assertEqual(sorted(parsed), ["src/euv/macros/a.md",
                                              "src/euv/macros/b.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
