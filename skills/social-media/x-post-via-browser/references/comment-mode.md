# A comment, and how it differs from a post

A comment is a reply: it hangs from somebody else's post. The scripts
do the same work for both -- like, compose, send, read back, prove -- but
the things around them differ, and the differences are where the
defects live.

## The parent comes first, and it is chosen before the copy is written

A reply has to answer the post in front of it. That makes the parent the
FIRST decision, not the last: the parent is found, read in full, and
only then is the comment written against it. A comment written before
the parent is known is a comment about a project in general, and a
general comment under a specific post is a wasted reply.

The parent's text is clipped by the timeline and by the search results.
The clipped half is usually the point, so read the parent from its own
permalink with `xread.py` before writing.

**Write the comment in the parent's language.** A reply to a Japanese
post in English answers nothing, and the reader learns that the account
replies in a language it does not think in. The parent's text is on
disk, so this is checkable, not a matter of taste.

**Say something the parent did not say.** A restatement of the post is a
wasted reply: the parent is already visible to everyone who reads the
thread. The comment's job is to add the thing the parent does not have.
For a project post, that thing is usually the mechanism -- what actually
happens inside, which is not in the announcement.

## The copy is bounded by X, and the bound is weighted

A reply is 280 weighted characters, not 280 characters. CJK counts two,
so 140 Chinese characters is the whole budget. `xlength.py` measures it
the way X measures it, and the composer refuses a longer copy AFTER it
has been typed -- which leaves the text sitting in the composer for the
next candidate to trip over. Measure before you write.

A dotted token is linkified by X, and the span it replaces reads back as
a line break, so a sentence split in two. `crates.io` in a reply is a
refusal, not a style note.

An address in a reply is a claim about the account: it says this reply
promotes this repository. Only one of the account's own repositories
may be promoted, and only at the end of the reply, preceded by exactly
one space. A reply about somebody else's project carries no address at
all, and one that needs an address to make sense is a post.

## Proving a reply landed, and proving it is a REPLY

The script's own `VERIFIED reply by @handle` line is the receipt. It is
printed only after the reply rendered on its own permalink, the landed
prose matched the copy that was sent, and the thread carried both the
parent and the reply.

There is a second question, and it is the one that separates a comment
from a post: **does it hang from the parent?** Read the reply's OWN
page. X renders a reply by mounting the parent as an article above it,
and a standalone post has nothing mounted above it.

Do NOT look for the reply on the PARENT's page. The parent's page loads
its replies lazily and RANKS them, so a busy thread pushes an answer off
the page. Measured on this account: a parent with 52 loaded replies did
not show a reply that WAS under it. "My reply is not on the parent's
page" is not evidence that the reply is not under that parent -- the
reply's own page is the place to look.

## A reply has an extra state the post path does not

The post path's states are pending, approved, claimed, posting,
posted_unverified, verified, uncertain, failed. A reply has one more
thing: the PARENT, and the parent is claimed at approval time, because
the comment was written to answer that specific post.

`posting` is still the irreversible boundary: it is written before the
click, and a row left there by a killed run may already be live. A row
in `posting` becomes `uncertain`, which STOPS the series, because
resending a reply that may already be live is how a duplicate is made.
A row in `claimed` that never crossed the boundary goes back to the
queue, because nothing was sent for it.

## What the reply does to the account's state

The parent's id is recorded when the reply renders, not after the last
proof passes -- otherwise the parent stays open and the next run answers
it twice. The reply's OWN id is not recorded as answered: it is not a
post to be answered, and recording it would hide it from the account's
own history.

The account is the scarce resource. Two writers on one account is how
it gets rate-limited into a timeline that renders but shows nothing, and
a run that cannot tell the difference reports a success it did not
earn. So the engagement job and the series check each other before
either writes.
