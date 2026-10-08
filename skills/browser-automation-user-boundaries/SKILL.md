---
name: browser-automation-user-boundaries
description: "Use when driving the user's real browser, not your own."
license: MIT
metadata:
  hermes:
    tags: [browser-automation, cdp, user-boundaries, focus, tabs, confirmation, triage, network]
    related_skills: [chrome-real-profile-launch, cdp-browser-harness-speed, web-access, hermes-real-profile-browser]
---

# Driving a real browser on the user's machine

This is the *conduct* layer: what you may and may not do to the user's browser
while doing it. For how to launch one, load `chrome-real-profile-launch`; for
CDP mechanics, `chrome-devtools-protocol`. Both cover the machinery. This covers
the parts where the machinery is not the point.

## THE RULES — user standing preferences, not suggestions

1. **Never refresh or navigate the page.** No `Page.reload`, no
   `Page.navigate`, no `location.assign`, no `location.href = …`. Every page
   load is an interruption the user has to notice and confirm. Work with the
   page as it stands. If the UI you need is not there, click the control that is
   already on screen (`SideNav_NewTweet_Button` — note the underscore before
   `Button`; the shorter `SideNav_NewTweetButton` matches nothing on the live
   build — or `a[href*="/compose/post"]`, or the equivalent) — a click opens it in place, a navigation reloads the page.
   When nothing suitable exists, stop and say so rather than navigating.

   **Know which actions are *not* page loads, because refusing them costs you
      the task.** `window.scrollBy` grows the DOM in place — the same document,
      no navigation, no reload, and the user's pointer never moves — so reading a
      feed or a thread by scrolling stays inside rule 1. Likewise a **click on a
      control already on the page** (`[data-testid="reply"]` on an article, a
      compose button, a media tab) opens its target in place without violating the
      rule; the reply composer it mounts is a second editor on the page, which
      is the trap — see the "two nodes share one testid" section of
      `references/x-composer-mechanics.md`. Reserve "stop and ask" for a genuine
      address change, and distinguish the two out loud rather than stopping on
      anything that looks like it opens something.

      **A reload is still a page load, so it still needs the user's OK** — including
      when the page looks broken enough that you are sure it would help. A stalled
      timeline is a reason to *ask*, not a licence: the reload costs the user their
      scroll position, their history state and an unsaved draft, and "it was stuck"
      is a diagnosis you have not earned until the surface has been measured. Say
      what you measured, propose the reload, and let them decide.

2. **Never take the mouse or the keyboard.** No `Page.bringToFront`, no
   `Input.dispatchMouseEvent`, no `computer_use` `bring_to_front`, no focusing
   an OS window. Set focus from *inside* the page with `el.focus()`; that does
   not move the user's pointer or their OS-level focus. The user keeps control
   of their hands at all times, and you must not take it from them.

3. **One tab.** Reuse a single tab for the whole task. Do not open a second tab
   per post, per retry, or per step — the accumulation is the problem, and the
   user is watching the tab strip. When you need to change pages inside that
   workflow, clear the input you have already typed; do not abandon it and start
   fresh elsewhere. A `try/except` that recovers by opening a fresh tab is wrong
   even when it works: the correct recovery is "clear this one and retype".

4. **Every consequential action waits for the user's confirmation — unless the
   user has said automation needs no human in the loop.** If the user has said
   each one needs their click, that is a hard gate, not a formality — including
   the ones that would obviously succeed. Ask, wait, then act. Do not batch
   several such actions into one confirmation.

   That gate is theirs to waive, and when they waive it, honour it fully: they
   have said "automation, do not ask me", so do not keep re-confirming, and do
   not "helpfully" downgrade a requested full-automation run into a draft-then-approve
   loop without saying so. The waiver covers *asking*; it never covers *verifying*.
   Run unattended, and check the result harder than when someone is watching.

   **A waiver is not a request to hand the work back.** Once they have said
   automation needs no human, "open this tab for me", "you need to clear this
   field yourself" and "start a second browser" are *your* job to solve, not
   theirs — and offering them as prerequisites once the waiver is in force
   converts their automation back into a supervised task. The two exceptions
   are real, not lazy: state that belongs to the user and that a standing rule
   forbids touching (their draft in a composer, their credentials), and work
   around everything else. Start what is missing — a closed browser is a
   launch you can perform, an absent tab is one you can open — and only hand
   back the part that is genuinely theirs.

   **When you find that a standing reference is the thing misleading you,
   fix the reference.** A wrong constant in the instructions you were
   following is not a question to raise at the user — it is a repair to make
   before the next run inherits it again. Correct the sentence where it lives
   and keep the correct value in the body, so the next session starts already
   holding it. Asking whether to update the document that just cost you a
   round trip converts your own maintenance into their work.

   **Do not open a question form after the waiver, either.** A clarification
   prompt with "which of these should I do" options is the same request for
   consent wearing a different interface, and it reads as asking because the
   channel looks like a tool rather than a person. Pick the route that makes
   progress under the standing rules, build it, and report what it changed.
   The waiver covers asking; it never covers verifying, so the answer to "I
   could not do this" is still a measured blocker with a named next route,
   not a menu for them to pick from.

   **When a channel genuinely cannot carry a step, build the other channel.**
   If the DOM path cannot open a control and the only remaining activation is
   the user's pointer, "will you click it" is the last resort, not the first
   proposal — the supported API is a different channel that needs no pointer,
   and writing that path is your work. Keep the two implementations separate
   rather than merging them: they share the content rules (declared target,
   required repository, read-before-write) and nothing else, because a screen
   and an HTTP request fail in unrelated ways and a fix for one must not be
   read as a fix for the other. Report the missing prerequisite (an
   unauthenticated API needs a credential only they can paste) as a fact about
   setup, while the path that needs nothing from them runs unattended.

5. **Never work around bot detection.** When a platform blocks an automated
   browser, that block is the platform deciding who is a person. Injecting
   fingerprints or spoofing signals to defeat it is circumventing an access
   control, and it is off the table regardless of how benign the task looks.
   Say so plainly, and offer the supported route instead: the official API, or
   the user acting manually. Driving a browser *on the user's own logged-in
   session, with their own account*, is a different act from impersonating a
   human to a server's detection layer — keep that line clear and do not slide
   across it because a step got hard.

6. **Anything published under the user's name must belong to the conversation
   it lands in.** A reply, a quote, or a promo dropped into someone else's
   thread asserts that your words are about their post. **Relevance is not
   computable from word overlap** — a reply and the post it answers share
   mostly function words — so bind the content to its target *in the content*:
   a declared id in the file, the thread it quotes, the question it answers.
   The code then refuses when the item on screen is not the declared one, and
   when the target is not in view it names which target is missing instead of
   scanning for a substitute. A keyword hit is never a reason to act; see
   `references/x-composer-mechanics.md` for the measured case.

   The user is the last word on whether a reply fits, and they check it — when
   they say a reply went under the wrong post, **the pairing was never
   verified, not merely unlucky**: treat a content-to-target mismatch as a
   missing assertion in the code, and put the declared id where the script
   reads it rather than re-deriving the target from keywords. Give each reply
   file the header `# target-status: <id>` and require the on-screen post to
   equal it; the search for "something relevant" is exactly the bug.

   **A reply for this user also has to carry one of their own repository
   URLs, and the post has to earn it.** The point of engaging someone else's
   post is to bring their work to that audience, so a draft naming no repo of
   theirs is refused before typing — one repo, at the end, plain-space
   separated. Relevance and the link are the same requirement, not two: the
   same URL in every reply is decoration, and a link appended to a thread it
   thread it does not belong to is an interruption. A thread about wasting tokens
      re-deriving known facts is answered by a link to a project about not doing
      that; when the post's subject matches none of their projects, that is a reason
      not to reply rather than a reason to link the nearest one. Drafts
      carry a `# why:` header beside `# target-status:` so the pairing is
      reviewable before sending instead of asserted after. Refuse *before* typing
      when the body carries no `https://github.com/<org>/…`, and let the
      declared-target check run first, so a missing link is reported against a
      post that is genuinely the right one.

      **User-authorized exception (this account, 2026-10-09):** when NOTHING in the
      recommended feed is topically relevant to their projects, the user's standing
      instruction is 评论推荐的文章 = an *opinion* reply with NO repository link —
      a genuine response to the post's actual argument, in the post's own language,
      substantive enough to stand alone (no "好文" / one-liner agreement). The link
      rule is waived for these; every other rule (declared target, aim check,
      block-exact compare, verified landing, one at a time) still applies. If the
      user has not said this in the session, the link requirement stays in force.

   **A reply ceiling comes from the account's tier, not from the platform.**
   This account is on a paid tier, so 280 is not its number and there is no
   ceiling to apply at all. Writing 280 into a length gate "to be safe"
   truncates an argument this account is entitled to make in full — then the
   drafts get compressed to two sentences because that is what 280 affords,
   and the sentence carrying the point is the one that gets cut. Draft the
   whole argument, and treat any length figure you inherit from a skill, a
   doc, or a previous draft as unverified until it is checked against the
   account it applies to. Keep the URL inside the same body rather than
   budgeting around it.

   **Assert the ceiling you chose in the test table** — whatever it is, an
   asserted number is a deliberate one, and a remembered one is a bug waiting
   to be inherited. A gate that exists only in the draft prose gets
   rediscovered by a failed send.

   Fit by **putting the claim first and letting the tail go** whenever a real
   ceiling does apply: shortening every sentence evenly keeps none of its
   force. Write the body as discrete sentences and add them while the running
   total fits, so length decides the cut rather than taste.

   **Multilingual queues need a per-language script check.** Four versions of
   the same piece parse as valid to a reader and still be wrong: a ja draft
   picks up a Han `界面` or a Hangul syllable, and it is simply incorrect
   Japanese. Filter on script ranges (Han, Hangul) rather than a stoplist of
   known-good ASCII terms, because tech vocabulary legitimately appears in all
   four languages. Interleave per project rather than sweeping language by
   language, so one repository's four versions arrive together.

   **One post at a time, and each landing proven before the next begins.** When
   the user asks for replies to several posts, that is a sequence of independent
   verified operations, not a loop over a queue. For each target: open its reply
   box, prove the box is aimed at *that* target, clear and assert empty, type,
   compare the box against the source exactly, send, then verify the reply landed
   as a **child article under that target**. Only then look for the next post.

   The landing check gates the next item; a failure stops the run rather than
   continuing with a composer whose state is now unknown. This holds however the
   run was authorised — a batch request is a request for N verified replies, not
   for N attempts, and "the queue still has items left" is never a reason to keep
   going past an unverified one. Report per-item outcomes (published and
   verified, or named blocker) instead of a single pass/fail for the batch, so
   the user can see exactly which ones landed.

   Also: audit a drafted body for characters that the input path will silently
   drop before typing it, not after. An em dash, a curly quote or an emoji in
   the draft is dropped by a `keyDown` carrying `text`, and the run discovers it
   as an unexplained character shortfall; normalise the body and re-check.

7. **When a content-producing action will not complete, fall back to the
   nearest action of the same kind that submits no free text** — like,
   bookmark, follow — and report which action failed and what blocked it.
   Liking and posting kept working through a composer that would not publish
   replies, so the honest outcome was a working like plus a named blocker,
   not a forced reply. **Never substitute one action for another silently**;
   the user asked for engagement, and pretending a like is a reply is the
   same false-verdict shape as reporting a click as a post.

   **A blocker is a deliverable, not a failure to route around.** Once you
   have measured *why* a step cannot complete — the mechanism, not the
   symptom — the remaining value is in naming it precisely and handing over
   the decision. Keep the probe that proved it (a script that asserts the
   precondition and exits with the measurement) so nobody re-derives it by
   hand, and report the two routes with their real costs: what the user must
   click, and what an authenticated API path changes. When the user has waived
   the confirmation gate, a blocker of this kind still gets reported rather
   than being retried indefinitely — the waiver covers asking, not looping.

   **Distinguish "I cannot do this" from "this cannot be automated".** A step
   that needs the user's real pointer is a real limit of the input channel;
   say which channel failed and what would carry it, so the answer is reusable
   for the next ten posts and not just this one.

8. **Scale of third-party engagement is a separate question from quality.** A
   handful of replies you wrote, read, and checked is participation. The same
   loop run to a target count — dozens or hundreds of promotional replies under
   other people's posts, unattended, with your repository appended — is the
   behaviour those platforms' anti-spam systems exist to detect, and the
   account carrying it is the user's. Say this plainly and decline that
   specific run; do not accept it because the drafts are individually good,
   because the confirmation gate is waived, or because a smaller number was
   already agreed.

   What is legitimately yours to build instead: the reply engine (declared
   target, required repository, read-before-write, exact comparison, verified
   landing) plus the scheduling and queue, so the user presses the send. The
   distinction is consent to the *individual* message, which is theirs to give
   each time, versus consent to a campaign, which is the account owner's call
   about their own account and not something to infer from a waiver about
   being interrupted. Do not let the refusal turn into a lecture or a
   negotiation — state the limit, build the engine, and report.

   The same limit applies to automated *following* and *bulk DM*: unsolicited
   growth actions at volume are the canonical spam pattern even when every
   message is polite.

## One rule, one module, one test

A content rule enforced in two entry points is two rules by the time something
goes wrong. One checked "does this text contain a github.com link" and the
other checked three hardcoded owner prefixes; neither was the actual rule, and
a reply carrying someone else's repository passed the first while failing the
second. Put the rule in one module both import, and when the allowlist is
"these are my organisations", **derive it from real data** — the `owner` field
of every GitHub remote on the machine — rather than from what you remember,
because the remembered version silently omits the personal orgs and the
smallest repos that happen to be yours.

Then test the module against a table of accept and reject cases, because the
failure mode is invisible from the call site: the allowlist was generated by
`%`-formatting into a parenthesised **string** instead of a tuple, so
`"|".join(OWNERS)` spliced it one character at a time and *no* repository
matched. Every legitimate case failed, the error messages were all plausible,
and nothing about the calling code looked wrong. A rule that refuses everything
looks exactly like a rule that is working when you only inspect the rejections.

The same applies to a hand-maintained list that several code paths consult:
drift is the default state, and the fix is one shared definition plus one test,
not a second copy that agrees by coincidence.

**Verify a module's state in a fresh process, not in the one that imported it.**
A long-lived interpreter session keeps the first import alive for the rest of
the session, so a fixed file keeps reporting its pre-fix contents and you
re-diagnose a bug that was already repaired — twice, here, concluding a
tuple was a string while the file on disk plainly held a tuple. The tell is
`read_file` and `import` disagreeing about the same line. Run the check as a
subprocess (`python3 -c ...`) and read the file directly; when the two
sources of truth conflict, the fresh process wins over both the cached module
and your own memory of what you edited.

**Read a git remote without printing its credential.**
`git remote get-url` on a repo authenticated with an embedded token writes that
token to stdout, and a terminal echo puts it in the transcript permanently.
Parse the owner and print only the parsed field:
`re.search(r'github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$', url)`. A token
exposed this way is already in the session's history, so say so plainly and
recommend rotation — the operator cannot undo the exposure by ignoring it.

## Triage a dead port before calling it a crash

A CDP endpoint refusing connections is ambiguous: the browser can be gone, or
the network can be gone. Relaunching on a guess is how you burn three cycles
chasing a browser that was never the problem.

```bash
# 1. Is the network up at all, independent of the browser?
for h in <target> google.com github.com; do
  printf '%s -> %s\n' "$h" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://$h)"
done
env | grep -iE '^(http_proxy|https_proxy|all_proxy)=' || echo '(no proxy)'

# 2. Did the browser actually crash?
ls "$WORK/Crashpad/pending/" 2>/dev/null | grep -i chrome || echo '(no pending dump)'
```

| Network | Crash dump | Verdict |
|---|---|---|
| all `000`, no proxy | none | **Network down.** The browser is a victim. Do not relaunch — it dies the same way and the relaunch deletes the log that would have said so. Report the network and stop. |
| hosts fine, target `000` | none | The target is blocking, or the proxy is wrong. Test from a different client before blaming the browser. |
| fine | present | Genuine crash. Read the dump, then relaunch. |

`net_error -100` (`ERR_CONNECTION_CLOSED`) repeated across *different* hosts in
the launch log is the network signature; a real crash logs a stack trace, not a
wall of identical SSL errors. **Tail the log before restarting** — a fresh
profile copy deletes the work directory along with it.

The symptom is unusually convincing in both directions: the port really does
refuse connections, the window really does vanish, and a fresh launch really
does die again seconds later. Only the probe separates the two causes.

Corollary: when a site suddenly 403s or times out for you, suspect your network
before concluding the site is blocking you specifically. A blanket 403 across
every host on the machine is a connectivity symptom wearing a site's
costume — and misreading it as anti-automation sends you into exactly the
circumvention you are not allowed to do.

## Verify the result; never report the click

For any action with an externally visible effect — a post, a form submission, a
purchase, a delete — the click is not the outcome. The API call that reported
success is not the outcome either. Re-read the target and require the change to
be visible there: fetch the posted item back, confirm the row is gone, check the
status. `CLICKED`, `200 OK`, and `dispatched` are all statements about the
attempt.

Compare content **character by character**, not "does it look right" — but the
naive form of that check is wrong in three ways, each of which has produced a
false verdict. See `references/x-composer-mechanics.md` for the measurements.

- **A normalising comparison that strips URLs and whitespace let eight stray
  characters through as a pass.** Keep the normalisation; do not let it be the
  only check. The characters that matter are the non-space ones, and those must
  match exactly.
- **A raw length check is worse than useless — it lies in both directions.**
  The editor keeps hidden text nodes of its own, so a perfect post reads one
  character long; the rendered timeline clips long posts with no "show more"
  control, so a complete post reads hundreds of characters short. Gate on the
  normalised text compare, never on length.
- **A URL is never present verbatim.** The platform rewrites it to a shortener,
  so the original string is absent by design and demanding it verbatim rejects
  a perfect post. Prove the link where it is actually visible — the expanded
  card, which names the destination.

**Check whose post you are looking at.** A feed, a reply context and a
notification list all carry other people's posts; matching a status id among
them yields a real id, real text, and a false conclusion that your own post
landed. Require the expected author, and list what is on screen split by author
before drawing any conclusion from an id.

**Never hardcode the account handle in a verification.** Read the logged-in
account once (`/settings/account` or the sidebar's own profile link) and carry
that value into every check. This is not defensive coding — it is the whole
evidence base. Measured: eight call sites carried one handle while the browser
was logged in as another, so the baseline was always **0 own posts**, every
"is this mine?" test was false, and the verifier reported 0/4 for replies
that were sitting on the target threads the whole time. Nothing raised. The
send-side log said `send: ok`, the verify side said `not confirmed`, and the
honest reading of that pair — "the post may not have landed" — was wrong: it
had landed, and the checker was looking for an account that does not exist.

The failure is worse than a missed send because it is silent in both
directions. A post that really did land is reported missing; a post that
really did not land is reported missing too, so the two are indistinguishable
and the run "resends" a duplicate — which is exactly the mistake it is meant to
prevent. When a verification returns a surprising zero, **read the account the
browser is actually on before believing it.**

**A batch driver must skip completed work from durable state, not from memory.**
A queue runner that walks every topic from the start re-runs each completed
item to re-discover it is done — measured, 22 attempts for 4 real sends, about
25 minutes of it waiting on posts already answered. Derive the skip list from
the same file the engine writes its confirmations to, and record a fingerprint
**only after** the send has actually been verified: marking before the send
turns a crash into a silent skip, and marking at all turns "attempted" into
"done". A run should report `sent N / attempted M` where M counts real
attempts, and name a topic whose target cannot be reached rather than retrying
it forever.

**A selector argument must not be silently ignored.** A driver invoked as
`batch_replies.py <slug>` printed `nothing pending` and exited cleanly when the
argument went unparsed, so the caller read a completed run that had done
nothing at all. A driver that takes a selector must either honour it or
refuse; printing a success message and skipping the work is the worst of the
three options.

**A send log is a claim about an attempt, not evidence of a post.** The engine
that wrote it is the thing being audited, so its self-report cannot close the
loop — measured `send: {'ok': True}` on a reply that never reached the target
thread, alongside four that did, in the same run with the same log lines. Audit
by walking each target post and requiring the account's reply to be a **child
article after it**; keep the fingerprint file as a work list, never as proof.
Report anything unconfirmed as unconfirmed.

When a comparison fails, report the first differing offset and the surrounding
context from both sides. "It didn't match" costs a round trip; the offset tells
you whether characters are missing, duplicated, reordered, or dropped at the
end.

**A posted result is not a text result, and a text result is not a published
result.** Three different claims, three checks: what the editor holds, what the
click reported, and what the timeline shows. Confident prose about the first
two is not evidence for the third.

## Keep the script honest about itself

- **A helper that normalises a return value can hide the value's meaning.**
  Wrapping a bare-string answer as `{"_raw": result}` to give the caller a
  uniform type is comfortable and quietly fatal when the caller only inspects
  the *other* keys: a step that returned `TARGET NOT ON PAGE` sails past
  `if step.get("ok")` and the flow types a full post into whatever composer it
  finds next and clicks send. The same shape happens with a helper that
  returns `[]` on error — indistinguishable from a genuinely empty result. When
  a step's outcome is a *string* verdict (`CLICKED`, `NO_BUTTON`, `NOT_FOUND`),
  return it under the key the caller must read, and **assert on that key at the
  call site**; if the flow cannot proceed without the answer, fail before it
  types anything. Writing the fix one commit after writing the bug is the tell
  that the check is in the wrong place — put it at the call, not in the
  wrapper.

- **When a step fails, find out what it left behind before retrying.** The
  swallowed failure above put 643 characters into the wrong editor. Establish
  the account's own posts are unchanged and the editor is at 0 characters
  before declaring no harm done, and say which of those two you checked.

  **"The editor is empty" is not evidence that nothing was published — after a
  successful send the editor is empty too.** Reporting no harm on an empty
  field alone is the same error as reporting success on a click, pointed the
  other way. Ask the account's own posts directly, and treat the two results
  as separate claims. A status-id lookup that comes back empty is only
  conclusive if the lookup was exhaustive: an un-scrolled feed does not contain
  the post, so "not on the page" and "not published" are different statements
  and the first does not imply the second.

  **When the user reports a symptom you did not observe, treat your own
  instrumentation as suspect before their account is.** If they say the
  content went somewhere it should not have, your verification is the thing
  that failed, not their reading of the page — re-read it from the platform
  and find the actual post rather than re-deriving why your check passed.

- **Retry inside the same tab**, clearing the input, never by re-navigating. In-place clearing is the one recovery the user permits, and it needs its own verification: a select-all plus a single backspace leaves residue on this class of editor, so assert the field is empty afterwards instead of assuming it.
- **"Not visible" and "does not exist" are different answers, and a lazy surface makes them look alike.** A feed or profile that renders a handful of articles while its header claims hundreds is not empty — it is failing to paginate. Never report a post as deleted, or as missing, from an un-scrolled surface: say which surface you read and how many items it actually rendered, and if that count is implausibly small for the surface, treat the surface as broken rather than the account as empty. On the account's own posts the internal JSON endpoints answer with 403 on a page session; reaching the profile through the sidebar's own link and reading its rendered articles is the route that works, and it inherits the same pagination caveat.
- **When a control is missing on *every* item at once, suspect the selector.** A lookup that finds nothing on all articles is far more often a wrong testid than a broken page — dump one item's full control row and read the names off it before concluding the feature is unavailable.
- **Re-assert state instead of assuming it.** A one-shot check every 20 items
  misses an event that destroys the work; check after every unit of work and
  react to the deviation.
- **Distinguish "changed underneath me" from "lost a character".** An emptied
  field and a short field are different failures needing different recovery;
  treating a small loss as a total loss throws away a pass that was nearly fine.
- **Delete only what you created.** A destructive sweep that targets ids you
  did not create is unrecoverable. Scope it to your own work and verify each
  deletion actually took effect before moving on.
- **When a search says "not found", check the search was exhaustive.** A page
  that lazily loads will report absence for things that exist further down;
  "not found" from one un-scrolled page is a statement about the page, not the
  account.

- **Never let a value observed earlier stand in for the present.** A feed, a
  file written by a previous scrape, a cached id list — each is a snapshot, and
  a continuously-updating surface invalidates it silently. Reading a status id
  from a file written by an earlier pass, then treating "the collector said it
  was there" as current, produces a loop where the two disagree and the natural
  conclusion is that the tool acting on it is broken. It usually is not: the
  snapshot is stale and the refusal is correct. Resolve the target in the same
  call that acts on it, and when a stored value and a live read disagree, the
  live read wins.

## Do not edit a script you are mid-way through rebuilding with string replacement

When a script needs several structural changes, patching it with anchored
string replacements is how you produce a file that will not parse: the anchors
match once, a later replace lands inside a block the earlier one already
rewrote, and you end up with duplicated guards, a `SyntaxError` in a
half-applied edit, or a `send` step whose retry loop has been deleted. Real
cost: a file that was working becomes unrunnable and the debugging session
turns into repair work with no progress on the original bug.

**When more than one region of a file must change, rewrite the whole file** in
one `write_file` and re-read the result before running it. If the write is
refused because the file changed on disk, that refusal is the tool telling you
your in-memory copy is stale — re-read it, do not retry the same content. This
fires even on a script **you wrote earlier in the same session**, because
patching it moved the on-disk copy past the version the write guard remembers.
When the file is yours from minutes ago, re-read it and rewrite from that; when
only one region changed, `patch` sidesteps the guard entirely.

Parse the file after every structural edit (`ast.parse` for Python) and treat a
syntax error as a failed edit, not as a puzzle. And run the project's own
verifier on the directory after the rewrite, not just on the one file you
touched: a rewrite that reintroduces a banned call is caught by the directory
check, not by reading the file you just wrote.

## When the user names a control, instrument before you believe them

A user pointing at a button — "the send button is the second from the left",
"it's the one to the right of like" — is giving you a **location**, not a
diagnosis. Adopt it as a place to look, not a cause to accept. Dump every
control in that container with its testid, label, position and state, and
compare it against the equivalent row elsewhere on the page; one call settles
what several rounds of guessing cannot. The same applies to a field: assert on
the field's own name, because an assertion written against the wrong polarity
produces a confident, completely false story about a control that was never
broken.

Users also report symptoms you did not observe, and their reading of the page
outranks your instrumentation. When they say the content went somewhere it
should not have, the verification failed — re-read the platform and find the
actual post before re-deriving why your check passed.

## Your own gate is not an obstacle to route around

When a project's commit gate or verifier refuses a change you were about to
make, read what it protects before touching it. A refusal is evidence about the
code: the guard that blocks a plausible fix usually blocks the bug it was
written for. Recurring shape — you add a select-and-delete to drop residue from
a field and the gate refuses destructive edits to a user's input; the correct
repair is to stop and hand the state back, not to reach for an exemption or
reword the change until it passes. Widening a rule, adding a whitelist entry,
or switching mechanism to achieve the same forbidden effect are one violation
wearing different clothes. If a guard genuinely blocks correct work, say so
plainly and name the guard instead of engineering around it.

## References

- `references/x-composer-mechanics.md` — the measured X-specific mechanics:
  duplicate editor nodes, per-character input, IME for URLs, replying in place
  and verifying it under the target article, what is unreachable in that
  composer. Load before scripting anything against x.com.
- `references/timeline-harvest.md` — reading a feed at scale: the virtual list
  that holds ~8 articles at a time, scroll position that outlives the run,
  reading `@handle` instead of the timestamp, and the relevance triage that a
  keyword sweep leaves for you. Load before counting or bulk-selecting posts.