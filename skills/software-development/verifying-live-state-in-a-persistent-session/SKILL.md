---
name: verifying-live-state-in-a-persistent-session
description: 'Use when runtime output contradicts the file it read.'
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [verification, debugging, caching, stale-state, measurement]
    related_skills: [systematic-debugging, verifying-against-a-real-gate]
---

# A measurement tool that survives your edits will re-measure the stale object

## When to Use

Load this when a value produced at runtime disagrees with the source it was read
from — the file is correct on disk but the code reports something else — or when
a measurement is being carried across an edit and its result is being reused.

## The failure

You edit a file. You read the file and it is correct. You run code that reads
the same file and it reports the old value. The natural reaction is to conclude
the file is wrong and "fix" it to match the runtime — which is backwards, and
turns a correct file into a broken one.

Code-execution tools whose variables and imports persist across calls are the
usual source. The module is bound on the first `import`; every later call in
that session reuses the object already in memory, so the edit is invisible to
it. Cached bytecode (`__pycache__`) is the milder sibling of the same cause and
can survive a fresh interpreter in the same directory.

**The tell: the on-disk read and the runtime value disagree about the same
file, at the same moment.** Not a stale build, not a concurrent edit — a
disagreement about one specific value.

## Rule

Verify anything cached at first use in a **fresh process**, never in the session
that populated the cache. One subprocess settles it; the reason it must be a
subprocess and not another call is that the point is to be outside the cache.

```bash
find . -name __pycache__ -type d -exec rm -rf {} +          # the bytecode layer
python3 -c "import mod; print(type(mod.CONST), mod.CONST)"  # a NEW process
```

Compare `type()` as well as the value. A container that should be a tuple and is
a string is a different bug from a value that is merely stale, and printing the
type is what separates them.

## The general form

Anything memoized at first use — an imported table, a parsed config, a
connection handle, a cached lookup, an expensive computation you did not think
to invalidate — keeps serving its first value for the life of the process. When
a runtime value contradicts the source that produced it, re-derive it out of
band before concluding anything about the source. The question is never "is the
file right?" while you are holding a value the file cannot have produced.

## What this is NOT

Not a flaky test, and not fixable by re-running. A flake varies run to run; this
is constant and deterministic, which is why it survives a dozen re-runs and then
sends you editing correct code.

## The browser is a cache you did not ask for

A build artifact's URL usually does not change between builds, so a browser
profile reuses the previous copy and the page runs code that predates your fix.
The symptom is a fix that provably changed nothing, which reads as "the fix is
wrong" and sends you back to editing correct source.

A cache-buster on the **entry page** does not help. `index.html?cb=123` busts
the HTML only; `pkg/app_bg.wasm` is a separate request and is still served from
cache. Turn the cache off **and re-navigate** — the first load is already
served before the override takes effect, so without the reload you are still
reading the old build:

```python
await tab.call("Network.enable")
await tab.call("Network.setCacheDisabled", {"cacheDisabled": True})
await tab.nav(url)          # the reload is the part that matters
```

Byte-comparing served vs on-disk does **not** catch this: both sides are the
same stale-but-internally-consistent copy, so the check passes and hides the
problem. Assert instead on something only the new build contains:

```bash
strings www/pkg/app_bg.wasm | grep -c 'a-literal-only-the-new-build-emits'
```

Non-zero proves the artifact is current; zero means the rebuild never took,
which is a different bug from the one you are chasing. Read the decisive value
out of the **stylesheet/DOM the running page actually has** rather than from the
source file you edited — when a runtime rule contradicts the file you just
changed, the file is the one giving way.

Injected test styles survive a hash-only navigation. A single-page app that
routes on `location.hash` does **not** reload the document, so a
`<style>` element you appended to `document.head` for one measurement is
still there when you "navigate" to the next route and measure again. The
injected rule then silently contaminates the second measurement — often
making an already-fixed state look broken, or a broken state look fixed.

Two habits that prevent it:

- **Re-assert your baseline in the same call as the measurement.** Never
  treat a "BEFORE" number carried over from an earlier call as a control;
  print it again next to the "AFTER" so a surviving injection shows up as
  a mismatch rather than as a result.
- **Serve each build from a fresh port.** `python3 -m http.server <new
  port>` per rebuild gives a new origin, so neither the wasm bundle nor
  the document is reused from the browser cache and no injected `<style>`
  carries over. When the server log shows `304 Not Modified` for the
  bundle, you are reading the previous build no matter what the DOM says.

The general rule is the same one this skill is about: anything cached or
injected for the sake of a measurement outlives the measurement. State
what you injected, and make each measurement environment independent of
the last.

## Your own probes degrade the thing you are measuring

A cache holds a value you did not write. An interactive target — an editor, a
composer, a live input surface — holds **state your probes create**, and each
probe makes the next one measure a different object than the first did. This
is the write-side twin of the sections above, and it is the one that produces
confident false findings.

Measured, one probe series against one editor: probe 1 reported a real
result; probe 5 reported characters from probe 1 still resident in the field;
probes 6 onward returned empty while a different node held the text. The
series then "showed" that two input methods both failed, which was an artifact
of the series, not of either method. Two independent mistakes compounded it —
a selector that picks a different node at read time than at write time, and a
clear operation that removes one block and stops, leaving the rest.

So a probe series carries three obligations:

- **Restart from a known state between probes, and assert the state you
  restarted from.** "Cleared" means length is 0, read back — never "the clear
  loop ran".
- **Identify the target the same way before and after.** If the selection can
  resolve to a different node at read time than at write time, the read
  measures something the write never touched. Assert the identity matches.
- **Attribute residue.** Tag probe text with a unique marker per run, so the
  next read can tell its own leftovers from a pre-existing draft. Without
  that, probe output becomes the next probe's "unattributable state" and the
  series can no longer tell its pollution from what it was investigating.

And the corollary that matters most: **one success is not a result.** When a
measurement of a stateful target contradicts an earlier one, the earlier one
was measuring a fresher target, not a more correct method. Restart the target,
re-run, and only treat a difference that survives the restart as evidence about
the method.

## Before citing a number, re-derive it against the current tree

A gate that passed earlier does not describe the tree as it is now. Re-run the
check you are about to cite, and capture the command's own exit status before
summarizing its output — a filtered count (`build | grep -c error`) prints a
real number on failure and `0` on success with the same exit code, so the count
alone is not a measurement. Report `EXIT=…` and the count as two separate facts.
