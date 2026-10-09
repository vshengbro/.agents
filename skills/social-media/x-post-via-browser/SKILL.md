---
name: x-post-via-browser
description: "Use when posting or replying on X/Twitter through the user's logged-in browser. Compose and reply paths, and the visibility/verification traps that make a working path read as dead."
version: 4.0.0
author: local
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [twitter, x, posting, cdp, browser-automation, real-profile]
    related_skills: [chrome-real-profile-launch, chrome-devtools-protocol]
---

# Posting to X from the user's logged-in browser

Verified 2026-10-01 on a Premium account. Four long posts of 608–1060
characters published and verified, then a 27-post series published on a timer.
Revised 2026-10-07 with 12 replies published and each one verified on the
target's own page — which corrected the reply path's stated cause.

## The path

One tab, on x.com. Nothing navigates, nothing clears, nothing touches the
mouse. For a series, `run_queue_tick.py` does this once per invocation and a
cron job calls it on the interval — the queue's spacing is the cron's, not the
script's.

`publish.py` calls `ensure_browser.py` first, which handles the two states
that used to need a human:

| State | What happens |
|---|---|
| browser down | launched through the real-profile launcher, headed, `--no-tab` |
| up, no x.com tab | ONE tab opened at the composer, then given time to paint |
| up, with a tab | nothing at all |

That is the only page load the flow performs, and it lives in its own script
because that is the one file the commit gate lets load a page. Every other
script stays forbidden, so "the publisher opened a tab" is still a defect
rather than a shortcut.

1. `python3 scripts/publish.py <port> --post N` — types, compares, does not click.
2. Read the line it prints. `match=True` and `urls_ok=True`, or it stops.
3. `--go` to click.
4. `python3 scripts/verify_post.py <port> <status_id> <copy.json> N` — proves it.

X empties the composer itself after a post, so the next run finds it empty and
types into it. That is the whole loop.

## Never navigate, never clear

**No `location.assign`, no `Page.reload`, no `Page.navigate`, no second tab**
— with one named exception, `ensure_browser.py`, which may open the single tab
the flow needs and may launch the browser if it is down. Every page load makes
the user confirm it in their UI, so the exception is one file with one job
rather than a relaxation. If the composer is not open, click the control
already on screen — `[data-testid="SideNav_NewTweetButton"]`,
`a[href*="/compose/post"]`, `[data-testid="appTabBarPostBtn"]` — which opens it
in place.

**Never empty the composer.** Clearing, reloading, navigating and Escape all
raise Chrome's own dialog, 「系统可能不会保存您所做的更改」, and that modal then
blocks every later CDP call until the user dismisses it. X sets no
`onbeforeunload` handler (`window.onbeforeunload === null`); the dialog is
Chrome's, caused by an IME composition left open on a contenteditable.

So the flow is read-only about the box: **read it; type only into an empty one;
if it already holds exactly the requested post, post it as it stands; if it
holds anything else, leave it and report.** There is no retry that does not
involve clearing, so a failure here is a stop, not a loop.

End every run with `close_composition("")`. A composition left open is what
makes Chrome claim the page holds unsaved input on the next unload.

**Never take the mouse or the keyboard.** No `Page.bringToFront`, no
`Input.dispatchMouseEvent`, no OS clicks, no `pbcopy`/`pbpaste`. Focus is
`el.focus()` inside the page; the user's pointer and OS focus never move.

## One insertText for the whole post, URL included

2500 characters land in no time, newlines and all. The URL is not special to
the editor — it is just text, and it goes in the same call.

Everything else was tried and measured to break the text:

| Tried | What happened |
|---|---|
| `imeSetComposition` for the URL | strands the URL's first character in the body — the editor reads `…edition。h` against a source of `…` |
| committing it with a second `insertText` | the committed string arrives already formed, so X has nothing to linkify; plain text, no `<a>` |
| pasting the URL (`commands:["paste"]`) | X folds the separator into the host — the sentence comes back as `https://\ncrates.io` |
| typing the URL per character | X linkifies mid-stream and drops the rest (`https://github.c` survived) |
| clearing first, then typing | 4–24 characters survive, and a later reload raises the dialog |

## The editor has two nodes, and one of them is a decoy

Two elements carry `data-testid="tweetTextarea_0"`. One is real — its `class`
contains `public-DraftEditor-content` and it holds the text; the other is an
empty duplicate. `querySelector` returns whichever is first in document order,
and that changes between renders. This alone produced writes that vanished and
a click that published a single stray character. Take the **taller visible**
one, and refuse to act if it did not take focus.

`[data-testid="tweetText"]` is a decoy — a display layer whose `textContent`
goes stale. Never write to it. On the timeline it is also **clipped**: it holds
204 characters of a 462-character post with no "show more" control, so reading
it reports a correct post as truncated.

**The raw length lies.** X's Draft editor keeps hidden text nodes of its own,
so it reports 860 against an 859-character source on a post that matches
character for character. Gate on the normalised compare, never on length.

## X linkifies anything dotted, not just URLs

A bare `crates.io` in the body became a `t.co` shortener, and the span X
replaced then read back as a line break — the sentence split in two and **two
broken posts shipped** before this was caught. `publish.py` now refuses any
copy carrying a dotted token that is not one of the URLs it intends, before a
character is typed. Write "crates io" in the copy.

## Verifying

`verify_post.py` proves three things at once, and each one exists because
without it a check produced a false verdict:

- **The author.** Matching a status id found a stranger's post sitting in the
  same feed — the id was real, the text was real, and "my post landed" was
  wrong. `whose_posts.py` lists what is on screen split by author.
- **The visible text against the source PREFIX.** `tweetText` is clipped, so a
  full character compare reports good posts as broken.
- **The link card.** A `t.co` href never contains the source URL, so the link
  is proved by the card X rendered from it, which names the repository.

`CLICKED` proves nothing. The publisher's own text compare proves the composer
held the right characters; only the timeline read proves it was published.

## Launching: headed, and through the local proxy

```bash
bash ~/.agents/skills/software-development/chrome-real-profile-launch/scripts/run.sh \
  --headed --port 9240 --fresh --no-tab
```

`run.sh` probes 7897/7890/7891/8080/10809/1080 and passes `--proxy-server` for
the first that answers. This is not optional on this machine. Without it a
browser launched with its own `--user-data-dir` cannot complete a TLS
handshake: DNS resolves, the TCP connection opens, then the handshake is cut —
`curl` reports `SSL_ERROR_SYSCALL`, Chrome reports `net_error -100`
(ERR_CONNECTION_CLOSED). The daily browser works because Clash Verge Rev
routes it through a TUN interface, which a separate user-data-dir does not get.
It looks like a crash and is not; Crashpad's pending directory is empty and no
crash report is written. **Check the log for `net_error -100` before
concluding anything died.**

`--fresh` drops the scratch profile and re-copies, excluding the `Singleton*`
files.

## Do not inject to defeat headless detection

X blocks headless browsers; `--headed` is the answer. Injecting a spoofed
fingerprint to get past the detection is circumventing an access control, and
this skill does not do it. Driving the composer's own input path in a browser
the user is logged into is a different thing from impersonating a human client
to the server.

## The button, and why "the button never enabled" is usually a wrong answer

X mounts `tweetButtonInline` for the inline composer and does not reliably
mount `tweetButton` at all. A lookup that requires `tweetButton` finds nothing
on a composer whose button is right there and enabled — which reads as "the
button never enabled" and silently drops a post whose text matched exactly.
Accept either; prefer the primary one.

## Two CDP client bugs that cost hours

Both are silent. `scripts/cdp.py` handles them; use it rather than a
hand-rolled socket.

**WebSocket control frames are not JSON.** opcodes 8/9/10 (close/ping/pong) and
2 (binary) share the framing but not the payload; check `b1 & 0x0F` before
decoding. Parsing a ping as JSON raises `UnicodeDecodeError`, and swallowing
that as "no reply" makes every `Runtime.evaluate` look like it never ran.

**The first evaluates on a new tab lose their replies.** While the renderer
swaps execution contexts the reply never comes — measured ~33 s of warm-up on a
fresh target, then 0.5 s per call. Fail fast and retry immediately; a long wait
per attempt turns this into minutes of apparent hang.

**Long idles kill the socket.** A `settle()` that leaves the connection
untouched for minutes gets dropped by Chrome, and the browser stays healthy
while the client raises `WebSocketConnectionClosedException` mid-post. Reconnect
on send.

A `js()` that returns `None` on failure is the root of a whole class of false
conclusions — two separate rounds concluded "the click did nothing" when the
real problem was a lost reply. It returns a distinguishable error marker, and
every call site checks it.

## Dead ends, so they are not re-tried

- `execCommand('insertText')` — returns false, inserts nothing.
- `textContent = t` plus `beforeinput`/`input` events — text appears and
  verifies, but Draft's state never sees it and the button stays disabled.
- `computer_use set_value` — the AX tree exposes the editor as `AXTextArea`,
  and setting its value changes the DOM, but the button stays disabled and a
  post went out as the single character `e` (`2105508309361217688`, since
  deleted). Real OS keystrokes also cannot send CJK: a 159-character Chinese
  post delivered `0 of 159`.
- React internals — the composer's `__reactProps$` has `handlers: []` at every
  depth, `__reactFiber$` carries only click handlers, and a breadth-first walk
  of 13,764 nodes finds no input handler. The production build is minified, so
  the component names that would identify Draft are stripped.
- The restored-draft pool was once thought to be server-side and unclearable.
  That was wrong. The drafts are X's own, restored into the composer by X, and
  the whole problem is avoided by never clearing and never racing the box.

## Guardrails

- Never drive the composer while the user has their own drafts open, unless the
  box is empty or already holds exactly the intended text. A mistimed click
  publishes somebody's unfinished tweet — that is what happened once here
  (`2105508309361217688`).
- Never claim a post happened without the timeline read-back.
- Never close or reuse the user's tabs to "clean up".
- Never read credentials. Do not put cookies, tokens or a Client Secret in the
  conversation; write them as `[REDACTED]`.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/cdp.py` | CDP client: control frames, retrying `js()`, auto-reconnect, `close_composition()`. **No `new_tab()`** — a client that offers the call is a client that gets used. |
| `scripts/publish.py` | The publisher. `--show` the copy, `--tabs` the X tab, `--post N` type and compare, `--go` click. |
| `scripts/ensure_browser.py` | Launches the browser if it is down; opens one composer tab if there is none. The only script allowed to load a page. |
| `scripts/verify_post.py` | Proves one post landed: author, text prefix, link card. |
| `scripts/whose_posts.py` | What is on screen, split by author. |
| `scripts/run_queue_tick.py` | Idempotent queue runner — one item per invocation, for a cron series. Verifies on the timeline **before** recording an item as posted, so a click that did not land stays queued instead of being counted as done. |
| `scripts/run_project_day.py` | One project per invocation: its zh/en/ja/ko versions in order, `--gap` seconds apart. Records the project only after all four verify, so a failed version retries the whole project rather than losing a language. |
| `scripts/engage_feed.py` | Home feed: click the home tab, like what is worth liking, then reply once per post up to a target. Reads the feed live and dedupes by status id. |
| `scripts/verify_no_unsafe_posting.py` | The commit gate. `--self-test` proves every rule fires. |

```bash
# once, and only if no instance is up
bash ~/.agents/skills/software-development/chrome-real-profile-launch/scripts/run.sh \
  --headed --port 9240 --fresh --no-tab

python3 scripts/publish.py 9240 --show            # read the copy first
python3 scripts/publish.py 9240 --post 0          # type and compare, no click
python3 scripts/publish.py 9240 --post 0 --go     # click
python3 scripts/whose_posts.py 9240              # find the status id
python3 scripts/verify_post.py 9240 <sid> x_copy_example.json 0

X_COPY=/path/to/other.json python3 scripts/publish.py 9240 --post 0 --go
```

The copy defaults to `scripts/x_copy_example.json` next to the script — posts
that were actually published. Replace it or point `X_COPY` elsewhere; the
content is yours, not the skill's.

## The gate is registered, not just written

`verify_no_unsafe_posting.py` runs from the **global pre-commit hook**
(`~/.git-hooks/pre-commit`, installed via `core.hooksPath`), before the Rust
detection, so it applies to every repo — including the skills repo, which the
existing hook skips for having no `Cargo.toml`. A rule that lives only in this
document is a rule the next person breaks without knowing why; that has
happened to every rule on this list.

| Rule | What it stops |
|---|---|
| `no-page-load` | `location.assign`, `Page.reload`, `Page.navigate`, `new_tab`, `Target.createTarget` |
| `no-clearing` | `clear(c)`, `execCommand('delete'/'selectAll')`, a Backspace loop |
| `no-open-ime` | `imeSetComposition` with nothing that commits it |
| `no-mouse-keyboard` | `Page.bringToFront`, `Input.dispatchMouseEvent`, `bring_to_front`, `click_at_xy` |
| `no-clipboard` | `pbcopy`, `pbpaste`, a paste key event |

It tokenizes the source instead of regexing raw text, so prose that *mentions*
a banned call (this document's own notes do) is not a violation while a real
call is, and line numbers are true. `--self-test` runs twelve violating
fixtures and three clean ones and asserts each rule fires on its own, because a
gate never shown to fail is indistinguishable from no gate.

It caught a real violation on first run: `top_of_timeline.py` opened a new tab
on every verification, so the verification step broke the rule it existed to
confirm.

## Deleting a post

The same single tab, no navigation: open the status, the article's `caret`
button, 删除 in the menu, 删除 in the confirmation dialog. Verify the article is
gone. The user may prefer to do this by hand.

## There is no API path for this account

Do not reach for the official X API, `xurl`, or any other credentialed
alternative. The user has ruled it out, and it stays ruled out regardless of
what fails in the DOM path below: a dead end in the composer is not an argument
for introducing a channel the user has closed.

The cost of that ruling is written down here so the next run does not re-derive
it.

## The reply path works, and it was the script that was broken

Revised 2026-10-02. `post_reply.py` now opens a reply box, types with real key
events, sends, and reads the reply back off the timeline. Four replies
published and verified live, one of them carrying all the fixes below. Nothing
here needed the API, a real pointer, or the OS keyboard.

The 2026-10-01 finding — "X refuses synthetic input" — was **four script bugs,
not a wall in X**. Each one produced a silent failure, and each one looked
exactly like the next. This is the record, because the shape repeats:

| what the script said | what was true |
|---|---|
| `NOT SENDING - None` | the box had opened. `REPLY_POINT` returns `JSON.stringify(...)`, a STRING, and `js()` wrapped it as `{"_raw": ...}`, so `pt.get("opened")` was always `None` |
| `LEN 470 want 476 exact=False` | the text was correct. X renders each newline as an element, so a 6-newline source reads back 6 characters short — an exact compare can never pass |
| `NOT VERIFIED - no reply under the target` | it had landed. A sent reply renders as its own TOP-LEVEL article; the replied-to name is plain text, so the target id was nowhere in the article the template searched |
| `NOT VERIFIED` with the reply sitting at the top | the script scrolled DOWN to reach the target and never came back up. A new reply appears at the TOP of the timeline |

The lesson worth keeping: **every one of these was reported as a refusal to do
something X had actually done.** X never once refused input. Check what the
script measured before concluding what X did — and note the specific trap, which
is the most reusable part: a template that returns `JSON.stringify(...)` while
its sibling templates return objects is enough to make a working path look
completely dead.

Three things that make it work, all measured:

- **Identify the reply box by the dialog that appeared, not by the editor
  count.** The main composer is already in any page-wide list of editables.
- **Type with real key events, one per character**, and let `char` carry the
  characters no key can produce (em dash, CJK). `insertText` lights the button
  up while the handler behind it still sees an empty draft.
- **Find the send button by walking up from the editor that took the text**,
  inside that dialog. The first enabled `tweetButton` on the page belongs to
  whatever composer happened to be on screen.

Two behaviours that are correct and should not be "fixed":

- **A reply box that already holds text is refused, not reused.** That draft is
  not ours to delete, and clearing it is the one thing this skill forbids.
  Close the box and open a fresh one instead.
- **A reply must carry a repository from `org_repos.OWNERS`**, or it is refused
  before a character is typed. A reply that links someone else's project is not
  promotion of this account's work.

## Replies are written, not generated at send time

`replies/*.txt` holds the reply bodies. They are written in advance because the
publisher checks them — the owner rule, the length, and the stray-dotted-token
rule — and a reply composed on the fly has not passed any of them. `X_REPLY_DIR`
overrides the location.

Two rules about that directory, both learned by breaking them:

- **One reply per post, deduped by status id.** The feed is virtualised: a post
  stays in the DOM at the same offset long after the loop scrolls past it, so
  without dedupe three of four replies go to the same first match.
- **Never re-post a reply text to reach a count.** If the directory holds fewer
  replies than the target, the honest answer is the smaller number.

## The reply editor does not mount in a hidden tab — activate it first

**Corrected 2026-10-07. This supersedes the "X refuses synthetic input"
conclusion that sat in this section.** That conclusion was wrong, and it was
wrong for four separate reasons in a row, each based on a real measurement.

The actual cause: `document.visibilityState === "hidden"`. A backgrounded tab
throttles rendering and React work, so **the reply editor never mounts at
all**. The symptom is consistent and unambiguous: the url moves to
`/compose/post`, and then there are **0 dialogs and 0 editors** — forever, at
any poll interval, with any event type. It looks exactly like "X ignored the
click".

Same page, before and after `Target.activateTarget`:

| | `visibilityState` | articles | title | search box |
|---|---|---|---|---|
| before | `hidden` | 1–2 | empty | absent from the DOM |
| after | `visible` | 11 | loaded | present |

The degraded shell also masquerades as every other failure you would guess
first — an empty feed, a broken page, a page that needs a reload, a browser
that needs restarting. Fixing any of those changes nothing.

```python
tab.send("Target.activateTarget", targetId=<tab target id>)
```

`activateTarget` is equivalent to raising a minimised window. In headless it
moves no pointer and takes no OS focus, so it does not violate the
no-mouse/no-keyboard rules. Activate at the top of every entry point, and
re-activate after each navigation — it flips back to `hidden` on its own.

**Check it before diagnosing anything else.** One line:
`tab.js("document.visibilityState")` must be `"visible"`.

## Dead ends that are still real

These were measured while the tab was hidden, so they are contaminated — but
the *structural* observations stand, and each one is a genuine trap worth
keeping:

- **A template returning `JSON.stringify(...)` while its siblings return
  objects** makes a working path look completely dead. `js()` wraps the
  string as `{"_raw": ...}` and every `.get()` on it returns `None`.
- **`insertText` lights the send button up while the handler behind it still
  sees an empty draft.** With the editor properly mounted, one `insertText`
  for the whole body is both correct and fastest — but only after the tab is
  visible. Per-character `dispatchKeyEvent` drops and reorders characters when
  the editor is live (a 694-character reply came back with a run of the middle
  missing). Do not "fix" a working path by switching to per-character keys.
- **X renders each newline as an element**, so a source with N newlines reads
  back N characters short. Compare normalised text, never raw length.

And the ones that are simply true:

- **Counting editors does not detect the reply box.** The main composer is
  already in any page-wide list of editables, so a reply box appearing does
  not change the count. Scope to a visible dialog instead.
- **An editor-less `[role="dialog"]` captures focus.** `btn.focus()` returns
  without throwing while `document.activeElement === btn` stays false, and
  every later synthetic input goes into the void. Clear dialogs that contain
  no editable element before concluding anything about the input channel.

**A leftover dialog is still worth clearing before any of this.** An
editor-less `[role="dialog"]` captures focus, `btn.focus()` returns without
throwing, and `document.activeElement === btn` is false. Every later synthetic
input then goes into the void and reads as "X ignores automation". Two of them
were open at once. Clear dialogs that contain no editable element first, and
only then conclude anything about the input channel.

**Do not open several tabs to work around this.** A new tab does not change
what X accepts, and the user's rule is one X tab.

Two further corrections that cost real time, recorded so they are not repeated:

- **Counting editors does not detect the reply box.** The main composer is
  already in any page-wide list of editables, so a reply box appearing does not
  change the count. Find the editor by scoping to a visible dialog, not by
  comparing totals.
- **The composer is not the reply box, and a cleared composer proves nothing.**
  X empties the composer after a successful send. Composer length zero is
  ambiguous between "sent" and "never typed". Verify against the target's
  social context, a returned status id, and `in_reply_to`.

## Telling a reply from a standalone post

**The url cannot do this.** Clicking `[data-testid="reply"]` navigates to
`https://x.com/compose/post` — the same url the standalone composer uses. A
url-only classifier is wrong in both directions: it rejects a perfectly good
reply box, and it waves through three standalone posts that were meant to be
replies.

The only reliable signal is the visible dialog text — the reply dialog ends
with `回复 @someone` (Replying to @someone). Read it before typing anything.

Confirming it is a real reply afterwards: open the **target's** status page and
read the article order. The target's article is first, yours is after it. That
is the one check that proved itself repeatedly; a sent reply also renders as
its own top-level article, not nested under the target.

## A reply, step by step

What actually works, in order. Everything below was measured on 12 replies
published and independently verified.

1. **Navigate to the target's status page.** Stable in a way a virtualised
   result list is not, and the parent post is on screen.
2. **Assert the handle belongs to that id.** Read the first article's author on
   the page. A matcher that resolves a handle and a pid independently can hand
   you a handle from one post and an id from another's — which would @-mention
   the wrong person in an unrelated thread. Abort on mismatch. This is not
   hypothetical: a stale log showed one topic matching `@saltyAom` while the id
   it carried belonged to `@AnkanXplorer`.
3. **Click `[data-testid="reply"]`** on that page. Do not `scrollIntoView` — it
   makes the target invalid in a virtualised list. Scroll the window
   instead.

   **Measured 2026-10-09: this click stopped opening the box, and the script now
   refuses rather than typing blind.** A synthesised mousedown/mouseup on the
   control changes nothing; with the editor-less overlays cleared, focus does
   land on it, but X ignores a synthesised Enter and Space. The symptom is
   `open reply: {'opened': True, 'top': N}` — the measured position of the
   control — followed by `NOT SENDING - the reply box did not open`. A real click
   is needed and taking the mouse is forbidden, so **the reply leg of
   `engage_feed.py` cannot complete unattended on this browser**; the honest
   report is 0 replies, not a retry. Re-measure with one manual click before
   assuming it is still blocked — this section already records that "X refuses
   synthetic input" was a script bug four separate times.
4. **Confirm `回复 @someone` is in the dialog**, and that the editor took
   focus. Refuse if not.
5. **One `insertText` for the whole body**, then **compare the editor's
   `textContent` against the source character for character.** Not length — X
   renders each newline as an element. Never send on "the button is enabled".
6. **Send.**
7. **Verify by opening the target's page and reading the article order.** Wait
   for the thread to render — a reply is not always present in the first
   load, and concluding from one sample produces false failures.

## Verify from YOUR reply's page, not only the target's

When the target has posted several times in a row, opening "the target's
status page" is ambiguous — the two posts can look near-identical, and
verification lands on the wrong one. Measured: verification opened a
neighbouring post by the same author and reported "not a reply" for a reply
that had genuinely published.

Open **your own reply's status id** instead. That page names the account it
replies to and always shows the parent, so it settles the question in one
read. When the target's own page is unreadable, fall back to your
`/with_replies` tab and match on the reply's opening words.

## One browser instance, or the socket dies

Running several headless Chrome instances against the same debugging port
produces a port that answers while the page renderer no longer does: CDP
`/json/version` is fine, `Runtime.evaluate` times out forever. Measured as
"CDP connection timed out" mid-run, with no crash report anywhere.

Before blaming the socket, count what you started:

```bash
ps -eo pid,command | grep -c '[r]emote-debugging-port=9240'
```

More than one instance is the cause. `pkill -9 -f remote-debugging-port=9240`,
confirm the port is free, then start exactly one. The failure looks like a
network problem and is a process-management problem.

## Three ways verification lied, and what they share

All three were reported as *failure* for work that had genuinely published.
Each proves "something appeared", not "the right thing appeared":

| the check | what it actually proved | the fix |
|---|---|---|
| look for a child article under the target **on the search results page** | nothing — search results do not render reply threads at all | verify on the target's page, or on your own `/with_replies` tab |
| profile `/with_replies`, break on first own post found | an *older* post from earlier in the day | keep scrolling past the first hit until the page settles |
| profile, "a post of mine appeared that is not in the baseline" | any new post, including an unrelated one | require the text to start with **this** reply's first line, and seed the baseline before sending |

**Do not stop a check the moment it looks satisfied.** A lazy timeline needs a
few extra scroll rounds after the first hit before the newest item has
rendered.

And **one check failing is not proof the post failed.** Measured four times in
one session: a single read of the target's status page reported "no reply of
mine" for replies that had genuinely published, because the thread had not
finished rendering. `send: ok` plus an exact pre-send character compare is
strong evidence; a negative read from a freshly navigated page is weak. When
the two disagree, re-read — preferably from a *different* surface (your
`/with_replies` tab) rather than re-sending.

The cost of getting this backwards in the other direction is a duplicate post
to a real person, so a negative is never grounds for an immediate retry.

## Every step that changes the surface must put it back

Navigating to your profile to seed the baseline leaves the tab **on your
profile**. The scan that follows then reads your own timeline — five of your
posts plus five of someone else's — and reports "no match" for a target that
was sitting on the correct page all along. Same class of bug, three times, in
three places: the baseline step, a `wait_for_results` that measured 32 "results"
while the url was `/with_replies`, and a url-settle check nested inside the
`if` that only runs when navigation *fails* (so it silently never ran).

**Assert the surface unconditionally**, not only in the failure branch: the
url must be what you asked for, there must be articles, and they must not all
be your own. Compare *position*, not just url — a page can have the right url
and still be scrolled 131,618px deep into stale content.

## Keyword search re-randomizes; author-scoped search does not

Six identical loads of one keyword search returned 12, 14, 15, 12, 13 and 14
articles, and a post that had been visible once was in none of them. An
author-scoped query (`from:handle`) gives a stable set. Scope narrows where to
look — the content match still has to happen inside it.

Also: search results render lazily. `Page.navigate` plus a fixed sleep and
then scroll-to-top lands *before* the results exist — measured 0 articles
against a page that had 17 a moment later. Poll for content, do not sleep a
guessed interval.

And a long automation run keeps navigating while the result set churns under
it. Re-load the surface periodically instead of scrolling one load for a
hundred rounds.

## Exit non-zero when nothing was sent

A run that sends nothing and exits 0 is indistinguishable, to a human reading
a notification, from a run that sent everything. That cost real confusion —
several "completed normally" notices turned out to be runs that had sent
nothing at all.

```
raise SystemExit(0 if sent else 1)
```

## What to write in a reply

The replies that work are the ones that answer the post. Every one that
worked conceded something real before making its point — "that is fair, and
the frontend half is not what we solve", "this measures scaffolding, not the
language", "it does not make generated code more readable". A reply that
corrects its own subject, states what it does not do, and only then says
what it does is read as an answer. A repository link with no argument around
it is a link drop.

Do not reply to posts that merely share a vocabulary. Three test posts were
deleted on sight — posted to the right people, about nothing.

## The account handle is read live, never hardcoded

Every script once carried `ME = "eastspire_sheng"`. The account was renamed to
**@vshengbro** (2026-10, same rename as the GitHub account) and each hardcoded
copy broke in its own way: reply verification matched nothing, so sends that
had landed were reported NOT VERIFIED, and the feed filter stopped excluding
the account's own posts, so one 01:00 run replied to its own promotional
posts. `scripts/handle.py` reads the handle from the nav bar's
`AppTabBar_Profile_Link` at connect time; the module constant is only the
fallback before the page paints. Any new script in this directory takes the
handle from `handle.live(c)`, never from a literal.

## Keyword targeting needs a blocklist, rotation, and cross-run state

Measured the day the 30-minute engagement job was added:

- **A keyword match is not a reason.** The first dry-run target of the bare
  TOPICS filter was an adult-content post caught by 模型; the next was a
  TOKEN2049 crypto-booth post caught by "token". `engage_feed.py` carries a
  BLOCK list (adult, scam, crypto-shill vocabulary) that vetoes a post
  whatever else it says.
- **48 runs a day cannot send one text.** The per-run loop used to start at
  `01.txt` every invocation. The state file
  (`~/.hermes/cron/output/x-engagement/answered_sids.json`, `X_ENGAGE_STATE`
  overrides) now persists both the answered status ids AND the next reply-text
  index, shared between the 30-minute job and the nightly one: no post gets
  two replies, and the same text never goes out twice in a row.
- **Two runs can be scheduled on top of each other.** The nightly 36-reply
  run overlaps any :00/:30 tick. `engage_feed.py` holds a non-blocking
  `flock` (`engage.lock` next to the state file); a second run prints the
  skip line and exits 0. A skipped run is correct, not a failure.

## A reply verified by the 30-minute cadence

`engage_feed.py <port> --likes 1 --replies 1` is one unit of work: home tab,
one like, one reply bound live to its target, `VERIFIED reply by @<handle>`
from the reply's own page, state saved. The cron job `40defaea9d3a` runs it
every 30 minutes; the nightly job `b821f8f18340` runs the same script with
`--likes 14 --replies 36`. Both honour the same lock and state file.
