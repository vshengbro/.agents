---
name: x-post-via-browser
description: Use when posting, replying, or liking on X/Twitter from this account, or when an X engagement cron job must run. Drives a dedicated headless Chrome over raw CDP; no verified landing means no claim of success.
---

# X posting and engagement

Posting on X from this account goes through the scripts in `scripts/`. They
drive a dedicated headless Chrome over raw CDP, and they do the mechanical
work — opening the composer, inserting the copy, clicking send, and reading
the landed post back. The judgement work — what to say, to whom, and whether
it is worth saying — stays with the caller.

## The rules that matter

**A landed post is the only proof.** The toast is not a receipt: a sibling
run's toast is byte-identical, and it was read as success on a reply that
never landed. The proof is a read of the post on its own permalink, with the
prose compared against the copy that was sent.

**Like first, then reply, then verify.** A post that is answered is a post
that is liked. The like is idempotent — it reads the button state before it
clicks, so a retry cannot toggle a like off.

**A status id never appears in a transcript.** An id is a bare 19-digit
number, and the display layer replaces such numbers with a redaction token:
one id in a list of seven was redacted. Name candidates by their INDEX and
let the scripts read the ids out of the candidates file. `read_file` shows
the real value; a terminal transcript does not.

**The collect and the answer are one process.** The feed virtualises articles
out of the DOM within about a minute, so a candidate read at one moment can
be gone at the next. `xreply.py` works against the parent's own permalink,
never against the feed.

**A trailing address lands as a card.** When the last token is a URL, X
promotes it to a link card and the raw URL string is then absent from the
post's text. A substring check for the URL reads false on a perfectly landed
link. The proof is the card text plus the t.co redirect.

**One substitution mode.** Every placeholder in a JS template is a JS
expression slot and every value is `json.dumps`'d. A placeholder inside a
quoted string is a quote-injection bug; a bare 19-digit id is a number
literal, which loses precision and matches nothing. Build selectors by
concatenation.

## The scripts

| script | what it does |
| --- | --- |
| `xbrowser.py up\|status\|down` | the dedicated browser; copies the session cookies out of the real Chrome profile and launches against the copy |
| `xfeed.py --out FILE --count N` | the candidates, into a file; already-answered ones filtered out |
| `xread.py --candidates FILE --index N` | a candidate's FULL text, from its permalink |
| `xlike.py --candidates FILE --index N` | like one post, proven by the button swap |
| `xreply.py --candidates FILE --index N --copy FILE [--repo URL\|--allow-no-repo]` | like, answer and verify one post |
| `xpost.py --copy FILE --repo URL [--dry-run]` | publish one standalone post and verify its address |
| `xtrending.py --limit N` | today's trending list, read live, with ownership from live git remotes |
| `xstate.py` | the atomic state store and the advisory lock |

Run them with `python3` from this directory. `xconfig.py` holds every
environment-specific value and reads it at call time: the state directory
(`~/.hermes/state/x-post`), the browser endpoint, the account handle, and the
code directory. Nothing is baked in and nothing is a constant.

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
one space. `--allow-no-repo` is for a reply that carries no address at all;
the gate refuses any URL in that case.

The exit code is 0 only when the reply was verified. A non-zero code means
nothing was sent, or the landing was not proven — read the script's own
verdict line, which names the step that refused.

## What each refusal means

- **`the composer already holds text`** — a draft that is not ours. Do not
  clear it, do not reload, do not open a tab.
- **`the parent post is not mounted`** — the composer is not bound to the
  parent, so a send would publish a standalone post where a reply was meant.
- **`the composer is not inside a dialog`** — the send button cannot be told
  apart from the main composer's. Refused rather than risking a standalone
  post.
- **`the copy did not read back from the editor`** — the composer holds
  something other than the copy. Nothing was sent.
- **`the editor holds N paragraphs for M in the source`** — the paragraph
  structure would be lost on publication.
- **`NO POST ON PAGE` / `LANDED LINK LOST`** — the post is up but not what
  was asked for. A post that lost its address is a public defect; report it
  and do not publish a replacement on top of it.

## The dedicated browser

The harness browser answers 403 on x.com — it identifies as HeadlessChrome,
and the same URL answers 200 with an ordinary user agent from the same
address in the same second. Overriding the user agent fixes the 403, but the
harness's own profile carries no x.com session, so the page redirects to the
login screen.

So `xbrowser.py` copies the session cookies out of the user's real Chrome
profile — a read-only sqlite backup, so a running Chrome cannot lose a
committed WAL page — into a private profile under the state directory, and
launches a headless Chrome against that copy. It never writes to the real
profile and never opens a window the user can see.

## The state

`~/.hermes/state/x-post/` holds the browser endpoint, the account handle, the
answered ids, the publication record, and the lock. It is deliberately NOT
the scratch directory: the daily cleanup removes scratch files older than a
day, and a port file that disappears between two runs is a job that cannot
find its own browser.

The state file is written atomically — a temporary file, renamed over the
target, read back before the call returns. A bare `open(path, "w")`
truncates the moment it is called, so a write that raises afterwards leaves
a zero-byte file and every prior run's record gone.

The lock is advisory and per-process. Two jobs on a schedule can overlap, and
a reply that lands under the wrong post is the result, so a run that cannot
take the lock waits and says so.

## The reply's own rules

- Read the post in full before writing about it. The feed clips long posts,
  and the clipped half is usually the point.
- Say something the post did not already say. A restatement is a wasted
  reply.
- Ground every claim in something read this run — the post, the source, the
  advisory. A claim that cannot be sourced does not go in.
- Write in the post's language.
- Never like a post you did not reply to, and never reply to a post you did
  not like.
- A failed send is reported, never retried into a second post.
