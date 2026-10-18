# Automating a real, logged-in account through CDP

Applies when the target is the user's own authenticated session — a social
feed, a SaaS dashboard, a mail client — rather than a throwaway profile. The
techniques in SKILL.md (targets, `Runtime.evaluate`, readiness polling) all
hold; what changes is the blast radius of a mistake.

## Pick the least-privileged channel that can do the job

Rank before writing any script. Prefer the channel that cannot touch user
data, not the one that is fastest to start.

| Channel | Touches the user's session? | When to use |
|---|---|---|
| Official API with the user's own token | No — a separate, legible record of what was posted | Default for posting/replying/DM. Token setup is a user action; never ask for the secret in chat. |
| CLI over that API | No | Same, with convenient shortcuts. |
| CDP/browser tool into a real-profile browser | **Yes** — the same tabs, cookies and drafts | Read-only research and inspection. Consumer sites refuse headless, so this also means headed. |
| Native input on the real app (OS keystrokes) | **Yes, and irreversibly** | Viable for writes once the three gates hold. |

**A logged-in web session is usually read-only in practice, not by policy.**
Modern web apps typically won't accept a captured web-session token on their
write endpoints — the error names the required auth types (e.g. "Supported
authentication types are [OAuth 1.0a User Context, OAuth 2.0 User Context]").
That's a server-side decision, not a harness bug, and more credential capture
or a guessed operation id won't change it. So: establish whether the official
API is available; if not, **say so and deliver the finished artifact for the
user to publish** rather than escalating through riskier channels. Escalating
past a refused boundary is what turns "I could not post" into "I destroyed
your work".

**The user's restrictions are constraints on the method, not preferences about
phrasing.** "Use the browser", "don't paste", "no headless" — satisfy them with
a different technique and say which method is blocked, rather than reporting
the restriction as a blocker or silently falling back to a forbidden channel
because it was easier.

## Before touching a real account, inventory it — read-only

```bash
curl -s http://127.0.0.1:<port>/json/list \
  | jq -r '.[]|select(.type=="page")|.url' | sort | uniq -c | sort -rn
```

Multiple targets on one app URL is the signal that matters: those are tabs
with live state — a compose box mid-draft, a half-filled form. A count of one
doesn't prove it's empty; an editor that merely looks blank still holds text.

**A clean inventory doesn't mean the editor will be empty.** A compose route
restores unpublished content into a tab you just created, and successive fresh
tabs return *different* content. Two checks distinguish that from a stale
selector or a mis-targeted socket — both are needed before concluding "the
editor is empty":

```python
assert c.js("location.href") == the_url_we_requested        # attached to OUR tab
assert tab["id"] not in {t["id"] for t in http("/json/list")}  # genuinely new
```

If both hold and the editor still has text, the app restores it from its own
storage and **no tab inventory can predict what you'll get**. That makes the
write gates mandatory rather than advisory: "the user says they have no drafts
open" is not verifiable by asking — only the read-back gate protects you.

**Ask the app where restored text lives; don't infer it.** Clear local storage
via the protocol method (never enumerate databases from the page —
`indexedDB.databases()` hangs headless), deliberately excluding cookies:

```python
c.send("Storage.clearDataForOrigin", origin="https://site.tld",
       storageTypes="local_storage,indexeddb,cache_storage,service_workers")
# then open a FRESH compose target and read what it came back with
```

`Storage.clearDataForOrigin` returns success whether or not it removed
anything, so the return value is not the measurement — the next composer is.
Clear storage only after the user said the content is expendable, and say what
you are deleting: IndexedDB for a real app holds more than drafts.

**Report what you found and stop.** Do not tidy — closing, reloading or
navigating another tab to "get a clean slate" destroys work that exists nowhere
else. Tab count is evidence about the user's state, not clutter.

## The site may refuse headless, and the refusal looks like an empty page

A logged-in consumer service answers `403` to a headless fingerprint while
serving the same URL to headed Chrome. Cookies are irrelevant; re-copying the
profile changes nothing. Settle it with a control from the same machine:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://site.tld/
```

`200` from curl + `403` in the browser means the fingerprint is the cause:
relaunch headed. High-frequency retries against a 403 make the block worse.

**The dangerous part is that a refusal reports itself as an empty page.** The
telltale is the navigation having failed, not the content being short:

```python
href = c.js("location.href")
if not href.startswith("https://site.tld"):   # e.g. chrome-error://chromewebdata/
    raise RuntimeError(f"navigation was refused, not empty: {href}")
```

Every existence check on that page returns "empty", so "the composer is blank"
reads as verified success on a page that isn't the site. Assert the href before
trusting any content read; treat a below-threshold page on a known-good URL as a
failure, never an empty result.

## The three gates before any write

```python
# Gate 1 — bind to the target you created, never one picked from a list.
tab = http("/json/new?" + quote(url), method="PUT")
c = Cdp(tab["webSocketDebuggerUrl"])

# Gate 2 — the field must be empty, or hold only text this run put there.
before = c.js("document.querySelector('[data-testid=\"...\"]')?.textContent")
if before and before.strip():
    raise RuntimeError("field already holds text that is not ours: " + repr(before[:200]))

# ...write...

# Gate 3 — read back and compare BEFORE any submit/click.
after = c.js("document.querySelector('[data-testid=\"...\"]')?.textContent")
assert "".join(after.split()) == "".join(INTENDED.split())
```

**Gate 3 is the one that actually fires.** Gate 2 assumes you can predict the
state; when the app restores state you cannot, and only the diff catches it. In
the case that produced this rule, gates 1 and 2 both passed — right tab, right
socket — and the editor still held a complete unrelated draft the user had
written; the diff refused and a dozen unpublished drafts survived.

**Never loosen the comparison to make a run pass.** Matching a prefix, or
comparing only the first N characters, converts this gate into the exact hazard
it exists to prevent. If the diff fails, stop and report — the alternative is
publishing someone else's unfinished work.

Normalise whitespace when comparing: `innerText` and `textContent` disagree
about blank lines inside a contenteditable, and paragraph breaks are cosmetic.
A rich-text editor stores newlines as *elements*, so `textContent` has no
newline characters at all and an exact compare can never pass for multi-line
text — comparing non-space characters preserves the guarantee that matters (a
dropped character can't hide behind a space). Use `len(got) - len(want)`
matching the source's newline count as a diagnostic that the editor normalised
layout; any other delta is a real difference worth reporting.

## Proving which node you are editing

**A rich-text editor is a `contenteditable` DIV, and a testid whose name
mentions "text" is often a decoy** — a sibling display node whose `textContent`
goes stale, so working input reads as a no-op. Identify the editing node before
concluding anything is undrivable:

```js
(() => {
  const wrap = document.querySelector('[data-testid="tweetTextarea_0"]');
  const ed = [wrap, ...wrap.querySelectorAll('*')].filter(
    e => e.getAttribute('contenteditable') === 'true' || e.isContentEditable);
  return JSON.stringify(ed.map(e => ({
    tag: e.tagName, testid: e.getAttribute('data-testid'),
    role: e.getAttribute('role'), text: e.textContent.slice(0, 40) })));
})()
```

**Before reporting any rich-text target as undrivable, re-run the node probe
against the selector you actually used and re-derive the claim.** A technique
that fails against one node says nothing about another — the most expensive
mistake available here is a "this framework cannot be driven" conclusion the
user then acts on.

## Writing through the composer

A write to a rich-text composer is three tools doing three jobs, because no
single one does all three correctly:

| Step | Tool | Why that one |
|---|---|---|
| Clear the field | **CDP** — select all, `execCommand('delete')`, caret to end | The only reliable way to know a restored draft is gone, on the real editor node. |
| Write the text | **`computer_use` `set_value`** | A DOM write or a CDP key event never updates the framework's state; the AX tree exposes the real editor as a text field and setting its value does. |
| Verify and submit | **CDP** | Read back through the same node, compare, then click. |

- **Clear once, before the first write — never after.** Clearing wipes what the
  write just produced, and an empty state then reads as "the write didn't land".
- **Non-Latin text needs `set_value`; a keystroke path cannot send it** (a
  159-character Chinese post came back `delivered 0 of 159` via key events and
  arrived intact via `set_value`). Reserve keystrokes for ASCII.
- **`set_value` collapses paragraph breaks** — cosmetically wrong, still
  verifiable under the whitespace-normalised comparison, and still far better
  than a keystroke path that cannot send the text at all.
- **Pure CDP has no reliable multi-line write to a rich editor.**
  `Input.insertText` with a multi-line string writes nothing, and line-by-line
  writes only the first line — Enter rebuilds the editor's internal state and
  later inserts are dropped.
- **Don't route text through the clipboard.** It needs a focused document
  (`Page.bringToFront`) and a real paste is refused anyway, via key event or
  `execCommand('paste')` — that only adds a failure mode and leaves the user's
  clipboard holding whatever was there.
- **AX indices go stale on every re-render** (`element_outside_target_window`).
  Re-capture before addressing an element; the index list is truncated at its
  cap, so scroll into view and capture again rather than guessing.

**Never infer the text from the button state — they are independent.** An empty
composer and a 23-character one both read `disabled: false`, while a full post
read `disabled: true`. Gate 3 is the only reading that means anything about the
write. Select the submit button by `data-testid` and read the whole list
rather than label-regex-plus-`.find()`, because one composer carries two
(`tweetButton` and `tweetButtonInline`) and the regex may be reporting on the
other element.

**A permanently disabled button with clean text usually means the app is waiting
on something asynchronous**, in this order: (1) missing reply context — a reply
route renders without it (`hasReplyContext: false`) and needs the inline box
under the actual post; (2) an unresolved link preview — a URL makes the app hold
the button until the preview loads, and when *the browser cannot reach that
URL* (`ERR TypeError: Failed to fetch` from inside the page) it never resolves.
That's a property of the machine's network, not of the automation: the remedies
are the user's (reword without the URL, configure egress, publish by hand), so
report it instead of retrying an unbounded wait.

**Read the reply target from a structured field, never by regexing the dialog.**
`dlg.innerText.match(/Replying to\s*@(\w+)/)` is a value fabricator: when a saved
draft replaces the header with a plain `Draft` label, a looser fallback sweep
matches an unrelated handle further down and hands the caller a confident, wrong
answer. Ask the element that owns the identity
(`dlg.querySelector('[data-testid="User-Name"]')`), assert it equals the handle
you meant to answer before typing, and log the raw header as a diagnostic
rather than parsing it. The cost is not a failed send — it's a send to the wrong
human.

**A reply composer is a dialog you open per target.** Modal containers
accumulate: after several targets the DOM holds a hidden dialog per reply
already made. Remove *all* dialogs before opening the next one, and read the
identity of the **last** dialog in the DOM — the first is the oldest, not the
current.

## Driving a live feed

An infinite feed replaces its contents continuously and virtualises what is on
screen, which breaks the obvious loop.

- **Re-read the page each iteration; never carry a target id across steps.** An
  id saved by an earlier read names something no longer on screen.
- **Dedupe by the id you just used, and mark it before you act.** A virtualised
  list keeps an article at the same offset long after the loop scrolls past it,
  so `next(match ...)` re-picks the same first match every pass — three replies
  to one post instead of one each. Marking before the write is deliberate: a
  reply that fails to verify has still consumed that post's one answer.
- **A scroll is not a navigation**, so it's the sanctioned way to reach new
  content. Detect the end by comparing the distinct-id count before and after a
  scroll: no growth means the feed is exhausted — stop and report the real count
  instead of looping or padding with repeats.
- **Reach new content through a control already on screen.** A nav tab is an
  anchor in the DOM; clicking it returns to the feed in place, where
  `location.assign` would be a page load the user has to confirm.
- **A changed URL is not a loaded page.** `Page.navigate` returns before render;
  asserting the URL alone lets every downstream step run against the previous
  page. Gate on content, not URL:

  ```python
  tab.send("Page.navigate", url=target_url)
  for _ in range(16):
      time.sleep(1.4)
      if (tab.js("document.querySelectorAll('article').length") or 0) > 0:
          return True
  raise RuntimeError(f"url ok but no articles: {tab.js('location.href')}")
  ```

  The same rule applies to any assertion resolving an owner or identity from
  page content: a `None` there is a **load-state failure**, not "not found".
  Never let an empty read fall through to a default or fallback path.

**Dedupe across processes, not just within one — and record only confirmed
sends.** Persist the sent-id set to disk; an in-memory `done` set doesn't
survive a restart, and a batch driver running the same topic in two processes
posts twice. Write the marker **after** the send is confirmed (a pre-write
marker turns every transient failure into a permanent skip) and key it on
**content**, not a handle or post id — the same author posts repeatedly and
several posts can belong to one draft. A duplicate sent to a real person is the
most expensive failure here: it then needs locating, verifying by author **and
full body**, and deleting. Drive the skip decision from that same persisted set
so a run starts at the pending work rather than re-paying for every completed
item.

## Never pad a count to reach a target

If the work ran out — fewer replies written than requested, or the feed ran
dry — the honest deliverable is the smaller number, reported as two facts: how
many verified, and how many were attempted. Re-posting the same text to hit a
number, or composing new bodies on the fly to fill the gap, turns a measured
shortfall into a fabricated one. **Know the yield before quoting a number**: a
harvested candidate pool is mostly noise (across 601 collected candidates, a
topic/length filter left 459 and reading those left roughly fifteen worth
answering), so measure the ratio once rather than implying a per-item
conversion you haven't established.

When the target exceeds what the pool supports, that's a **scope decision for
the user, not a licence to lower the bar** — the honest options are to stop
early with a smaller verified count, widen the topic scope (accepting less
relevance), or relax the quality floor (turning the work into the mechanical
link-dropping the task exists to avoid). Put those to the user with the
measured yield attached; don't pick one silently, because each spends the
account's credibility differently. Bodies should exist as files the publisher's
own checks have already run (ownership, length, stray-token) rather than being
composed at send time — a body generated during the run has passed none of
them.

## Stop and report rather than proceeding when

- **Unpublished user content is visible in the target.** A failed post is
  noise; a destroyed draft is a loss the user cannot undo.
- **The task needs a credential you were not given.** Say which one and where
  to get it. Never accept a secret pasted into chat.
- **Read-back disagrees with intent at any point.** Don't "try the submit and
  see".
- **A previous attempt was declared impossible and then succeeded.** Each time
  a different input channel "proved" the target undrivable, the finding was a
  fact about the node or channel probed — not about the target. Re-derive the
  conclusion from a corrected probe before reporting a wall, and correct the
  earlier claim explicitly rather than quietly superseding it.
- **The blocker is environmental** (unreachable host, refused fingerprint,
  machine capability limit). That's a fact to hand to the user with the
  options — not a technique to keep retrying.

In each case: state plainly what you observed, state plainly that you did not
modify it, and offer the options. That report is the deliverable.

## A wrong conclusion costs more than a slow one

The most expensive failure mode is not failing to post — it's reporting a
confident "this is impossible" that a later, corrected probe overturns. The
user then decides on a false premise.

- **Attribute every negative result to what you actually probed.** "Every input
  channel fails" is only true of the channels tried, against the node selected.
  Name the node and channel in every negative claim.
- **Prefer a probe that reports a typed value over one that reports presence.**
  "The control exists" and "the control was accepted" get conflated repeatedly.
- **When several distinct failures all say "refused", suspect the harness
  before the site.** A real refusal is one bug with one signature, not four
  unrelated ones; when four separate harness bugs each reported "the site
  refused", nothing about the site had changed.
- **When one measurement contradicts another, resolve it before continuing.**
  Opposing readings mean at least one is wrong.

Report a wall only after the corrected probe still hits it. If an earlier claim
is later disproved, say so in the same terms it was made.
