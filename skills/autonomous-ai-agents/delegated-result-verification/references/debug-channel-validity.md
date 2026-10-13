# The debug channel invents symptoms the app does not have

A page that publishes a debug/state object writes it on *its* cadence; a CDP
harness samples on *its* cadence. When those differ, the harness manufactures
periodic, convincing, entirely fictional symptoms. This is the reference form of
`delegated-result-verification` §20 — that section states the rule, this file
gives the diagnostics, the atomic-snapshot fix, and the sibling artefacts.

## 1. Read the frame-number sequence before believing any periodic verdict

The published snapshot is usually rewritten every N frames. A harness that walks
the counter and calls each skipped publish "a frame where nothing moved"
**manufactures a perfect periodic stall out of a smooth walk** — and the
manufactured period is exactly the throttle stride, which reads as a very
convincing bug.

```
throttled trace : 267, 270, 273, 276           <- fixed stride == throttled writer
real trace      :  43,  44,  45,  46, ... 90   <- no gaps
```

Gaps at a fixed stride = throttled writer. Non-advancing consecutive numbers =
real. So a stall, freeze, "frozen input", or "every third frame is dead" verdict
is not evidence until the sampler has been ruled out.

- Build the trace **in-page**: an unthrottled sampler appending to an array,
  returned in one round trip. Keep every *decision* in the harness language so a
  faster stride cannot change what counts as success.
- Cross-check with a path that bypasses the event layer — inject the movement
  intent directly. Bypass clean + event path dirty means the defect is in input
  handling, not the physics under test.
- When you revise a cause you already stated, **name which part was wrong**. A
  right conclusion resting on a wrong reason is the next session's starting
  point. Observed: the correct conclusion ("no walk stutter") was first
  attributed to the fixture being beside a wall, when the real cause was the
  throttle; the reason had to be retracted explicitly even though the verdict
  stood.

A real periodic stall has a signature the artefact does not: it shows a **peak at
the period lag** in the per-frame displacement autocorrelation, with a monotone
decay elsewhere. A throttled-sampling artefact is monotone-decay-from-lag-1
with no peak at the throttle stride.

## 2. Snapshot atomically, or the fields move under you

Once the channel is known to be rewritten on a cadence, **any two reads are two
different documents.** A script that prints one field and then indexes it again
for logic can see `None` and then a `KeyError` on the *same field*:

```
door = null
interiors = {"count": 40, "inSolid": false}
KeyError: 'door'          <- `v` is no longer the dict `door` came from
```

The tell is a field present in one read and absent in the next with no
corresponding code change. It reads as "this field is conditionally emitted" and
sends you auditing the wrong thing.

```
v = await s.st()                                    # ONE read of all channels
door = v.get("door"); camd = v.get("cameraDist")   # all fields from that snapshot
```

Use `.get()` for fields you do not control — a debug export that emits a field
conditionally is a normal shape, not a defect. To decide whether the page
advanced between reads, compare the **monotonic frame number**, never
`v == prev`.

**Steer the child to this, do not only fix it yourself.** It is a rule the
verification children need in their brief, and a subagent that has not been told
will write the multi-read form every time.

## 3. A saturated frame-time cap makes two modes arithmetically identical

When a frame-time cap is exceeded the sim compensates with fixed sub-steps. In
software rendering that can be *every* frame, which makes distinguishable
behaviours measure identically:

```
cap 0.25 s, real rAF 0.58 s  ->  2 sub-steps per frame
WALK_SPEED * cap  = 0.3067 m/frame
measured          = 0.6133 m/frame  = 0.3067 x 2
```

Walk and sprint then show the *same* per-frame displacement, and any "sprint is
slower than walking" verdict is an artefact of the cap, not a binding failure.
Two independent probes producing a ratio near 1 is the tell: a number close to
1, close to a round fraction, or close to a measurement with no shared cause has
not yet been shown to have had room to differ. Measure the real frame interval
and the cap, and report both.

**The corollary the acceptance side owns:** throttled sampling produces false
*positives* (invented stalls) **and** false *negatives* (a real change that fell
between two publishes and read as "no change"). Both directions need the
unthrottled trace before they can be classified. Any verdict produced by
sampling a throttled channel is `UNDETERMINED`, not PASS and not FAIL.

## 4. An interaction FAIL is a proximity artefact until you measure the distance

An enter / pick up / interact check returning "failed" has usually not found a
broken binding — the fixture is too far away. Compute the distance from the
agent's own state before dispatching a fix:

```
player (33.5, 45.0)
car0  (33.5, 57.3)  ->  12.34 m     <- interact radius ~2 m; this FAILED correctly
car1  (25.4, -13.8) ->  59.40 m
```

The same log often shows the *setup* step did not run: a child dispatched to
test whether a teleport channel executes reported a failed interaction, which is
evidence the teleport never happened — the bug is one step earlier than the
assertion that caught it. Trace the chain backwards before dispatching.

## 5. Render-affecting config belongs in the initial URL

Hiding batches, forcing resolution, or selecting a reverse-experiment mode has to
be in the URL the session was *opened* with. Injecting it mid-session via
`history.replaceState` hides the wrong set and yields a blank canvas, which then
reads as "the app is broken". Use a separate `Session(..., hide=[...])` per
configuration.

If a screenshot comes back uniformly blank, check the page booted before
concluding anything about rendering: assert state fields are non-null, not merely
that a PNG exists. A 4 KB PNG of a blank page is a successful screenshot of
nothing.

## 6. Screenshot the state you claim, at the resolution you claim

The reverse-experiment screenshot (hide everything except the subject) is the
only thing that settles "does this assemble into the intended shape". Two traps:

- **Re-capture it yourself in the parent session.** Do not relay a child's
  before/after description of its own screenshots. Look at both frames. Stale
  files from an earlier build are indistinguishable from new ones by path, and
  the description can be right while the artifact was never re-taken. When the
  independent re-capture disagrees, the independent one is the measurement.
- **Absolute brightness is not evidence.** A sky gradient satisfies "contrast
  above 40" and "non-black above 15%" while the box contains no object at all.
  The sound contrast test is *inside vs immediately outside* the box; when those
  are statistically indistinguishable that is a **result to report**, not a gate
  to tune until green. Subjects only tens of pixels tall against a bright sky
  are legitimately un-separable by luma statistics and separate by eye — which is
  why the perceptual read is acceptance and the statistic is a liveness guard.

A related numeric trap: a bounding box that degenerates to zero width because its
two points coincide on axis **inflates the measured subject size**. Observed: a
fragmented mesh stretched its own bounding box, which *masked* a separate probe
defect — "charBox is 3 px wide" turned out to be a symptom of broken geometry, and
the probe only became meaningful after the geometry was fixed. A pixel-count
threshold sized against a degenerate box is unreachable by construction, and
reaching for it sends you to tune the threshold instead of fixing the subject.

## 7. A gate inside the harness can be hardcoded false, or stale about the source

A failing check is not always a statement about the app. Two shapes produce
failures that survive every app-side fix, because the verdict was never computed
from the app:

**A hardcoded verdict.** A worker builds its result as
`Verdict("V 切相机", False, "…no KeyV branch (grep empty)…")`. No input can
change it. The note is also a *claim about source* that goes stale the moment the
feature lands, so the gate reports a defect that was fixed weeks ago.

**A source-derived table frozen at authoring time.** A `missing = ["Space",
"KeyG", "KeyH", "Tab"]` list drives four verdicts. When the keybinds are
implemented, the table is still consulted, so all four report the absence the
list asserts.

The tell in both: **the note repeats a conclusion instead of a reading**, and the
worker's *own measured values in the same line* contradict it. Observed side by
side:

```
note:   「src/ 全文无 'Space' 分支」       <- conclusion, stale
read:   「按住 Space: y 0 -> 0.6933, grounded true -> false」   <- it jumped
```

When a verdict's note and its own reading disagree, **the reading wins** and the
gate is the defect. Settle it by reading the code the note claims to summarise, not
by re-running the worker — re-running reproduces the same hardcoded line.

Two related staleness traps in the same family:

- A note that greps for a **literal token** goes stale when the code moves to a
  named constant (`KEY_GRENADE: &str = "KeyG"`). The parent version of this is in
  SKILL.md; here it is the *harness* carrying the stale knowledge.
- A note describing a key's **old semantic** ("Tab is third_person 取反") stays
  true as prose long after Tab is remapped. A remap is a defect-list item, not a
  stale-gate item — the gate is correct, the expectation is.

**Before accepting a FAIL, open the gate.** For a small harness this is one read
of the module and it is decisive:

```bash
grep -n 'Verdict(' tools/verify8/wN_*.py | head        # look for literal bools
grep -n 'missing' tools/verify8/wN_*.py                # frozen expectations
```

Report these as **harness faults, never as app failures**, and say which of the
two it is rather than relaying the count.

## 8. A channel field whose name lies about what it controls

A debug channel is an API; treat each field's *name* as untrusted until you have
read what writes it. Two distinct failures, opposite in direction:

**The field does something else.** `{speed: N}` read as "walk speed N×" and
measured as a speed ratio. It is a **time-warp multiplier**: it feeds
`K_TELEPORT_SPEED` → `speed_scale`. The measurement was a dead channel wearing a
name that invites a physics conclusion, and it produced a confident "sprint is
broken" from a ratio of `1.0`.

**The field is dead.** `speed_scale` is declared, assigned on request, and
initialised — and has **no reader anywhere**. A write-only field makes its channel
silently inert: `{speed: 8}` and `{speed: 1}` are bit-identical.

Both are found the same way, and the check is one command:

```bash
grep -rn "<field_name>" src/     # count sites; 3 hits = decl + assign + init, and no read
```

**A field that only ever appears in declaration, assignment, and initialisation is
a dead channel.** Report it as dead code, delete it rather than fixing the
measurement around it, and re-derive any conclusion you had drawn from it. The
tell that you are in this trap: a ratio of exactly 1.0, or two settings producing
byte-identical readings.

## 9. A swept/tessellated physics fix validated at one speed is not validated

Collision and support queries get fixed for the motion the test happened to
produce, and the defect survives one magnitude up. A frame-sweep fix for stairs
("long frame crosses several treads, so subdivide the frame and re-query the
support along the way") was verified at the walking speed, where one frame is
~0.6 m against a 0.45 m tread. It passed. At the sprint speed one frame is
~1.0 m — over two treads — and the sweep's sub-step was still sized for walking,
so the sweep still skipped surfaces and the test failed outright:

```
walk UP    m/frame 0.375 - 0.43    peak_y 3.1022 / 3.2    dy<0(stair) = []   OK
sprint UP  m/frame 0.96  - 1.08   peak_y 0.15 / 0.455     end_x = 1.77 / 5.1   FAIL
```

The failing signature is worth naming: **`dy<0` was empty and `peak_y` never rose
past the first tread** — the subject did not fall, it never *landed*. A subject
that never rises is a sampling sweep that skipped its surfaces, which is a
different bug from the collapse that motivated the fix, and reading it as a
regression sends the next writer to undo correct work.

Rules for this class:

- **Derive the fix's threshold from the geometry, not from the test.** "Subdivide
  the frame" is only a fix if the sub-step is bounded by the *smallest feature
  dimension* (tread depth, step height, wall thickness), and the bound is then
  checked against **every** speed the game permits, not the one in the trace.
  A fixed sub-step count sized for one speed is a fix for that speed.
- **Verify the full matrix, not one row.** Walking up, sprinting up, walking down,
  sprinting down. This session's first fix broke the *down* case as collateral —
  its sweep "never accepts a surface below the feet" (needed to stop the ground
  slab pulling the player down) also rejected the next tread down, leaving the
  player hovering. A second writer found and fixed it; the first could not see
  it because it only ever ran the up path.
- **Add a regression that pins the fast case, or it will not be pinned.** The
  cross-check the fix kept is that at normal frame rates the swept path
  degenerates to the old point query (`substeps == 1` ⇒ identical behaviour) —
  assert that explicitly, so a future "optimisation" cannot silently change the
  normal-frame-rate path.
- **Include a proximity read in the verdict.** `end_x` running 70 m past the
  subject is what distinguishes "swept under every tread" from "climbed then
  slipped". A verdict that reports only a peak height cannot see the difference
  and will call it a collapse.
- **When re-testing a fix, confirm the fixture actually reached the subject.** A
  mid-run teleport that lands the subject beside the stairs (rather than on the
  tread) reports a clean run that measures nothing. `on_tread=False` in the
  child's own output is the tell; see §4 — and in this class it inverts, because
  an invalid fixture produces a *passing* run, which is worse.
