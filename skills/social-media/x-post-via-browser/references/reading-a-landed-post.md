# Reading a landed post: the three traps that made a good post read as a bad one

Diagnostics for the "is this post actually landed?" question. Each one
produced a false rejection of a post that had landed perfectly, and each one
is now pinned by a script test.

## The card hydrates AFTER the post's own text

The article mounts first; the card wrapper and the t.co anchor arrive a beat
later. A landing read that stops as soon as the text is there is reading a
half-hydrated post, and it calls a link that landed with its card a lost one —
a reply that was up, with the card naming the repository and the t.co
resolving to it, was reported as rejected. So the read keeps polling until
BOTH the card and the t.co are present, and only then does it judge the
address. `link_ready()` is that gate, and `xcompare_test.py` pins it in both
scripts.

## A trailing address lands as a card, so the landed text has no url in it

When the last token is a URL, X promotes it to a link card and the raw URL
string is then absent from the post's text. A substring check for the URL
reads false on a perfectly landed link, and a comparison that leaves a marker
where the span was makes the two differ by exactly that one character — so a
reply that landed perfectly reads as a mismatch. Remove the url span from
BOTH sides and compare as prose; the address is proved by following the t.co
to the place it names. `xcompare_test.py` pins this in both `xreply.py` and
`xpost.py`; run it after touching either.

## The card's TITLE is not the address

It carries the target page's own title, so it names the repository only for a
bare repository address — a pull request address ends in a number, and no
title contains a number. Follow the t.co and compare the place it names with
the address that was sent. `references/refusals.md` has the case.

## The copy is measured the way X measures it

X does not count characters; it counts WEIGHTED characters, and the limit is
280 of them. A CJK character weighs 2, an address weighs 23 whatever its real
length is, and a Latin character weighs 1 — so a Chinese reply of 186
characters is 372 and is refused by the site, while `len()` says it fits. The
gate measures the weighted length, before anything is typed, because a copy
refused at the send button leaves the text sitting in the composer where the
next candidate trips the "composer already holds text" refusal.
`xlength.py` holds the measurement and `xlength_test.py` pins it against
twitter-text's own configuration; run the test after touching either.

## A landed post is the only proof

The toast is not a receipt: a sibling run's toast is byte-identical, and it
was read as success on a reply that never landed. The proof is a read of the
post on its own permalink, with the prose compared against the copy that was
sent — read from the post's OWN text element, not the whole article, which
carries the link card and the engagement chrome and reads false on a
perfectly landed post. Find the owning article by the article whose own time
link points at the id, so a quoted post is never mistaken for the one being
verified.

## The copy goes in through CDP, not through the page

`Input.insertText` is a real input event and the editor's own path accepts
it. `document.execCommand('insertText')` was measured DOUBLING the copy —
208 characters read back as 416 — and `execCommand('delete')` to clear the
selection first is a banned call: it raises Chrome's unsaved-changes dialog,
which then blocks every later CDP call.
