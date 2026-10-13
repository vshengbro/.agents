# What does not belong in a skill

A skill is standing instructions for doing a **class** of task. That definition
excludes several things that are easy to write into one — usually right after a
session where something went wrong and the reflex is to make the rule permanent.

This file exists because those rules are hard to write correctly by intention.
Each one below is a rule that is natural to add, looks responsible, and is
wrong.

## Do not encode a limit of the model or the moment as a rule

The reach of the current model is not a property of the task. It moves, and a
rule written against it outlives its own reason — the next session is more
capable and still constrained by prose written when it was less.

The tell is the rule's own wording. If it explains itself with a capacity
claim rather than a correctness one — "this is a lot of content", "this is
beyond what can be done in one turn", "an agent cannot reliably do this" — it
is a statement about capacity, not about correctness. **If the work is wrong it
is wrong at any volume, and if it is right it is right at any volume**, so there
is nothing for a volume rule to protect.

Write the procedure and the evidence standard instead, and let the model be as
capable as it is that day. Concretely: instead of "refuse campaigns at scale",
write "each item declares its target and is checked against it, and nothing is
padded to hit a number" — which is true regardless of what the model can do.

## Do not write the user's decision into the skill

When the user sets a target count, a schedule, or a budget, **that is the input
to the task**, and it belongs in the job, the queue, or the request.

Encoding it as a standing rule makes the skill contradict the next request that
changes it, and the agent is then stuck between violating the skill and ignoring
the user — with no reading under which both can be satisfied. The user's
decision is read at the time it applies, not pre-judged once in prose at
authoring time.

The distinction: a skill says *how to check the work*; the request says *what
work*. A skill that contains a number, a quota, or a cadence has taken the
second job and will lose it.

## Do not generalise one incident into a prohibition

When a session goes wrong, there are two things to extract and they are not
equal:

- **The check that would have caught it** — read the target before acting,
  verify the result rather than the click, clear the field and assert empty,
  exclude by path rather than by age. This generalises and belongs.
- **The refusal, the apology, or the standing prohibition** that followed. It
  encodes one outcome as a permanent constraint and belongs nowhere.

The second is the reflex because it feels like safety. It is a permanent cost
for a one-time repair.

## Fix the sentence that misled; do not append a correction

If a rule in a skill was wrong, edit it in place. A skill that accumulates
`UPDATE: actually…` lines beneath the original now holds two rules, and a model
reading it has no way to know which one wins — it will apply whichever it
reaches first, which is usually the stale one.

The corollary for review: when patching a skill to remove a rule, **delete the
old wording in the same operation**. Leaving it in place is not a smaller edit,
it is a contradiction.

## When a user asks you to remove a rule

Do it as an edit, not as an append. Re-read the skill, find the rule, remove it,
and if it was carrying real weight underneath, write down what it was actually
protecting so that protection can live somewhere valid — usually as a check on
the work rather than as a prohibition on doing the work. Then say plainly what
changed, so the user can tell whether the underlying risk is still covered.