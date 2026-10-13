# Wave planning for a gap-completion effort

How to split an audit's findings into implementable waves without one wave becoming unreviewable or one PR becoming unreviewable.

## Order by value-per-unit-risk, not by feature size

Rank every gap on two axes and sort by the ratio:

- **value**: how many things break if it stays broken. A missing call inside the main loop outranks a missing subsystem: absent is obvious and blocks honestly, silent is worse because everything downstream is quietly wrong.
- **risk**: how much existing behaviour a change can disturb. A new self-contained module is low risk. Anything touching the per-frame path, the publish surface, or a type's constructor signature is high.

Cheap-and-high-value goes first even if tiny. It buys credibility for the larger waves and, more practically, several cheap items are often *preconditions* that make the large ones testable.

## Typical wave shape

| Wave | Content | Gate before starting it |
|---|---|---|
| 0 | audit (read-only) | audit verified, premises spot-checked |
| 1 | hard API blocks + confirmed bugs with tiny fixes | nothing — but keep it one branch, several small commits |
| 2 | root-cause layers (the missing dispatcher/registry that makes existing code live) | wave 1 landed and green |
| 3 | new self-contained subsystems | wave 2 landed; interfaces stable |
| n | docs, then version bump + PR | all prior waves green |

**The root-cause layer is the highest-leverage wave and the easiest to under-size.** When many implemented components are never driven by anything, the fix is one dispatch/registry layer that activates all of them at once — a far better return than the components themselves. Verify the premise first: search each component's update entry point across the whole crate, because "implemented" and "wired up" are independent facts.

## One branch per wave, several commits per branch

Commit granularity: one logical change per commit, conventional-commits prefix, so a reviewer can skip or revert individually. Do not squash a bug fix into a refactor commit — they have different risk profiles and different reasons to exist.

Keep the audit report in the wave-1 branch or a location the next session will actually read. An audit that lives only in a scratch file is re-run from scratch next time, at full cost.

## Fix the documentation in the same wave as the code

When the crate's own doc comment promised a capability that was not implemented, the wave that touches that area is the wave that fixes the claim. Do not defer doc-accuracy to a final cleanup pass — it will not happen, and until it does the crate actively misleads.

Two acceptable resolutions, and the choice belongs to the user: narrow the claim to what exists, or implement until the claim is true. Silently leaving an overstated claim while implementing some of the promised surface is the worst option, because the reader can no longer tell which parts to trust.

## What to hold out of the first pass

State these explicitly in the plan rather than letting them creep in:

- anything requiring an external dependency the project has deliberately avoided
- large accelerators/structures whose absence is a performance limit rather than a correctness one
- features that are only useful together with another missing feature (a 3D content pipeline with no mesh type is not shippable alone)
- any item whose premise you could not verify

Naming what you are *not* doing this round is what makes the remaining scope finishable.

## Repo-ownership discipline across waves

Before dispatching an agent into a repo the user owns, check for uncommitted work (`git status --short`) and tell the agent explicitly not to stash, switch branches, or rebase. Waves run back to back on one branch by design; an agent that switches branches to get a baseline will detach the branch out from under its siblings.

If the repo carries a pre-existing stash entry belonging to the user, mention it in the report and leave it alone — a stash is the user's unsaved work, not a build artifact.
