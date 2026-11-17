#!/usr/bin/env python3
"""Real Git object/index regressions for manifest symlink context."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(os.environ.get("DEP_ORDER_HELPER", Path(__file__).resolve().parents[1] / "dep_order_check.py"))
SCRIPTS = Path.home() / ".agents/skills/rust-standards/scripts"
GOOD = '[package]\nname = "app"\nversion = "0.1.0"\n\n[dependencies]\nshared = { workspace = true }\n\nserde = { workspace = true }\n'
BAD = GOOD.replace('shared = { workspace = true }\n\nserde = { workspace = true }', 'serde = { workspace = true }\n\nshared = { workspace = true }')
WORKSPACE = '[workspace]\nmembers = ["app", "shared"]\n\n[workspace.dependencies]\nshared = { path = "shared" }\n\nserde = "1"\n'


class ManifestLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dep-links-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.git("init", "--initial-branch=master")
        self.write("Cargo.toml", WORKSPACE)
        self.write("shared/Cargo.toml", '[package]\nname = "shared"\nversion = "0.1.0"\n')
        self.write("storage/deep/manifest.data", GOOD)
        self.link("storage/hop", "deep/../deep/manifest.data")
        self.link("app/Cargo.toml", "../storage/hop")
        self.git("add", ".")

    def git(self, *args, input=None, check=True):
        result = subprocess.run(["git", *args], cwd=self.root, env=self.env, input=input,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def link(self, path, target):
        link = self.root / path
        link.parent.mkdir(parents=True, exist_ok=True)
        link.unlink(missing_ok=True)
        link.symlink_to(target)

    def baseline(self):
        tree = self.git("write-tree")
        commit = self.git("commit-tree", tree, input="test: baseline Git object context\n")
        self.git("update-ref", "HEAD", commit)

    def check(self, code):
        index = (self.root / ".git/index").read_bytes()
        result = subprocess.run(["python3", str(HELPER), str(self.root), str(SCRIPTS)],
                                cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertEqual((self.root / ".git/index").read_bytes(), index)
        if code == 2:
            self.assertIn("dep-order gate error:", result.stderr)
        return result

    def test_initial_chain_non_cargo_target_and_workspace_inheritance(self):
        self.check(0)

    def test_initial_bad_inherited_order_is_blocked(self):
        self.write("storage/deep/manifest.data", BAD)
        self.git("add", ".")
        self.check(1)

    def test_clean_index_ignores_unstaged_target_and_link_poison(self):
        self.write("storage/deep/manifest.data", BAD)
        self.link("app/Cargo.toml", "/does/not/exist")
        self.write("Cargo.toml", '[workspace]\nmembers = []\n')
        self.check(0)

    def test_unstaged_target_repair_cannot_hide_staged_bad_manifest(self):
        self.write("storage/deep/manifest.data", BAD)
        self.git("add", ".")
        self.write("storage/deep/manifest.data", GOOD)
        self.check(1)

    def test_head_and_index_resolve_independently(self):
        self.baseline()
        self.write("storage/replacement", BAD)
        self.link("app/Cargo.toml", "../storage/replacement")
        self.git("add", ".")
        self.write("storage/replacement", GOOD)
        self.check(1)

    def test_unchanged_head_debt_does_not_become_new_violation(self):
        self.write("storage/deep/manifest.data", BAD)
        self.git("add", ".")
        self.baseline()
        self.link("app/Cargo.toml", "../storage/deep/manifest.data")
        self.git("add", "app/Cargo.toml")
        self.check(0)

    def test_renamed_manifest_keeps_logical_workspace_context(self):
        self.baseline()
        self.git("mv", "app/Cargo.toml", "app/Previous.toml")
        self.link("app/Cargo.toml", "Previous.toml")
        self.git("add", "app/Cargo.toml")
        self.check(0)

    def test_directory_link_in_chain(self):
        self.link("storage/alias", "deep")
        self.link("app/Cargo.toml", "../storage/alias/../deep/manifest.data")
        self.git("add", ".")
        self.check(0)

    def test_unsafe_links_fail_closed(self):
        for target in ("/etc/passwd", "../../outside", "../.git/config", "../.GiT/config", "../missing", "../storage/hop/child"):
            with self.subTest(target=target):
                self.link("app/Cargo.toml", target)
                self.git("add", "app/Cargo.toml")
                self.check(2)

    def test_external_file_is_never_read(self):
        self.write("outside", GOOD)
        self.link("app/Cargo.toml", str(self.root / "outside"))
        self.git("add", "app/Cargo.toml")
        self.check(2)

    def test_cycle_fails_closed(self):
        self.link("storage/hop", "../app/Cargo.toml")
        self.git("add", "storage/hop")
        self.check(2)

    def test_bad_head_link_cannot_be_hidden_by_good_index(self):
        self.link("app/Cargo.toml", "../missing")
        self.git("add", "app/Cargo.toml")
        self.baseline()
        self.link("app/Cargo.toml", "../storage/hop")
        self.git("add", "app/Cargo.toml")
        self.check(2)

    def test_unmerged_non_manifest_target_fails_closed(self):
        path = "storage/deep/manifest.data"
        oid = self.git("rev-parse", ":" + path)
        self.git("update-index", "--force-remove", path)
        self.git("update-index", "--index-info", input=f"100644 {oid} 1\t{path}\n100644 {oid} 2\t{path}\n100644 {oid} 3\t{path}\n")
        self.check(2)

    def test_missing_object_fails_closed(self):
        self.git("update-index", "--cacheinfo", "100644," + "1" * 40 + ",storage/deep/manifest.data")
        self.check(2)

    def test_non_blob_object_fails_closed(self):
        tree = self.git("write-tree")
        self.git("update-index", "--cacheinfo", f"100644,{tree},storage/deep/manifest.data")
        self.check(2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
