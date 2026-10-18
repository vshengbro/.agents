# Network, API and source-repository fallbacks

## Read transport failures before changing credentials

1. Test the exact endpoint with bounded timeouts and visible HTTP status.
2. Distinguish DNS/TLS/proxy failures, throttling and permission errors. A working
   REST endpoint does not prove SSH or smart-HTTP works, and the reverse is true.
3. Use an authorized existing transport. If changing a remote is necessary,
   record the old value, confirm the intended repository, and disclose the change.
   Do not route private code or credentials through untrusted public mirrors.

A bounded archive fetch is useful for **reading** source without Git history:

```bash
curl --fail --location --retry 3 --connect-timeout 15 --max-time 180 \
  -o <owned-scratch>/repo.tar.gz \
  'https://codeload.github.com/<owner>/<repo>/tar.gz/<exact-commit-sha>'
tar -tzf <owned-scratch>/repo.tar.gz
```

Check the archive command's exit status, not just its entry count. Extract only
into a new owned directory, inspect paths before extraction, and identify the
exact revision. Say "downloaded/extracted", not "cloned". To contribute changes,
use a real repository and preserve/compare the base tree before committing;
`git init` over an archive does not reconstruct its history.

## Read through the Contents API

```bash
gh api 'repos/<owner>/<repo>/contents/<path>?ref=<exact-sha>' --jq .content | base64 -d
```

Confirm encoding/type and response status before decoding; directories, large
files and submodules need their appropriate API route. A failed read is not an
empty file. Never place tokens in URLs or command logs.

An API file write is still a repository mutation: it requires the same user
scope, English commit text, personal identity and applicable validation. Do not
use Contents/Git Data API writes to escape mandatory local hooks. If a required
validated checkout cannot be obtained, report the blocker instead of silently
substituting an unchecked remote commit. After any authorized API mutation,
read the exact branch ref and file blobs back.

## Build output is not necessarily source

Inspect the target's root files, deployment workflow and commit history. Generated
HTML/assets plus deploy commits suggest an output repository, but absence of a
build manifest alone is not proof: a hand-maintained static site may be source.
Resolve the actual source from deployment configuration; do not guess a private
sibling repo from its name. Fix verified source and let its normal deploy run.
A direct output hotfix needs explicit authorization and a source-side follow-up,
otherwise the next deploy can erase it.

Remove owned archives, extraction/worktree directories and temporary processes
after use; retain only requested evidence or deliverables. Never prune shared
caches or delete another task's checkout to recover disk space.
