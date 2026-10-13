---
name: hermes-cronjob-editing-and-verification
description: Use when creating, editing or resuming a Hermes cron job.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [cron, cronjob, scheduling, verification]
    related_skills: [agent-runtime-disk-hygiene]
---

# Editing a Hermes cron job: `next_run_at` is not recomputed

## The trap

`action='update'` that changes only `prompt` / `name` leaves `next_run_at`
exactly as it was. `action='resume'` of a paused job keeps the timestamp from
the moment it was **paused**. Both return `success: true`, and both can leave a
job reporting `enabled: true`, `state: scheduled` — that never fires.

**The only field that forces a recomputation is `schedule`.** Change it to any
other valid expression and back:

```python
cronjob_manage(action='update', job_id=job_id, schedule='2 1 * * *')  # recomputes
cronjob_manage(action='update', job_id=job_id, schedule='0 1 * * *')  # real value
```

Pause/resume is NOT a substitute — it recomputes nothing.

**Do both edits when a paused job's stale timestamp must be cleared.** One
`schedule` update leaves the job on the throwaway expression you typed to force
the recomputation. The second call — restoring the real expression — is what
lands the intended time, and it re-recomputes too. Verify after the SECOND
call, not the first.

## Verify by reading the clock, not the status flags

`enabled` and `state` are not evidence. A **paused** job still reports
`enabled: true`. The only check that counts is reading `next_run_at` back and
confirming it is in the future:

```bash
date "+now: %Y-%m-%d %H:%M:%S %Z (%z)"
python3 -c "
import json
d = json.load(open('$HERMES_HOME/cron/jobs.json'))
for j in (d['jobs'] if isinstance(d, dict) else d):
    print(j.get('name'), '|', j.get('schedule', {}).get('display'),
          '| next:', j.get('next_run_at'), '| enabled:', j.get('enabled'))
"
```

A `next_run_at` earlier than the `date` you just printed is a job that will not
run. Do this after **every** edit to an existing job, not once at the end.

## An agent-mode job with internal sleeps owns its whole run window

A prompt that says "post A, wait 10 min, post B, wait 10 min, post C" occupies
the run for ~30 minutes. The agent firing it at 01:00 has no other way to know
that, so the prompt must state it:

- **Say the wait is expected, do not kill and do not re-run.** Re-running does
  not "catch up" — an idempotent-by-state queue publishes the *next* item early
  instead, so the two runs together over-publish.
- **`cmd1 && cmd2` serialises the sleeps.** If step 2 must not wait behind
  step 1's delay, they have to be separate jobs.

State the expected duration AND the exact command in the prompt, so a firing
agent runs the script rather than improvising a replacement for it.

## Prompts that drive a script, not the agent

When a job's real work is one script, the prompt should be short and literal:
the exact command, what to read from its stdout, and the refusal cases. Two
recurring requirements:

- **State which output proves success.** `CLICKED` is not evidence a post
  landed; a read-back from the page is. Say which line counts.
- **Say what a refusal means: report and stop.** A publisher that declines to
  act is a correct outcome, not an obstacle to work around. Without that line,
  a firing agent retries, forces the item through, and defeats the safety
  behaviour the script was written to have.
- **Say what an honest short count looks like.** When the job's target is a
  count (N replies, N posts) and the script may legitimately come up short —
  the queue ran dry, the feed had nothing left to answer — the prompt must say
  "report the smaller number, do not pad it and do not re-post to reach the
  target". Without it a firing agent invents work or repeats a text, which is
  worse than reporting 20 of 36.

Keep the "do not touch the user's draft / do not reload / do not open a second
tab" list in the prompt too — those boundaries live in the script's skill, and
the job's agent has not read it.

## A cron job's input files are load-bearing, and nothing backs them up

A job's prompt usually names the paths it reads: a queue, a state file, a
copy source. Those files are the job's *input*, and when one goes missing the
job does not degrade — it throws at its first read and publishes nothing, while
the schedule keeps firing and the run history shows only failures.

The consequence to plan for is that **rebuilding the file is not the job's job.**
If its content is generated, regeneration is a script away. If it is
hand-authored, it is unrecoverable once swept — and there is no honest partial
recovery, because writing a replacement means authoring content the account
owner wrote, then publishing it under their name. When that happens, stop and
hand it back rather than substituting a generated version.

Two durable consequences for how a job is set up:

- **Put input files where cleanup does not reach them.** A shared scratch or
  cache directory is swept by age; a directory under the agent's own state tree
  that only this job references is not. See the disk-hygiene skill's rule about
  excluding by path rather than by age.
- **Check the inputs exist before firing.** `cronjob_manage(action='list')`
  shows `last_error`; a job whose recent history is a run of identical
  failures is usually a missing input, and firing it again reproduces the same
  error after a full wait.

## Firing a job on demand: read the failure first

`action='run'` fires immediately in the background and hands back a delegation
id, so the answer arrives later as a new message. Two things decide whether
firing is even worth it:

- **A job whose last several runs failed for the same environmental reason will
  fail again for that reason.** Read `last_error` and `last_status` from
  `action='list'` first. A quota or rate-limit error that the user has just
  resolved is different from one they have not — and firing into an unresolved
  one burns the wait for nothing.
- **Only the scripts that do not depend on a missing input can be fired now.**
  When a job's input file is gone, separate the schedule's jobs into the ones
  that can run and the one that cannot, and report the split rather than firing
  everything and letting some fail.
- **Fire the group's leader first and wait for it.** If several jobs share one
  browser or lock, firing them together produces the worst outcome of all:
  the first one's state is unreadable while the second one types into it.
  Fire one, confirm it is progressing, then queue the rest.

  A `run` that returns "already being fired by the scheduler" means a previous
  fire is in flight — not that nothing will happen. Check the job's state file
  for progress rather than firing again, because a second run of an
  idempotent-by-state queue publishes the NEXT item early instead of
  duplicating the current one.

  When the ordering matters and you are not going to sit in the conversation
  waiting, a short one-shot job that polls for the lock to clear and then fires
  the next one is more reliable than an in-turn sleep: the poll survives your
  turn ending. Give it a bounded number of attempts and have it report rather
  than force a start if the wait runs out.
- **An `action='run'` prompt is transient context, and that is where campaign
  consent goes.** Pass what the job's own prompt would let a careful agent
  infer anyway — that the target count and schedule are the user's decision
  and are not to be re-litigated mid-run. A bare `run` of a job whose author
  declined its scale would otherwise re-run that refusal on every tick.

**Watch a running job's own state file to confirm progress, rather than
polling the delegation.** An agent-mode job updates its input or state file as
it works, so two samples of that file seconds apart answer "is it moving?"
without touching the job:

```python
import json, time, pathlib
p = pathlib.Path(state_file)
a = json.loads(p.read_text())
time.sleep(45)
b = json.loads(p.read_text())
print(len(a[sids]) , "->", len(b[sids]))
```

Progress plus a live lock file is enough to know the run is healthy. Silence
with no process behind it means it died — check the script's own output, not
the delegation's eventual message.

Two jobs sharing one browser, one profile, or one lock cannot run concurrently —
they interleave on the same state. Fire them in sequence.

## A run that reads external content needs that content checked in, not recalled

When a job composes posts from material the agent regenerates each run, the
regeneration is part of the job and can be re-derived. When the material is
hand-written copy that happened to live in a deleted file, there is no source
left to read — and that is a blocker to report, not a prompt to write
replacement copy, even when the format and the subject matter are obvious.

**Ask which it is before declaring the file unrecoverable.** The distinction
that decides the answer is whether the content is *derivable* from something
that still exists:

- Source is in a **repository** the job can read → regenerating is ordinary
  work. Point the prompt at the read commands and let it compose from them.
- Source is an earlier draft **of this same account's posts** → regenerable
  too, and the account owner has usually delegated exactly that.
- Source is copy the user **wrote and approved by hand**, with no surviving
  original → authoring replacements publishes new claims under their name.

So "the queue file is gone" is not a terminal fact. Exhaust the derivable
cases before reporting a blocker, and ask the user only for the case that
genuinely has no source. The cost of asking is one turn; the cost of guessing
wrong is publishing unreviewed content under someone's account.

**Regenerating from source is the fix; freezing today's facts into the prompt
recreates the same loss one level up.** When you replace a lost queue with live
reads, the tempting repair is to paste the facts you just read — version
numbers, crate counts, member names — into the prompt so the firing agent does
not have to go looking. That is the same snapshot with a longer shelf life: it
goes stale at the next release, and nothing in the prompt will notice, because
a prompt that states a version reads as authoritative. The prompt's job is the
**read commands and the read-before-writing rule**:

```
git -C ~/code/<repo> fetch origin master
git -C ~/code/<repo> show origin/master:README.md
git -C ~/code/<repo> show origin/master:Cargo.toml
```

plus "if a read fails, say so and skip that project rather than writing copy
from memory". If the prompt must know *which* projects exist, have it ask a
module that derives that list from the same real data, not a name you typed.

Derive eligibility too rather than naming exclusions: a project whose last push
is older than a fortnight is not a promotion target, and a freshness check
against `git log -1 --format=%ct origin/master` retires that set automatically
instead of leaving a hand-maintained "do not promote X" line that outlives the
reason it existed.

**An allowlist, a selector or a state file derived from real data fails the
same way as one written by hand — and fails at import time.** Rewriting it as a
computed value is only half the fix; any constant derived from it that is built
when the module loads captures the value from *before* the first read, which is
the staleness you just removed. Build derived constants at call time or cache
them explicitly after the read, and grep the module for every consumer.

**Storing the input under the agent's own state tree** removes the question
entirely for next time — see the disk-hygiene skill on excluding by path
rather than by age.

## Writing the job's prompt, and the skill behind it

A scheduled job's prompt and the skill its scripts live in are written together
and drift apart, so two habits keep them honest: put a job's target count,
schedule and scope in the **prompt**, and keep the **skill** to the procedure
and the checks. Encoding a quota or a cadence as a standing rule in the skill
makes the skill contradict the next request that changes it, and the agent is
then stuck between violating the skill and ignoring the user.

`references/what-does-not-belong-in-a-skill.md` covers this and the adjacent
traps — writing a model's current limit as a permanent rule, generalising one
incident into a prohibition, and patching a wrong rule by appending a
correction instead of editing the sentence that misled. Read it before adding a
rule to any skill.

## Reporting a scheduled run

Report what the script's own output said, never a re-derivation from context.
For a long run, the count is partial until the slow part reports.
