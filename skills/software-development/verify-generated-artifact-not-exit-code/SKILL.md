---
name: verify-generated-artifact-not-exit-code
description: Use when a build exits 0 but output is broken.
license: MIT
metadata:
  version: "1.0.0"
  category: software-development
  hermes:
    tags:
      - verification
      - build-systems
      - codegen
  related_skills:
    - systematic-debugging
    - verifying-against-a-real-gate
    - verifying-before-dispatching-repairs
---

# Verify the generated artifact, not the exit code

## When to Use

Use when any of these hold:

- A build or codegen step reports success but the output is suspected wrong.
- A crash surfaces far downstream from the step that produced the data it reads.
- One fault is reported twice by the same runtime (primary + poisoned instance).
- A config contract changed in one repo and consumers live in other repos.
- You are about to accept "build green" as proof the generated output is valid.

A build that exits 0 proves the tool ran. It does not prove the tool produced
usable output. When a build step GENERATES a data structure that is consumed
later — at runtime, by a deploy, or by a downstream consumer — the validity of
that structure is the real contract, and the exit code does not cover it.

## Why this happens

Validators are usually written to fire while iterating their input:

```
for entry in config_entries:
    if not valid(entry):
        fail(f"bad entry: {entry}")
```

If the input is EMPTY the loop body never runs, every check passes, and the build
exits 0 having produced an empty structure. The failure surfaces downstream, often
far from the build that caused it.

The same shape appears as a silent drop rather than an explicit one:

```
entries = [parse(e) for e in raw if parse(e) is not None]   # filter_map
```

Every malformed entry vanishes with no diagnostic. One typo removes one entry;
remove them all and you get a zero-length list that every downstream check happily
iterates.

**The rule**: any loader that validates user-supplied config must assert
non-emptiness explicitly and must name the offending entry — its index or
identifier, plus the specific key that failed. A validator that only fires inside
its loop cannot catch "there was nothing to validate". A build error is the only
place that failure is cheap to fix; the alternative is a crash at the point of
use.

Prefer accumulating into a `Result` that names the bad entry over an `Option`
that a later `filter_map` discards silently.

## Verification procedure

1. Locate the generated artifact and read it. Build scripts emit into a scratch or
   output directory — find the newest file matching the generated name rather than
   assuming a fixed path.
2. Assert the structural invariants directly: non-empty, contains every element
   you configured, no duplicates or route/identifier collisions.
3. Where the output is consumed at RUNTIME, a static read is not the last word —
   serve it and exercise the real entry point. An HTTP 200 on the entry document
   proves almost nothing when the page is hydrated by a compiled bundle; a runtime
   panic renders a served page perfectly happily.
4. When one generator feeds several downstream repos, verify each consumer
   separately. The same generator can produce a valid artifact for one config
   shape and a broken one for another.

## Symptom signature worth recognising

When one fault reports twice — a primary error, then a secondary "unreachable" /
poisoned-instance / "module trapped" error from the same runtime — the second is a
consequence, not a second bug. Investigate the primary and ignore the echo;
chasing the second wastes the debugging budget.

## Where the data must come from

Trace the value back to its origin in the generator before concluding anything
about a runtime crash. A crash that appears at use-time is frequently caused by a
missing or renamed INPUT KEY, not by the code at the crash site. Reading the
parser that consumes the config answers this faster than reading the consumer, and
it points at the file that needs fixing.

When a generator and its consumer live in different repos, the input contract
belongs to the generator — fix the config there and check the consumer for
assumptions that the old contract allowed.

## Cross-repo ordering

When the shape of a shared contract changes and downstream repos are updated to
match, land the STRICTER side first, then fan out the consumers. The reverse order
leaves consumers written against a contract the producer does not yet enforce, and
the window in between is where the breakage ships. State explicitly which order is
required and make the earlier PR's merge a precondition of the later one.

## References

- `references/euv-docs-site-config.md` — the euv-docs `locales:` frontmatter
  contract: which keys are required (`prefix`, `dir`, `label`), why a missing
  `dir` produces a browser panic rather than a build error, how routes are derived
  from locale dirs, and how to verify the generated `docs_gen.rs`. Read this when
  an euv-docs site panics in the browser with `index out of bounds` from
  `router/fn.rs`, or before changing locale prefixes / content directories.

## Do not accept

A green build, a non-empty output directory, or a successful deploy is not evidence
that the generated structure is correct. Read it.