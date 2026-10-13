# Reading the audit's counts, and splitting the follow-up

How to interpret `audit_rust_standards.py` output across a multi-round fix, and
how to turn the result into work that parallel children can take without
colliding.

## A PASS total that stays flat while the FAIL count rises is progress

The audit prints one `PASS: n` / `FAIL: n` line per rule plus an `n/45 passed`
total. When the last violation of a rule is cleared, that rule's own line flips
to PASS — and the same edit frequently *unmasks* checks that were never
reached, so the FAIL list grows in the same run that raised the total. Read
both numbers; never quote the total alone.

Observed shape: a repo sat at `36/45` with 9 FAILs. Clearing the single
largest check (56 hits of direct field access) took it to `37/45` and revealed
8 further FAILs totalling 89 hits that had been invisible the whole time. The
hit count went **up by 89** while the pass total went **up by one**. Describing
that as "the fix made things worse" is wrong, and so is re-quoting `36/45` as
the new baseline.

### Establish which rules are masked, before planning any work

A short-circuiting check stops scanning early, so its own report understates
what is there. The cheap tell is arithmetic — the printed detail lines account
for far fewer hits than the audit claims, or the FAIL-line count is unchanged
across a large fix.

```bash
audit_rust_standards.py 2>&1 | grep -E '^(PASS|FAIL): [0-9]+' | grep FAIL
```

Get the real per-file distribution before splitting work across children. A
distribution derived from the printed sample splits wrongly — two agents land
on the same file, or the file with the most hits is assigned to nobody. The
clean way to take the full list is to run each failing check's own verifier
directly — never patch the audit script's detail cap, and if you ever do,
restore it at once and verify the restore landed:

```bash
python3 <audit script dir>/verify_<rule>.py <repo>
```

Verifiers disagree on path format: some print repo-relative paths
(`cli/src/build/fn.rs:353`), others absolute (`/home/.../repo/cli/...`). A
grep anchored on one form returns empty on the other and reads as "no
violations in this crate" — match on `/<crate>/` or strip a known prefix
before bucketing per crate.

```python
# cap-patching alternative — avoid; if used, restore + verify
p = "<audit script>"; s = open(p).read()
open(p, "w").write(s.replace("for o in out[:5]:", "for o in out[:500]:"))
# ... read the full distribution ...
open(p, "w").write(s)          # restore, always
```

A verifier script left patched is a shared resource every later run silently
depends on.

## Linter output under-reports the same way as the audit sample

`cargo clippy`'s per-target summary (`(test "mod") generated N warnings`) and
the detail blocks do not always agree with what a filtered pipeline collects:
`grep -A6 '^warning:' | grep -- '-->' | head -150` silently drops sites past
the head cut, and an incremental re-run can emit a different subset than the
first full pass. The failure shape is patching every site you listed and still
having leftovers on re-run. Build the site list from the full saved log
counted with `grep -c` per lint, and re-run the linter to zero — the re-run
is the arbiter of "done", never the first enumeration.

## Split follow-up work by file, not by rule

Rules like `let` type annotations, closure annotations and doc comments hit
every module, so a rule-per-agent split guarantees two agents editing the same
file — and their string-replace passes interleave. File-per-agent is disjoint
by construction, and each agent can verify with the full suite without
coordinating with anyone.

Give each child its own explicit file list in the task context, and say which
files are off-limits. Without that, a child greps the audit output, finds the
biggest number, and starts on a file another child is already in.

## In a Cargo workspace, the split unit coarsens from file to crate

File-per-agent is the disjointness rule; in a workspace the natural file set
is the crate directory. Split by crate whenever a fix crosses files *within*
one crate — a qualified-path sweep, for example, rewrites both the sub-file
(`std::fs::read_to_string` → unqualified) and the crate's `lib.rs` / `mod.rs`
(which gains the import). Assigning those to different agents turns every
`lib.rs` into a shared write target; assigning each crate to one agent keeps
every `lib.rs` / `mod.rs` in exactly one write set, and the crate's `tests/`
tree rides along with it.

Brief each crate's agent with its own measured numbers (run the verifiers on
the crate subdirectory, as above), the package name for scoped cargo commands
(`cargo fmt -p <pkg>` — never workspace-wide `cargo fmt` from a parallel
child), and a consumer smoke check (`cargo check -p <dependent>`) when other
crates depend on it.

Iterate on the text verifiers, gate on cargo. Verifiers answer in under a
second; cargo is the compile gate. Parallel children sharing one workspace
`target/` serialize on cargo's lock — correct but not concurrent — so the
brief should reserve `cargo check -p <pkg>` / `clippy -p <pkg>` for the end of
an edit batch, not per site.

### A visibility-reduction sweep is producer-side work

Reducing `pub` → `pub(crate)` belongs to the agent that owns the *defining*
crate, because the compile error from an over-reduction lands in a *consumer*
crate whose owner cannot widen it back. The producer greps the whole workspace
read-only — every `src/` and every `tests/` tree — before reducing:

- Any name a `tests/` tree references stays `pub` — integration tests are
  external crates, and reducing past them is E0603 in a tree nobody in this
  dispatch is allowed to edit.
- A name used only inside its own crate drops to `pub(crate)`; used only
  within its module subtree, to `pub(super)` or private.
- Usage ambiguous → leave it `pub` and report it. A widened-back API is
  cheaper than a broken consumer nobody is allowed to fix.

Consumer-side agents report cross-crate needs ("ui needs X re-widened"), they
never edit the producer crate to get it.

## One rule's prescribed fix generates another rule's findings

Rewriting direct field access into hand-written accessors (Rule 41) *creates*
doc-comment findings, because each new accessor needs `# Arguments` /
`# Returns` sections a generated one never had. Fixing the two in either order
in the same pass makes them chase each other: the doc sweep runs before the
accessors exist, the accessor pass then adds undocumented items after it.

Sequence it: rewrite accessors first, then sweep the doc comments they now
require, re-auditing between the two phases.

## The doc-comment verifier cannot parse every return type

A verifier that splits a return type on `,` and `;` will not accept a nested
generic containing either — `Vec<[f32; 2]>` gets truncated to `Vec<[f32`, and
the finding persists no matter how the doc reads. When a doc comment is
correctly shaped and still reported, test the verifier before rewriting the
doc a fourth time: import it directly and call it on the file.

```python
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("v", "<verifier>.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for h in m.audit_one(pathlib.Path(src)): print(h)
```

The fix that satisfies both is to give the return type a name the verifier can
match — introduce a `Vec2` alias for `Vec<[f32; 2]>` and annotate
`- `Vec2` - ...`. That also reads better than repeating the array shape at
every signature.

## The staged gate is stricter than the full audit, and it is the real one

The pre-commit hook compares against `HEAD`, so it counts a violation as *new*
whenever the line moved, even when the code is unchanged and the finding is
pre-existing debt. The full audit may pass on a file the hook blocks.

Treat the hook as authoritative for what will land, and expect the iteration to
converge in steps: this session went 15 → 9 → 1 → 0 new violations over four
commit attempts. When the remaining findings are all in code you did not touch,
check whether the finding predates your work (`git show HEAD:<file>`) before
rewriting the line — some are genuinely new (a function's signature gained
parameters in an earlier commit of the same series and its doc comment was
never updated) and some are the verifier's parsing limit again.
