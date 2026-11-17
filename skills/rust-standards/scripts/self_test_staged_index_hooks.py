#!/usr/bin/env python3
"""Exercise installed Git hook callers in a disposable clone; never commit."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile

SOURCE = Path(os.environ.get('STAGED_HOOK_FIXTURE_SOURCE', str(Path.home() / 'code/euv')))
SCRATCH = Path.home() / '.hermes/cache/scratch'
SCRATCH.mkdir(parents=True, exist_ok=True)
ROOT = Path(tempfile.mkdtemp(prefix='staged-hook-regression-', dir=SCRATCH))
REPO = ROOT / 'fixture'
INSTALLED = Path.home() / '.git-hooks'
HOOKS = INSTALLED if '--installed' in sys.argv else ROOT / 'hooks'
if HOOKS != INSTALLED:
    shutil.copytree(INSTALLED, HOOKS)
    shutil.copytree(Path.home() / '.agents/skills/rust-standards/scripts', ROOT / 'scripts',
                    ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['pre-commit', 'prepare-commit-msg']:
        path = HOOKS / name
        path.write_text(path.read_text().replace('"$HOME/.agents/skills/rust-standards/scripts"',
                        f'"{ROOT}/scripts"').replace('"$HOME/.hermes/skills/rust-standards/scripts"',
                        f'"{ROOT}/absent"'))
subprocess.run(['git', 'clone', '--local', '--no-hardlinks', '--quiet', str(SOURCE), str(REPO)], check=True)
subprocess.run(['git', '-C', str(REPO), 'remote', 'set-url', 'origin', 'git@github.com:euv-dev/euv.git'], check=True)
print(f'Evidence directory: {ROOT}', flush=True)
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'STAGED_FILE_GATE_JOBS': '1', 'TMPDIR': str(SCRATCH)}
RESULTS = []
GUARD = Path.home() / '.agents/skills/git-standards/scripts/guard_no_verify.py'
ownership = subprocess.run([sys.executable, str(GUARD), '--repo', str(REPO)],
                           env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(ROOT / 'ownership.json').write_text(json.dumps(dict(returncode=ownership.returncode,
    stdout=ownership.stdout.decode(), stderr=ownership.stderr.decode()), indent=2))
if ownership.returncode != 0 or 'VERDICT: ENFORCED' not in ownership.stdout.decode():
    raise RuntimeError('fixture ownership must resolve live to ENFORCED')


def git(*args, **kwargs):
    return subprocess.run(['git', '-C', str(REPO), *args], env=ENV, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs).stdout


def reset(initial=False):
    git('symbolic-ref', 'HEAD', 'refs/heads/master')
    git('reset', '--hard', 'refs/remotes/origin/master')
    git('clean', '-fdx')
    if initial:
        git('symbolic-ref', 'HEAD', 'refs/heads/hook-unborn')
        git('read-tree', '--empty')
    git('config', 'core.hooksPath', str(HOOKS))


def write(path, text, stage=False):
    p = REPO / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    if stage:
        git('add', '--', path)


def worktree_fingerprint():
    digest = hashlib.sha256()
    for directory, subdirs, files in os.walk(REPO):
        subdirs[:] = sorted(name for name in subdirs if name != '.git')
        for name in sorted(subdirs + files):
            path = Path(directory) / name
            digest.update(os.fsencode(path.relative_to(REPO)))
            digest.update(str(path.lstat().st_mode).encode())
            if path.is_symlink():
                digest.update(os.fsencode(os.readlink(path)))
            elif path.is_file():
                digest.update(path.read_bytes())
    return digest.hexdigest()


def run(label, blocked):
    for hook in ['pre-commit', 'prepare-commit-msg']:
        command = ['git', '-C', str(REPO), 'hook', 'run', hook]
        if hook == 'prepare-commit-msg':
            command += ['--', str(ROOT / 'COMMIT_EDITMSG')]
        index_before = (REPO / '.git/index').read_bytes()
        worktree_before = worktree_fingerprint()
        result = subprocess.run(command, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        index_unchanged = (REPO / '.git/index').read_bytes() == index_before
        worktree_unchanged = worktree_fingerprint() == worktree_before
        log = ROOT / f'{len(RESULTS):03d}-{label}-{hook}.log'
        log.write_bytes(result.stdout)
        passed = (result.returncode != 0) == blocked and index_unchanged and worktree_unchanged
        RESULTS.append(dict(case=label, hook=hook, expected_block=blocked, index_unchanged=index_unchanged,
                            worktree_unchanged=worktree_unchanged,
                            returncode=result.returncode, passed=passed, log=str(log)))
        print(label, hook, result.returncode, 'PASS' if passed else 'FAIL', flush=True)
    (ROOT / 'results.json').write_text(json.dumps(RESULTS, indent=2))


GOOD = '[package]\nname = "fixture"\nversion = "0.1.0"\n'
BAD = GOOD + '# prohibited comment\n'
(RootMsg := ROOT / 'COMMIT_EDITMSG').write_text('test(hooks): verify staged snapshots\n')
for extension, good, bad in [('toml', GOOD, BAD), ('rs', '', '#[allow(dead_code)]\nfn sample() {}\n')]:
    path = 'hook fixture/Cargo.toml' if extension == 'toml' else 'hook fixture/src/fn.rs'
    for a in [True, False]:
        reset()
        write('hook fixture/Cargo.toml', GOOD, True)
        write(path, bad if a else good, True)
        write(path, good if a else bad)
        run(f'{extension}-' + ('A-bad-index' if a else 'B-good-index'), a)
reset()
write('hook fixture/Cargo.toml', GOOD, True)
write('hook fixture/src/fn.rs', '/// Execute the fixture.\n#[inline]\nfn sample() {}\n', True)
write('hook fixture/Cargo.toml', GOOD + '[lib]\ncrate-type = ["cdylib"]\n', True)
write('hook fixture/Cargo.toml', GOOD)
run('staged-wasm-context', True)
reset()
write('hook fixture/Cargo.toml', GOOD, True)
write('hook fixture/src/fn.rs', '/// Execute the fixture.\n#[inline]\nfn sample() {}\n', True)
write('hook fixture/Cargo.toml', GOOD + '[lib]\ncrate-type = ["cdylib"]\n')
run('unstaged-wasm-context', False)
reset()
write('hook fixture/Cargo.toml', GOOD, True)
write('hook fixture/src/fn.rs', '', True)
write('hook fixture/src/unstaged/sub/fn.rs', '')
run('unstaged-directory-context', False)
for bad in [False, True]:
    reset(True)
    write('Cargo.toml', BAD if bad else GOOD, True)
    run('initial-' + ('bad' if bad else 'good'), bad)
reset()
git('rm', '--', 'Cargo.toml')
run('delete', False)
reset()
git('mv', '--', 'Cargo.toml', 'renamed Cargo.toml')
run('rename-space', False)
reset()
write('hook fixture/Cargo.toml', GOOD + '\n[dependencies]\nzebra = "1"\nalpha = "1"\n', True)
run('dependency-order-bad', True)
reset()
write('hook fixture/Cargo.toml', GOOD + '\n[dependencies]\nalpha = "1"\nzebra = "1"\n', True)
run('dependency-order-good', False)
# Damage only an isolated helper copy; the real verifier is never removed.
for bad in [False, True]:
    reset()
    write('frontend/Cargo.toml', '[workspace]\nmembers = ["app", "shared"]\n\n[workspace.dependencies]\nshared = { path = "shared" }\n\nserde = "1"\n', True)
    write('frontend/shared/Cargo.toml', '[package]\nname = "shared"\nversion = "0.1.0"\n', True)
    dependencies = 'shared = { workspace = true }\n\nserde = { workspace = true }\n'
    if bad:
        dependencies = 'serde = { workspace = true }\n\nshared = { workspace = true }\n'
    write('frontend/app/Cargo.toml', '[package]\nname = "frontend-app"\nversion = "0.1.0"\n\n[dependencies]\n' + dependencies, True)
    write('frontend/Cargo.toml', '[workspace]\nmembers = ["app"]\n')
    write('frontend/shared/Cargo.toml', '[package]\nname = "renamed"\nversion = "0.1.0"\n')
    run('inherited-context-' + ('bad' if bad else 'good'), bad)
reset()
p = REPO / 'engine/src/lib.rs'
write('engine/src/lib.rs', p.read_text() + '\n', True)
run('unchanged-legacy-debt', False)
reset()
write('hook fixture/Cargo.toml', GOOD, True)
write('hook fixture/src/fn.rs', '', True)
(REPO / 'hook fixture/Cargo.toml').unlink()
(REPO / 'hook fixture/src/fn.rs').unlink()
run('index-files-missing-worktree', False)
# Internal links are context, not an exemption from the complete-tree audit.
def link(path, target):
    p = REPO / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.symlink_to(target)
    git('add', '--', path)


for case in ['internal-readme', 'chain-relative-readme', 'chain-relative-cargo', 'external', 'absolute', 'broken', 'cyclic', 'git-metadata']:
    reset()
    write('hook fixture/Cargo.toml', GOOD, True)
    write('hook fixture/src/fn.rs', '', True)
    write('link-context/README.md', 'Staged context.\n', True)
    if case == 'internal-readme':
        link('README-link.md', 'link-context/README.md')
        write('link-context/README.md', 'Unstaged context must not be copied.\n')
    elif case == 'chain-relative-readme':
        link('link-context/second-link.md', '../link-context/README.md')
        link('README-link.md', 'link-context/second-link.md')
    elif case == 'chain-relative-cargo':
        (REPO / 'hook fixture/Cargo.toml').unlink()
        write('link-context/package.toml', GOOD, True)
        link('link-context/manifest.toml', 'package.toml')
        link('hook fixture/Cargo.toml', '../link-context/manifest.toml')
    elif case == 'external':
        link('README-link.md', '../outside.md')
    elif case == 'absolute':
        link('README-link.md', str(REPO / 'link-context/README.md'))
    elif case == 'broken':
        link('README-link.md', 'missing.md')
    elif case == 'cyclic':
        link('README-link.md', 'second-link.md')
        link('second-link.md', 'README-link.md')
    else:
        link('README-link.md', '.git/config')
    run('symlink-' + case, case not in ['internal-readme', 'chain-relative-readme', 'chain-relative-cargo'])

# Prove a relative Cargo chain actually supplies staged verifier context.
reset()
write('hook fixture/src/fn.rs', '/// Execute the fixture.\n#[inline]\nfn sample() {}\n', True)
write('link-context/package.toml', GOOD + '[lib]\ncrate-type = ["cdylib"]\n', True)
link('link-context/manifest.toml', 'package.toml')
link('hook fixture/Cargo.toml', '../link-context/manifest.toml')
write('link-context/package.toml', GOOD)
run('symlink-staged-wasm-context', True)

# Inspect real snapshot Git metadata and the actual ignored-file collector.
reset()
write('.gitignore', (REPO / '.gitignore').read_text() + '\ntracked-ignored.rs\n', True)
write('tracked-ignored.rs', '')
git('add', '-f', '--', 'tracked-ignored.rs')
write('link-context/README.md', 'Staged context.\n', True)
write('link-context/tool', '#!/bin/sh\nexit 0\n', True)
git('update-index', '--chmod=+x', '--', 'link-context/tool')
link('README-link.md', 'link-context/README.md')
write('link-context/README.md', 'Unstaged context must not be copied.\n')
scripts = Path(__file__).resolve().parent if HOOKS == INSTALLED else ROOT / 'scripts'
spec = importlib.util.spec_from_file_location('snapshot_gate_fixture', scripts / 'staged_file_gate.py')
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
collector = gate.load_verifier(scripts, 'verify_doc_comment_format')
source_tree = git('write-tree').decode().strip()
index_before = (REPO / '.git/index').read_bytes()
worktree_before = worktree_fingerprint()
head_before = git('rev-parse', 'HEAD')
metadata = []
for label, tree in [('head', head_before.decode().strip()), ('index', source_tree)]:
    destination = ROOT / ('metadata-' + label)
    gate.materialise(REPO, tree, destination)
    expected = {relative: (mode.decode(), oid.decode()) for relative, mode, kind, oid in gate.entries(REPO, tree)}
    actual = {}
    for record in gate.git(destination, 'ls-files', '--stage', '-z').split(b'\0'):
        if record:
            header, relative = record.split(b'\t', 1)
            mode, oid, stage = header.split()
            assert stage == b'0'
            actual[os.fsdecode(relative)] = (mode.decode(), oid.decode())
    assert actual == expected, 'snapshot index must match the entire source tree'
    assert gate.git(destination, 'rev-parse', 'HEAD') == head_before
    assert not any(path.is_symlink() for path in (destination / '.git').rglob('*'))
    proof = dict(snapshot=label, tree=tree, tracked_count=len(actual), exact_index=True)
    if label == 'index':
        ignored = subprocess.run(['git', '-C', str(destination), 'check-ignore', 'tracked-ignored.rs'],
                                 env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        collected = [str(path.relative_to(destination)) for path in collector._list_rs_files(destination)]
        assert ignored.returncode == 1 and not ignored.stdout
        assert 'tracked-ignored.rs' in collected
        assert (destination / 'README-link.md').read_text() == 'Staged context.\n'
        assert (destination / 'link-context/tool').stat().st_mode & 0o777 == 0o755
        assert (destination / 'link-context/README.md').stat().st_mode & 0o777 == 0o644
        proof.update(check_ignore_exit=ignored.returncode, tracked_ignored_collected=True,
                     staged_link_content=True, executable_mode=True, ordinary_mode=True)
    metadata.append(proof)
assert (REPO / '.git/index').read_bytes() == index_before
assert worktree_fingerprint() == worktree_before
assert git('rev-parse', 'HEAD') == head_before
(ROOT / 'snapshot-metadata.json').write_text(json.dumps(dict(snapshots=metadata,
    index_unchanged=True, worktree_unchanged=True, head_unchanged=True), indent=2))
print('snapshot-metadata-and-collector PASS', flush=True)

if HOOKS == ROOT / 'hooks':
    reset()
    write('hook fixture/Cargo.toml', GOOD, True)
    helper = ROOT / 'scripts/verify_doc_comment_format.py'
    original = helper.read_bytes()
    helper.unlink()
    try:
        run('missing-verifier', True)
    finally:
        helper.write_bytes(original)
    try:
        helper.write_text('raise RuntimeError("fixture import exception")\n')
        run('import-exception', True)
        helper.write_text('def audit_one(path):\n    raise RuntimeError("fixture audit exception")\n')
        write('hook fixture/src/fn.rs', '', True)
        run('audit-exception', True)
        helper.write_text('VALUE = 1\n')
        run('missing-audit-entrypoint', True)
        helper.write_text('raise SystemExit(0)\n')
        run('import-system-exit-zero', True)
        helper.write_text('def audit_one(path):\n    raise SystemExit(0)\n')
        run('audit-system-exit-zero', True)
    finally:
        helper.write_bytes(original)
    dep = HOOKS / 'dep_order_check.py'
    dep.rename(HOOKS / 'dep_order_check.saved')
    try:
        run('missing-dependency-helper', True)
    finally:
        (HOOKS / 'dep_order_check.saved').rename(dep)
print(json.dumps({'total': len(RESULTS), 'passed': sum(x['passed'] for x in RESULTS)}, indent=2))
sys.exit(0 if all(x['passed'] for x in RESULTS) else 1)
