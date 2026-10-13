---
name: filesystem-destructive-operation-safety
description: Use when deleting or sweeping files on a live machine.
license: MIT
metadata:
  version: "1.0.0"
  author: curator
  category: devops
  audience: agent-runtime
  hermes:
    tags:
      - filesystem
      - cleanup
      - safety
    related_skills:
      - agent-runtime-disk-hygiene
---

# Destructive Filesystem Operation Safety

## When to use

Load this before any `rm -rf`, purge, prune, sweep, or "clean up my disk" on a
machine that is running: deleting scratch or build artifacts, clearing a tmp
directory, removing caches, or reclaiming space. Also load it before telling a
user a path is safe — or unsafe — to delete.

Applies to any `rm -rf` / sweep / prune on a machine that is *live* — running
processes, active config, and remote state all still depend on the filesystem.
The failure mode is not a crash; it is deleting something load-bearing and
discovering it weeks later, with no error at delete time.

## Core rule: never let the filesystem's appearance decide what's disposable

A path's name, location, or an empty-looking sibling directory proves nothing
about whether it is safe to delete. **Same filename ≠ same file**, and an
official directory reading `0B` does not mean the resource is unused — on
macOS, simulator runtime volumes read `0B` while the real runtime is mounted
read-only from a cryptex disk image elsewhere.

Resolve identity from **the tool that manages the resource**, then confirm by
exercising the resource:

```bash
# 1. Ask the managing tool where the real thing lives. JSON is authoritative.
xcrun simctl runtime list -j        # .path / .mountPath / .parentMountPath
docker image inspect <img> --format '{{.GraphDriver.Dir}}'

# 2. Compare device+inode. Different ino = different file, whatever the names.
stat -f "dev=%d ino=%i  %N" <a> <b>    # macOS
stat -c "dev=%d ino=%i  %n" <a> <b>    # Linux

# 3. Find what actually backs a mount.
hdiutil info | grep -i image-path      # macOS
mount | grep -i <subsystem>            # Linux

# 4. Verify functionally: boot the device, pull the image, run the build.
```

## "Only copy" claims must be earned, not inferred

Before telling a user *"this is the only copy — don't delete it"* (or the
inverse), resolve the path from the managing tool's inventory and confirm the
deletion or retention functionally. Asserting a data-loss outcome from a path
name stalls a cheap reversible delete; asserting safety from a path name
destroys something unique. When the evidence changes, correct it plainly and
name the check that settled it — do not quietly proceed.

## Protect-list: build it from evidence, not from names

Before any sweep, derive what must survive:

```bash
# Live config pointing into the target area — makes an inert-looking file
# (a log, a token) into a hard dependency.
git config --get-all credential.helper    # -> "store --file=/tmp/.../git-cred"
grep -rl "<path>" ~/Library/Preferences /Library/Preferences /etc 2>/dev/null

# Processes holding files open — including your own agent runtime.
lsof 2>/dev/null | grep -F "<path>" | awk '{print $1, $2, $NF}' | sort -u
ps -p <pids> -o pid,comm
```

Deleting a config-referenced path breaks auth/tooling **silently** — no error
at delete time. When you find one, report it as a keep, not as reclaimed space.

## Reversibility triage for each candidate

| Candidate | Safe to delete when |
|---|---|
| Build cache (`target/`, `CACHEDIR.TAG`) | no build tool running *and none hung* (`pgrep -fl 'cargo\|rustc'`) — see below |
| Bare git clone | `git log @{u}..HEAD` **and** `git status --porcelain` empty for *every* clone, and a remote is configured |
| Reproduce/fetcher profile | prefix allowlist only, never a bare `*` |
| Socket / lockfile owned by root | skip — it is a live IPC endpoint |
| Same-named copy outside the managed area | inode differs from the managed path **and** the managed path is confirmed live |

Check *every* clone, not a sample — a single unpushed repo is silent data loss
once the working clone is gone.

## A running build tool is not the same as a hung build tool

A long-elapsed build process is ambiguous evidence: it may be a legitimate
multi-hour compile or a deadlock that will never finish. Wall time cannot
separate them — cumulative CPU time can. A process whose `TIME` is near zero
against a large `ELAPSED` is hung, and that is a finding to report with the
number, not an adjective.

```bash
ps -p <pid> -o pid,etime,state,time,%cpu,command
```

Clear the hung one during a cleanup pass for two reasons: it holds the cache
directory's lock, so the cache reads as "in use" and blocks both reclamation
and the next build, and it has been consuming a build slot for the whole
period. Kill the whole process *tree* — a `sh -c 'build | grep | head'` wrapper
is several processes, and killing only the driver leaves the pipeline tail
alive holding the same descriptors, so the next check still shows a build.

```bash
ps -Ao pid,ppid,etime,command | awk '$1==<parent> || $2==<parent>'   # enumerate first
kill -TERM <deepest> <driver> <wrapper>; sleep 2; kill -KILL <same set>
pgrep -fl 'cargo|rustc' || echo "clear"    # confirm, do not assume

## Before deleting a dir other tooling references

Grep the referencing tools for `mkdir -p` on that path. A script that creates
its own working directory survives the deletion; one that assumes it exists
does not. This is often the difference between "breaks the workflow" and
"fully regenerable".

## App-residue sweeps: an absent `.app` is not an uninstall

When a user asks to clear "leftovers from X" — or, as the request usually
expands, leftovers from X *and any other program* — three failures recur. Each
has a cheap check that settles it before anything is deleted.

**An app missing from `/Applications` is still installed.** macOS installs
several classes of program outside that directory. A 518 MB input method at
`/Library/Input Methods/<Name>.app` reads as "already gone" if the scan only
lists `/Applications`, so the "residue" gets reported as kilobytes while the
real payload is untouched. Before calling anything uninstalled, check every
other install root:

```bash
ls -d /Library/Input\ Methods/*.app /Library/PrivilegedHelperTools/* \
      "/Library/Application Support"/* ~/Library/Input\ Methods/*.app 2>/dev/null
sfltool dumpbtm 2>/dev/null | grep -i -B2 -A6 "<vendor>"   # background items
```

`sfltool dumpbtm` is the authoritative inventory of registered background
items; `launchctl list` shows loaded jobs only and misses the rest.

**Prove the successor does not depend on the orphan's helper.** A vendor ships
several products sharing a prefix (one app's helper, another's stale copy).
The names alone will not decide it — resolve non-dependence by scanning the
surviving app's binary for the orphan's identifier:

```bash
strings "/Applications/<Survivor>.app/Contents/MacOS/<survivor>" \
  | grep -i -E "<orphan-helper-id>|<orphan-label>" | sort -u
```

Empty output is the evidence that the orphan is safe. Non-empty means stop —
you have just found a live dependency.

**Recency and lock files prove liveness when nothing else does.** A tool with no
`.app` and no `PATH` entry is not a residue candidate; state directories carry
their own liveness proof:

```bash
cat "<state-dir>/*_install.lock.pid" 2>/dev/null | xargs -I{} ps -p {} -o pid,etime,command
stat -f "%Sm %N" -t "%F %H:%M" "<state-dir>"          # mtime today = used today
```

A dead PID is not the same as a dead tool — the state dir's mtime is the
stronger signal, because a scheduled or on-demand invocation rewrites the
config/log files without leaving the process resident.

**Do not let a name in `/Library/Application Support` imply third-party.**
Root-owned entries there are frequently Apple's own and load-bearing: `livefsd`
carries the Developer `CoreDevice` `DeviceFS` mount records, and `BTServer`
holds GarageBand/Logic/Keynote sound content. Read the plist and check
`codesign` before classifying, and when a plist names a live mount point, that
is a keep by evidence rather than by caution.

Two mechanics that follow from the same sweep:

- **`launchctl bootout` before deleting the binary.** Removing a job's
  executable while its plist is still registered leaves launchd respawning into
  errors. Boot out the label first, then delete plist and binary together.
- **Commit plist deletions by restarting the preference daemon.** `cfprefsd`
  caches `~/Library/Preferences`; delete the plist, then
  `killall -u "$(id -u)" cfprefsd` or the change reads as not applied.

**A cloud-held container refusing deletion is a skip, not a failure.** Empty
`~/Library/Mobile Documents/iCloud~<vendor>~<app>` shells return
`Permission denied` even to their owner because the iCloud daemon pins them.
Confirm they are empty, leave them, and say so — forcing them is a fight with
the OS, and iCloud reclaims them itself.

**Split the report at the privilege boundary.** A sweep almost always has a
user-level half you may run and a root half that needs a password. Run yours,
then hand over the root half as a *ready-to-run script* with the exact `sudo`
line, not a list of paths for the user to act on. State which files were kept
and the evidence for each keep — the user can only object to a keep they can
see, and a named keep with its reason is how a 518 MB mistake gets caught
before it happens.

## Prefer reversible over destructive

Suggesting a fix the user can undo (relocate, re-run a script, drop a cache
that regenerates) beats a delete that cannot be walked back — even when the
delete is faster. Never `rm -rf /tmp/*`; always allowlist.

## Deleting source code: the compiler decides, not a grep

A textual "is this identifier referenced anywhere?" scan is a **candidate
generator, never a delete decision**. A real codebase produces three classes
of false positive from that scan constantly:

- Test entry points (`#[test]`, `wasm_bindgen_test`) are legitimately
  unreferenced by name — the harness calls them, not your code.
- `pub` library API is unreferenced *inside its own crate by definition*, and
  consumed by downstream crates the scan never read.
- A live `const`/`fn` reached through a re-export or a glob re-export the
  scan did not follow.

Each false positive is a build break the instant you delete it. Resolve
candidates with the tool that actually resolves names — the compiler's
`never used` / `never constructed` / `never read` output — and treat a clean
compiler run as the only evidence that a candidate was genuinely dead. If
the compiler is clean, the honest answer to "delete dead code" is "there
isn't any", not a hand-rolled list.

Two further rules that only surface when you do this:

- **Match module registration with raw identifiers.** `mod r#input;` registers
  the module named `input`; a naive prefix or substring match calls it
  unregistered and deletes a live module. Strip the `r#` before comparing.
- **A directory whose contents were never `mod`-registered is a different
  finding than dead code.** Those tests were written and never compiled.
  Report it as "not running" and fix it by registering the module — not as
  "unused" and fix it by deleting the directory. Check for an empty `fn.rs`
  *and* a matching subsystem in `src/` before calling a test dir dead.

Scanning cost matters too: a per-identifier regex re-scan over a large tree
is quadratic and times out, while one tokenizing pass into a name→count map
answers the same question in well under a second.

Run the sweep before proposing any deletion:

```bash
python3 <skill>/scripts/dead-code-sweep.py <repo> --target wasm32-unknown-unknown
```

Runs the compiler pass and the orphan-module sweep together, prints the
evidence next to each candidate, and deletes nothing. `RESULT: nothing to
delete.` is a complete and correct answer — report it as one rather than
substituting a grep-derived list.

For disk-reclaim cleanup (the "my disk is full" class of task) the macOS
candidate map, config-resolved cache locations, and `simctl` / Docker Desktop
handling are in `references/macos-workstation-reclaim.md`. The full per-vendor
residue scan — every macOS location an uninstalled app leaves behind, the
container/orphan-launchd detectors, and the worked example — is in
`references/app-residue-sweeps.md`; `scripts/orphan-launchd.sh` is a read-only
scanner for launchd jobs whose target binary is gone.

## Scale: mass-delete is a script, not a loop

Bulk deletes trip a mass-deletion guard that blocks multiple `rm -rf` in a
short window. Write the allowlist to a file and have one script consume it, so
the guard sees a single process and the allowlist stays reviewable.

Re-check liveness *inside* the script, per entry, immediately before deleting
it — the scan and the delete are minutes apart and something can open a cache
directory in between. A path that was free at scan time may be a live browser
profile by the time the script reaches it:

```bash
if lsof 2>/dev/null | grep -qF "$p"; then
  echo "SKIP (in use): $p"; skipped=$((skipped+1)); continue
fi
```

Printing the skipped path is what makes the report useful — the user can only
object to a keep they can see. Report
`removed=N skipped=N failed=M` and **investigate every failure** — a run of
`FAILED` lines means the permissions assumption was wrong, not that the
skipped files were unimportant. Root-owned sockets and OS logs failing to
delete is the normal, correct outcome, not an error to retry.

## A stale git lock is not evidence the lock is empty — read it before removing it

A `.git/*.lock` left by an interrupted operation blocks the next `add` or
`commit` with a message that reads like "someone else is using this repo". The
reflex is to delete it, and the command is irreversible.

**The lock file is the only record of what the interrupted operation was
writing.** Zero bytes is the normal state for a ref lock — git writes the new
sha at update time, so an empty `refs/heads/<branch>.lock` is not evidence of
nothing. Read it before touching it:

```bash
cat .git/refs/heads/<branch>.lock     # the sha the interrupted op was writing
cat .git/refs/heads/<branch>          # the sha the branch is actually at
git reflog show <branch> | head -5    # did a commit get made but not landed?
```

The reflog is what settles it. A commit listed there that no branch contains is
**orphaned work** — created, then lost when the ref update failed. That work
exists only as an unreferenced commit and is destroyed permanently by
`git gc`; the recovery is to give it a ref *before* touching the lock:

```bash
git branch recovered/<short> <orphaned-sha>    # make it reachable, keep the lock
rm .git/<the-one-lock>.lock                    # now safe: nothing unreferenced left
```

Two orderings matter. **Check whether the sha is an ancestor of `HEAD` before
assuming the lock is stale** — `git merge-base --is-ancestor <sha> HEAD` — and
be prepared for the answer to be no, which is the case that matters. And
**enumerate every lock** (`find .git -name '*.lock'`), because they appear one
at a time as each blocked operation is retried, and removing them one per
round is what makes it look like a persistent repository problem.

When a stale lock is blocking work and the content behind it is not obviously
recoverable, do not choose between deleting and merging on the user's behalf —
make the unreachable commit reachable, commit your own work, and report both
the recovered branch and the open question of whether to merge it. That is
non-destructive in every direction and still unblocks the task.

## `git checkout <file>` is a destructive operation, not a cleanup

Discarding uncommitted work is irreversible from inside the repo, and the
command reads as a neutral "put this file back". Treat it exactly like `rm`:
check what is about to be destroyed, and keep a recoverable copy first.

```bash
# What would I lose? Uncommitted change is invisible to git until it is gone.
git status --porcelain -- <file>
git diff --stat -- <file>

# Keep the work before touching it.
cp <file> /tmp/<file>.bak      # cheap, and the only copy if it was never staged
```

The specific trap: using `git checkout` to strip **temporary instrumentation**
added during debugging. The instrumentation and every real edit in the same
file disappear together, and the real edits are gone. Revert an instrumented
region with a targeted `patch`/`edit` call instead, or edit a copy under
`/tmp` and run that.

Uncommitted work is invisible to `git status --short` in the way people expect
— the file simply shows ` M` whether it holds one line of legitimate change or
a full day of it. Stash (`git stash push <file>`) is reversible and is the
right tool; `git checkout` is not.

## Verify in a directory that has the tool's manifest

A post-cleanup check run from the wrong working directory reports *the check*
as broken, not the cleanup. `cargo metadata` in a non-Rust directory fails
because there is no `Cargo.toml` there — that failure says nothing about
whether the build tool still works.

```bash
cd <real project root> && cargo metadata --no-deps --format-version 1 >/dev/null && echo OK
```

Attribute a failing check before reporting it as cleanup damage, and when the
cause turns out to be your own invocation, correct it in the report rather than
leaving a bare `FAIL` line in the transcript for the user to worry about.

## Path-shape notes

- macOS: `/tmp` is a symlink to `/private/tmp`; use `/private/tmp` for both
  listing and deleting so `search_files` and `du` results agree.
- A terminal session whose cwd was deleted fails with exit 126 before running
  anything. Pass an explicit `workdir` (e.g. the home dir) to re-anchor.
- Report actual bytes reclaimed, not "cleaned up".
