# Automating a real, logged-in account through CDP

Applies whenever the target is the user's own authenticated session — a social
feed, a SaaS dashboard, a mail client — rather than a throwaway profile. The
techniques in SKILL.md (targets, Runtime.evaluate, readiness polling) all hold;
what changes is the blast radius of a mistake.

## Pick the least-privileged channel that can do the job

Rank the options before writing any script. Prefer the one that cannot touch
user data, not the one that is fastest to start.

| Channel | Touches the user's session? | When to use |
|---|---|---|
| Official API with the user's own token | No — a separate, legible record of what was posted | Default for posting/replying/DM. Token setup is a user action; never ask for the secret in chat. |
| CLI over that API (e.g. `xurl`) | No | Same, with convenient shortcuts. |
| Headless CDP into a real-profile browser | **Yes** — the same tabs, cookies and drafts | Read-only research and inspection. Headless is also refused by most consumer sites (see below). |
| Headed CDP + real OS-level input | **Yes, and irreversibly** | Viable for writes once the three gates hold. See "Writing through the composer" below. |

**Launch headed from the start.** Headless is refused by consumer sites with
bot management, and the refusal is cheap to avoid: `--headed` on a real
profile. It is also required for the clipboard and for OS-level input, so a
headless instance is a dead end for writes regardless of what else you try.

### The user's instructions govern the channel, not just the wording

When someone restricts the mechanism — "use the browser", "don't paste", "edit
it directly", "no headless" — treat it as a hard constraint on the *method*,
not a preference about phrasing, and satisfy it with a different technique
rather than by reporting the restriction as a blocker. A "can't post" that
follows from a method you were told not to use is your constraint to solve,
not the platform's. Say which method is blocked and what you tried instead;
do not silently fall back to a forbidden channel because it was easier.

Prefer the top two when the platform will issue credentials. The browser rows
are the fallback when it will not — and the third row is not read-only in
capability, only in caution. The browser is the user's working surface, so a
write through it needs the gates below, but it is not a channel to rule out.

**A logged-in web session is usually read-only in practice, not by policy.**
Before treating the browser as a posting channel, check whether the platform
will accept its credentials at all. Modern web apps typically do not: the
session's bearer token is rotated per deploy (a copied/stale one fails), and
even a freshly captured valid one is rejected by the write endpoints with an
error naming the required auth types — e.g. "Supported authentication types
are [OAuth 1.0a User Context, OAuth 2.0 User Context]". That is a server-side
decision, not a harness bug, and it cannot be worked around by capturing more
credentials or guessing a versioned operation id.

So the order is: establish whether the official API is available; if it is not
available, **say so and deliver the finished artifact for the user to publish**
rather than escalating through riskier channels. Escalating past a refused
boundary is what turns "I could not post" into "I destroyed your work".

## Before touching a real account, inventory it — read-only

```bash
curl -s http://127.0.0.1:<port>/json/list \
  | jq -r '.[]|select(.type=="page")|.url' | sort | uniq -c | sort -rn
```

Multiple targets on the same app URL is the signal that matters. Those are
tabs with live state — a compose box mid-draft, a half-filled form, a checkout
step. A count of one does not prove it is empty; an editor that merely looks
blank still holds text.

**A clean tab inventory does not mean the editor will be empty.** A compose
route restores unpublished content into a tab you just created, and successive
fresh tabs return *different* content. Two checks distinguish that from a stale
selector or a mis-targeted socket, and both are needed before concluding
"the editor is empty":

```python
# 1. we are attached to the tab we opened, not a tab we picked from a list
assert c.js("location.href") == the_url_we_requested

# 2. the target is genuinely new, not a pre-existing one re-listed
assert tab["id"] not in {t["id"] for t in http("/json/list")}
```

If both hold and the editor still has text, the app is restoring it from
its own storage, and **no tab inventory can predict what you will get**. That
makes the write gates below mandatory rather than advisory, and it means "the
user says they have no drafts open" is not verifiable by asking — only the
read-back gate protects you.

### Where the restored text actually lives: ask the app, do not infer it

Open the app's own drafts panel and read it. **An empty panel while a fresh
composer comes back pre-filled proves nothing about where the content lives** —
and it is not evidence that the content is local and clearable. That inference
is the expensive one: it invites deleting an account's IndexedDB on the theory
that it holds nothing but drafts.

Establish location by measurement, not by reasoning from which API is
convenient to read:

```python
c.send("Storage.clearDataForOrigin",
       origin="https://site.tld",
       storageTypes="local_storage,indexeddb,cache_storage,service_workers")
# deliberately NOT "cookies" — that would sign the user out
# then open a FRESH compose target and read what it came back with
```

`Storage.clearDataForOrigin` returns success (an empty `clear: {}`) whether or
not it removed anything, so the return value is not the measurement. The
measurement is the **next** composer. If it still arrives pre-filled — and with
content that *differs* from the last one, showing an app-side pool rather than
one stored string — the content is server-side or otherwise outside this
machine's reach. Do not escalate to clearing more storage; there is nothing
further to clear.

Use the protocol method rather than enumerating databases from the page:
`indexedDB.databases()` hangs indefinitely under headless Chrome, while
`Storage.clearDataForOrigin` never depends on the page being responsive.

Either way, clear local storage only after the user has said the content is
expendable, and say what you are deleting — IndexedDB for a real app can hold
more than drafts.

**Neither of the two easy inferences is safe.** "localStorage and
sessionStorage are empty, so it must be server-side" ignores IndexedDB, which
those two APIs say nothing about. "The drafts panel is empty, so it must be
local" has no support at all — panel contents and composer restoration are
different subsystems, and the panel being empty is compatible with either. The
clear-and-recheck above is the only thing that settles it, and both wrong
inferences cost real time: one turns a clearable problem into "irreversible,
must not touch", the other turns an unreachable one into "delete the user's
IndexedDB".

The other half is equally load-bearing: "closing the tabs will clear it".
Closing every compose tab, then opening a fresh one, and still finding text is
the measurement that settles it — and it is the opposite of what tab-hygiene
instinct predicts.

Report what you found and stop. Do not tidy: closing, reloading or navigating
another tab to "get a clean slate" destroys work that exists nowhere else, and
tab count is evidence about the user's state, not clutter.

## The site may refuse headless, and the refusal looks like an empty page

A logged-in consumer service (social, banking, anything behind bot management)
answers `403` to a headless fingerprint while serving the same URL normally to
headed Chrome. Cookies are irrelevant here, so re-copying the profile or
re-checking the login changes nothing.

Settle it with a control from the same machine — a request that does not carry
a headless fingerprint:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://site.tld/
```

`200` from curl and `403` in the browser means the fingerprint is the cause:
relaunch headed. Neither "wait out a rate limit" nor "clear cookies" is the
right response, and high-frequency retries against a 403 make the block worse.

**The dangerous part is that a refusal reports itself as an empty page.** The
telltale is the navigation having failed, not the content being short:

```python
href = c.js("location.href")
if not href.startswith("https://site.tld"):   # e.g. chrome-error://chromewebdata/
    raise RuntimeError(f"navigation was refused, not empty: {href}")
```

A refused page is a few dozen characters, contains no target element, and has
no editor in the DOM. Every existence check then returns "empty" — so
"the composer is blank", "there is nothing to clear" and "no drafts are
present" all read as **verified success** on a page that is not the site at
all. Assert the href before trusting any content read, and treat a
below-threshold page length on a known-good URL as a failure, never as an
empty result.

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

Gate 3 is not paranoia; it is the only thing standing between a mis-targeted
write and an irreversible publish. It also catches a completely ordinary
failure — a rich-text editor that accepted a keystroke into the wrong tab
reads exactly like a "logged out" bug until you diff the text.

**Gate 3 is what actually fires in practice.** Gate 2 assumes you can predict
the state; when the app restores state you cannot predict, and the diff is the
 only thing that catches it. In the case that motivated this rule, gates 1
 and 2 both passed — right tab, right socket — and the editor still held a
 complete, unrelated draft the user had written. The text diff refused, and
 roughly a dozen unpublished drafts survived intact.

**Never loosen the comparison to make a run pass.** Matching a prefix, or
comparing only the first N characters, converts this gate into the exact hazard
it exists to prevent. If the diff fails, the correct action is to stop and
report — the alternative is publishing someone else's unfinished work.

Normalise whitespace when comparing. `innerText` and `textContent` disagree
about blank lines inside a contenteditable, and paragraph breaks are cosmetic,
not corruption.

## Writing through the composer

The gates above are the safety net; this is the mechanism. A write to a rich
text composer is three different tools doing three different jobs, because no
single one does all three correctly. This exact split published a real post:
135 characters written, matched character for character, button enabled, click
accepted, and the post visible on the profile within seconds.

| Step | Tool | Why that one |
|---|---|---|
| Clear the field | **CDP** — select all, `execCommand('delete')`, caret to end | The only reliable way to know a restored draft is gone, and it works on the real editor node. |
| Write the text | **computer_use `set_value`** | A DOM write or a CDP key event never updates the framework's state; the AX tree exposes the real editor as a text field, and setting its value does. |
| Verify and submit | **CDP** | Reading back through the same node and comparing, then clicking. |

**Clear once, before the first write — never after.** Clearing wipes whatever
`set_value` just wrote, and the resulting state (`len: 0`) reads as "the write
did not land" rather than as "the clear ran too late".

**Non-Latin text needs `set_value`; a keystroke path cannot send it.**

```js
// CDP: clear and focus the REAL editor (see pitfall 21 — not the decoy)
const el = document.querySelector('[data-testid="tweetTextarea_0"]');
el.focus();
const sel = window.getSelection(), r = document.createRange();
r.selectNodeContents(el); sel.removeAllRanges(); sel.addRange(r);
document.execCommand('delete');
const r2 = document.createRange();
r2.selectNodeContents(el); r2.collapse(false);
sel.removeAllRanges(); sel.addRange(r2);
```

```python
# CDP: gate 3 against the same node, then submit
after = c.js("document.querySelector('[data-testid=\"tweetTextarea_0\"]')?.textContent")
assert "".join(after.split()) == "".join(INTENDED.split())
c.js("""(() => { const b = [...document.querySelectorAll('button')]
      .filter(x => x.offsetParent !== null)
      .find(x => /^(Post|发帖|发布|回复|Reply)$/i.test((x.innerText||'').trim()));
      if (!b || b.disabled) return 'DISABLED';
      b.click(); return 'CLICKED'; })()""")
```

**`computer_use`'s `type` cannot deliver CJK.** A 159-character Chinese post
came back `delivered 0 of 159` via its key-event path, while the same string
through `set_value` arrived intact. Reserve keystrokes for ASCII; use
`set_value` for any non-Latin text.

**`set_value` collapses paragraph breaks** — a 194-character post arrives as
188 characters with the lines run together. That is cosmetically wrong but
still verifiable under the whitespace-normalised comparison, so prefer it over
a keystroke path that cannot send the text at all.

**Two delivery modes, and the escalation between them matters.** Background
delivery routes input without raising the window; when a result's verdict
reports `delivery_failed` and names foreground as the escalation, that is the
next rung. A background `type` of ASCII can also succeed where foreground
fails, so a refused foreground call does not mean the session is gone —
re-check with a free call (`list_windows`, `capture`) before concluding it is.

**Never infer the text from the button state — they are independent.** An
empty composer and a 23-character one both read `disabled: false` in one
measurement, while a full 188-character post read `disabled: true`. Gate 3
(the text diff) is the only reading that means anything about the write; the
button is a separate fact about whatever the app is waiting for.

### Read the reply target from a structured field, never by regexing the dialog

The composer shows who a reply is addressed to in a header, and the natural
way to read it is a regex over the dialog's text. That is a value
**fabricator**: when the app renders the header differently — a saved draft
replaces `Replying to @x` with a plain `Draft` label — the regex fails to
match and a looser fallback sweep over the whole dialog text matches some
unrelated `@handle` mentioned further down. The caller receives a confident,
wrong, specific answer.

```js
// WRONG - invents a target when the expected header is absent
target: (dlg.innerText.match(/Replying to\s*@(\w+)/)||[])[1] || null

// RIGHT - ask the element that owns the identity
target: (dlg.querySelector('[data-testid="User-Name"]')?.innerText || '')
          .split('\n').find(l => l.trim().startsWith('@'))?.trim() || null,
header: dlg.innerText.slice(0, 24)     // log it; do not parse it
```

Assert the returned identity against the handle you meant to answer **before**
typing, and abort on mismatch. Log the raw header alongside it: the header is
the diagnostic, and reading it as a string while the identity comes from a
field keeps the two failure modes apart.

The cost of getting this wrong is not a failed send — it is a send to the
wrong human, or a guard that blocks correct work while reporting an error that
never happened. Both are worse than an exception, because neither looks like a
bug. A reply box on a thread with no such reply displayed an identity for an
account that appears nowhere in that thread, and it took a direct DOM dump of
every open dialog to establish the target was right and the *reader* was wrong.

**Select the submit button by `data-testid`, never by its visible label.** One
composer carries **two** buttons (`tweetButton` and `tweetButtonInline`), and
a label regex plus `.find()` over `offsetParent !== null` buttons can match
either — or, on an empty editor, something else entirely. That is where the
contradictory "disabled: false on an empty composer" readings came from: the
selector was reporting on a different element than the one being clicked.
Select all of them and read the whole list:

```python
bs = [...document.querySelectorAll(
        'button[data-testid="tweetButton"], '
        'button[data-testid="tweetButtonInline"]')].filter(
            b => b.offsetParent !== null)
print(json.dumps([{ "id": b.getAttribute('data-testid'),
                    "disabled": b.disabled} for b in bs]))
```

**A permanently disabled button with clean text usually means the app is
waiting on something asynchronous, not that the text is wrong.** Two verified
causes, in the order worth checking:

1. *Missing context.* `compose/post?in_reply_to=<id>` renders without the reply
   context (`hasReplyContext: false`) while the text compares clean — a reply
   needs the inline box under the actual post.
2. *An unresolved link preview.* A URL in the text makes the app render a
   preview card and hold the button until it loads. When the **browser cannot
   fetch that URL**, the card never resolves, the progress indicator never
   clears, and the button stays disabled forever. This is not an app bug and
   not a harness bug — diagnose it by asking the page what it can reach, and
   check for a spinner at the same time:

```javascript
(async () => { const o = {};
  for (const u of ['https://host.tld/path'])
    o[u] = await fetch(u, {signal: AbortSignal.timeout(8000)})
              .then(r => r.status).catch(e => 'ERR ' + e);
  return JSON.stringify({
    fetch: o,
    spinning: [...document.querySelectorAll(
      '[role="progressbar"], [aria-busy="true"]')]
      .filter(e => e.offsetParent !== null).length }); })()
```

`ERR TypeError: Failed to fetch` from inside the page means the host is
unreachable **from this browser**, which is a property of the machine's
network, not of the automation. The remedies are then the user's to choose —
reword the copy without the URL, configure egress, or publish by hand. Do not
keep retrying: the wait is unbounded, so retries add nothing.

**Pure-CDP has no reliable multi-line write to a rich editor.** Against the
real editing node, `Input.insertText` with the whole string writes **nothing**
when it contains newlines, and line-by-line writes **only the first line** —
the Enter between lines rebuilds the editor's internal state and every
subsequent insert is silently dropped. ASCII single-line text is the only
shape CDP writes reliably. This is why the write path uses `set_value`.

**Do not route the text through the clipboard.** `navigator.clipboard` needs a
focused document (`NotAllowedError: Document is not focused` until
`Page.bringToFront`, and it round-trips correctly after that), but a real paste
into the editor is refused regardless — via key event with `commands:["paste"]`
or via `execCommand('paste')`. The clipboard is reachable and the editor's
paste handler is not; going through the clipboard only adds a failure mode and
leaves the user's clipboard holding whatever was last there.

**The AX index goes stale on every re-render.** An index that worked against
one composer is rejected on the next with `element_outside_target_window`.
Re-capture before addressing an element, and remember the index list is
truncated at its cap — if the editor is not in the visible portion, scroll it
into view and capture again rather than guessing.

## Driving a live feed: pick targets fresh, and never answer one twice

An infinite feed is not a static list. It replaces its contents continuously and
virtualises what is on screen, so two properties break the obvious loop.

**Re-read the page each iteration; never carry a target id across steps.** An id
saved by an earlier read names something no longer on screen, and the reply
lands under the wrong post or nowhere.

**Dedupe by the id you just used, and mark it before you act.** A virtualised
list keeps an article in the DOM at the same offset long after the loop has
scrolled past it, so `next(match for row in rows if ...)` re-picks the same
first match every pass — three replies to one post instead of one each. Keep a
`set` of answered ids and exclude them:

```python
done = set()
row = next((r for r in rows if r["sid"] not in done and topic_ok(r)), None)
if row is None:
    scroll(); continue                   # nothing new in view — go further
done.add(row["sid"])                    # mark BEFORE acting, not after
```

Marking before the write is deliberate: a reply that fails to verify has still
consumed that post's one answer, so re-picking it would spend the next reply on
a post that already got one.

**A scroll is not a navigation.** If the harness forbids page loads, scrolling
is the sanctioned way to reach new content — and it is also what makes an
otherwise-infinite feed finite. Detect the end by comparing the distinct-id
count before and after a scroll: no growth means the feed is exhausted, so stop
and report the real count instead of looping or padding with repeats.

**Reach new content through a control already on screen.** A nav tab is an
anchor already in the DOM; clicking it returns to the feed in place, where
`location.assign` would be a page load the user has to confirm.

### A changed URL is not a loaded page — gate navigation on rendered content

`Page.navigate` returns before the page renders, and asserting the URL alone
lets every downstream step run against the *previous* page. The url check
passed, the target was resolved to `None` because there were zero articles to
resolve it from, and the fallback then acted on a dialog that had been sitting
open since an earlier step. Each symptom was defensible on its own and the
chain was still wrong.

Gate navigation on **content**, not on the url:

```python
tab.send("Page.navigate", url=target_url)
for _ in range(16):
    time.sleep(1.4)
    if (tab.js("document.querySelectorAll('article').length") or 0) > 0:
        return True
# url changed but nothing rendered - report it, do not act on the old page
raise RuntimeError(f"url ok but no articles: {tab.js('location.href')}")
```

The same rule applies to any assertion that resolves an owner or an identity
from page content: if it returns `None`, that is a **load-state failure**, not
a "not found". Never let an empty read fall through to a default or to a
fallback path — that is how a navigation bug becomes a wrong-target send.

### Dedupe across processes, not just within one — and record only confirmed sends

In-memory `done` sets do not survive a restart, and a batch driver that runs
the same topic in two processes posts twice. Persist the sent-id set to disk.
Two ordering rules make it safe:

- **Write the marker after the send is confirmed, never before.** A marker
  written first converts every failure — wrong target, blocked, no network —
  into a permanent skip, and the item can never be retried.
- **Key on content, not on a handle or a post id.** The same author posts
  repeatedly and several posts can belong to one draft; a per-author set
  marks a second legitimate target as already answered.

The failure this prevents is the most expensive one on this page: a duplicate
sent to a **real person**, which then needs locating, verifying, and deleting —
with the author's handle and the full body verified before removal, because
the harness cannot otherwise tell a duplicate from the one good copy.

A batch driver that walks its whole work list from the start on every run pays
for every completed item again — here eighteen finished replies cost about
twenty-five minutes of re-attempts before the four new ones were reached, plus
several minutes each burned on items that were never going to work. Drive the
skip decision from the same persisted set the sender writes, so a run starts at
the pending work.

## Never pad a count to reach a target

If the work ran out — fewer reply texts written than replies requested, or the
feed ran dry — the honest deliverable is the smaller number, reported as two
facts: how many verified, and how many were attempted. Re-posting the same
text to hit a number, or writing new bodies on the fly to fill the gap, turns a
measured shortfall into a fabricated one.

**Know the yield before quoting a number back.** A harvested pool is mostly
noise: across 601 collected candidates, a straightforward topic/length filter
left 459, and reading those left roughly fifteen worth answering — the rest
were tutorials, job-seeking posts, repo showcases, "50 repos that replace your
subscriptions" lists and non-English content. Any count the user asks for
should be answered with what the pool supports, so measure the ratio once
rather than implying a per-item conversion you have not established.

When the target exceeds what the pool supports, that is a **scope decision for
the user, not a licence to lower the bar** — the honest options are to stop
early with a smaller verified count, to widen the topic scope (and accept less
relevance), or to relax the quality floor (which turns the work into the
mechanical link-dropping the task exists to avoid). Put those three to the
user with the measured yield attached; do not pick one silently, because each
spends the account's credibility differently. State the real number achieved
alongside the number requested, never a projection of what might be possible.

Bodies should exist as files that the publisher's own checks have already run
against (ownership, length, stray-token) rather than being composed at send
time, because a body generated during the run has passed none of them.

Stop and report rather than proceeding when any of these hold:

- **Unpublished user content is visible in the target.** The cost of being
  wrong is asymmetric: a failed post is noise, a destroyed draft is a loss the
  user cannot undo.
- **The task needs a credential you were not given.** Say which one and where
  to get it. Never accept a secret pasted into chat.
- **Read-back disagrees with intent at any point.** Do not "try the submit and
  see".
- **A previous attempt was declared impossible and then succeeded.** Each time
  a different input channel "proved" the target undrivable, the finding was a
  fact about the node or the channel that was probed — not about the target.
  Re-derive the conclusion from a corrected probe before reporting a wall, and
  correct the earlier claim explicitly rather than quietly superseding it.

  **A negative conclusion assembled from several silent failures is the least
  reliable thing this reference can carry, and it compounds.** When each of four
  separate harness bugs reported itself as "the site refused", the natural
  reading was a wall — and every one of them was the harness lying, in four
  different ways: a return value that was a string where the caller wanted an
  object, a comparison against text whose newlines the editor stores as
  elements, a verification selector that assumed a DOM shape the app does not
  use, and a viewport left scrolled past the result. Nothing about the site
  ever changed. Two habits prevent the wall: **prefer a probe that reports a
  typed value over one that reports presence**, because "the control exists"
  and "the control was accepted" have been conflated here repeatedly; and
  **when several distinct failures all say "refused", suspect the harness
  before the site**, because a real refusal is one bug with one signature, not
  four unrelated ones.
- **The blocker is environmental, not procedural.** An unreachable host, a
  refused fingerprint, or a machine capability limit is a fact to hand to the
  user with the options — not a technique to keep retrying.

In each case: state plainly what you observed, state plainly that you did not
modify it, and offer the options. That report is the deliverable.

## A wrong conclusion costs more than a slow one

The most expensive failure mode here is not failing to post — it is reporting
a confident "this is impossible" that a later, corrected probe overturns. The
user then makes a decision on a false premise: they hand the work to a human,
or drop the approach, believing the tool cannot do it.

Two habits prevent it:

- **Attribute every negative result to what you actually probed.** "Every input
  channel fails" is only true of the channels tried, against the node selected.
  Name the node and the channel in every negative claim, so a later probe that
  changes either can invalidate it explicitly.
- **When one measurement contradicts another, resolve it before continuing.**
  Opposing readings mean at least one measurement is wrong; continuing to act
  on a coin-flip is how a wrong story hardens into a written conclusion.

Report a wall only after the corrected probe still hits it. If an earlier claim
is later disproved, say so in the same terms it was made.
