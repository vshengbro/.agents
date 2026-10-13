# Verifying Chinese Statutes by Fetch

Never write a Chinese statute citation from model memory. Article numbers
drift between versions, an amending decision renumbers whole chapters, and a
misnumbered citation is caught immediately by the receiving authority or court.

Verify every article whose text you rely on, and verify that the text you got
is the article you asked for.

## Source ladder

Try in order; move down only on failure.

1. **Official publisher** — `gov.cn`, `npc.gov.cn`, `samr.gov.cn`, `mee.gov.cn`,
   ministry sites. Highest authority.
2. **`court.gov.cn` / `gongbao.court.gov.cn`** — judicial interpretations.
3. **Wikisource** (`zh.wikisource.org`) — clean full-text mirrors of national
   law. Reliable for 民法典 / 消法 / 民事诉讼法; useful as a second opinion
   when an official page has a broken paginated layout.
4. **Provincial government reposts** — `.gov.cn` subdomains that reprint the
   national text whole. Useful when the central page is unreachable.

## The TOC-drift trap

An aggregated copy of a law may list its articles out of order, truncated, or
from a superseded version. Extracting "the Nth article" by position returns
confidently wrong text.

**Detection.** After extracting an article, read it. If the content does not
sound like what you expected — wrong subject matter, different parties, a
definition clause, a *consequence* provision rather than the *duty* provision
you wanted — you have the wrong article, regardless of what the label said.

A specific failure mode: fetching the 消法 from a short page that renders only
some chapters returns chapter-boundary misalignments, so `第26条` comes back as
a national-protection provision when `第26条` is in fact the format-terms
provision. The extraction "succeeds" and every citation downstream is wrong.
Re-fetch from a different source before trusting any article from a page whose
extracted length looks short.

## Fetching: curl with a browser UA

The default page extractor is frequently refused by Chinese government hosts
(it reports the URL as targeting a private or internal address). Curl with a
desktop browser User-Agent is the reliable path.

```python
import re, subprocess, html

UA = ["curl", "-sSL", "--max-time", "40", "-A",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"]

def txt(url):
    t = subprocess.run(UA + [url], capture_output=True).stdout.decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", "\n", t)
    return re.sub(r"\n\s*\n+", "\n", html.unescape(re.sub(r"[ \t\xa0]+", " ", t)))

def article(text, cn_num, span=700):
    m = re.search(r"第%s条\s*(.{0,%d}?)(?=第[一二三四五六七八九十百零]+条)" % (cn_num, span),
                  text, re.S)
    return m.group(1).strip() if m else "NOT FOUND"
```

Notes on the shape:

- `capture_output` then `.decode("utf-8", "ignore")` — passing `text=True`
  raises `UnicodeDecodeError` on government pages served in GBK/GB2312.
- Article numbers are Chinese numerals. Build the alternation class once;
  adding a literal `第条` (e.g. `第157条条`) silently matches nothing and every
  lookup returns `NOT FOUND` while appearing to work.
- Print the extracted text and read it. Do not chain straight into the draft.

## Verify the fit, not just the number

The citation must support the specific sentence it sits beside. A real
article number attached to an unrelated proposition is worse than no citation,
because it signals that the citation was never opened.

Quick check per citation:

- Is this the provision that **imposes the duty / grants the remedy**, rather
  than a neighbouring provision that only mentions the topic?
- Does it cover the subject matter at hand (consumer protection, contract
  format terms, pricing) or a different regime?
- Is it still in force and not superseded by a later amendment?

## Common articles worth confirming each time

Do not reuse a prior session's confirmation — re-fetch when the specific
article matters to the outcome. These are the ones most often cited from
memory and most often misremembered:

- **《消费者权益保护法》** — 20 (truthful/misleading advertising, duty to answer
  queries), 23 (service quality/performance must match representation), 26
  (format terms; invalid content), 39 (dispute resolution routes), 53
  (prepaid services not delivered → refund), 55 (fraud → triple damages), 56
  (administrative penalties, incl. misleading advertising and refusing refunds).
- **《民法典》** — 148 (fraud → rescission), 151 (grossly unfair → rescission),
  157 (restitution after rescission), 497/498 (invalid / construed against the
  drafter of format terms).
- **《明码标价和禁止价格欺诈规定》** — the provision requiring services to
  display pricing **or the pricing method**, and the one barring failure to
  prominently disclose terms unfavourable to the consumer. Price-fraud
  arguments usually live here rather than in the consumer law itself.
