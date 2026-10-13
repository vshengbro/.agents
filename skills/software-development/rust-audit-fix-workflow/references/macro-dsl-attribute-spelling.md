# Macro-DSL attribute spelling: conditional braces, and the bulk-edit trap

Applies to `html!` and any hand-rolled declarative macro where an attribute value
is syntactically more than "an expression".

## A static value is a bare ident, not a braced expression

```rust
class: CLASS_FEATURE_CARD          // static content — bare ident
class: { CLASS_FEATURE_CARD }      // braced expression form
```

Braces select the *braced-expression* form. A `clippy` suggestion to remove them
is usually correct for static content — and applying it in bulk usually breaks
the build, for a reason that has nothing to do with the line you edited.

## The one shape where braces are required

The element's immediately next child is a `{ ... }` text node:

```rust
div {
    class: { CLASS_FEATURE_CARD_ICON }   // required
    { feature.icon }
}
```

A bare ident followed by `{` reads as one continuing expression, the attribute
list never ends, and the build fails:

```
error: expected `,`
  --> home_page/view/fn.rs:150:32
   |
150 |                         feature.icon
   |                                ^
```

**The error points at the line inside the text child, not the class line.** That
misplaced location is the whole reason this misreads: it looks like the text node
is broken. It is not — the identical child compiles once the class keeps its
braces. Confirm by restoring the braces on that one site and recompiling.

## Read untouched precedent first

Never treat an `attr: { CONST }` as necessary without checking neighbours in the
same file. Existing `class: c_page_container()` lines disprove "this DSL requires
braces" in one glance, and they cost nothing to look at. A sweep that hoists
constants tends to add braces everywhere, so every one it adds is a fresh
`unnecessary braces around function argument` warning.

## Never run `cargo clippy --fix` over macro-DSL arguments

It cannot see the conditional requirement and will strip braces that were load-
bearing. If the residual warnings are the text-child sites above, report the
count in the commit message instead of silencing with `#[allow]` — the lint is
correct for ordinary Rust and wrong only at those positions.

# One failed bulk edit does not establish a syntax requirement

Strip every site with one regex, get a compile error, conclude "the DSL requires
this construct". This is the most expensive wrong turn available, because the
conclusion then ships as fact in a PR description.

Before believing a bulk edit failed:

1. **Untouched precedent in the same file.** Settles it in one glance. Do this
   first, before touching anything.
2. **Bisect one site at a time.** If N sites give some successes and some
   failures the rule is *conditional* — keep the successes, diagnose the
   failures. "Five of nine compiled" is the finding, not a nuisance.
3. **`git diff` your own edit for collateral damage.** A multi-line pattern, or
   one that captures a neighbouring `{ ... }`, rewrites lines you never intended
   — and *that* is the real error, not the syntax.

**A compile error reported at a line you did not edit is a parser cascade, not a
defect at that line.** Read the first error and re-read the source around it
before editing anything else. When the error location and the line you changed
disagree, suspect the edit before the language.

## Line-anchored patterns for line-oriented edits

A `perl -0pi -e 's/\{ \n expr \n \}/…/'` (or any `-0` / `re.DOTALL` pattern) with
a loose `\s*` swallows an adjacent multi-line block. The failure then presents as
a syntax error in the block you were only reformatting, and the reflex "fix the
block" deletes the expression the pattern was meant to preserve.

Anchor so a hit can only ever be one whole line, and assert the changed-line
count equals what you enumerated:

```bash
perl -i -pe 's/^(\s*attr: )\{ (CONST) \}$/$1$2/ if /^\s*attr: \{ CONST/' file.rs
git diff --stat -- file.rs   # must equal the enumerated site count
```

Same rule as a helper rename: **construct a pattern the target cannot match
incidentally**, then check the count.
