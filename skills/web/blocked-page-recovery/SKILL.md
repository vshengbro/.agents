---
name: blocked-page-recovery
description: "Use when a fetch returns 403/429, a Cloudflare or bot wall, or a paywall. Work down an archive/API ladder with provenance instead of retrying."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Archives, Wayback, Paywall, WAF, Fallback]
    related_skills: [chrome-devtools-protocol]
---

# Blocked-Page Recovery

When a page won't fetch — 403/429, "Just a moment…", a bot wall, a paywall —
don't loop on the same URL and don't hammer the origin. A third party often
holds a **copy**. Work this ladder, cheapest first.
## Index

Stop conditions — read before climbing · The ladder — one script · Provenance discipline (non-negotiable) · Fake successes — routes that LIE · Proxy relays: don't · Resource lifecycle · Not this skill


## Stop conditions — read before climbing

- **A paywall or "subscribers only" is an authorization decision by the
  publisher.** An archive of that URL is the publisher's own past distribution of
  the same gated content — reading what the paywall withholds through it is
  circumvention, not recovery. If the page is gated: say so, offer the public
  parts (headline, lede, metadata, the publisher's own RSS/API), and stop. Use a
  subscription only if the user actually has one; never guess or fabricate
  credentials.
- **Never defeat bot protection, CAPTCHAs or login walls** — no rotating
  User-Agents, no spoofed headers, no solved challenges, no session replay to
  impersonate an entitled reader. When the ladder is exhausted the answer is
  "this page is gated — here is what I can legitimately reach", not "try
  harder".
- **Public archives and public APIs are fair game**: Wayback, archive.today,
  open RSS/sitemaps, and any endpoint the publisher serves without a session.
- **2 failed attempts per route, then move down** — retries against a 403/429
  make the block worse and can rate-limit your IP across routes.
- **Respect robots/ToS signals on the origin**; archives exist for content you may not fetch directly.

## The ladder — one script

```bash
python3 scripts/recover_page.py "https://example.com/blocked-article" --json
```

Stdlib only. Flags: `--json` (metadata), `--out FILE` (write the body),
`--timeout N` (default 25). Exit 0 = recovered, 1 = nothing worked, 2 = bad
invocation. It walks every route in order, validates each body, and prints the
first genuine hit with its provenance.

```
1. Wayback Machine  - archive.org "available" API, then the closest snapshot; CDX
                       (.../cdx/search/cdx?url={URL}&output=json) to enumerate; CDX
                       503s under load -> back to `available`, don't retry
2. archive.today    - domain rotation: archive.ph -> .md -> .li -> .is (rate-limits hard)
3. Jina Reader      - only if JINA_API_KEY is set (live server-side render; anonymous 401)
4. API-first pivot  - /api/, /graphql, .json, RSS/Atom, /sitemap.xml on the same host
5. Real browser     - last, most expensive resort; same rules still apply
```

WAFs protect the HTML surface far more aggressively than the data endpoints
behind it, so route 4 is the highest-value manual step — and public endpoints are
not a bypass. Stdlib-only calls:

```bash
curl -sL "https://archive.org/wayback/available?url={URL}"
curl -sL --max-time 20 "https://archive.ph/newest/{URL}"   # rotate domains
curl -s -H "Authorization: Bearer $JINA_API_KEY" "https://r.jina.ai/{URL}"
```

## Provenance discipline (non-negotiable)

| Route | Provenance | How to cite |
|-------|-----------|-------------|
| Wayback / archive.today | `snapshot` | Cite **with the snapshot date**: "as archived 2026-08-06". Never present a snapshot as the live page — it may be stale. |
| Jina Reader / live fetch / browser | `live` | Cite normally. |

If the user needs *current* data (prices, availability, breaking news), a
snapshot is context, not an answer — say so explicitly and note its age.

## Fake successes — routes that LIE

These return HTTP 200 with a plausible body that is NOT the page:

- **Google Cache is dead** (since mid-2024). `webcache.googleusercontent.com`
  returns 200 + tens of KB of Google Search interstitial with a JS redirect.
  Never use it.
- **AMP caches** (`*.cdn.ampproject.org`) mostly return a ~300-byte
  `<title>Redirecting</title>` meta-refresh stub pointing back at the original
  (blocked) URL — treating that as success creates a fetch loop.
- **Rate-limit bodies**: archive.today 429 pages are multi-KB HTML. Validate
  against the target's actual content, not just size or status code.

`recover_page.py` rejects these via per-route byte floors, interstitial titles
("Just a moment", "Redirecting", "Google Search", "Attention Required") and
redirect stubs whose target is the original host. Reject them by hand too when
running routes manually.

## Proxy relays: don't

Generic "web proxy" relays are man-in-the-middle by construction. Never send
cookies or Authorization headers through one, and don't use them for anything
the user will rely on — provenance is unverifiable. Prefer archives, which at
least timestamp their copies.

## Resource lifecycle

`recover_page.py` owns nothing beyond the file you pass `--out`. Route 5 does:
a browser, tab, port or container you launch is yours to close on **every** exit
path, read back by exact id before you call it done, and retained only if the user
explicitly asked. Policy: [`agent-skills-source-sync`](../../agent-skills-source-sync/SKILL.md#临时验证资源生命周期硬规则-3-细则).

## Not this skill

- A page that loads fine but you want structured data → `web_extract` /
  `browser_exec`.
- Browser you must drive (login state, clicks, uploads) → `browser_exec`, or
  `web/chrome-devtools-protocol` for raw CDP.
- Blocking caused by your own tooling (proxy, firewall, offline machine) →
  diagnose that first; it is not a site block.
