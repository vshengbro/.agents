# Authoring a new rust-standards rule end to end

A new rule is not one edit — it is spec text, a verifier, a registration in the audit, a script-index row, and proof the verifier can tell right from wrong. Skipping any of the five leaves a rule that either does not run or runs wrong.

## The five landing places

| # | Where | What | If skipped |
|---|-------|------|-----------|
| 1 | `references/<NN>-<topic>.md` | Rule prose: what it forbids, what the compliant form is, why, with a real example | A future session reads the script, not the spec, and reverses the rule |
| 2 | `scripts/verify_<rule>.py` | The checker | Nothing is enforced |
| 3 | `audit_rust_standards.py` `CHECKS` | Registration; name the rule and its `§` in the label | The rule exists but never runs |
| 4 | `SKILL.md` script index | One row + one-line description | The script is invisible to every future session |
| 5 | Fixture proof | Compliance direction proven | You cannot distinguish a correct verifier from a coincidentally-green one |

Order matters: write the spec first, because the verifier's job is to implement *that* sentence, and the audit label quotes it back in every failure report.

The pre-commit hook calls `audit_rust_standards.py` directly, so registration at #3 is what makes the hook enforce the rule. Do not hunt for a separate hook wiring — verify the hook's own output names the new check number when a violation exists, and that it blocks.

## Differential fixtures: prove the rule can fail

A verifier tested only on violating input is untested. A verifier tested only on compliant input passes for the wrong reason constantly.

Build three fixtures minimum:

| Fixture | Must |
|---------|------|
| `violating` | every forbidden form the user named, each spelled distinctly — reports all of them |
| `compliant` | the adjacent forms that must **not** fire, plus edge shapes — 0 reports |
| `tiebreak` | input where the rule's *discriminator* decides the outcome, and a plausible wrong implementation would answer differently |

The tiebreak fixture is the one people skip and the one that carries the value. If the rule sorts by `(length, lexicographic)`, a fixture like `Gebra` / `Zebra` / `Apple` is sorted-clean under pure lexicographic and unsorted under length-first — a plain alphabetical implementation fails it. Without that fixture, a lexicographic verifier can look identical to a correct one on every ordinary input you would think to try.

For "this syntax is redundant" rules, the compliant fixture must carry the **narrowing** forms (`pub(crate)`, `pub(super)`) and the parser-hostile shapes (the token inside a comment, a same-named non-macro attribute, the keyword as a substring of an identifier). A rule written as "delete the keyword" will delete `pub(crate)`'s prefix and break the build; the fixture is what catches that before the user's repo does.

**Write the fixture before changing the rule, not after.** The fixture is
what shows the rule was previously backwards. A rule that exempts exactly the
files it was written to police reports 0 on the repo that violates it and
flags a compliant tree — running the fixture against the *old* implementation
is how you demonstrate both directions at once, and it converts a hunch about
what is wrong into a measurement. A tightening that only shows green
afterwards leaves open whether the old code was actually enforcing anything.

**Then mutate the rule and confirm the fixture catches it** — re-widen the
exemption, disable the check, invert the comparison, and require a FAIL each
time. A fixture that has never failed is indistinguishable from a rule that
does not work; the mutation table is the only evidence that the test has
teeth. See the mutation recipe in `verifying-against-a-real-gate`.

**Correct a spec's factual claims when the measurement contradicts it.** A
rule's justification often names specific counts ("this repo carries 24 of
these"). If the measurement says the files sit in leaf directories with no
sub-modules and are therefore not flagged at all, the count was describing a
hypothetical shape, not the real repo. Fix the sentence that misled in place —
do not append a correction underneath it, because the sentence is what the
next session reads.

## Before choosing a split axis, measure which items are shared

When a structural rule forces a directory split, the obvious axis (by file
name, by feature, by backend) is usually wrong, and picking it wrong produces
a layout that compiles only because a sibling module happens to re-export what
it needs. Measure the cross-references before committing to an axis.

```python
# which top-level items does each would-be new module reference?
for mod in (NEW_DIRS):
    refs = {name: 0 for name in all_items}
    for f in mod.rglob('*.rs'):
        for name in all_items:
            if re.search(rf'\b{re.escape(name)}\b', f.read_text()):
                refs[name] += 1
    shared = {k: v for k, v in refs.items() if v and k not in mod}
```

**An item referenced by two or more of the new modules is not a member of any
of them.** It belongs in a shared tier, and the split gains a level:
`shared/` + one directory per implementation. Splitting on an axis that
separates two consumers of the same type produces exactly the coupling the
split was meant to remove — one implementation module reaching into a sibling
implementation module, which is worse than the layout you replaced.

The same measurement settles **feature-vs-backend** splits. A renderer with
two backends looks like it wants `webgpu/` and `webgl/`, and it does, until you
count that `FilterMode` / `AddressMode` / `CompareFunction` / `BlendFactor` /
`IndexFormat` / `DrawArgs` are referenced from both. Those enums are the
renderer's vocabulary, not either backend's, and the split becomes
`state/` + `descriptor/` + `webgpu/` + `webgl/`.

Also check the item counts, not just the references: a five-item "shared"
tier and a fifty-item one imply different splits, and a keyword classification
by name is unreliable — `LoadOp` reads like a WebGPU concept and is used by
the WebGL path too. Route by content, then confirm with the counts.

**Report the measurement, not just the layout.** The user is the one who
picks the axis when it is not forced, and a table of "referenced by N of M
modules" is what lets them choose. Present it with the recommendation and the
cost of the alternative.

When a rule deletes something that a macro was expanding — an explicit visibility argument, an explicit type, a redundant `impl Trait` — "the verifier is clean" is not the proof. The proof is three independent measurements:

1. **Diff precision.** Insertions equal deletions, every deleted line is the construct in question, and every added line is exactly its deleted counterpart minus the removed token. Assert this mechanically over `git diff -U0` rather than reading a sample. A regex rewrite that also ate an adjacent form shows up here as a count mismatch.
2. **Narrowing cases untouched.** Snapshot the count of every form the rule must *not* touch, before and after. Zero delta on `pub(crate)` is the evidence that the rewriter distinguished widening from narrowing.
3. **The compiler.** This is the load-bearing one. If a macro default changed, or the explicit argument was doing work, then downstream call sites stop resolving and the build fails with `E0599` / `E0624` / `E0603` on the *first* external use. A clean build is proof the meaning survived; the other two measurements only prove the edit was surgical.

Run all three. Reports that lead with "0 violations" and omit the build are asserting the rule fired, not that behaviour held.

## Keeping a repo's check count comparable

Adding a check changes the denominator (`N/M PASS` → `N+1/M+1`), so a before/after comparison of the summary line is meaningless across a rule addition. Compare the *named* check, not the ratio: "check 23 went FAIL → PASS" survives the renumbering; "33/42 → 34/42" does not read the same way twice.

The same applies to `cargo` state: a minor bump leaves the tree unable to resolve its own workspace. Align the pinned path-dependency versions, run the real gate, then restore — and verify the restore, because a forgotten revert shows up later as an unexplained dirty manifest.

## Scope hygiene when committing

`git add -A <dir>/` inside a `docs/`-shaped or build-output-shaped directory sweeps in untracked artifacts — generated HTML, bundles, `.wasm` — that no `.gitignore` covers. Scope the add to the files you actually edited.

**Tell:** the commit's diffstat lists paths in a directory you never opened.

**Fix:** `git rm -r --cached <artifact-dir>` then `git commit --amend --no-edit`. Confirm the artifact is back on disk and untracked afterwards — `--cached` removes it from the index, not the working tree, and you want it still there.

**Verify before amending:** `git show --stat HEAD` after the amend, not before. The pre-amend output is the one containing the mistake.
