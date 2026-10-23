---
name: x-post-via-browser
description: Use when posting, replying, or liking on X/Twitter from this account, or when an X engagement cron job must run. Drives a dedicated headless Chrome over raw CDP; no verified landing means no claim of success.
---

# X posting and engagement

## When to Use

Posting, replying or liking on X/Twitter as this account; an X engagement
cron job that has to collect, like, reply and prove each one landed; a
promotion post that has to carry this account's project address.

Not for: reading X as research, other social platforms, or unsent copy.

The scripts in `scripts/` drive a dedicated headless Chrome over raw CDP
and do the mechanical work — composer, insert, send, read back. The
judgement work stays with the caller.

## The rules that matter

**A landed post is the only proof.** The toast is not a receipt. Read the
post on its own permalink and compare its own text element against the copy
that was sent.

**Like first, then reply, then verify.** A post that is answered is a post
that is liked, and the two sets must match exactly. The like is idempotent
— it reads the button state before it clicks, so a retry cannot toggle a
like off.

**A status id never appears in a transcript.** An id is a bare 19-digit
number, and the display layer replaces such numbers with a redaction
token: one id in a list of seven was redacted. Name candidates by their
INDEX and let the scripts read the ids out of the candidates file.

**The collect and the answer are one process.** The feed virtualises
articles out of the DOM within about a minute, so a candidate read at one
moment can be gone at the next. `xreply.py` works against the parent's
own permalink.

**A trailing address lands as a card, so the landed text has no url in
it.** Remove the url span from BOTH sides and compare as prose; the address
is proved by following the t.co to the place it names. The card hydrates
AFTER the post's own text, so the read must poll until both the card and
the t.co are present — and the card's TITLE is not the address, it carries
the target page's own title. All three, and the tests that pin them, are in
[references/reading-a-landed-post.md](references/reading-a-landed-post.md).

**A reply that is up is answered, whatever the address proof says.** The
parent's id is recorded the moment the reply renders on its own
permalink — not after the last proof passes. A run that rejected a
landed reply before recording it left the parent open, and the next run
answered it a second time.

**The copy goes in through CDP, not through the page** — `Input.insertText`
only. `execCommand` doubles the copy and its `delete` variant raises
Chrome's unsaved-changes dialog, which blocks every later CDP call.

**One substitution mode.** Every placeholder in a JS template is a JS
expression slot and every value is `json.dumps`'d. A placeholder inside
a quoted string is a quote-injection bug; a bare 19-digit id is a number
literal, which loses precision and matches nothing.

**The copy is measured the way X measures it** — weighted characters, not
`len()`. `xlength.py` holds the measurement and `xlength_test.py` pins it
against twitter-text's own configuration; run the test after touching either.
The weights and the CJK trap are in
[references/reading-a-landed-post.md](references/reading-a-landed-post.md).

**A refusal is the script declining on purpose.**
`references/refusals.md` says what each one means and what to do about
it. Every one exists because the alternative produced a public defect.
The verdict strings in that table are the API a run reads, so it drifts
from the code the moment a verdict is renamed; the reference carries a
runnable check — run it after touching any refusal message.

## The scripts

| script | what it does |
| --- | --- |
| `xbrowser.py up\|status\|down\|prune` | the dedicated browser; copies the session cookies out of the real Chrome profile and launches against the copy; `prune` drops the stale X tabs |
| `xfeed.py --out FILE --count N` | the candidates, into a file; already-answered ones filtered out |
| `xread.py --candidates FILE --index N` | a candidate's FULL text, from its permalink |
| `xlike.py --candidates FILE --index N` | like one post, proven by the button swap |
| `xreply.py --candidates FILE --index N --copy FILE [--repo URL\|--allow-no-repo]` | like, answer and verify one post |
| `xpost.py --copy FILE --repo URL [--dry-run]` | publish one standalone post and verify its address |
| `xtrending.py --limit N` | today's trending list, read live, with ownership from live git remotes |
| `xrepo.py --pick\|--list\|--network` | which own repository may be promoted, and whether the network is broken |
| `xcompare_test.py` | the landed-text comparison, in both posting scripts; run it after touching either |
| `xlength.py` | the copy's length as X counts it — weighted, 280, CJK weighs 2; `python3 xlength.py FILE` prints it |
| `xlength_test.py` | the weighted-length measurement, pinned against twitter-text's own configuration |
| `verify_no_unsafe_posting.py` | the commit gate on these scripts; run its `--self-test` after changing it |

Run them with `python3` from this directory. `xconfig.py` holds every
environment-specific value and reads it at call time.

## A reply, end to end

```sh
python3 scripts/xbrowser.py up                       # once per session
python3 scripts/xfeed.py --out /tmp/cand.json --count 10
python3 scripts/xread.py --candidates /tmp/cand.json --index 3
# write the copy, grounded in what you read, to /tmp/reply.txt
python3 scripts/xreply.py --candidates /tmp/cand.json --index 3 \
    --copy /tmp/reply.txt --allow-no-repo
```

`--repo URL` is for a reply that promotes one of this account's own
repositories; the address must appear exactly once, at the end, preceded by
one space. `--allow-no-repo` is for a reply with no address at all. The exit
code is 0 only when the reply was verified; a non-zero code means nothing was
sent or the landing was unproven, and the verdict line names the step.

## The browser and the state

The harness browser answers 403 on x.com and carries no x.com session, so
`xbrowser.py` copies the session cookies out of the user's real Chrome
profile into a private profile and launches a headless Chrome against the
copy. `~/.hermes/state/x-post/` holds the browser endpoint, the account
handle, the answered ids, the publication record and the lock — NOT the
scratch directory, which the daily cleanup empties. `references/browser-and-state.md`
has the details.

## The reply's own rules

- Read the post in full before writing about it — the feed clips long posts,
  and the clipped half is usually the point.
- Say something the post did not already say; a restatement is a wasted
  reply.
- Ground every claim in something read this run — the post, the source, the
  advisory. A claim that cannot be sourced does not go in.
- Write in the post's language. A failed send is reported, never retried
  into a second post.

## When the site fails

`references/site-failures-and-pacing.md` covers the states a run cannot
tell apart by eye — the site serving its error page, the site rate-limiting
an account that answers too fast, the proxy being dead, and the shared
browser being busy — and how to tell them apart. Read it when the feed
comes back empty, a page stops rendering, or a CDP call times out. A busy
browser is contention, not breakage: a landing can be proved over plain
HTTP while the browser is occupied.

**Zero candidates is not "nothing worth answering".** The feed reads as
empty under an error page, and a run that cannot tell the two apart reports
a success it did not earn. `xfeed.py` retries before giving up; when the
retries are exhausted, report the failure, not a target count of zero. The
empty feed is usually stale tabs rather than rate limiting: `xbrowser.py
prune` drops them, and `xfeed.py` calls it before each retry. **Pace the
replies** too — one account answering dozens of posts inside an hour trips
the same limit. The count is a target, not a quota.

## Which own repository may be promoted

`xrepo.py --pick` decides it, and the decision is **reachability**, not
on-topic-ness: a repository that answers 404 anonymously is not a
candidate, because the link would be dead for every reader who is not
signed in. One whose last push is over a fortnight old is not worth
promoting either.
