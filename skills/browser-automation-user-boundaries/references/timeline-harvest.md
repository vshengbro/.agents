# Harvesting a timeline, measured

Reading a feed is not a snapshot call. The DOM you can see is a moving window,
and every count taken from it is a statement about that window.

## The feed is a virtual list holding ~7-8 articles at a time

A scrolled home timeline exposes a `scrollHeight` in the tens of thousands of
pixels while `document.querySelectorAll('article').length` stays in single
digits — the list recycles its nodes. So **one pass cannot see N posts**, and a
harvest that loops to its limit inside a few rounds has collected the window,
not the feed.

Iterate: collect → `scrollBy(0, innerHeight * 0.85)` → wait for the list to
re-render → collect, dedupe by status id, until the limit is reached or N
consecutive rounds add nothing new. Scroll-then-count returns the same handful
of ids forever and looks like a working script returning a small result.

**Scroll position is state that outlives the run.** A second harvest started
where the previous one stopped and returned 3 posts where the first had
returned 102 — nothing was wrong, the collector was reading the tail of a feed
it had already walked. Return to the top (`scrollTo(0,0)`) and let it settle
before counting anything. The check is the **position**, not the URL: a guard
written as "the URL is /home, so we are on the timeline" passes while the feed
sits 131618px down, and every subsequent scroll then descends into older
content.

**Assert the surface you are on before counting, and after every crash.** A tab
left on `/compose/post` or on a status page still has a scrollbar, still scrolls,
and still answers queries — so a harvest run there reports a handful of items
that happen to be the quoted post inside a modal, and reads as an empty
timeline. Require `/home` in the URL **and** `scrollTop` near zero **and** no
dialogs open before the first collection, and re-assert it at the start of every
run rather than trusting the previous one.

**A feed that stops growing has stopped serving, not ended.** Measured: a
document reporting ~9-10k of scrollHeight while the number of rendered
`article` elements never exceeded 3, across 40+ scroll rounds. That is the
platform failing to paginate, and it is not distinguishable from "you scrolled
to the end" unless you check the ratio. Compare the rendered count against the
requested limit and the scroll position against the bottom: a deep document
with a handful of articles means the surface is broken. Report that as a
broken surface, never as "the feed contains N posts", and never as evidence
that a post was deleted — an un-paginated surface proves nothing about what
exists, only about what it happened to render.

**Bottom detection beats a round cap.** The feed ends when
`scrollTop + clientHeight >= scrollHeight - 50`; report that as "the feed ends
here", because a count below the requested target is otherwise indistinguishable
from a scraper that undercounted. Say which of the two it was.

## Read the author, not the timestamp

`[data-testid="User-Name"]` innerText is `display\n@handle\n17小时` — the **last**
line is the relative time, and `.split('\n').pop()` returns it. That silently
produces a field reading `'17小时'` where an account handle belongs, and every
downstream filter, dedupe and audit is then wrong in a way that looks like
plausible data. Take the line that starts with `@`; take `line[0]` for the
display name.

## Guard the return before indexing it

A DOM `.map()` can hand back `undefined` or a partial shape, and `rows[i]["status"]`
then raises `KeyError` mid-collect, losing the whole run. Use
`tab.js(...) or []` and skip non-dicts. The same discipline as returning a
string verdict under the key the caller reads: assert the shape at the call
site, not inside the helper.

## Relevance triage is the real work, and its cost is the finding

A keyword filter over a harvested feed is a *candidate generator*, never a
selection. Read the full text of every candidate before drafting, and expect
the survivors to be a small fraction. From a feed of ~100 posts, a
dev/backend keyword sweep returned ~24 candidates of which a handful had a
genuine answer — the rest were markets, weather, model pricing, emoji jokes.

Classes that a keyword sweep admits and that a human reading rejects:

| Class | Why it is not a target |
|---|---|
| Official org product announcements | Replying to a vendor's own release with a third-party repo is an interruption |
| Engagement-farming quiz accounts | "A. React / B. jQuery — which?" posts exist to collect replies |
| Off-topic lifestyle, markets, personal stories | A link appended here is spam by construction |

Present the triage as a **table with a verdict per candidate** and state the
counts — "102 harvested, 24 candidates, N genuinely answerable" — rather than
handing back a silently truncated list. The user can see where the judgement
was made and overrule it; a bare list hides it.

## A revisited For-You feed re-serves — act on likes from a stable surface

Measured: 41 posts harvested from /home, then /home was re-entered and NONE of the
three like targets ever rendered again across 50 scroll rounds — the feed had
re-served fresh content. Search-result pages
(`/search?q=from:<handle>%20<keyword>&f=live`) are stable: the same post stayed
findable across rounds there, and all three likes landed first try. If an action
target came from a feed read that has since been left, re-locate it through search,
not by re-walking the feed.

## Harvesting is not consent to publish

A collector that walks a feed at the user's request is not authorisation to
reply to everything in it. Reply scale is a separate decision from reading
scale, and the account carrying it is the user's — see the standing rule on
bulk third-party engagement.