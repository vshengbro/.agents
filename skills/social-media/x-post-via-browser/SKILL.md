---
name: x-post-via-browser
description: "Use when acting on X/Twitter in the user's logged-in browser. Post, reply, quote, repost, edit, delete, upload media, like, bookmark, read a profile or thread, work the feed — and the traps that make a working path read as dead."
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

Exercised on a Premium account: four long posts of 608–1060 characters
published and verified, then a 27-post series published on a timer, then 12
replies published with each verified on the target's own page — which
corrected the reply path's stated cause.

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

### The shortest path that published a real post

Measured 2026-12-11 on a Premium account, one end-to-end run, 1250
characters, verified off the timeline. Five steps, in this order:

```bash
# 1. the tab must be VISIBLE — this is the step that is easy to skip and
#    that decides whether anything below can work at all
python3 scripts/preflight.py          # 5 checks; non-zero means stop

# 2. the copy must survive X's linkifier — check BEFORE typing a character
python3 scripts/check_copy.py <copy.json>

# 3. type and compare; this clicks nothing
python3 scripts/publish.py <port> --post 0

# 4. only if step 3 printed match=True and urls_ok=True
python3 scripts/publish.py <port> --post 0 --go

# 5. prove it landed — the click is not the outcome
python3 scripts/whose_posts.py <port>          # find the status id
python3 scripts/verify_post.py <port> <sid> <copy.json> 0
```

**`document.visibilityState` must be `"visible"` before anything else.** A
backgrounded x.com tab reads `hidden` with the composer mounted and empty,
which looks identical to a working page. `Target.activateTarget` flips it and
touches no pointer and no OS focus:

```python
tab.send("Target.activateTarget", targetId=tab_target_id)
```

It flipped `hidden` → `visible` on the headed surface in the measured run,
and it is the only step in this flow that is not a read. Every other step
before the click is read-only, so a run that stops at any of them has changed
nothing on the account.

**Preconditions, all five, and what each one prevents.** Checking them costs
one round trip and each failure looks like something else:

| Check | If it fails |
|---|---|
| `visibilityState === "visible"` | editor may never mount; reads as "X ignored automation" |
| exactly one visible editor | two `tweetTextarea_0` nodes, the decoy pair |
| composer length 0 | a non-empty box is **refused, never cleared** |
| `SideNav_NewTweet_Button` present | otherwise the compose click opens nothing |
| a `tweetButton*` is mounted | only `tweetButtonInline` mounts; `tweetButton` often absent |

### What the measured run actually cost

Four things were true that were not true before it, and each would have
failed the run silently:

- **`--headed` is the surface.** `ensure_browser.py` passes it
  unconditionally now, and both the publish path and the reply path were
  used successfully on it.
- **The compose control is `SideNav_NewTweet_Button`,** underscore before
  `Button`. The short spelling matches zero nodes and was masked by the
  `a[href*="/compose/post"]` fallback in the same selector list.
- **`NO_WARMUP_BLOCK` is not always fatal, and always needs explaining.** The
  warm-up space is removed by a pass that deletes forward from the start of
  each block; a body whose block structure does not match defeats it, and the
  run reported `match=True` anyway because the canonical compare strips
  whitespace. Before accepting that, confirm the editor holds the source
  exactly:

  ```python
  FLAT(STRIP(editor_innerText)) == FLAT(STRIP(source))
  ```

  A true comparison is the only thing that separates "the space did not
  matter" from "the text is mangled and the gate cannot see it". This is the
  one known defect left in the publish path.
- **`CLICK tweetButtonInline` proves nothing.** The published post was proved
  by `whose_posts.py` finding it under `MINE` and `verify_post.py`
  confirming author, text prefix and link card.

### The copy, before it is typed

Two refusals that fire before a character is written, both because X mangles
them rather than the script:

- **No dotted token that is not an intended URL.** X linkifies `crates.io`
  and the span it replaces reads back as a line break, which splits one post
  into two — and both ship. Write "crates io".
- **No version numbers.** `0.28.12` is a dotted token with the same trap.

A 1250-character post containing one URL passed both checks unchanged.

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
# $X_LAUNCHER is resolved for you; --port must match $X_PORT
bash "$X_LAUNCHER" --headed --port "$X_PORT" --fresh --no-tab
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
| `scripts/check_copy.py` | Refuses a copy X would mangle before a character is typed — dotted tokens that are not URLs, version numbers, empty bodies. Offline; no browser. |
| `scripts/preflight.py` | Reads all five publish preconditions (visibility, one editor, empty composer, compose control, post button) and refuses to continue. Read-only. Run it before `publish.py`. |
| `scripts/verify_no_unsafe_posting.py` | The commit gate. `--self-test` proves every rule fires. |

```bash
# once, and only if no instance is up
bash "$X_LAUNCHER" --headed --port "$X_PORT" --fresh --no-tab

python3 scripts/publish.py "$X_PORT" --show        # read the copy first
python3 scripts/publish.py "$X_PORT" --post 0      # type and compare, no click
python3 scripts/publish.py "$X_PORT" --post 0 --go # click
python3 scripts/whose_posts.py "$X_PORT"           # find the status id
python3 scripts/verify_post.py "$X_PORT" <sid> x_copy_example.json 0

X_COPY=/path/to/other.json python3 scripts/publish.py "$X_PORT" --post 0 --go
```

The copy defaults to `scripts/x_copy_example.json` next to the script — posts
that were actually published. Replace it or point `X_COPY` elsewhere; the
content is yours, not the skill's.

## Configuration is environment-only

No account name, port, path or owner is baked into the code. Every
environment-specific value has a working default, so a fresh checkout runs
with nothing set; the variables exist to override that default, not to make
it work.

**Every one of these is read at CALL time, inside the function that needs
it — never at import time.** This is deliberate and it is easy to get wrong:
a module-level `PORT = os.environ.get("X_PORT", ...)` freezes the value the
moment the module is imported, so exporting `X_PORT` afterwards — which is
exactly what a cron wrapper or a shell that sets it after the import chain
starts does — silently has no effect. If you add a variable, read it inside
the function, not at the top of the module.

| Variable | Default | Meaning |
|---|---|---|
| `X_PORT` | the browser's CDP debug port, read from `~/.hermes/state/chrome-real-profile.port` | which browser instance to drive |
| `X_SITE` | `x.com` | the site whose tabs count as "the" tab |
| `X_HANDLE` | empty | handle fallback for a page that has not painted yet; empty means "read it live or refuse" |
| `X_LAUNCHER` | `chrome-real-profile-launch/scripts/run.sh`, found by glob | the script that starts the real-profile browser |
| `X_STATE_DIR` | `~/.hermes/state/x-post-via-browser` | where per-feature state files are written |
| `X_GITHUB_OWNERS` | owners derived from real git remotes under `~/code` | which repositories this account may promote; an empty set **refuses** promotion rather than widening the gate |
| `X_TOPICS` | the built-in topic list | keywords that select a feed post as a candidate |
| `X_BLOCK` | the built-in adult / scam / crypto-shill list | vocabulary that vetoes a post whatever else it says |
| `X_COPY` | `scripts/x_copy_example.json` | the post text to publish |
| `X_ENGAGE_STATE` | `~/.hermes/cron/output/x-engagement/answered_sids.json` | answered status ids and the reply-text rotation index, shared across runs |
| `X_QUEUE` | the queue file beside the scripts | which items a queue runner takes next |
| `X_POST_STATE` | the state file beside the scripts | which queue items have already been posted |

## The gate: what is actually wired

`verify_no_unsafe_posting.py` is a real script with real rules. The intended
wiring — and the part worth checking, because it is what was broken — is the
**global pre-commit hook** at `~/.git-hooks/pre-commit`, which git finds
through `core.hooksPath` (`git config --global core.hooksPath
~/.git-hooks`). That hook is supposed to run the guard over the **staged**
Python files and exit non-zero on a violation, which blocks the commit.

**Status as of writing: the hook does not contain that call yet.** An empty
`grep -n "verify_no_unsafe_posting" ~/.git-hooks/pre-commit` means the gate is
**documented but not enforced** and the rules below are advice, not a gate.
Verify before trusting this section rather than the reverse:

```bash
grep -n "verify_no_unsafe_posting" ~/.git-hooks/pre-commit
```

That distinction is the whole point: a rule that lives only in this document
is a rule the next person breaks without knowing why, and that has happened to
every rule on this list.

The shape the wiring is meant to have, and the one to hold it to:

- **It is a staged-file gate, not a full-repo audit.** It only sees what is
  about to be committed. A violation already sitting in the working tree, or
  in history, is invisible to it.
- **It fires only when a staged path is under
  `skills/social-media/x-post-via-browser/scripts/`.** Every other repo, and
  every other path, skips it silently and costs nothing.
- **It runs before the hook's non-Rust early-exit.** That ordering matters:
  the hook skips repos with no `Cargo.toml`, and the skills repo has none, so
  a gate placed after that check would never execute here at all. That was
  the original defect — the section that used to sit here claimed the gate
  "applies to every repo, including the skills repo", which was true only of
  the intent.
- **It is bypassed by `git commit --no-verify`,** like every hook.

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

`post_reply.py` now opens a reply box, types with real key
events, sends, and reads the reply back off the timeline. Four replies
published and verified live, one of them carrying all the fixes below. Nothing
here needed the API, a real pointer, or the OS keyboard.

The early finding — "X refuses synthetic input" — was **four script bugs,
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
- **A reply must carry a repository from `org_repos.owner_set()`**, or it is refused
  before a character is typed. A reply that links someone else's project is not
  promotion of this account's work.

## Replies are composed live, never pre-written

**The `replies/*.txt` pool this section described is
deleted.** The account owner's standing rule: canned reply files are forbidden;
every reply is composed at send time by the firing agent, grounded in source
read during the same run. See "Reply content is composed live, never
pre-written" below for the flow.

Two rules from the pool era still hold:

- **One reply per post, deduped by status id.** The feed is virtualised: a post
  stays in the DOM at the same offset long after the loop scrolls past it, so
  without dedupe three of four replies go to the same first match. The shared
  state file carries the answered ids across runs.
- **Never re-post a reply text to reach a count.** If nothing earned a reply,
  the honest answer is the smaller number.

## The reply editor does not mount in a hidden tab — activate it first

**Corrected. This supersedes the "X refuses synthetic input"
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

`activateTarget` is equivalent to raising a minimised window. It moves no
pointer and takes no OS focus, so it does not violate the
no-mouse/no-keyboard rules. Activate at the top of every entry point, and
re-activate after each navigation — it flips back to `hidden` on its own.

Measured on the headed surface (2026-10-12): a backgrounded x.com tab read
`visibility: hidden` with the composer mounted and empty, and
`Target.activateTarget` flipped it to `visible` with nothing else touched.

**Check it before diagnosing anything else.** One line:
`tab.js("document.visibilityState")` must be `"visible"`.

## The shortest path that replied to a real post

Measured 2026-12-11 on the headed surface. `post_reply.py` published a
307-character Chinese reply and verified it off the timeline. The reply leg
was previously marked blocked on this surface, so this is the run that
settled it.

```bash
# 1. read candidates from the live feed — nothing is sent or marked
python3 scripts/engage_feed.py <port> --suggest 6 --likes 0

# 2. EXPAND the chosen post before writing anything about it
#    (see "read the whole post" below — this step is not optional)

# 3. compose, then send. --allow-no-repo is required for an opinion reply;
#    without it the run refuses before typing, by design
python3 scripts/post_reply.py <port> <sid> <reply.txt> --allow-no-repo

# 4. expand the PUBLISHED reply on the timeline, then compare it
```

The run's own output, unmodified:

```
no repository link — opinion reply (--allow-no-repo)
  carries None, 307 characters
open reply: {'opened': True, 'top': 844}
  reply box: new=True in_dialog=True editors=2 send=tweetButton:dis
  typing 307 characters
  LEN 301 want 307 exact=True
SEND {'sent': 'tweetButton'}
VERIFIED reply by @vshengbro: 2109649655340712288 reply_marked=True
```

**`new=True in_dialog=True` is the line that matters.** On this surface the
reply box DID mount as a dialog — the thing that was measured broken here
earlier. That single field is the whole safety margin: when it is False, the
gate refuses, and that refusal is correct. Read it before anything is typed.

**`LEN 301 want 307 exact=True` is not a contradiction.** X renders each
newline as an element, so a source with N newlines reads back N characters
short. The exact compare already accounts for it, which is why the raw
length is never the gate. Do not "fix" it.

**An opinion reply needs `--allow-no-repo`.** The first attempt refused with
`REFUSING - no repository from this account's GitHub owners`. That refusal
is the promotion rule working, not a fault: a reply that names no repository
of this account's is not promotion of its work. The account owner granted a
standing exception for opinion replies, and `--allow-no-repo` is how a run
states it. Without the flag the refusal happens before a character is typed,
which is the correct place for it.

### Read the whole post before answering it

The feed returns a PREFIX. Measured on this run: the chosen post arrived
clipped at "这个 PR 是 Hatoba（我在做的 SSH", with
`[data-testid="tweet-text-show-more-link"]` present on the article. The full
post was three paragraphs longer and contained the actual argument — that
the twenty-nine commits were all correct fixes to a design assumption nobody
questioned.

A reply composed against the prefix would have been about a story about a
PR, instead of about the thing the author was actually saying.

```javascript
// click show-more on THAT article only — an on-screen control, opens in place
const a = [...document.querySelectorAll('article')].find(...);
a.querySelector('[data-testid="tweet-text-show-more-link"]').click();
```

**The same trap applies to verifying your own reply.** After publishing, the
new reply is clipped on the timeline too — a 307-character reply reads back
as ~80 characters, and an exact compare against the source returns `False`
for a reply that is perfectly correct. Expand it first:

```
still clipped: False
exact match vs source: True
```

Without the expand step the honest report is "could not verify", never
"mismatch". A truncated read is not evidence of a wrong post — this is the
fourth time the same lesson appeared, and it is why every verification here
compares a prefix against a prefix.

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

   **Measured: this click stopped opening the box, and the script now
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
ps -eo pid,command | grep -c "[r]emote-debugging-port=$X_PORT"
```

More than one instance is the cause. `pkill -9 -f remote-debugging-port=$X_PORT`,
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

## What the live build actually calls its controls

Measured 2026-10-12 by a read-only DOM census against the signed-in
account — every expression a read, nothing clicked. Recorded because a
selector that is merely believed is a selector that fails silently later.

**The compose control is `SideNav_NewTweet_Button`, with an underscore before
`Button`.** The shorter `SideNav_NewTweetButton` matches **zero** nodes on the
live build. Two selectors survive: `SideNav_NewTweet_Button` and
`a[href*="/compose/post"]`. The publish path had been relying on the second to
cover for the first being wrong, which is why it never visibly broke.

| Control | Live status | Note |
|---|---|---|
| `SideNav_NewTweet_Button` | **PRESENT** | the real one |
| `SideNav_NewTweetButton` | absent | zero nodes |
| `a[href*="/compose/post"]` | PRESENT | the fallback that was silently carrying publishing |
| `appTabBarPostBtn` | absent | absent on this surface |
| `tweetButtonInline` | PRESENT | enabled, `tweetButton` not mounted — the inline button is the only one |
| `reply` / `retweet` / `like` | PRESENT (3 each) | with `aria-label` counts, e.g. `14 次转帖。转帖` |
| `caret` | PRESENT (7) | the overflow menu; also the entry to 编辑/删除 |
| `tweetText` / `tweetTextarea_0` | PRESENT | the decoy pair, both mounted |
| `fileInput` | PRESENT, `type=file` | the composer's media input — so media needs no upload API |
| `User-Name` | PRESENT | profile name cell |
| `AppTabBar_Profile_Link` / `AppTabBar_Home_Link` | PRESENT | nav |
| `SideNav_AccountSwitcher_Button` | PRESENT | the account menu |

**`bookmark`, `removeBookmark`, `share`, `follow` and `unfollow` read as absent
on a feed with three articles on screen.** That is a measurement of the
*default* state: X mounts several of those inside the `caret` overflow menu or
only on hover, and a census that does not hover cannot see them. So "absent
here" is not "does not exist" — it is "not mounted until its own surface is
open", and confirming each one needs the surface it lives on, opened for
that purpose.

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

Every script once carried its own hardcoded `ME = "..."`. The account was
renamed once, and each hardcoded copy broke in its own way: reply
verification matched nothing, so sends that had landed were reported NOT
VERIFIED, and the feed filter stopped excluding the account's own posts, so
one 01:00 run replied to its own promotional posts. `scripts/handle.py` reads
the handle from the nav bar's `AppTabBar_Profile_Link` at connect time; the
module constant is only the fallback before the page paints. Any new script
in this directory takes the handle from `handle.live(c)`, never from a
literal. The fallback itself is now empty unless `X_HANDLE` sets it, so a
rename can no longer be papered over by a stale constant.

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

`engage_feed.py "$X_PORT" --likes 1` is one unit of work for the likes: home
tab, one like, state saved. Replies are a separate explicit step — `--suggest`
to collect candidates, `--reply-to` to send the composed text (see the
live-composition section below). The 30-minute engagement cron runs the pair
on that cadence; the nightly engagement cron runs the same pair with 14 likes
and up to 36 replies. Both honour the same lock and state file.

## Reply content is composed live, never pre-written

Standing rule from the account owner: canned reply files are
forbidden. The firing agent composes every reply at send time, grounded in
source it read during the same run. The scripts carry the mechanics, the
agent carries the words:

1. `engage_feed.py <port> --suggest N` prints up to N live candidates as
   JSON (sid, who, text) and marks nothing — a declined post is not burned.
2. The agent picks the one post it can genuinely answer, reads the LATEST
   source without touching any worktree (`git -C ~/code/<repo> fetch origin
   master`, then `git show origin/master:<path>`), and writes the reply —
   the post's language, one owned repository link at the end when a project
   genuinely answers, a plain opinion with no link when none does.
3. `engage_feed.py <port> --reply-to <sid> --file <path>` sends it through
   post_reply.py and records the sid in the shared state. Opinion replies
   add `--allow-no-repo`; a foreign repository link is refused even then.

**Steps 2 and 3 are two separate invocations, and the feed is virtualised
between them.** Measured: `--suggest 5` returned five candidates,
and by the time the composed reply was sent `--reply-to` reported
`open reply: {'why': 'target not on page'}` → `NOT SENDING - target not on
page` → `NOT MARKED - <sid> stays available for a later batch`. The post had
scrolled out of the DOM; the feed is a window, not a store. The sid survives
in state, so this is a correct refusal and a correct skip — report it and
stop. Do not reopen a tab, re-suggest, or pick a different post to force the
number up. The fix is upstream (the reply leg has to navigate to the target's
status page, which this path does not do), not something to retry at send
time.

## Headed is the only surface; the reply leg is now measured working

**Ruled 2026-10-12 by the account owner: this skill uses the HEADED surface
only.** `ensure_browser.py` passes `--headed` unconditionally and has no mode
parameter, so there is no path left that can start a headless copy.

**The reply leg works on this surface.** Measured 2026-12-11: a reply dialog
mounted headed, `new=True in_dialog=True`, and the reply published and verified
off the timeline. The full run is in "the shortest path that replied to a real
post".

The history is kept because it is why the gate exists. An earlier headed
measurement found the reply control routing to a context-less `/compose/post`
— the MAIN composer, where typing publishes a standalone post under a reply's
intent — and on a clean `/home` headed mounted nothing at all: a click
navigated to `/compose/post`, a full mouse press at the control's coordinates
did the same, and focus+Enter focused nothing.

That was measured with the tab hidden. The current rule is the difference:

```bash
python3 scripts/preflight.py <port>   # tab visible, before anything else
```

`preflight.py` passing is what separates this run from those. A hidden tab is
where the reply control was measured going to the main composer. So
`post_reply.py` keeps its two-surface box gate exactly as it was — that gate
is what stops a reply from publishing as a standalone post, and it is why a
future run fails loudly instead of damaging the account. Read `new=True
in_dialog=True` as the real precondition; when the gate refuses, it is right.
