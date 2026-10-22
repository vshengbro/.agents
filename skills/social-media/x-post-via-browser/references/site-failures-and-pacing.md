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

**Zero candidates is not "nothing worth answering".** The feed reads as
empty under an error page, and a run that cannot tell the two apart
reports a success it did not earn. `xfeed.py` retries an error page
before giving up; when the retries are exhausted, report the failure —
not a target count of zero.

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
