# The audit half and the fixer half are different tools

Applies to any script that both **reports** violations and **rewrites** files to
fix them. Related: §5 hooks, and the rule that a fixer tested only on clean
input has never run its rewrite path.

## The failure: a clean report while the tree is being corrupted

A doc-comment fixer was a pure regex line-scan with no raw-string awareness, so
it parsed WGSL entry points inside `r#"…"#` literals as undocumented Rust
functions and wrote **64 doc comments into the shader source**. The companion
checker, which blanks string bodies before matching, found nothing wrong.

**77 `///` lines sat inside raw strings and the audit reported zero findings.**
The damage was invisible precisely because the output looked like success — the
worst failure shape, since a reader who sees "audit passes" concludes the file
is clean.

`///` is not valid in that language at all. It survived only because the shader
parser happened to treat `//` as a line comment: inert by luck, not by
construction, and one stricter toolchain away from a build break. Note the
provenance — it entered in an early commit and was still present several
commits later, invisible to every gate in between.

## Rules

- **Audit the two halves separately.** For each, ask what it can *misread*, not
  just what it can miss. A reporting bug produces a false pass; a rewriting bug
  produces silent damage, and only the second is unbounded.
- **Fix the misparse; never weaken the check to match the buggy behaviour.** The
  fix is a lexical scanner for raw-string spans that skips line/block comments,
  normal strings, char literals and lifetimes — so an `r#"` appearing inside a
  string cannot fake a span. Wire it into **every** call site, including any
  post-insert re-scan the fixer performs on its own output.
- **Prove the rewrite half on input that forces a rewrite.** Exercised on a
  compliant tree it only ever runs its no-op path.
- **After the fix, confirm the check did not go blind.** A scanner that now
  skips raw strings must still flag a synthetic undocumented Rust `fn`, and
  genuinely-clean files must still audit clean.
- **If the safe fix is non-trivial, make the fixer refuse to edit spans it
  cannot parse** rather than edit them.
- **Diff after any tool rewrites source.** The signature is a diff landing where
  no semantic change was possible.
- **Never reason "it parses, so it is harmless."** Ask whether the language's
  comment syntax made it inert, and record that the survival was contingent.

## Corollary: split a count before deleting to it

Told "77 bad lines", a child found 64 machine-generated junk and 13
hand-written engineering notes, deleted the junk, and **kept the notes** — and
was right to. The 13 documented the two conventions that had already cost this
project real time: an axis direction that flipped a scene upside down, and a
depth domain that differed from the source API's. Deleting them would have
destroyed the record *and* left the function undocumented, so the tool would
simply re-inject.

When your count and a child's split disagree, read what the child kept before
accepting the split. Distinguishing junk from hand-written is a provenance
judgement only the child has evidence for, and the hand-written half is often
the more valuable one. Bulk-deleting to a round number is how the knowledge is
lost.
