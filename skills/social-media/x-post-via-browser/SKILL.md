---
name: x-post-via-browser
description: Use when posting, replying, or liking on X/Twitter from this account, or when an X engagement cron job must run. Drives a dedicated headless Chrome over raw CDP; no verified landing means no claim of success.
---

# X posting and engagement

## When to Use

Posting, replying or liking on X/Twitter as this account; an X engagement
cron job that has to collect, like, reply and prove each one landed; a
promotion post that has to carry this account's project address.

Not for: reading X as research, other social platforms, or copy that is
not going to be sent.

The scripts in `scripts/` drive a dedicated headless Chrome over raw CDP
and do the mechanical work — opening the composer, inserting the copy,
clicking send, reading the landed post back. The judgement work stays
with the caller.

## The rules that matter

**A landed post is the only proof.** The toast is not a receipt: a sibling
run's toast is byte-identical, and it was read as success on a reply that
never landed. The proof is a read of the post on its own permalink, with
the prose compared against the copy that was sent — read from the post's
OWN text element, not the whole article, which carries the link card and
the engagement chrome and reads false on a perfectly landed post. Find the
owning article by the article whose own time link points at the id, so a
quoted post is never mistaken for the one being verified.

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
it.** When the last token is a URL, X promotes it to a link card and the
raw URL string is then absent from the post's text. A substring check for
the URL reads false on a perfectly landed link, and a comparison that
leaves a marker where the span was makes the two differ by exactly that
one character — so a reply that landed perfectly reads as a mismatch.
Remove the url span from BOTH sides and compare as prose; the address is
proved by the card text and the t.co redirect. `xcompare_test.py` pins
this in both `xreply.py` and `xpost.py`; run it after touching either.

**The copy goes in through CDP, not through the page.**
`Input.insertText` is a real input event and the editor's own path
accepts it. `document.execCommand('insertText')` was measured DOUBLING
the copy — 208 characters read back as 416 — and `execCommand('delete')`
to clear the selection first is a banned call: it raises Chrome's
unsaved-changes dialog, which then blocks every later CDP call.

**One substitution mode.** Every placeholder in a JS template is a JS
expression slot and every value is `json.dumps`'d. A placeholder inside
a quoted string is a quote-injection bug; a bare 19-digit id is a number
literal, which loses precision and matches nothing.

**A refusal is the script declining on purpose.**
`references/refusals.md` says what each one means and what to do about
it. Every one exists because the alternative produced a public defect.

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
| `verify_no_unsafe_posting.py` | the commit gate on these scripts; run its `--self-test` after changing it |

Run them with `python3` from this directory. `xconfig.py` holds every
environment-specific value and reads it at call time — the state
directory, the browser endpoint, the account handle, the code directory.

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
one space. `--allow-no-repo` is for a reply that carries no address at all.
The exit code is 0 only when the reply was verified; a non-zero code means
nothing was sent or the landing was unproven, and the verdict line names
the step that refused.

## The browser and the state

The harness browser answers 403 on x.com and carries no x.com session, so
`xbrowser.py` copies the session cookies out of the user's real Chrome
profile into a private profile and launches a headless Chrome against the
copy. `~/.hermes/state/x-post/` holds the browser endpoint, the account
handle, the answered ids, the publication record and the lock — NOT the
scratch directory, because the daily cleanup removes scratch files older
than a day. `references/browser-and-state.md` has the details.

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

`references/site-failures-and-pacing.md` covers the three states a run
cannot tell apart by eye: the site serving its error page, the site
rate-limiting an account that answers too fast, and the proxy being
dead. Read it when the feed comes back empty or a page stops rendering.

**Zero candidates is not "nothing worth answering".** The feed reads as
empty under an error page, and a run that cannot tell the two apart
reports a success it did not earn. `xfeed.py` retries an error page
before giving up; when the retries are exhausted, report the failure,
not a target count of zero. **Pace the replies** too: one account
answering dozens of posts inside an hour trips the same limit. The count
is a target, not a quota — fewer replies, each landed and verified, beats
a burst that ends in a rate-limited run and an unverifiable last reply.

## Which own repository may be promoted

`xrepo.py --pick` decides it, and the decision is **reachability**, not
on-topic-ness: a repository that answers 404 anonymously is not a
candidate, because the link would be dead for every reader who is not
signed in. One whose last push is over a fortnight old is not worth
promoting either.
