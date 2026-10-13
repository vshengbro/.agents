# Making a rewriter safe to put in a commit gate

A rewriter is any tool that edits files: formatter, fixer, doc generator, import
organiser. Three properties decide whether it is safe to run in a pipeline that
other people depend on. Check all three before wiring one in.

## 1. Scope — it may only touch the current change

The default failure is a whole-repo sweep. Symptom: the tool reports success while
having rewritten files the caller never edited, and the volume dwarfs the change
that triggered the run.

Add a file-scope parameter, and make the caller pass the change set. The change set
has three sources and all three are needed — omitting any one produces a false
"nothing to do":

```python
paths = set()
# 1. committed ahead of the base
paths |= set(git("diff", "--name-only", f"{base}...HEAD"))
# 2. uncommitted worktree + index edits   <-- the most commonly forgotten
paths |= set(git("diff", "--name-only"))
paths |= set(git("diff", "--name-only", "--cached"))
# 3. untracked files
paths |= set(git("ls-files", "--others", "--exclude-standard"))
```

**Never let an empty scope mean "everything."** With a variadic flag
(`nargs="*"`), omitting the values yields an empty list that a `if files:` guard
reads as false and falls back to whole-repo — the exact opposite of the intent.
Make emptiness mean *skip the tool*, and require an explicit opt-in flag for a
full sweep.

Keep the three states distinguishable, and say which one is active in the output:

| state | meaning |
|---|---|
| explicit sweep flag | caller asked for whole-repo; say so loudly |
| non-empty list | only these files |
| empty list | scope computed, nothing to do — skip, do not sweep |

## 2. Baseline — a gate must compare, not count

A check whose only question is "how many violations exist" blocks forever on a
repo with legacy debt, and keeps blocking after you fix your own change. It is
also indistinguishable from a real regression, so it trains people to bypass it.

Block on the **delta** against `HEAD`, not on the absolute count:

```python
before = run_check(repo, baseline_version_of_file)
after = run_check(repo, working_file)
if len(after) > len(before):
    report(after[len(before):])   # only the delta
```

Two details that make this work:

- **The baseline file must live at a path that preserves relative resolution.**
  A checker that walks up to the nearest manifest to read a package name will fail
  on a temp file in a scratch directory. Write the baseline beside the real file,
  under a suffix that does not match the checker's own discovery patterns
  (not `*.py`, not the canonical filename), and delete it in a `finally` block.
- **Import the checker's per-item function rather than shelling out per file.**
  File-path arguments are the most common source of interface mismatch (see §3),
  and importing also guarantees one parser per rule instead of two.

When you cannot add a baseline (a whole-repo audit, for instance), the manual
equivalent for a one-off report is: stash your changes, re-run, compare numbers,
pop. Identical numbers means the failures predate your change — report them as
pre-existing debt, not as a failure of the work you just did.

## 3. Idempotence — the same input must give the same output

A non-idempotent fixer compounds. Each run adds on top of the last, so scoping
alone will not contain it: a single file can explode on the first run.

Test explicitly, not by inspection:

- Run on **already-compliant** input → expect zero changes.
- Run twice → expect **byte-identical** output (`diff`, not eyeballing).

The usual cause is an insert that does not check whether its target already
exists. Every insert needs the same predicate the auditor uses to report the
violation:

```python
# wrong — appends a second full block every run
insert_after(doc_end, build_section(name))

# right — same condition the auditor checks
if "# Arguments" not in doc_text:
    insert_after(doc_end, build_section(name))
```

## 4. Belt and braces: detect out-of-scope writes anyway

Even after scoping, snapshot the repo around the call and report anything that
changed outside the declared scope. This catches the next tool that violates the
rule, instead of waiting for a user to notice a 7000-line diff.

```python
before = snapshot(root)            # path -> size, cheap
run_tool()
drift = [p for p, size in snapshot(root).items()
         if before.get(p) != size and p not in scope]
if drift:
    print(f"WARNING: tool modified {len(drift)} file(s) outside scope")
```

## 5. Ship the referenced files with the reference

A pipeline that invokes a script must ship that script. If a hook or orchestrator
references a file that is untracked, it works on the author's machine and fails on
every fresh clone.

```bash
git ls-files <referenced-script>     # empty output = never committed
```

Verify before pushing, not after someone reports a broken CI:

```bash
git clone --depth 1 file:///path/to/repo /tmp/check
# then assert every referenced path exists and parses in the clone
```

## Order of work

1. Reproduce the damage on a small, reversible input; record the baseline dirty
   count.
2. Read the tool's CLI contract — what argument type does it actually accept?
3. Add scope; add the baseline delta; add the idempotence guard.
4. Re-test all three properties, each with an explicit pass/fail observation.
5. Confirm every referenced file is tracked, and that a clean clone of the tree
   still satisfies the pipeline.
6. Commit the tool fixes separately from any change to the user's repository.
