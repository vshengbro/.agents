# Token migration skips pseudo-elements and absolutely-positioned children

Applying one unified edge-distance token across a component library is the
standard fix for "the left and right insets don't match". Done once, it
silently leaves that component's decorations behind.

## The bug class

You migrate an element's `padding` (or `left`/`right`) onto a design token.
The element you were looking at is now correct everywhere. But the hairline
dividers, gradient rules, or carets that share its box still carry the old
value — and the component renders a rule visibly wider or narrower than the
content it frames.

**Start by deciding the role split, not the value.** One universal gutter
looks tidier and fails: a drawer that must sit 16px from the screen edge on
mobile cannot also read the desktop nav token. Ship one token per role and
let the media query choose between them:

| Role | Typical | Consumers |
|---|---|---|
| shell gutter (desktop) | 28px | top bar, main content |
| shell gutter (mobile) | 16px | same, under a max-width query |
| nav / drawer interior | 20px | drawer + sidebar items, footer |
| bottom floating | 20px | FAB, log button |

A floating element anchored to two axes (bottom **and** right) is a separate
role from the shell gutter, even when the numbers happen to match today.

**Keep the pre-migration token names as aliases** pointing at the new tokens
rather than deleting them. They cost one line each and keep every external
consumer compiling; deleting them trades a tidy diff for a breaking change.

**Cause: nothing inherits the parent's padding.** Two categories get missed
because neither shows up in a search for the property you changed:

- `::after` / `::before` nested inside the same rule block — they carry their
  own `left` / `right` / `bottom`.
- a sibling `position: absolute` element whose offsets were hand-tuned to
  match the parent's padding.

No single computed value looks wrong. You have to compare the decoration
against the content, which is exactly the check nobody runs on the first pass.

**Responsive widens the blast radius.** Adding `@media (max-width: 767px)` to
the parent's padding but not to its `::after` yields a component that is
correct on desktop and visibly broken on mobile only — so a single-viewport
verification reports success.

## The rule

**When you change an element's inset to a token, migrate every child that
expresses the same distance in the same edit.** Inside the block you touched,
these are part of the one change:

```rust
pub c_nav_header {
    padding: format!("{} {}", var!(space-xl), var!(edge-gutter-nav));
    @media ((max-width: 767px)) {
        padding: format!("{} {}", var!(space-xl), var!(edge-gutter-mobile));
    }
    ::after {                              // ← same change
        left: var!(edge-gutter-nav);
        right: var!(edge-gutter-nav);
        @media ((max-width: 767px)) {      // ← same change
            left: var!(edge-gutter-mobile);
            right: var!(edge-gutter-mobile);
        }
    }
}
```

## The grep that catches what you forgot

The pseudo-elements live *inside* the block you edited, so any of these
surfaces them:

```bash
# every pseudo-element + absolute box in the file you changed
grep -nE '::?(after|before)|position: "absolute"' <file>

# then confirm each offset uses the token you migrated to, not a raw px
# value or a *different* spacing token — the classic miss is left/right
# migrated while bottom stayed hardcoded
grep -nE '(left|right|bottom|top):' <file>
```

A leftover `space-lg` / `space-xl` sitting next to your new token reference
in the same rule is the tell.

## Verifying

Measuring only the parent proves nothing about the divider. Probe the
decoration's own box and compare it to the content's inset, on **every**
viewport the component renders at:

```python
info = pg.evaluate("""() => {
    const hdr = document.querySelector('.c_nav_header');
    const cs = getComputedStyle(hdr);
    const after = getComputedStyle(hdr, '::after');
    return {
        padLeft: cs.paddingLeft, padRight: cs.paddingRight,
        afterLeft: after.left,  afterRight: after.right,
        matches: after.left === cs.paddingLeft
              && after.right === cs.paddingRight,
    };
}""")
# Verified only when `matches` is true. A 4px divergence is visible in review.
```

For a sibling absolute element, compare its rect against the host container's
and assert the *relative* insets are equal:

```python
const host = document.querySelector('.c_mobile_nav_drawer').getBoundingClientRect();
const logo = document.querySelector('.c_mobile_nav_drawer_header a').getBoundingClientRect();
const x    = document.querySelector('.c_mobile_drawer_close_button').getBoundingClientRect();
({ logoLeft: logo.left - host.left,
   closeRight: host.right - x.right,
   aligned: Math.abs((logo.left - host.left) - (host.right - x.right)) < 1 })
```

Do **not** assert this with a raster ink-scan — a full-bleed highlight
background, a centred glyph, and a letter's side bearing all produce
plausible-but-wrong "first inked column" values that read as misalignment.
Assert on `getBoundingClientRect()` / `getComputedStyle()` relationships.

**Subtract the container's border before declaring an off-by-N.** A panel with
a 2px border and 20px padding puts its first child at `x=22`, which is
correct. Likewise a gradient rule's transparent end makes its faint first
pixels start later than the element's real `left` — a per-row brightness
profile or a direct read of the computed `left` settles it, and pixel
thresholding does not.

**When vision is unavailable, that is not a blocker.** Vision timeouts are an
availability failure, not a measurement failure: box geometry plus a per-row
brightness scan answers the same question. Keep the probe as a reusable script
so a re-check is one command rather than a hand-edit per viewport.

## Ordering

Migrate parent **and** decorations, then rebuild, then verify on every
viewport, then only then report. A verifier that inspects the elements you
edited — and nothing else — will pass on a component whose dividers are 4px
wrong, and that defect ships.
