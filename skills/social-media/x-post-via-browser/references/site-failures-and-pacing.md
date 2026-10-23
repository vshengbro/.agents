# When the site fails, and how fast to post

Three states look the same from a run's seat: the page renders but the
feed is empty, the page stops rendering articles at all, and the network
is down. They need different responses, and guessing costs the run.

## The error page

X serves an error page instead of the timeline when it is unhappy with
the request rate. The page still renders — the sidebar, the compose
button, the footer all appear — so a check that only asks "did the page
load?" passes, and the article count is ZERO.

**Detect it by the article count, not by the page title.** An article
count of zero on a page that otherwise rendered IS the error page.

**The error page is per-surface, not per-account.** The timeline can
serve it while a status permalink still renders the article, and a
different tab can serve it while the first recovers. So "one page
rendered empty" does not mean the account is blocked — and a run that
concludes "X is down" from one empty timeline has measured one page.

**Distinguish it from an empty feed by asking for a second surface.**
Open a known-good status permalink and count its articles. If the
permalink renders and the timeline does not, the timeline is serving the
error page. If both are empty, the session or the network is the
problem. `xrepo.py --network` answers the network half.

**THE CAUSE IS USUALLY STALE TABS, NOT THE REQUEST RATE.** Measured on
2026-10-22: the timeline went to zero articles with the session still
signed in and the network healthy, and the browser was carrying **16
stale tabs** — leftovers from runs that were killed or whose tab close
did not land. The feed came back by dropping them, not by waiting.

So the recovery is **prune, then retry**: `xbrowser.py prune` closes
every page tab except the newest, and `xfeed.py` does that automatically
before each retry. Opening another tab is NOT the fix — a browser
carrying the stale tabs serves the error page on the new one too. A
restart of the browser (`xbrowser.py down && xbrowser.py up`) is the
heavier version of the same remedy, and it works.

**A tab that is closed in a `finally` is closed.** The stale tabs exist
because a run was killed before its cleanup ran. A tab left open by an
interrupted run is the thing that eventually takes the feed down, so
close them as you go.

**Zero candidates is not "nothing worth answering".** The feed reads as
empty under an error page, and a run that cannot tell the two apart
reports a success it did not earn. `xfeed.py` retries an error page
before giving up; when the retries are exhausted, report the failure —
not a target count of zero.

## The refusal that is not the error page

A third state looks like the error page and is not it: **the document
request is refused and the page renders EMPTY.** Measured 2026-10-23:
after a run of permalink navigations on one tab — 55 in one run, 64 in
another — every later request for an HTML document on that origin came
back **403 with a zero-length body**, and the DOM reported
`readyState: "complete"` with `document.body.innerText` empty,
`document.title` empty and `document.documentElement.outerHTML.length`
of 39.

So the article count is zero — the same reading as the error page — but
there is no error page, no sidebar, no footer, and **the usual remedies
change nothing**. Measured, none of these restored access: a **new tab**
on the same browser, the **same tab re-navigated**, a **browser restart**
(`xbrowser.py down && xbrowser.py up`), and **clearing cookies plus site
data** for the origin. The same browser served `example.com` and
`x.com/robots.txt` normally throughout, so this is neither the network,
the proxy, nor the session.

**Tell the two apart by asking for the status, not by counting articles.**
`document.querySelectorAll('article').length` is zero in both cases. The
status is in the navigation entry:

```js
performance.getEntriesByType('navigation')[0].responseStatus  // 403
```

At the CDP level the same fact arrives on `Network.responseReceived` —
filter on `params.type == "Document"`, **not** on the mime type, because
the refusal is served as `text/plain` and a `text/html` filter matches
nothing.

**The recovery is TIME, and it needs no action.** Measured: the same
browser answered 403 for every document, then answered 200 with the
full timeline again later, with nothing done to it in between — no
restart, no cookie change, no new tab. So a run that retries through a
refusal spends its budget and still fails, while the site recovers on
its own; the useful move is to stop, report that the site refused the
requests, and let the next run find the site healthy. Because the
refusal arrived after a run of permalink reads both times it was
measured, pace the reads rather than treating a long read loop as free.

## Pacing

One account answering dozens of posts inside an hour trips the same
limit, and the symptom is the error page above: the run collects
candidates, reads them, and then every permalink renders empty. The
replies that landed are still real and verified; the ones after the limit
are not sent.

**The count is a target, not a quota.** Fewer replies, each landed and
verified, beats a burst that ends in a rate-limited run and an
unverifiable last reply. A run that has already posted its share and
then sees the error page should stop and report what it landed — not
keep collecting.

**The lock and the state are what make a partial run resumable.** The
answered ids are written as each reply lands, so the next run skips them
and the count is a running total rather than a per-run guess.

## The proxy

`xrepo.py --network` distinguishes the two network states in one command:

- every PROXIED host times out while a DIRECT host answers → **the proxy
  is dead.** Not Cloudflare, not the network, and not a user agent to
  bisect.
- a host answers 403 → the site is refusing the client, and the network
  is fine.

Bisecting user agents against a dead proxy is the classic way to burn a
whole run's budget on the wrong question.

## One run, one browser

Two runs driving one tab put a reply under the wrong post. The advisory
lock in the state directory serialises the posting scripts, and the
browser endpoint file is written once per browser, not once per run.

## A rejected landing does not mean nothing was posted

The posting scripts refuse in two very different places, and they are not
the same failure:

- **A refusal BEFORE the send click** means nothing was published. The
  composer was untouched.
- **A refusal AFTER the send click** means a post IS up. The reply
  rendered on its own permalink; only the proof of it failed.

So when a run reports a rejection after the send, READ the landed post
before concluding anything. A reply that is up with its card and its
t.co has landed, whatever the script said.

The cause of the false rejection on 2026-10-22 was a race, not a
defect in the reply: a post's own text mounts before its link card, and
the landing read stopped on the text, so it judged a half-hydrated post
and called the card a lost link. The read now waits for the card.

**Record the parent as answered as soon as the reply renders.** The
answered set is what stops a later run from answering the same post
twice. A run that refuses after the send but before recording leaves the
parent open, and the next run posts a second reply to it — two public
replies under one post, which is the defect the lock and the answered set
exist to prevent.
