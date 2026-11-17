#!/usr/bin/env python3
"""Regression-test parser build-directory selection without executing fixture binaries."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('verify_fn_body_blank_lines.py')
spec = importlib.util.spec_from_file_location('parser_cache_subject', SCRIPT)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class ParserBuildCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.target = self.home / 'compiler-output'
        subject.parser_binary.cache_clear()
        self.addCleanup(subject.parser_binary.cache_clear)

    def invoke(self, *, fork=False, metadata_failure=False, missing_output=False):
        calls = []

        def run(command, **options):
            calls.append(command)
            self.assertIn('CARGO_TARGET_DIR', options['env'])
            if command[1] == 'metadata':
                if metadata_failure:
                    return subprocess.CompletedProcess(command, 2, '', 'metadata fixture failure')
                record = {'target_directory': str(self.target)}
                if fork:
                    record['build_directory'] = str(self.home / 'intermediates')
                return subprocess.CompletedProcess(command, 0, json.dumps(record), '')
            self.assertEqual(command[1], 'build')
            if not missing_output:
                binary = self.target / 'debug/rust-standards-parser'
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b'unit-test fixture; never executed')
            return subprocess.CompletedProcess(command, 0, '', '')

        with patch.object(subject.Path, 'home', return_value=self.home), \
                patch.object(subject.subprocess, 'run', side_effect=run):
            result = subject.parser_binary()
        self.assertEqual(result, self.target / 'debug/rust-standards-parser')
        self.assertTrue(result.is_file())
        self.assertEqual([command[1] for command in calls], ['metadata', 'build'])

    def test_standard_target_directory(self):
        self.invoke()

    def test_intermediate_build_directory_is_not_an_executable_directory(self):
        self.invoke(fork=True)

    def test_metadata_failure_is_closed(self):
        with self.assertRaises(RuntimeError):
            self.invoke(metadata_failure=True)

    def test_success_without_binary_is_closed(self):
        with self.assertRaises(RuntimeError):
            self.invoke(missing_output=True)


if __name__ == '__main__':
    unittest.main()
