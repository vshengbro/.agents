# What each refusal means

Every refusal below is the script declining ON PURPOSE. The alternative in
each case produced a public defect: a standalone post where a reply was
meant, a post missing its address, a copy that was not the copy that was
written. Do not work around a refusal. Read the verdict line, report the
reason, and move to the next candidate.

| verdict | what happened | what to do |
| --- | --- | --- |
| `the composer already holds text` | a draft that is not ours is in the composer | Do not clear it, do not reload, do not open a tab. Report and stop. |
| `the parent post is not mounted` | the composer is not bound to the parent, so a send would publish a standalone post where a reply was meant | Report and move on. Do not force it. |
| `the composer is not inside a dialog` | the send button cannot be told apart from the main composer's | Refused rather than risking a standalone post. Report and move on. |
| `the copy did not survive the re-read` | the composer holds something other than the copy | Nothing was sent. Report the mismatch. |
| `the editor holds N paragraphs for M in the source` | the paragraph structure would be lost on publication | Nothing was sent. Check the source file for blank lines — a blank line becomes a doubled line in the editor, so the copy must use single newlines. |
| `the landed text is not the copy that was sent` | the post is up but its prose differs from the copy | **Read the landed post before concluding anything.** A trailing address becomes a card, so the landed text has no url span while the copy has one: that is a ONE-CHARACTER difference, not a mangled post. See `xcompare_test.py`. |
| `NO POST ON PAGE` | nothing was established on the permalink | Nothing is proven. Report it; do not publish a replacement. |
| `LANDED LINK LOST` | the post is up WITHOUT its address | A public defect. Report the URL, do not send the remaining versions, do not send a replacement. |
| `LANDED LINK PRESENT BUT NOT PROVEN` | the post is up and carries a rewritten link, but the address does not resolve to the one that was sent | Treat as a failure. Report it. |
| `the link landed as no card and no t.co` | the post is up but the read saw no card and no t.co | The card hydrates after the text. The read now waits for both; if it still refuses, the address really is not there. Report it; do not send a replacement. |
| `the link landed without a card` | the post is up with a t.co but no card wrapper | The card is the proof that the address survived publication. Report it; do not send a replacement. |
| `the link does not point at the address that was sent` | the post is up and its link resolves to a different place | The redirect names the place, and it names the wrong one. A public defect. Report it; do not send a replacement. |
| `another engagement run holds the lock` | a correct skip | Report and stop entirely. Do not wait it out inside the run. |
| `weighted length N over X's M` | the copy is longer than X will accept, counted the way X counts | Nothing was sent. Shorten the copy. The count is not `len()`: a CJK character weighs 2 and an address weighs 23, so a Chinese reply of 186 characters is 372 and is refused. |

## The refusals that exist because of a measurement

**A REFUSAL TABLE DRIFTS FROM THE CODE THAT PRINTS IT.** The verdict
strings here are the API: a run reads them to decide what to do next, so
a table that names a string the scripts stopped printing sends the reader
after a verdict that no longer exists — and the one that DID replace it
goes unmentioned. The copy insertion moved to a different mechanism and
its refusal message changed with it, while the table kept the old one.

So when a script's verdict changes, change the table in the same commit,
and prove it mechanically rather than by reading:

```sh
python3 - <<'EOF'
import re, glob, pathlib
ref = pathlib.Path("references/refusals.md").read_text()
src = "".join(pathlib.Path(p).read_text() for p in glob.glob("scripts/*.py"))
for v in re.findall(r"^\| `([^`]+)`", ref, re.M):
    static = re.sub(r"\b[NM]\b", "", v).strip()
    parts = [p for p in re.split(r"\s{2,}", static) if len(p) > 8]
    hit = all(p in src for p in parts) if parts else static in src
    print("OK " if hit else "MISS", v)
EOF
```

Every line must print OK. A MISS means the table describes a verdict the
code does not emit.

**THE SEND BUTTON MUST COME FROM THE EDITOR'S OWN DIALOG.** On the reply
route the page holds a main composer and a reply dialog, and the FIRST
enabled `tweetButton` on the page belongs to the main composer. Clicking
it publishes a standalone post where a reply was meant. The only thing
separating them is the button's `disabled` attribute, and that changes as
the text is typed. Take the button from the dialog that CONTAINS the
editor the copy went into, and refuse when there is no such dialog.

**THE PARENT IS IDENTIFIED BY THE TARGET'S OWN TIME LINK, NOT BY THE
ROUTER.** The reply control navigates to `/compose/post`, so the URL no
longer says which post is being answered. The article whose own time link
points at the target id is the one the composer is bound to. Matching on
any status link picks up a quoted post or a reply instead.

**THE COPY GATE REFUSES A LETTER-SUFFIXED DOTTED TOKEN, AND NOTHING
ELSE.** X linkifies any dotted token whose last part is letters, and the
span it replaces reads back as a line break — a bare `crates.io` in the
body split a sentence in two. A version number ends in digits, X does not
linkify it, and a reply about a release is mostly version numbers. A
gate that refuses decimals refuses the reply most worth sending.

**THE COPY IS MEASURED THE WAY X MEASURES IT.** X counts WEIGHTED
characters, not characters, and the limit is 280 of them: a CJK
character weighs 2, an address weighs 23 whatever its real length is, and
a Latin character weighs 1. A gate that measures `len()` therefore lets
through a Chinese reply that the site refuses — 186 Chinese characters
read as 186 to Python and as 372 to X. That is not a near miss: the copy
goes into the composer, the send is refused, and the text stays there, so
the NEXT candidate trips "the composer already holds text" and the run
answers nothing.

The rules come from twitter-text v3, the library the web client uses to
size its composer, and `xlength.py` implements them: the four ranges
whose characters weigh 1, the default weight of 2, and the fixed length
of 23 for an address. `xlength_test.py` pins the measurement.

**THE ADDRESS IS PROVED BY THE REDIRECT, NOT BY THE CARD'S TITLE.** The
card X renders for a trailing address carries the TARGET PAGE's own
title, so it names the repository only for a bare repository address. A
pull request, an issue or a release address lands a card titled with the
REQUEST — and the last path segment of such an address is its NUMBER, so
the check that looked for that segment in the title read false on a post
that had landed perfectly. That is what happened on 2026-10-22: a
standalone post carrying a pull request address was up, with its card and
its t.co, and the run reported it as unproven.

So the short link is followed to the place it names, and that place is
compared with the address that was sent. The card's title stays a second
proof, for the bare repository case and for the case where the redirect
cannot be read at all. `xcompare_test.py` pins both.
