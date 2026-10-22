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
| `LANDED LINK PRESENT BUT NOT PROVEN` | the post is up and carries a rewritten link, but no card names the repository | Treat as a failure. Report it. |
| `another engagement run holds the lock` | a correct skip | Report and stop entirely. Do not wait it out inside the run. |

## The refusals that exist because of a measurement

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
