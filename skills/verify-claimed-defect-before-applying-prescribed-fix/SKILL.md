---
name: verify-claimed-defect-before-applying-prescribed-fix
description: Use when a task prescribes an exact code fix to a "defect" — measure the real geometry/behaviour first, then confirm the prescribed change actually addresses it before committing.
---

When a task says "fix defect X by changing constant A from v1 to v2", do not assume the premise. Reproduce the defect, measure it, and check that the prescribed change is the cause. Report a mismatch instead of silently implementing a no-op fix.

**Why:** A prescribed fix can be plausible, harmless, and irrelevant to the actual bug. Committing it under a "fix" message hides the real defect behind a green test run and a plausible diff. In one real case a task asked to thicken a tank's track band (TRACK_R 0.13 -> 0.20) and cut the wheel count, but the actual defect was a swapped axis order in the tube() call: the swept band ran crosswise through the hull instead of lengthwise along the wheels. The prescribed change was measurable and harmless but addressed nothing.

**How to apply:**

1. **Establish the axis convention from ground truth, not assumption.** Read the control tables / schema comments the builder is built from, not the function signature you assume. A `_wheel(m, x, y, r, w)` helper plus a `tube(m, path, ...)` call with a `(p[0], sy*1.36, p[2])` remap means the *first* path component lands on X, not Y.
2. **Measure with a probe against the source of truth.** Build the mesh in headless Blender and print per-part bounding envelopes in AUTHORING space (`part.mesh.pos`), before the exporter's axis rotation. Envelopes answer "which axis is this part long in" exactly; a render does not.
3. **Corroborate with a colour-coded orthographic render.** Give the suspect part a distinct material colour, view straight down the up axis, and state in the prompt which image axis is which world axis. Vision reads orientation reliably here and cannot resolve a dark unlit silhouette.
4. **Test the real fix in an isolated scratch copy** of the tree (`cp -R` to a temp dir), never in the repo, so you can prove the alternative works before proposing it.
5. **Check triangle arithmetic for coherence.** If the count delta equals `wheels_removed x tris_per_primitive` exactly, your change did what you think; a delta you cannot decompose means something else also changed.
6. **Renders can lie about what is dark and what is absent.** Unlit near-black assets on a dark background produce false "gaps between wheels". Only trust lit, colour-coded, numerically corroborated evidence.

Related: [[shared-worktree-check-index-before-committing]]
