# X composer mechanics, measured

What the composer of a logged-in X session actually does when you drive it
programmatically. Every claim here is a measurement; several contradict the
obvious approach, which is why they are written down.

## A reply ceiling is an account property; a post is never limited the same way

Same composer, different ceiling, and the difference is invisible until a send
fails. **Get the account's tier before writing a length gate** — 280 is the
free-tier number, and an account on a paid tier has no reason to be held to it.
Writing 280 into code "to be safe" does not fail loudly: the drafts simply
compress, and the sentence that carried the point is the one that gets cut,
because trimming an argument to fit a budget it did not need spends the
argument for nothing.

This was measured the wrong way round twice. Drafts written to the post limit
— 560 to 1167 characters — read as perfectly reasonable prose and were
unsendable under a free-tier cap; drafts then compressed to 154–280 to satisfy
that cap, and were thin for no reason. The number was never the platform's; it
was a remembered constant in a skill and in a length gate, inherited into
code without anyone checking the account it applied to.

So: the URL is part of the body, not a separate reservation against it, and
the ceiling belongs in the test table as an asserted value so that a wrong
one is a failing test rather than a silently short post. When a real ceiling
does apply, trim by leading with the claim and dropping the tail — a uniformly
shortened argument keeps none of its force. Write the body as discrete
sentences and add them while the running total fits, letting length decide
the cut.

## Two nodes share one testid

`[data-testid="tweetTextarea_0"]` matches two elements. One is the real editor
and carries `class="... public-DraftEditor-content"`; the other is an empty
duplicate. `querySelector` returns whichever is first in document order, and
that changes between renders — so writes land in one node and reads come from
the other. This alone produced writes that vanished, lengths that jumped to 194
or 0 at random, and a click that published a single stray character.

Take the **taller visible** one, then require that focus actually landed on it
before writing. Refuse to act otherwise.

`[data-testid="tweetText"]` is a display layer, not the editor. Never write to
it, and do not read it to decide whether text landed.

## One insertText for the whole body, URL included

2500 characters land in no time, newlines and all. A Premium account posts
long-form and the platform expands past 280 into a thread on its own, so there
is no reason to split a long post or to type it character by character.

**The URL is not special to the editor — it is just text, and it belongs in the
same `insertText` call.** Every attempt to give it its own input path broke the
text:

| Attempt | What happened |
|---|---|
| `Input.imeSetComposition` with the whole URL | strands the URL's first character in the body — the editor reads `…edition。h` against a source of `…` |
| committing it with a second `insertText` | the committed string arrives already formed, so there is nothing left to linkify: plain text, no link element at all |
| pasting it (`Input.dispatchKeyEvent` with `commands:["paste"]`) | inserts, but the platform folds the separator into the host and the sentence reads back as `https://\ncrates.io` |
| typing it character by character | linkification happens mid-stream and the tail is dropped — `https://github.c` was all that survived |

If someone proposes "improving" the URL path, this table is the reason not to.

## It linkifies anything dotted, not just URLs

A bare `crates.io` in prose became a shortener, and the span that was replaced
then read back as a **line break** — so the sentence split in half and two
broken posts went out before this was caught. Write `crates io` in the copy and
reserve the dotted form for the one URL you actually want.

Check the copy *before* typing: refuse any dotted token that is not one of the
URLs you intend.

## The button may not be the one you are looking for

The inline composer mounts `tweetButtonInline` and does not reliably mount
`tweetButton` at all. A lookup that requires `tweetButton` finds nothing on a
composer whose button is right there and enabled — which surfaces as "the
button never enabled" and **silently drops a post whose text matched exactly**.
Accept either testid; prefer the primary one when both exist.

The enabled check and the click must ask the same question. When one looked for
`tweetButton` and the other for either, a post reported as unmatched was
actually ready to send.

## A changed url is not a loaded page

`Page.navigate` resolves and the url is already the new one while the thread
has rendered **zero** articles. Every later step — the ownership read, the
reply click, the target-handle check — then silently operates on the previous
page or on nothing, and the run reports `nothing rendered` on a post that was
there all along. Measured: `goto_status` returned `True` on a page with no
articles at all, and four sends died there before the wait was added.

Require content before returning success:

```python
if pid in now:
    for _ in range(16):
        if (tab.js("document.querySelectorAll('article').length") or 0) > 0:
            return True
        time.sleep(1.4)
    break   # url changed but nothing rendered - retry, do not proceed
```

Assert the url **and** the article count. A url check alone is satisfied by the
navigation having started.

## Reading the result back

Three separate readings, and confusing them is how a good post gets reported as
broken or a broken one as good:

- **In the editor** — `textContent` over the Draft node. Hidden text nodes of
  the platform's own make this read one character long on a perfect post.
- **In an empty editor** — `innerText` reads `"\n"`, the empty DraftEditor's own
  block terminator. An emptiness guard written as `if len(read) > 0: refuse to
  type` therefore refuses on a **virgin composer**, reporting "editor already
  holds 1 chars" and stalling the run before anything is typed.

  The same field biases in opposite directions at the two ends: `innerText`
  **over**-reads an empty editor by one character, `textContent` **under**-reads
  a full one. So pick the read that biases toward *stopping* you for the
  question being asked — `textContent` truthiness (or a whitespace-only strip)
  to ask "is this empty?", `innerText` to ask "is this what I sent?". Never ask
  one question with the field that answers the other.
- **On the timeline** — `tweetText` is **clipped**: it held 204 characters of a
  462-character post with no "show more" control, so a full character compare
  reports a complete post as truncated. Compare the visible text against the
  source *prefix*, and prove the rest by the link card.
- **The link** — the href is a shortener, so the original URL is never in the
  text. The card rendered from it names the destination and is the thing to
  assert on.

Never gate on the raw character count in either direction.

## Whose post is it

The open tab is usually a feed, not your profile. It lists other people's posts
alongside yours, and matching a status id among them returns a real id, real
text and a wrong conclusion. Split what is on screen by author and require the
expected one before claiming anything.

## Replying needs no navigation

Every article on a timeline carries a reply control, and replying is the one
"engage with other people's content" move that stays inside the no-navigation
rule — so reach for it rather than concluding the task is blocked. No
`Page.navigate`, no new tab, no reload; the composer is meant to mount in
place.

**Whether the click actually mounts it is a separate question, and on the
current build it did not.** Measured, in order, on a live timeline:

| Activation | Result |
|---|---|
| `element.click()` | only fires `click`; nothing mounted |
| synthesised `mousedown`+`mouseup`+`click` on the element | nothing mounted — 12s of polling found no new editable element anywhere on the page |
| `el.focus()` then `rawKeyDown` Enter, then Space | focus landed on the control (`document.activeElement === btn`) and X ignored both keys |
| `Input.dispatchMouseEvent` at the control's coordinates | not tried — the project's own gate refuses it, because it is the user's mouse |

**Diff the page around the click instead of searching for a known testid.**
Every probe here searched for `[data-testid="tweetTextarea_0"]` and kept
finding only the main composer, which is equally consistent with "the box did
not open" and with "the box uses a different testid". Snapshot *every*
element matching `contenteditable`, `textarea`, `[role=textbox]` or
`*DraftEditor*` before the click, then again after, and print only what
appeared. That separates the two causes in one pass, and it is the only probe
that can find a composer you have not named yet.

**`opened: true` from your own click is not evidence the box opened.** A
handler that checks the button has a size, and dispatches, reports success
whether or not anything mounted — the false positive reads exactly like the
success case. Assert a visible editor appeared *after* the click, scoped to
the dialogs that contain one, and treat a click that produced no new editor as
a stop rather than as a reason to type.

So treat "the reply box opened" as **unverified on this build**: assert a
visible editor appeared inside a dialog after the click, and if none did, say
so instead of continuing. A path that opens the box when the user clicks it by
hand and does not open it under any synthetic activation means the constraint
is the input method, not the script — at that point the working routes are a
real user click or the official API, and the script should name which one it
is waiting on rather than retrying.

**Two overlays lock focus and make every later click a no-op.** This is the
single most expensive thing on the page. A `[role="dialog"]` left over from an
earlier run — an empty shell, no editor inside — captures keyboard focus:
`btn.focus()` returns without throwing, and `document.activeElement === btn`
is **false**. Every synthesised click and keypress then goes into the void,
which reads as "X ignores synthetic input" when the truth is "focus is in a
modal somewhere else". Two of them were open at once; clearing dialogs that
contain no editable element took focus from refused to granted immediately.
**Clear editor-less dialogs before touching the page, and again after the
click** — the draft prompt appears *after* the click, not before. Verify with
`document.activeElement === target` rather than assuming focus worked.

**Scope a dialog query by its contents, not by document order.**
`document.querySelector('[role="dialog"]')` returns whichever came first, and
with a draft prompt open that is the wrong one — the reply editor is never
found inside it, so the code reports "no dialog" while a reply box sits right
there. Select dialogs that *contain a visible editor* and search within those.
The same applies to the close control: closing the first dialog on the page
closes the draft prompt and leaves the reply box holding its text, which is
why "open a fresh one" appears to do nothing.

Two further traps:

- **Target the article that owns the status id.** Querying for *any*
  `a[href*='/status/']` inside an article matches quoted posts and reply
  context, so the reply lands under someone else's content. Require the link
  whose href tail equals the target id and is not an
  `/analytics|/photo|/video|/retweets|/likes` suffix.
- **Bind the send control to the reply box; do not pick the tallest editor.**
  The reply composer is a second Draft node on the page and the main composer
  is still mounted, so "tallest visible editor" and "first visible editor" both
  resolve to the *main* composer on a timeline — the reply text goes in as a
  standalone post, and the send button found afterwards is the main composer's.
  The tallest-editor heuristic from the duplicate-testid section above is for
  the single-composer case only; do not carry it into a reply.

  Identify the reply box by **what appeared**: snapshot the visible editors
  before the click, then take the one that is not in the snapshot, preferring
  one inside `[role="dialog"]`. Look the send button up by walking up from that
  editor to its dialog/form — never "the first enabled `tweetButton` on the
  page", which is the main composer's button.

  **Refuse to send unless the editor holding the text is inside a dialog.**
  This one assertion is what makes the difference between a reply and a
  standalone post, and it is the check whose absence turns a failed reply click
  into a published post. Assert it twice: once before typing, once after, since
  the editor that ends up holding the text is not necessarily the one that
  started empty.

  **The URL is not the discriminator — it cannot be, and using it rejects
  working boxes.** Clicking reply on the timeline AND on the target's own status
  page both land on `/compose/post`, the same path a standalone post uses, so a
  check written as "reply means `/compose/tweet`, post means `/compose/post`"
  refuses every correct reply box on this build. That false negative looks
  exactly like a refusal to publish, and it will stall a run that was about to
  succeed.

  The reliable discriminator is the dialog's own affordance, and it sits at the
  **end** of the dialog text, beside the send button:

  ```js
  const head = dlg.innerText || '';
  const isReply = /回复\s*@|Replying to/.test(head) ||
    [...dlg.querySelectorAll('[aria-label*="回复"],[aria-label*="Replying"]')]
      .some(x => /回复|Replying/.test(x.getAttribute('aria-label') || ''));
  ```

  **But never extract the handle with a regex over that text.** With a draft
  present the header renders as `草稿` instead of `回复 @x`, so the regex fails
  and the fallback — a looser match anywhere in the dialog — walks into the
  quoted post and returns whoever *that* mentions. Measured: a thread with no
  such reply reported `box replies to @axeng200`, which sent the guard looking
  for a mis-aimed composer that did not exist. Read the handle from the
  dialog's **own** user element:

  ```js
  const target = (dlg.querySelector('[data-testid="User-Name"]')?.innerText || '')
    .split('\n').find(l => l.trim().startsWith('@'))?.trim() || null;
  ```

  And take the **last** dialog that holds a visible editor, never the first —
  a draft prompt and the reply box can both be mounted, and document order is
  not which one you opened.

  Read the **tail**, not the head: the dialog opens with the quoted post's
  author and body, so any substring test over the first ~120 characters can be
  satisfied by the quoted content — including its own `回复 @someone` line —
  and will attribute the reply to the wrong person. Capture the handle and
  require it to equal the target, which is what turns "a box opened" into "a box
  aimed at the right post".

**The overflow menu is `caret`, not `Dropdown`.** Measured on this build: every
article exposes `[data-testid="caret"]` and no `Dropdown` at all, so a delete or
overflow lookup written against `Dropdown` reports "no menu" on an article that
has one — and a cleanup pass then reports every id as already gone when nothing
was touched. When an action control is "missing" on *every* article at once,
suspect the selector, not the page, and dump the control row before concluding
anything (see the instrumentation rule in SKILL.md).

**Being in the DOM is not being on screen.** A target can be a present
`<article>` while sitting 31000px below the fold, with its reply control
entirely outside the viewport. `element.click()` on an off-screen control is
a no-op that still reports success — the reply open logged `CLICKED` and mounted
no composer at all, which reads as "the click failed" and is really "the click
went nowhere". Before clicking, compare the article's `getBoundingClientRect()
.top` against `window.innerHeight` and `scrollIntoView({block:'center'})` when
it is out of view. That is a scroll, not a navigation, so it stays inside the
no-navigation rule — and assert the box opened afterwards, because `CLICKED`
from an off-screen element is indistinguishable from a real open.

**Scroll the control, not the article.** Centring the article is not enough:
the action row sits at the *bottom* of a post, so an article whose top edge is
comfortably in view can still have its reply control below the fold. One
measured case: article top inside the viewport, reply control at `y=1440` in a
`1233`-tall window, and the open attempt returned "no reply control" while
the article itself passed every in-viewport test. Measure the **reply
control's** `getBoundingClientRect()` and scroll until it sits inside the
window with margin, not the article's.

**A scroll must settle before the control is activated.** The timeline is a
virtual list: scrolling re-renders it, so the element at the previously
measured coordinates is a stale one. Activating into that stale position is
read as leaving the editor, which is what raises a "keep your draft" prompt.
Re-measure the control's coordinates after the scroll, sleep briefly, and only
then activate.

**Verify the reply where it appears:** the target article must gain a *child*
article from the expected account whose text starts with the source prefix.
Checking your own timeline for the new post instead cannot tell a reply from a
standalone post — that check passes for a post that went out standalone, and
it is how a reply-versus-post mix-up can reach the user before you notice.

**A status id is only valid for the read that observed it.** An infinite feed
replaces its contents continuously, so an id captured by an earlier scroll pass
names a post that is no longer on screen — the timeline may hold 15 articles
while your file still lists 27, and the id you picked is in the missing 12.
Treating that file as the present produces a loop where the collector reports
the post as present and the publisher reports `TARGET NOT ON PAGE`, and the
instinct is to blame the publisher. It is the collector's snapshot that is
stale; the publisher's refusal is correct.

Resolve the target **inside the same call that acts on it**: read the live DOM,
pick a post, click its reply control, without an id crossing a process or file
boundary in between. If an id must be passed, assert the target is present
immediately before clicking and re-read rather than trusting a stored value.
When the two disagree, the live read wins.

**Relevance is not keyword matching.** Selecting a target by scanning for words
like "AI", "model" or "compile" picks posts that merely contain the vocabulary —
a thread about quant trading and the limits of statistical modelling will match
"AI" and "模型" and then receive a reply about compile-time checking, which
reads as spam because it is unrelated. Either the reply must genuinely answer
what that post argues, or the target is wrong; do not let a keyword hit stand in
for having read it.

**The input path decides whether the reply publishes.** Observed state at the
moment of failure: the reply control reported `CLICKED`, the reply editor was
newly mounted and inside a dialog, the text compared equal, the send control
resolved to a `tweetButton` *inside that dialog*, clicking it closed the editor
(visible editor count dropped back to one) — and the target article still had
zero child articles, with none of the account's posts anywhere on the page.
Every precondition was satisfied and the post never landed.

The send button was never the problem. It reads `disabled: false` both before
and after typing, and it lives in the right dialog. The fault is that
`Input.insertText` writes the characters into the DOM **without** touching the
editor's own state: the button lights up because the DOM has text, while the
handler behind it still reads an empty draft, so the click submits nothing.

| Input path | Box contents | Published |
|---|---|---|
| whole-string `insertText` | correct | **no** |
| `insertText` then a real `rawKeyDown`/`keyUp` on the last character | correct | **no** |
| per-character `keyDown`/`keyUp` with `text` set | correct | **yes** |

Per-character key events travel the path a person's keystrokes take, which is
what the handler reads. This is slow — a few hundred characters takes tens of
seconds — and it is the working method. "The characters are in the DOM" is not
evidence the draft will submit, and a length match after typing is not evidence
either; the only way to tell the two input paths apart is to send and look.

**Split the input path by whether a keyboard key produces the character.**
`Input.dispatchKeyEvent`'s `key` field is a *key name*, so a character with no
key behind it is silently dropped: an em dash, any CJK character, an emoji.
A 941-character reply with two em dashes read back as 935, and the strict
length check is what caught it before anything was sent. Send ASCII through
`keyDown`/`keyUp` with `text` set, and everything else through a single
`type: "char"` event. **Compare the box against the source exactly after
typing** — this is the check that turns an invisible partial write into a
stop rather than a short post.

**Read a button's state field by its own name.** A dump that reports
`button=False` where the field is `disabled` reads as "the button is missing"
or, inverted, "the button is enabled" — and an assertion written against the
wrong polarity produces a confident diagnosis of a control that was never the
problem. Print `send_disabled: true/false` and let the field name carry the
meaning; while instrumenting, check whether the suspected control is even
varying, because the real fault is usually the step nobody was watching.

**When the user names a specific control, instrument the whole control row
before acting on their hypothesis.** A user who says "the button is the second
one from the left" has given a location, not a diagnosis: dump every control in
that container with its testid, label, `x`/`y` offset and disabled state, and
compare against the row on the target article. This costs one call and settles
the question, where adopting the user's guess can send the investigation
somewhere that was never broken.

**A reply draft survives closing and reopening its box.** The text persists,
so "open a fresh one" does not yield an empty composer. A draft this automation
did not write is the user's: it is not to be edited, appended to, cleared or
deleted — appending posts somebody else's sentence, and the normalisation used
for the text compare will happily call the result a match. Reopening and
finding it still there is a stop condition, not something to work around; say
so and hand it back. Verify the box was empty *before* typing, and compare the
result exactly rather than through a whitespace-stripping normaliser, which
lets appended text pass.

When this happens, the cheapest way to separate "my click never opened the
box" from "my input path is wrong" is to instrument before asking the user for
anything: clear the editor-less overlays, re-click, and assert a visible
editor appeared in a dialog. Only once a dialog-mounted editor is confirmed
does the input-path table above apply — and per-character `keyDown`/`keyUp` is
the path that publishes from it.

If the box opens when the user clicks by hand and not under any synthetic
activation, the honest report is a named blocker plus the nearest working
action (a like, which kept working), not a retry loop and not a claim that
replying is automated. `xurl` with an authenticated session is the route that
does not touch the DOM at all, and it is the only one that scales past a
handful of replies.

**Do not let "the editor emptied" or "the box closed" be read as published.**
That is the same error as reporting success on a click, pointed the other way,
and it is what made a silent failure look like a completed one.

## One post at a time, and prove each landing before the next

A multi-reply run is a sequence of independent verified operations, not a loop
over a queue. For each target, in order:

1. find the live post and click its reply control **in the same pass** (below)
2. prove the box is a reply box and is aimed at that target
3. clear it, assert empty
4. type, compare the box against the source exactly
5. send
6. verify the reply landed **as a child article under the target**
7. only then look for the next post

Step 6 gates step 1 of the next item. If it does not verify, stop the run —
the next reply would be typed into a composer whose state is now unknown, and a
partial failure mid-queue is how the account ends up with a reply aimed at the
wrong post. "The queue still has 8 items left" is not a reason to continue.

**A scan that returns before acting invalidates its own result.** Measured: a
scan walked 63 posts deep, returned the target's id, and the very next call
reported `article not in DOM after 30 tries` — the scan had scrolled past it
and the virtual list had recycled the article. Find the match *and* click it in
one evaluate, and never let an id cross a process, file, or function boundary
between the read and the act. This is the "a status id is only valid for the
read that observed it" rule below, applied to the position as well as the id.

## Scroll position is state that outlives the run, and a URL check misses it

A guard written as "if the URL is /home, we are on the timeline" returns true
while the feed sits 131618px down: the path is right and the position is wrong.
Every subsequent "scroll the feed" then descends further into old content, and
a target that was live at round 0 is unreachable at round 70. The symptom is a
healthy-looking page returning nothing.

Assert the **position**, not the path: `/home` in the URL **and**
`scrollTop < 50` **and** no dialogs open. Then `scrollTo(0,0)` and let it settle.
The same applies after any crash leaves the tab on `/compose/post` or a status
page — there "scroll the feed" scrolls a 1690px page with no feed on it, and a
harvest reports one article, which reads as an empty timeline rather than as
the wrong surface.

## Wrapping a JS template in a second IIFE returns the function, not its result

`Runtime.evaluate` is given `(() => (TEMPLATE))(arg)` for a target-taking
template. The outer arrow evaluates `TEMPLATE` — a function object — and
returns it **uncalled**. The result is
`{"result": {"type": "function", "value": {}}}`: an empty object, which a
`if not result.get("found")` loop reads as "target absent" and scrolls past,
forever.

Measured cost: a 150-round scan of a 74000px feed reported "target not found"
while a direct probe at round 5 had the article in hand.

Two distinct mistakes produce the same empty object, so fix both:

| Written | Evaluates to | Symptom |
|---|---|---|
| `TEMPLATE = ((x) => {...})` then `(() => (TEMPLATE))(arg)` | function | `{}` |
| `TEMPLATE = (x) => {...}` then `(() => (TEMPLATE))(arg)` | function | `{}` |

So unwrap the double parentheses in the template **and** call the template
directly — `({TEMPLATE})(arg)`. The same bug hides in a `CLEAR_DIALOGS`-style
constant written as `(() => {...})()` and then wrapped again at the call site:
it returns a function, clears nothing, and the reply box "never opens".

**Assert the returned type, not just that the value is a dict.** An empty
`{}` passes `isinstance(value, dict)`, so the first version of the guard did
nothing. Reject `result["type"] == "function"` explicitly, and name the cause
in the error so the next run starts at the fix.

**The same empty object arrives from two other shapes, and one wrapper cannot
serve both.** A helper that dispatches on the template's form must separate
three cases, because a single `f"({expr})"` wrapper is correct for none of them
in general:

| Template | Must be evaluated as | Wrapping it in `(...)` gives |
|---|---|---|
| bare expression `document.title` | `(document.title)` | correct |
| arrow template `(pid) => {...}` | `(pid) => {...}("123")` — called with the arg | the function object, `{}` |
| already-invoked IIFE `(() => {...})()` | as written | a second call on a boolean/undefined result |

Measured cost of getting this wrong: a rebuild of the CDP helper applied
`(expr)` uniformly, so `who_owns` returned `{}` for every page. Nothing raised —
the ownership guard read `{}`, compared it to the expected handle, and every
direct-pid send aborted with `nothing rendered`. The symptom said "the target
post is not loading"; the cause was a wrapper three layers from the DOM.

So detect by form, not by a single rule:

```python
source = expr.strip()
is_iife = source.startswith("(()")          # already invoked - leave alone
is_fn = source.startswith("(") and "=>" in source and not is_iife
call = f"{source}({args!r})" if is_fn else f"({source})"
```

Do **not** test `"=>" in source.split("=>")[0]` to find an arrow head: a short
head like `(pid => ...` puts the whole body after the arrow, the split returns
just `(pid `, and the template is then misclassified as a bare expression.
Test the whole string.

## A status id in a file may be a bare id; the DOM href carries the handle

A reply file declares `# target-status: 2107454350306300020` — a bare id — and
the DOM holds `/AnkanXplorer/status/2107454350306300020`. Comparing the full
path against the bare id never matches, and the scan runs to its end reporting
the target absent. Normalise **both** sides to the numeric id before
comparing:

```js
const id = String(target).match(/\d{15,}/)?.[0] || String(target);
// and on each href:
(h.match(/\d{15,}/) || [''])[0] === id
```

This is the same class of bug as comparing a stored id against a live DOM:
two representations of one thing, compared as strings.

## The reply box persists across runs, so "a new editor appeared" never fires

A draft this automation wrote survives a failed run, and the dialog stays
mounted. On the retry there are already two editors, so a "did the editor
count increase?" test reports `no new editor (have 2, had 2)` and the run
stops — while the box it wanted sits right there, in a dialog, focused.

Scope the reply editor by **membership in a dialog**, not by novelty:

```js
const inDlg = eds.filter(e => e.closest('[role="dialog"]'));
const el = inDlg[0] ?? eds[eds.length - 1];
```

and treat `alreadyOpen: true` as success, not as a failure to re-open.

Related: the run that clears overlays must clear **editor-less** dialogs only.
Clearing every dialog destroys the reply box and its draft.

## Select-all does not work in this editor; backspace-per-character does

Measured: with focus confirmed on the editor
(`document.activeElement === tweetTextarea_0`), a select-all keypress left
`getSelection().toString().length === 0`, and the following backspace deleted
**one** character. So "select all, then one backspace" clears nothing useful
and the next read compares against residue.

Clear by backspacing until the field is actually empty, re-reading between
passes, and pace it — 10ms between presses silently dropped events and made a
3-character field survive; 60ms cleared it. Assert the field is empty
afterwards; "the loop ran N times" is not the same claim.

## Newlines are dropped by `text` on a keyDown, and by `type: "char"` with `"\n"`

Measured on a 636-character body: every paragraph break disappeared, reading
back 630 characters with no `\n` anywhere. `dispatchKeyEvent`'s `key` field is
a key *name*, and a newline has no key behind it, so both of these are
dropped:

| Newline attempt | Result |
|---|---|
| `type: "char", text: "\n"` | dropped — no break inserted |
| `keyDown Enter` with `text: "\r"` | inserted, but only with an accompanying `keyUp` |

Isolate this before typing a real body: clear, type `AB`, insert one newline
event, type `CD`, and require exactly `"AB\nCD"`. A whole-body compare catches
the loss only as an unexplained 6-character shortfall, which reads like a
dropped character instead of six dropped newlines.

## The harvest re-run starts wherever the last one stopped

The feed is a virtual list; a second harvest run begins at the previous
scroll position and counts the tail again. A 27-post run followed by a "3
posts" run was this, not a feed that emptied. `scrollTo(0, 0)` before counting,
every time — and note that the target lookup needs the same treatment, since a
refreshed feed no longer holds the article at the position it did before.

## The url cannot tell a reply from a standalone post — the dialog text can

Measured on the current build: clicking `[data-testid="reply"]` navigates to
`https://x.com/compose/post`. A standalone post opens **the same url**. So a
check written as "a reply box is not at `/compose/post`" rejects every working
reply box and passes every standalone post.

The only thing that separates them is the dialog's own affordance: the text
`回复 @someone` (or `Replying to`) beside the send button.

```js
const isReply = /回复\s*@|Replying to/.test(dialogText);
```

**Get this right before typing.** Two wrong calls in opposite directions, both
made in one session: refusing to type into a perfectly good reply box because
of the url, and — earlier, before this check existed — typing into a standalone
compose modal and publishing three orphan posts that had to be deleted.

## `scrollIntoView` on the target invalidates it; scroll the window instead

Measured: locate the article, call `btn.scrollIntoView(...)`, and the next
query returns "article not in DOM". Scrolling triggers the virtual list to
re-render, and the node the first query found is gone. Two steps that each work
in isolation, failing in sequence.

Scroll the **window** to the article's absolute offset and settle, then
re-query everything after:

```js
const absTop = article.getBoundingClientRect().top + window.scrollY;
window.scrollTo(0, Math.max(0, absTop - 180));
// sleep, then locate + click in the SAME evaluate
```

## Find the target and act on it in one pass — never across a boundary

Measured three ways in one session:
- harvest ids, then act: the id was live at scan time and gone by action time
- scan 63 posts, return, then look for the target: "article not in DOM after 30
  tries" because the scan had scrolled past it
- match the post and click it inside the same evaluate: worked first try

A harvested position is stale the moment you act on it. Also scan **deeply**:
a target was measured at round 63 of an 91164px feed, and a scan that stops at
60 posts reports it as absent.

## Assert the surface by POSITION, not by url

A guard written as `if (!url.includes('/home')) restore` returned early while
the feed sat at `scrollTop: 131618`. Every subsequent "scroll the feed"
descended further into old content, and a target live at round 0 was
unreachable by round 70.

Require `/home` **and** `scrollTop < 50` **and** no open dialogs. A page can
have the right url and be in the wrong place.

The same failure has a second form: the tab left on `/compose/post` or a status
page, and a "scroll the feed" then scrolls a 1690px document containing one
quoted post. 70 scroll rounds returned exactly one article, which reads as an
empty feed rather than as the wrong surface.

## A degraded page presents as an empty feed

Two distinct page states produced the same symptom — "no posts match":
1. genuinely nothing relevant in the feed
2. the page shell is broken: `document.title` empty, the search box absent from
   the DOM, 1–3 `article` elements against a 40 000px document

Distinguish them by probing the shell, not the content: title non-empty,
`[data-testid="SearchBox_Search_Input"]` present, article count per pass.
When the shell is broken, restarting the browser is the fix — and on a headless
instance with a copied profile it is *cheap*: kill the process, relaunch the
same `--user-data-dir`, and the feed is healthy on the next load (measured: a
broken instance showing 2 articles per pass came back with title, search box,
8 articles and a 30 000px feed).

## The overflow control is `caret`, not `Dropdown`

`[data-testid="Dropdown"]` matches **nothing** on the current build; the post
overflow menu is `[data-testid="caret"]`. A delete routine that looked for
`Dropdown` reported "no Dropdown" on all three posts it had correctly located,
deleted nothing, and looked like a lookup failure rather than a wrong selector.
Dump the actual `data-testid` list of a post's controls before writing the
selector:

```
Grok 操作, caret, reply, retweet, like, bookmark, 分享帖子
```

Also: **"not in the feed" is not "deleted".** The timeline is ordered by
recency, so a post scrolls out of it while still existing. Only the profile
answers whether a post exists — and the profile timeline lazily renders too, so
a scan that sees 1 article under a "402 帖子" header has verified nothing.
Confirm a deletion on a surface that actually paginates.

## A full real mouse press does not open the reply editor

Measured, last resort after every synthetic path failed: locate the reply
control, get its `getBoundingClientRect()`, and dispatch the complete event set
a mouse produces — `mouseMoved`, `mousePressed` (buttons=1, clickCount=1),
`mouseReleased`. The url became `/compose/post` and **zero** dialogs and zero
editors existed for 36 seconds of polling.

So when the editor will not mount, "use better input events" is not on the
table, and neither is waiting longer. This is worth separating from the
DOM-shape bugs above, which all present as "found nothing" while a correct
selector and a single fixed wait fix them.

Note the boundary this crosses: a real press at real coordinates is what the
project's rules forbid, because it is the user's mouse. On a **headless**
instance with a copied profile there is no physical mouse and nobody watching,
so the hazard does not apply — but that is a decision to make explicitly, not a
default to assume.

## A run that sent nothing must exit non-zero

A script that reported "no replies confirmed" still exited 0, and its
completion notification was indistinguishable from a successful run — which
means every "completed normally" in a session log has to be read against the
output file, not the exit code. `raise SystemExit(0 if sent else 1)`.

## A draft prompt hides the reply target, and the header regex cannot see it

With a draft present, the reply dialog's header renders as `草稿` rather than
`回复 @x`. Any check built on `head.match(/回复\s*(@\w+)/)` therefore returns
nothing, and the loose fallback that walks the quoted post returns an unrelated
handle — producing a confident "box replies to @axeng200" on a thread with no
such reply, which sends the next hour of debugging after a phantom. Read the
handle from `[data-testid="User-Name"]` inside the dialog and compare that.

## Read the target article by its own status link, not by "contains the id"

A quote-tweet article contains the original post's status link, so
`article.querySelector('a[href*="/status/<pid>"]')` matches the quoting reply
rather than the post being replied to. Require the article whose **first**
status href tail equals the id and which is not itself a
`[data-testid="quoteTweet"]` container.

## A retweet's `article[0]` is the retweeted post, not the retweeter

On a retweet page the first article belongs to the original author and the
outer status the user sees belongs to the retweeter. Reading `article[0]` for
the owner attributes the post to someone who merely shared it, and the reply
opens correctly on the right thread while its opening line names the wrong
person. Scan for the article that actually owns the target id.

**The main composer is not the reply composer — insertText publishes from it.**
The reply input-path table above (insertText → "published: no") does NOT generalize
to the standalone composer: a 535-char post typed with one `Input.insertText`
published fine, link card and all. Use insertText for standalone posts; keep
per-character keyDown/keyUp for replies.

**"Not on the profile yet" is not "not published".** A profile read ~5s after send
showed the post ABSENT while it had already published (the id was later confirmed
with its link card). Acting on that false negative produced a duplicate that had to
be deleted. After a send: `scrollTo(0,0)`, read, re-read up to 3 times with ~5s
waits; only conclude failure after all reads miss. Symmetric with "editor emptied ≠
published": absence on a lazy surface ≠ absence on the platform.

**innerText over-reads empty Draft blocks; compare block-by-block.** Each blank
source line renders as an extra '\n' in innerText, so a "\n\n" source reads back as
"\n\n\n" (535 chars read as 538 on a perfect post). The reliable compare:
`[...editor.querySelectorAll('[data-block="true"]')].map(b => b.textContent)` joined
with '\n' must equal the source. Works for both storage shapes: per-char typing
creates one block per line; one insertText stores the whole body as ONE block with
literal '\n' chars inside — the join is identical either way.

**Backspace needs real key codes; typing does not.** CDP keyDown/keyUp with only
`key:'Backspace'` deletes nothing (Chrome maps editing commands through virtual key
codes — 1500 presses changed nothing). Pass `windowsVirtualKeyCode: 8,
nativeVirtualKeyCode: 51` (macOS) and deletion works. Printable typing never needed
codes because `text:` bypasses keycode mapping. Cmd+A selects nothing in this
editor even WITH key codes — clearing remains backspace-per-character.

**Typing pace has a floor; a scrambled draft is discard-only.** ~2.4ms per event
(535 chars in 2.6s) lets the editor process events out of order: paragraph blocks
rearranged, and the mangled draft then stalled backspace deletion at anchorOffset 0
mid-field. 12ms per event produced exact output. Never repair a scrambled draft by
backspacing — close the dialog (`[data-testid="app-bar-close"]`), confirm discard
(`[data-testid="confirmationSheetConfirm"]`), reopen, retype.

**The first keystroke after focus can be dropped.** Char 0 (emoji via
`type:'char'`) vanished as the first event after `el.focus()`. Send a warmup key
(ArrowLeft down/up) and a ~300ms settle before the real body.

**Reply verification when the thread page folds your reply.** A published reply can
be invisible on the target's status page: the reply count increments while the
article stays folded by ranking. The proving surface is your own `/with_replies`:
X renders the PARENT article directly above your reply, and that adjacency is the
parent-child proof — require `parent.head` to match the declared target before
claiming the reply landed.

**The no-password-exposure redactor eats status ids.** A 19-digit status id
Luhn-passes the card regex and arrives as `[CARD-19 REDACTED]` in tool output.
Never re-read ids from tool output; resolve targets live in-page, or persist them
to a file inside the same run.

## Clearing

**Clear every leftover dialog before opening a reply, including ones holding an editor.**
The measured failure: a run that "skipped dialogs with an editor" to
protect its draft left a stale reply box mounted and visible, so the next run's
`IS_REPLY` read the *old* dialog and reported the previous run's handle as the
current target. The protection was the bug. Either scope by dialog identity, or
clear everything and re-assert emptiness before typing.

Select-all plus a single backspace leaves 4–24 characters behind — enough to
make the next read compare against residue — and on the current build
select-all selects nothing at all, so clearing is backspace-per-character with
the emptiness asserted afterwards (see above). Assert the field is empty after
clearing. Emptying the field and a later reload are what raise the browser's
unsaved-changes dialog, which then blocks every subsequent call until the user
dismisses it; end every run by closing any open IME composition so the page is
not left holding unsaved input.
