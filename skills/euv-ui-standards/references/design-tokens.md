# euv design tokens

Single source: `ui/src/style/var/fn.rs` (light + dark) and `ui/src/style/css/fn.rs`
(reset + keyframes, injected by `inject_app_global_css()`). Never hardcode a value
here — reference it with `var!(token)`.

Regenerate the real token list from source rather than trusting this table:

```bash
grep -oE '^\s+[a-z0-9-]+:' ui/src/style/var/fn.rs | tr -d ' :' | sort -u
```

## Colour — monochrome

Black/white only; shadows and scrollbars are black/white alpha. A coloured token
is a design-system violation.

| token | light | dark |
|---|---|---|
| `background` | `#ffffff` | `#000000` |
| `foreground` | `#000000` | `#ffffff` |
| `muted-foreground` | `#000000` | `#ffffff` |
| `accent` | `#000000` | `#ffffff` |
| `accent-muted` | `#ffffff` | `#000000` |
| `border` | `#000000` | `#ffffff` |
| `text-on-accent` | `#ffffff` | `#000000` |

`muted-foreground` equals `foreground` in value but is a distinct semantic role
(secondary text / placeholder).

### Overlay / scrim alpha

`bg-overlay` is the scrim behind modals, drawers and floating layers. It is
**not** the `background` token, and **never override it inside a page** — change
the framework token instead, or the monochrome system breaks.

**Perceptual rule:** on a `#000` page any scrim brighter than `#000` reads as
"white". Users reject ≥30 RGB units of lift as a white halo and cannot
distinguish <15 units from the page. The sweet spot is ~20 RGB units of lift,
with the modal panel itself staying at `background` so the panel reads as a
deeper hole than its scrim.

- **Dark mode must never use `rgba(0,0,0, X)`** — invisible on a `#000` page.
  Use a white-tinted alpha.
- **Never go solid** — a solid scrim hides the content it is meant to dim.
- One token edit in `ui/src/style/var/fn.rs` reaches every overlay consumer.


## Spacing

Base scale: `space-2xs` 2 · `space-xs` 4 · `space-sm` 8 · `space-md` 12 ·
`space-lg` 16 · `space-xl` 20 · `space-2xl` 24 · `space-3xl` 32 · `space-4xl` 40 ·
`space-7xl` 80.

**Prefer composite tokens** — they encode intent: `gap-section` 16 ·
`gap-component` 12 · `gap-element` 8 · `gap-inline` 8 · `page-block-gap` 24,
each with a `-mobile` variant (12 / 10 / 20).


## Typography

No web fonts: `system-ui, -apple-system, sans-serif`; code uses
`ui-monospace, monospace`. Steps `font-xs` .75rem · `font-sm` .875rem ·
`font-base` 1rem · `font-md`/`lg` 1.125rem · `font-xl` 1.25rem · `font-2xl` 1.5 ·
`font-3xl` 1.875 · `font-4xl` 2.25 · `font-5xl` 3 · `font-6xl` 3.75.
`font-smoothing: antialiased`, `text-rendering: optimizeLegibility`.


## Radius, shadow, motion, scrollbar

Effectively `border-radius: 0px` — hard edges. The only round shapes are
functional: slider thumbs (`50%`, track `3px`) and `c_spinner`.

Never hand-write a CSS `box-shadow`; check the shadow tokens first
(`shadow-sm`, `shadow-modal`, `shadow-drawer`, `shadow-accent-sm/lg`). Dark
theme shadow alphas are white, not black.

### Motion

Global keyframes from `inject_app_global_css()`: `euv-spin` (rotate 0→360),
`euv-fade-in` (opacity 0+4px → 1+0), `euv-pulse` (scale 1↔1.15), `euv-progress`
(width 0%→100%), `euv-scale-in-modal` (opacity + translateY(24) scale(.95) → 1).

Transition tokens: `duration-fast` .15s · `duration-normal` .2s ·
`duration-slower` .4s · `duration-overlay` .2s · `duration-modal-overlay` .15s ·
`duration-modal-content` .3s. Easings: `ease-out cubic-bezier(.4,0,.2,1)` ·
`ease-in cubic-bezier(.4,0,1,1)` · `ease-in-out` (same as out) ·
`ease-bounce cubic-bezier(.34,1.56,.64,1)`.

Write transitions as
`format!("{property} {duration} {ease}", var!(duration-fast), var!(ease-out))`.

### Scrollbar

Desktop `::-webkit-scrollbar { width: 6px }`, square thumb, translucent
black/white by theme. Hidden under the mobile breakpoint.


## Global reset

```
*, *::before, *::after        { box-sizing: border-box }
h1..h6,p,ul,ol,dl,dd,figure,blockquote,pre,hr { margin:0; padding:0 }
a                            { color: inherit; text-decoration: none }
button                       { appearance:none; border:none; padding:0; margin:0;
                               background:transparent; font:inherit; cursor:pointer }
input,textarea,select         { font:inherit; background:transparent; border:none;
                               outline:none; appearance:none }
img,svg,video,canvas,audio,iframe,embed,object { display:block; max-width:100% }
strong,b                      { font-weight:700 }  em,i { font-style:italic }
code,pre,kbd,samp             { font-family: ui-monospace, monospace }
:focus-visible                { outline: none }   /* focus shown via border colour */
```

**Mobile inputs must stay 16px** — a smaller `font-size` makes iOS zoom on focus.
