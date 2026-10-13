# Triaging an acceptance FAIL: real defect, broken verdict, or harness limit

Every FAIL from the suite lands in exactly one of three classes. Decide the class
**before** dispatching a fix — a defect dispatched on a broken verdict costs a
rewrite, and a real defect relabelled SKIP disappears for good. The tell is
almost always in the reading itself.

| Reading looks like | Class | Discriminating evidence |
|---|---|---|
| speed ratio far from `RUN_SPEED/WALK_SPEED` | broken verdict | compute implied `dt = displacement / speed` per leg. If the two legs' implied dts differ, the ratio is void — the legs are not comparable. |
| stall frames at a spot next to geometry | broken verdict | repeat on open ground. Stall must be **clearance-aware**; contact and stuck are different states. |
| `dist != target` on frames where the feature is *supposed* to pull in | broken verdict | exclude the feature's own trigger mode from the check, then judge the rest. |
| a key does nothing; its constant is declared | real defect | `git grep -c '<CONST>' -- src/` → **1 hit = declared and never consumed**; 2+ = wired. |
| a verdict's own note contradicts its verdict | broken verdict | a table that contradicts your own readings hides real defects. Drop the hardcoded expectation and re-derive. |
| a one-frame flag read through a throttled channel | harness limit | unobservable, not broken. Return SKIP and name the channel. |
| a collection-scoped check over an empty collection | broken verdict | vacuous pass. Retry until non-empty, else return `None` — never PASS, never FAIL. |
| a reading taken while the app was in another mode | broken verdict | assert the **mode** precondition (driving / first-person / on-foot), not just position, before reading. |
| a worker reports a target 60 m away and drives 60 frames | harness limit | a scenario that cannot reach its subject cannot test it. Fix the route. |
| a check the app plainly implements, with green evidence beside it | broken verdict | the strongest signal is a FAIL whose own worker output proves the feature works. |

## The three rules that produce most of these

**Normalise every comparison by the effective dt, measured not assumed.**
Comparing per-frame displacement across two legs is only valid when both legs
integrated with the same dt. Derive it (`displacement / speed`) and compare
those, not the raw displacements. Deriving a dt from a *constant* in the source
is a guess; derive it from the reading.

**"Conservatively" judging FAIL is not a justification.**
When a check cannot measure the property it names, the answer is SKIP. Marking
it FAIL anyway to avoid under-reporting hides a defect behind a number that
looks safe. Under-reporting is recoverable; a hidden defect is not.

**A verdict must be satisfiable by some reachable app state, and a verdict that
fails needs the reference product's behaviour checked before you relabel it.**
A check that no app state can pass is a broken verdict (§20 of SKILL.md). A
check the app *deliberately* does not implement needs the reference product
consulted first — and if the reference does implement it, keep the FAIL. Do not
downgrade a confirmed defect to SKIP to improve the suite's numbers.

## Before dispatching a verdict-repair round

A suite with structurally unsatisfiable verdicts can never go green, so every
round the main agent re-triages the same red by hand. Repair the verdicts
first: it is the only step that makes the fix→verify loop converge. Confirm the
repair by per-item adjudication (defect / verdict / harness limit) **plus** the
before/after tally — the count alone cannot tell a repaired suite from a
silenced one, so pair it with the per-item list and the delta in SKIPs.
