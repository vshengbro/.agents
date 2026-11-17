# euv design tokens

Two owners, never one. The **theme** class (`c_theme_light` / `c_theme_dark`)
owns the semantic mapping and the universal structure scale — spacing, motion,
layout — and lives in `ui/src/style/var/theme/fn.rs`. The **scheme** class
(`c_scheme_<name>`) owns the colour roles, the radius scale, the shadow ramp,
the type ramp, the tracking and case treatments and the control heights, and
lives in `ui/src/style/var/scheme/<name>/fn.rs`. The keyframes come from
`ui/src/style/css/const.rs` via `inject_app_global_css()`; the element reset
is the `c_app_root` block in `ui/src/style/class/shell/fn.rs`.

Never hardcode a value here — reference it with `var!(token)`.

Regenerate the real token lists from source rather than trusting this table:

```bash
# the theme's own tokens (spacing, motion, layout, semantic mapping)
grep -oE '^\s{8}[a-z0-9-]+:' ui/src/style/var/theme/fn.rs | tr -d ' :' | sort -u
# one scheme's tokens (colour roles, radius, shadow, type, control heights)
grep -oE '^\s{8}[a-z0-9-]+:' ui/src/style/var/scheme/shadcn/fn.rs | tr -d ' :' | sort -u
```

The theme file holds two class blocks (`c_theme_light`, `c_theme_dark`), so its
list is the union of both — 105 unique names, of which `side-indent` and
`side-indent-num` exist only in the light block. The scheme file holds one
block, so its list is the scheme's own token set.

## Schemes

The system is **not** monochrome. `theme-monochrome` is one of the seventeen
schemes — `ui/src/style/var/scheme/` holds one directory each: antdesign,
bootstrap, cupertino, daisyui, fluent, geist, heroui, linear, mantine,
material, monochrome, notion, park, radix, shadcn, stripe, supabase — and each
is selected by a `theme-<name>` feature in `ui/Cargo.toml`. The built-in
selection chain lives in `ui/src/style/var/theme/fn.rs`
(`selected_scheme_class()`); more than one feature may be on at once — a
workspace-wide `--all-features` build turns them all on — so the order in
that chain decides which one wins.

Every scheme defines **the same 103 tokens**, and `ui/tests/theme` fails the
build if a scheme drops one, if the theme and a scheme ever own the same
token, if the registry reads a token nobody defines, or if a token is
orphaned. The test compares the shadcn scheme against the other sixteen by
name and count, so a scheme that adds or drops a token fails the build.
Copy `scheme/shadcn/fn.rs` as the shape reference; never copy its values.

## Colour

The colour values are per scheme. In the `shadcn` scheme, for example:
`role-background-light` `#ffffff` / `role-background-dark` `#0a0a0a`,
`role-foreground-light` `#0a0a0a` / `role-foreground-dark` `#fafafa`,
`role-border-light` `#e5e5e5` / `role-border-dark` `rgba(255, 255, 255, 0.10)`,
`role-ring-light` `#a1a1a1` / `role-ring-dark` `#737373`,
`role-muted-foreground-light` `#737373` / `role-muted-foreground-dark` `#a1a1a1`.

The theme reads them through `var!("role-…")`, so the generated CSS is
`var(--role-background-light)` rather than a literal — that indirection is
what lets one theme class serve every scheme.

### Overlay / scrim alpha

`bg-overlay` is the scrim behind modals, drawers and floating layers. It is
**not** the `background` token, and **never override it inside a page** —
change the framework token instead. The theme sets it directly
(`rgba(0, 0, 0, 0.45)` light, `rgba(0, 0, 0, 0.65)` dark).

**Perceptual rule:** on a `#000` page any scrim brighter than `#000` reads as
"white". Users reject ≥30 RGB units of lift as a white halo and cannot
distinguish <15 units from the page. The sweet spot is ~20 RGB units of lift,
with the modal panel itself staying at `background` so the panel reads as a
deeper hole than its scrim.

- **Dark mode must never use `rgba(0,0,0, X)`** — invisible on a `#000` page.
  Use a white-tinted alpha.
- **Never go solid** — a solid scrim hides the content it is meant to dim.
- One token edit in `ui/src/style/var/theme/fn.rs` reaches every overlay consumer.

### Media and drawing surfaces

`surface-media` (black) and `surface-drawing` (white) are **scheme** tokens,
not theme tokens — they carry the same value in light and dark, so a camera
feed and a canvas letterbox stay black and a drawing preview stays white
regardless of the mode.

## Spacing

Base scale: `space-2xs` 2 · `space-xs` 4 · `space-sm` 8 · `space-md` 12 ·
`space-lg` 16 · `space-xl` 20 · `space-2xl` 24 · `space-3xl` 32 · `space-4xl` 40 ·
`space-7xl` 80. Two half-steps sit between them: `space-xs-sm` 6 ·
`space-sm-md` 10.

**Prefer composite tokens** — they encode intent: `gap-section` 16 ·
`gap-component` 12 · `gap-element` 8 · `gap-inline` 8 · `page-block-gap` 24.
Where a mobile variant exists it is a separate token:
`gap-section-mobile` 12 · `gap-component-mobile` 10 ·
`page-block-gap-mobile` 20. `gap-element` and `gap-inline` have no mobile
variant.

## Typography

No web fonts: `ui-sans-serif, system-ui, sans-serif, …`; code uses
`ui-monospace, SFMono-Regular, Menlo, …`. The steps are **scheme** tokens:
`font-xs` .75rem · `font-sm` .875rem · `font-base` 1rem · `font-md` 1.125rem ·
`font-lg` 1.25rem · `font-xl` 1.5rem · `font-2xl` 1.875 · `font-3xl` 2.25 ·
`font-4xl` 3 · `font-5xl` 3.75 · `font-6xl` 4.5.
`font-smoothing: antialiased` and `text-rendering: optimizeLegibility` are
set on the shell class, not on a token.

## Radius, shadow, motion, scrollbar

The radius and shadow ramps are **scheme** tokens. In `shadcn`:
`radius-xs` 2px · `radius-sm` 6px · `radius-md` 8px · `radius-lg` 10px ·
`radius-xl` 14px · `radius-2xl` 16px · `radius-full` 50%; and a five-step
shadow ramp —
`shadow-xs` · `shadow-sm` · `shadow-md` · `shadow-lg` · `shadow-xl`. There is
**no** `shadow-modal`, `shadow-drawer` or `shadow-accent-*` token: an overlay
picks a step from the same ramp. Never hand-write a CSS `box-shadow`; check
the ramp first.

### Motion

Global keyframes from `inject_app_global_css()`: `euv-spin` (rotate 0→360),
`euv-fade-in` (opacity 0+4px → 1+0), `euv-pulse` (scale 1↔1.15),
`euv-skeleton-pulse` (opacity .55↔1), `euv-progress`
(width 0%→100%), `euv-scale-in-modal` (opacity + translateY(24) scale(.95) → 1).

Transition tokens: `duration-fast` .15s · `duration-normal` .2s ·
`duration-slower` .4s · `duration-overlay` .2s · `duration-modal-overlay` .15s ·
`duration-modal-content` .3s · `duration-press` .1s. Easings:
`ease-out cubic-bezier(.4,0,.2,1)` · `ease-in cubic-bezier(.4,0,1,1)` ·
`ease-in-out` (same as out) · `ease-bounce cubic-bezier(.34,1.56,.64,1)` ·
`ease-accelerate cubic-bezier(.3,0,.8,.15)`. The interaction layer also
carries `press-scale` .97.

Write transitions as
`format!("{property} {duration} {ease}", var!(duration-fast), var!(ease-out))`.

### Scrollbar

Desktop `::-webkit-scrollbar { width: 6px }` with a `radius-full` thumb and a
transparent track; Firefox gets `scrollbar-color` (thumb, track) — there is no
`scrollbar-width: thin` rule. Hidden under the mobile breakpoint
(`scrollbar-width: none`, width 0).

## Global reset

The element reset is the `c_app_root` block in
`ui/src/style/class/shell/fn.rs` — it is a class, not a stylesheet
constant:

```
*, *::before, *::after        { box-sizing: border-box }
h1..h6,p,ul,ol,dl,dd,figure,blockquote,pre,hr { margin:0; padding:0 }
ul, ol                         { list-style: none; padding:0; margin:0 }
a                              { color: inherit; text-decoration: none }
button                         { appearance:none; border:none; padding:0; margin:0;
                                 background:transparent; font:inherit; color:inherit;
                                 cursor:pointer; outline:none }
input[type=text|number|email|password|search|tel|url]
                               { appearance:none; border-radius: radius-sm }
textarea                       { appearance:none; resize:vertical;
                                 font-family:inherit; border-radius: radius-sm }
select                         { appearance:none; background-image:none;
                                 border-radius: radius-sm }
img,svg,video,canvas,audio,iframe,embed,object { display:block; max-width:100% }
table                          { border-collapse: collapse; border-spacing: 0 }
hr                             { border: none; margin: 0 }
:focus-visible                 { outline: none }   /* focus shown via the ring */
: focus:not(: focus-visible)   { outline: none }
h1..h6                         { font-weight: inherit; font-size: inherit }
strong,b                       { font-weight: font-weight-bold }  /* 700 */
em,i                           { font-style: italic }
code,pre,kbd,samp              { font-family: font-family-mono }
```

`inject_app_global_css()` injects a *separate*, zero-specificity reset —
`:where(*), :where(*)::before, :where(*)::after` plus the list, media and
form chunks (`APP_GLOBAL_CSS_RESET` / `_ROOT` / `_LIST` / `_MEDIA` / `_FORM`).
That one **retains native focus outlines** (the `browser_reset` test fails the
build if any injected chunk contains `outline: none`).

**Mobile inputs must stay 16px** — a smaller `font-size` makes iOS zoom on focus.
