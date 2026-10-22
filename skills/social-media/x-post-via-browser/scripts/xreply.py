#!/usr/bin/env python3
"""Like a post, answer it, and prove both landed.

ONE PROCESS, IN THIS ORDER

    like  ->  compose  ->  send  ->  verify

The like comes FIRST because the obligation is per reply: a post that is
answered is a post that is liked, and a reply on a post whose like did not
confirm is the defect this ordering exists to prevent. The like is
idempotent -- it reads the button state before it clicks, so a post that is
already liked is reported, not toggled off.

The collect and the answer are also one process. The feed virtualises
articles out of the DOM within about a minute, so a candidate read at one
moment can be gone at the next. This script therefore works against the
TARGET'S OWN PERMALINK, not against the feed, and it never asks the agent to
collect a second time.

WHAT COUNTS AS PROOF

Only a read of the landed post, on the reply's own permalink, counts. The
toast is not a receipt: a sibling run's toast is byte-identical to this
run's, and it was read as success on a reply that never landed. The
permalink is also the only place the full body is visible -- the profile
timeline clips even this account's own posts behind a "show more".

A LINK AT THE END OF THE COPY LANDS AS A CARD

When the last token is a URL, X promotes it to a link card, and the raw URL
string is then ABSENT from the post's text. A substring check for the URL
therefore reads false on a perfectly landed link. The proof is the card text
plus the t.co redirect, and the prose is compared as the span BEFORE the
card.

Usage:
    xreply.py --candidates cand.json --index 3 --copy reply.txt [--repo URL]
    xreply.py --candidates cand.json --index 3 --copy reply.txt --allow-no-repo
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402
import xcandidates                                        # noqa: E402
import xlength                                            # noqa: E402
import xstate                                             # noqa: E402
from xcdp import Browser, sub                             # noqa: E402

# An ordinary browser user agent, so the target answers the way a reader's
# browser gets it and not the way a bot is answered.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 "
      "Safari/537.36")

# Where a t.co's body names the place it points at. The server answers
# either with a 301 and a Location header, or with a 200 whose body
# carries the target in a meta refresh -- so both are read, because the
# proof must not depend on which one the server chose.
TARGET_IN_BODY = re.compile(
    r"(?:URL=|location\.replace\(\s*[\"'])(https?://[^\"'\s>]+)")

# The account whose posts these are.
HANDLE = """(() => {
  const a = document.querySelector("[data-testid='AppTabBar_Profile_Link']");
  if (a) {
    const m = (a.getAttribute('href') || '').match(/^\\/([A-Za-z0-9_]+)/);
    if (m) return m[1];
  }
  return '';
})()"""

# The article carrying the parent status id, with its like button state.
PROBE_ARTICLE = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return JSON.stringify({err: 'no-article', nArts: arts.length});
  const like = art.querySelector("[data-testid='like']");
  const unlike = art.querySelector("[data-testid='unlike']");
  const reply = art.querySelector("[data-testid='reply']");
  return JSON.stringify({
    found: true, nArts: arts.length,
    like: !!like, unlike: !!unlike, hasReply: !!reply,
    likeAria: like ? like.getAttribute('aria-label') : null,
    unlikeAria: unlike ? unlike.getAttribute('aria-label') : null
  });
})()"""

LIKE_CLICK = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return 'NO_ARTICLE';
  const b = art.querySelector("[data-testid='like']");
  if (!b) return 'NO_LIKE_BUTTON';
  b.click();
  return 'CLICKED';
})()"""

REPLY_CLICK = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return 'NO_ARTICLE';
  const b = art.querySelector("[data-testid='reply']");
  if (!b) return 'NO_REPLY_BUTTON';
  b.click();
  return 'CLICKED';
})()"""

# Every editor on the page, ranked, with the routing context of each.
ENUM_EDITORS = """(() => {
  const H = __HANDLE__, P = __PARENT__, S = __SID__;
  const flat = s => (s || '').split(' ').join('').split('\\n').join('').split('\\t').join('');
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const info = eds.map((e, i) => {
    let dlg = false, off = false, p = e;
    while (p && p !== document.body) {
      if (p.getAttribute && p.getAttribute('role') === 'dialog') dlg = true;
      if (p.classList && p.classList.contains('inline_reply_offscreen')) off = true;
      p = p.parentElement;
    }
    return {i: i, dlg: dlg, off: off,
            len: (e.innerText||'').trim().length, tc: (e.textContent||'').trim().length};
  });
  const btns = [...document.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")].map(b => {
    const r = b.getBoundingClientRect();
    return {tid: b.getAttribute('data-testid'), disabled: b.getAttribute('aria-disabled'),
            top: Math.round(r.top), bottom: Math.round(r.bottom)};
  });
  const body = document.body.innerText || '';
  // The parent's text is compared WITHOUT whitespace: the feed collapses a
  // post's line breaks into spaces, while the page keeps them, so a
  // character-for-character comparison of the same post never matches.
  const parentOnPage = flat(body).indexOf(flat(P)) >= 0;
  // The exact check: is the parent post still mounted as an article?
  const arts = [...document.querySelectorAll('article')];
  const parentSel = "a[href*='/status/" + S + "']";
  const parentMounted = arts.some(a => a.querySelector(parentSel));
  return JSON.stringify({nEd: info.length, eds: info, btns: btns,
    vh: window.innerHeight, scrollY: window.scrollY,
    bodyHasTarget: parentOnPage, parentMounted: parentMounted,
    ownLinks: document.querySelectorAll("a[href*='/" + H + "/status/']").length,
    route: location.pathname});
})()"""

# Insert the copy. The editor is ranked first, then the text goes in with one
# insert, then the DOM is compared against the source.
INSERT = """(function() {
  try {
    const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
    const score = e => {
      let dlg = false, off = false, p = e;
      while (p && p !== document.body) {
        if (p.getAttribute && p.getAttribute('role') === 'dialog') dlg = true;
        if (p.classList && p.classList.contains('inline_reply_offscreen')) off = true;
        p = p.parentElement;
      }
      return (dlg ? 3 : 0) + (off ? 2 : 0) + 1;
    };
    let best = null, bs = -1;
    for (const e of eds) { const s = score(e); if (s > bs) { bs = s; best = e; } }
    if (!best) return {err: 'no-editor'};
    // Focus the editor and select its contents, so the insertion REPLACES
    // whatever is there. The copy itself goes in through CDP's
    // Input.insertText, which is a real input event: document.execCommand
    // was measured DOUBLING the copy, and execCommand('delete') to clear
    // the selection first is a banned call.
    best.focus();
    const r = document.createRange();
    r.selectNodeContents(best);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    return {ok: true, score: bs, before: (best.innerText||'').trim().length};
  } catch (e) { return {caught: String(e && e.message ? e.message : e)}; }
})()"""

# READ-ONLY re-read. No focus, no insert, no delete: a read that changes
# what it reads is not a read.
REREAD = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const best = eds.map(e => ({e: e, len: (e.innerText||'').trim().length})).sort((a,b)=>b.len-a.len)[0];
  if (!best) return {err:'no-editor'};
  const txt = (best.e.innerText||'').replace(/\\s+$/,'');
  const flat = txt.split(' ').join('').split('\\n').join('').split('\\t').join('');
  const want = __COPY__.split(' ').join('').split('\\n').join('').split('\\t').join('');
  return {domLen: txt.length, domMatch: flat === want, head: txt.slice(0,40)};
})()"""

# The paragraph structure of the editor, read from the DOM.
#
# The Draft block MODEL is not read: walking the React fiber to reach the
# editor state finds a DIFFERENT editor's state (an empty one), which
# reports one block for a two-paragraph body and refuses a body that is
# correct. The DOM's paragraph count is what the post will actually carry,
# and it is directly observable.
#
# A one-block insertion can read back correctly and still lose the
# paragraph structure on publication, so the count is checked before the
# send: the editor renders a paragraph break as MORE newlines than the
# source has, so the count is of the SEPARATORS, not of the newlines.
BLOCKS = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const best = eds.map(e => ({e: e, len: (e.innerText||'').trim().length})).sort((a,b)=>b.len-a.len)[0];
  if (!best) return {err: 'no-editor'};
  const txt = (best.e.innerText||'').replace(/\\s+$/,'');
  const want = __COPY__;
  return {nParas: txt.split('\\n\\n').length,
          wantParas: want.split('\\n\\n').length,
          hasSeparator: txt.indexOf('\\n\\n') >= 0,
          domLen: txt.length};
})()"""

BTN_STATE = """(() => {
  const btns = [...document.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")];
  return JSON.stringify(btns.map(b => {
    const r = b.getBoundingClientRect();
    return {tid: b.getAttribute('data-testid'), disabled: b.getAttribute('aria-disabled'),
            top: Math.round(r.top), bottom: Math.round(r.bottom), vh: window.innerHeight};
  }));
})()"""

# The send button, taken from the SAME DIALOG as the editor the copy went
# into.
#
# "The first enabled button on the page" is not the reply button. The reply
# control navigates on some routes, and the page then holds BOTH the main
# composer and the reply dialog -- and the main composer's button is the
# enabled one in view. Clicking it publishes a STANDALONE POST where a reply
# was meant, which is the worst outcome this skill has.
#
# So the button is found by walking up from the editor to its dialog and
# taking the button inside THAT dialog. When the editor has no dialog
# ancestor, the button is looked for among the enabled ones and the caller
# is told the composer was not a dialog.
BTN_IN_DIALOG = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const score = e => {
    let dlg = false, off = false, p = e;
    while (p && p !== document.body) {
      if (p.getAttribute && p.getAttribute('role') === 'dialog') dlg = true;
      if (p.classList && p.classList.contains('inline_reply_offscreen')) off = true;
      p = p.parentElement;
    }
    return (dlg ? 3 : 0) + (off ? 2 : 0) + 1;
  };
  let best = null, bs = -1;
  for (const e of eds) { const s = score(e); if (s > bs) { bs = s; best = e; } }
  if (!best) return JSON.stringify({err: 'no-editor'});
  let dlgEl = null, p = best;
  while (p && p !== document.body) {
    if (p.getAttribute && p.getAttribute('role') === 'dialog') { dlgEl = p; break; }
    p = p.parentElement;
  }
  const scope = dlgEl || document;
  const all = [...scope.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")];
  const enabled = all.filter(b => b.getAttribute('aria-disabled') !== 'true');
  const desc = b => { const r = b.getBoundingClientRect();
    return {tid: b.getAttribute('data-testid'), disabled: b.getAttribute('aria-disabled'),
            top: Math.round(r.top), bottom: Math.round(r.bottom), vh: window.innerHeight}; };
  return JSON.stringify({inDialog: !!dlgEl, score: bs,
    nScoped: all.length, nEnabled: enabled.length,
    all: all.map(desc), enabled: enabled.map(desc),
    route: location.pathname});
})()"""

# Scroll the button into view, INSIDE ITS OWN DIALOG's scroller.
SCROLL_BTN = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const score = e => {
    let dlg = false, off = false, p = e;
    while (p && p !== document.body) {
      if (p.getAttribute && p.getAttribute('role') === 'dialog') dlg = true;
      if (p.classList && p.classList.contains('inline_reply_offscreen')) off = true;
      p = p.parentElement;
    }
    return (dlg ? 3 : 0) + (off ? 2 : 0) + 1;
  };
  let best = null, bs = -1;
  for (const e of eds) { const s = score(e); if (s > bs) { bs = s; best = e; } }
  if (!best) return JSON.stringify({err: 'no-editor'});
  let dlgEl = null, p = best;
  while (p && p !== document.body) {
    if (p.getAttribute && p.getAttribute('role') === 'dialog') { dlgEl = p; break; }
    p = p.parentElement;
  }
  const scope = dlgEl || document;
  const enabled = [...scope.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")]
    .filter(b => b.getAttribute('aria-disabled') !== 'true');
  if (!enabled.length) return JSON.stringify({err: 'no-enabled-button', inDialog: !!dlgEl});
  const b = enabled[0];
  let r = b.getBoundingClientRect();
  const vh = window.innerHeight;
  let scroller = null, q = b.parentElement;
  while (q && q !== document.body) {
    const st = getComputedStyle(q);
    if ((st.overflowY === 'auto' || st.overflowY === 'scroll') && q.scrollHeight > q.clientHeight + 20) { scroller = q; break; }
    q = q.parentElement;
  }
  if (scroller) scroller.scrollTop += (r.top - 0.6 * vh);
  else window.scrollBy(0, r.top - 0.5 * vh);
  r = b.getBoundingClientRect();
  return JSON.stringify({tid: b.getAttribute('data-testid'), hasScroller: !!scroller,
    inDialog: !!dlgEl, top: Math.round(r.top), bottom: Math.round(r.bottom), vh: vh,
    ok: r.top > 40 && r.bottom < vh - 40});
})()"""

# The click, on the same dialog's button.
CLICK_BTN = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const score = e => {
    let dlg = false, off = false, p = e;
    while (p && p !== document.body) {
      if (p.getAttribute && p.getAttribute('role') === 'dialog') dlg = true;
      if (p.classList && p.classList.contains('inline_reply_offscreen')) off = true;
      p = p.parentElement;
    }
    return (dlg ? 3 : 0) + (off ? 2 : 0) + 1;
  };
  let best = null, bs = -1;
  for (const e of eds) { const s = score(e); if (s > bs) { bs = s; best = e; } }
  if (!best) return 'NO_EDITOR';
  let dlgEl = null, p = best;
  while (p && p !== document.body) {
    if (p.getAttribute && p.getAttribute('role') === 'dialog') { dlgEl = p; break; }
    p = p.parentElement;
  }
  const scope = dlgEl || document;
  const enabled = [...scope.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")]
    .filter(b => b.getAttribute('aria-disabled') !== 'true');
  if (!enabled.length) return 'NO_ENABLED_BUTTON';
  enabled[0].click();
  return 'CLICKED ' + enabled[0].getAttribute('data-testid') + (dlgEl ? ' (in dialog)' : ' (NO DIALOG)');
})()"""

# After the click: the account's own status links on the page. The reply's
# own id is among them.
POST_SEND = """(() => {
  const H = __HANDLE__;
  const own = [...document.querySelectorAll("a[href*='/" + H + "/status/']")]
    .map(a => a.getAttribute('href'));
  const arts = [...document.querySelectorAll('article')];
  return JSON.stringify({route: location.pathname, own: own.slice(0,6), nArts: arts.length});
})()"""

# The landed reply, read on its OWN permalink.
#
# The whole ARTICLE's innerText is NOT the reply: it carries the author
# block, the link card and the engagement chrome, none of which are in the
# source copy. The reply's own text element is read instead.
#
# The owning article is found by the article whose OWN TIME LINK points at
# this id. Matching on any status link picks up a quoted post or a reply,
# and that is how a previous run reported a stranger's links for a post of
# its own.
OWN_READ = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const walk = (n) => {
    let s = '';
    for (const k of n.childNodes) {
      if (k.nodeType === 3) s += k.textContent;
      else if (k.nodeName === 'BR') s += '\\n';
      else s += walk(k);
    }
    return s;
  };
  for (const a of arts) {
    const own = [...a.querySelectorAll("a[href*='/status/']")].find(x => {
      const h = x.getAttribute('href') || '';
      return /\\/status\\//.test(h) && !/\\/(analytics|photo|video|retweets|likes)/.test(h)
             && h.split('/').pop() === __SID__;
    });
    if (!own) continue;
    const box = a.querySelector('[data-testid="tweetText"]');
    const body = box ? walk(box) : (a.innerText || '');
    const card = a.querySelector('[data-testid="card.wrapper"]');
    const tco = [...a.querySelectorAll("a[href*='t.co']")].map(x => x.getAttribute('href'));
    return JSON.stringify({nMine: 1, len: body.length, text: body,
      cardText: card ? (card.innerText || '') : '',
      hasCard: !!card, tco: tco});
  }
  return JSON.stringify({err: 'no-mine', nArts: arts.length});
})()"""

# How many of the account's own ARTICLES carry this reply id. Count
# articles, never hrefs: one article renders the same status href twice,
# and a href count reads two copies where there is one.
DUP_COUNT = """(() => {
  const H = __HANDLE__, R = __RID__;
  const arts = [...document.querySelectorAll('article')];
  let nMineArts = 0;
  for (const a of arts) {
    const hit = [...a.querySelectorAll("a[href*='/" + H + "/status/']")]
      .filter(h => (h.getAttribute('href')||'').indexOf('/' + H + '/status/' + R) >= 0);
    if (hit.length) nMineArts++;
  }
  return JSON.stringify({nArts: arts.length, nMineArts: nMineArts});
})()"""

# Both ids on one page: our own permalink renders the parent FIRST and then
# the reply, so both are visible at once.
THREAD_PROOF = """(() => {
  const H = __HANDLE__, R = __RID__, W = __WHO__, P = __PSID__;
  const arts = [...document.querySelectorAll('article')];
  let nTarget = 0, nMine = 0;
  for (const a of arts) {
    const hrefs = [...a.querySelectorAll("a[href*='/status/']")].map(x => x.getAttribute('href') || '');
    if (hrefs.some(h => h.indexOf('/' + W + '/status/' + P) >= 0)) nTarget++;
    if (hrefs.some(h => h.indexOf('/' + H + '/status/' + R) >= 0)) nMine++;
  }
  return JSON.stringify({nArts: arts.length, nTarget: nTarget, nMine: nMine});
})()"""


# --------------------------------------------------------------------------
# copy gates
# --------------------------------------------------------------------------

def canon(text: str) -> str:
    """Text reduced to the part that must match exactly.

    Three normalisations, all learned from a false result.

    1. URL SPANS ARE REMOVED, NOT REPLACED BY A PLACEHOLDER. A placeholder
       only balances when BOTH sides still contain a URL span, and a
       trailing address does not stay in the tweet text: X promotes it to a
       card, and the permalink then shows the prose with NO URL in it at
       all. The source copy keeps one span, the landed text has none, so a
       placeholder made the two differ by exactly one character and a
       perfectly landed reply read as a mismatch. The address is proved by
       the card and the t.co redirect (see compare_prose), never by a
       substring, so removing the span on both sides is what matches.

    2. The span is matched WITHOUT a greedy prefix. The old pattern
       started with ``\\S*``, which swallowed the token in front of the URL
       ("。https://t.co/x" lost the "。" too). The URL alone is removed; the
       whitespace around it goes with the whitespace rule.

    3. The renderer reflows the body, putting a line break between tokens
       that were space-separated in the source, so all whitespace goes.
       What is left is the non-space characters, which are the part that
       must match exactly.
    """
    text = re.sub(r"(?:https?://\S+|t\.co/\S+)", "", text or "")
    return "".join(text.split())


def flatten(text: str) -> str:
    """Text with every space removed, for comparing what was typed.

    A raw character comparison of the editor against the source is wrong:
    the Draft editor renders a paragraph break as MORE newlines than the
    source has, and X removes a space at a Latin/CJK boundary while
    typing. A copy that is character-for-character correct reads as one
    character off, which is the same false negative as a mangled post.
    What must match exactly is every NON-SPACE character -- a dropped or
    mangled character cannot hide behind a space.
    """
    return "".join((text or "").split())


def gate_copy(copy: str, repo: str | None) -> list:
    """Reasons the copy may not be sent. Empty list means it may.

    X linkifies any dotted token, not just one it recognises as a URL, and
    the span it replaces then reads back as a line break -- a bare
    "crates.io" in the body split a sentence in two and shipped twice
    before it was refused. So the check is on the COPY, before a character
    is typed.

    THE CHECK IS ON A LETTER-SUFFIXED TOKEN, AND NOTHING ELSE. A version
    number is not a linkifier: "8.2.35" and "7.4" end in digits, X does
    not linkify them, and a reply about a release is mostly version
    numbers. A rule that refused decimals would refuse the reply that is
    most worth sending -- and one did, and it was measured against a
    reply that carried "8.5.12 / 8.4.27 / 8.3.36 / 8.2.35" and was
    verified as landed.
    """
    problems = []
    if not (10 <= len(copy) <= 2000):
        problems.append("length %d outside 10-2000" % len(copy))
    weight = xlength.weighted_length(copy)
    if weight > xlength.MAX_WEIGHTED:
        problems.append(
            "weighted length %d over X's %d (CJK counts double, an address "
            "counts 23) -- shorten the copy"
            % (weight, xlength.MAX_WEIGHTED))
    dotted = [w for w in re.findall(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}", copy)
              if not w.startswith("github")]
    if dotted:
        problems.append("dotted tokens: %s" % dotted)
    if copy.count("�"):
        problems.append("replacement character in the copy")
    urls = re.findall(r"https?://\S+", copy)
    if repo:
        if urls != [repo]:
            problems.append("expected exactly the project address %s, got %s"
                            % (repo, urls))
        elif not copy.rstrip().endswith(repo):
            problems.append("the address must end the copy")
        elif (" " + repo) not in copy:
            problems.append("the address must be preceded by exactly one space")
    else:
        if urls:
            problems.append("a no-repository reply must carry no address, got %s"
                            % urls)
    return problems


# --------------------------------------------------------------------------
# landed-text comparison
# --------------------------------------------------------------------------

CHROME_LINES = {"·", "查看", "回复", "转发", "喜欢", "分享", "书签", "广告", "显示更多"}


def strip_chrome(raw: str) -> str:
    """The post's own prose, without the author block and the engagement chrome.

    The author block is stripped BY LINE: the handle is sometimes on its own
    line and sometimes on the same line as the display name, and a
    space-joined prefix strip removes nothing in the first case. The handle
    comes from the live account, never from a constant, so the script
    carries no account in it.
    """
    body = []
    own = xconfig.handle()
    for raw_line in raw.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if own and line in (own, "@" + own):
            continue
        if re.fullmatch(r"[·\s]*\d{1,2}:\d{2}", line):
            continue
        if re.match(r"^[·\s]*\d{1,2}月\d{1,2}日", line):
            continue
        if re.search(r"\d{1,2}:\d{2}\s*·\s*\d{4}年\d{1,2}月\d{1,2}日", line):
            continue
        body.append(line)
    while body and (body[-1] in CHROME_LINES or body[-1].isdigit()):
        body.pop()
    return "\n".join(body)


def link_ready(d: dict) -> bool:
    """Whether the landing read carries the address's evidence.

    The card wrapper and the t.co anchor are the two pieces that prove the
    address survived publication, and they arrive TOGETHER and AFTER the
    post's own text: the article mounts first, and the card hydrates a beat
    later. A read that stops on the text alone is therefore reading a
    half-hydrated post, and it reports a perfectly landed link as a lost
    one.

    So the read keeps polling until this is true, and only then does it
    judge the address.
    """
    return bool(d.get("hasCard")) and bool(d.get("tco") or [])


def resolve_target(url: str, timeout: float = 15.0) -> str:
    """The place a short link points at, or "" when it cannot be read.

    The answer is a 301 with a Location header, or a 200 whose body
    carries the target in a meta refresh. BOTH are read, because the
    proof of an address must not depend on which one the server chose.

    Nothing here touches the user's browser or the account: it is a
    plain request for a link that is already public.
    """
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            found = TARGET_IN_BODY.search(body)
            return found.group(1).replace("\\/", "/") if found else ""
    except urllib.error.HTTPError as exc:
        headers = exc.headers
        loc = headers.get("Location") if headers else None
        return loc or ""
    except Exception:
        return ""


def address_key(url: str) -> str:
    """An address reduced to the part that must match exactly.

    The scheme, the query and the fragment are dropped, and the trailing
    slash goes with them: X rewrites the address it shows, and a reader's
    browser may follow a redirect that adds a slash. What is left is the
    host and the path, which is what names the place.
    """
    text = (url or "").strip()
    text = re.sub(r"^https?://", "", text, flags=re.I)
    text = text.split("#", 1)[0].split("?", 1)[0]
    return text.rstrip("/").lower()


def address_points_at(tco: list, repo: str, resolver=None) -> tuple:
    """Where the landed link points, against the address that was sent.

    Returns (ok, detail). ``ok`` is None when the redirect could not be
    read at all -- an unreadable redirect is not evidence either way, and
    the caller decides what to do with an unknown.

    The card's TITLE is not the address: it carries the target page's own
    title, so it names the repository only for a bare repository address.
    A pull request address ends in its NUMBER, and no title contains a
    number. So the redirect is what names the place.
    """
    resolve = resolver or resolve_target
    want = address_key(repo)
    for short in (tco or []):
        target = resolve(short)
        if not target:
            continue
        got = address_key(target)
        print("RESOLVED:", got)
        if got == want or got.startswith(want + "/"):
            return True, "the link resolves to %s" % got
        return False, "the link resolves to %s, not %s" % (got, want)
    return None, "the redirect could not be read"


def compare_prose(landed: str, source: str, repo: str | None):
    """Compare the landed prose with the copy that was sent.

    Returns (ok, detail). A trailing address lands as a card, so the raw URL
    is absent from the landed text and the comparison is made on the span
    before the card.

    The comparison is WITHOUT whitespace, for the same reason the editor
    comparison is: X removes a space at a Latin/CJK boundary while typing
    and the card adds chrome lines of its own. Every non-space character
    must match exactly -- a dropped character cannot hide behind a space.
    """
    prose = strip_chrome(landed)
    if repo:
        # The URL span is removed from BOTH sides: X rewrites the address
        # as a t.co, so looking for the address in the text reads false on
        # a landed link. The address is proved by the card.
        ok = canon(prose) == canon(source)
        return ok, {"compared": "prose, address removed from both sides",
                    "landed_len": len(canon(prose)),
                    "expected_len": len(canon(source)),
                    "card_present": "GitHub - " in landed}
    ok = canon(prose) == canon(source)
    return ok, {"compared": "whole text", "landed_len": len(canon(prose)),
                "expected_len": len(canon(source))}


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------

async def run(index: int, sid: str, who: str, copy: str, repo: str | None,
              parent_hint: str, dry_run: bool = False) -> int:
    handle = xconfig.handle() or who
    url = "https://%s/%s/status/%s" % (xconfig.site(), who, sid)
    async with Browser() as b:
        tid, sess = await b.new_tab(url)
        try:
            await b.wait_for(sess, "document.querySelectorAll('article').length > 0",
                             timeout=45)
            live = await b.ev(sess, HANDLE)
            if isinstance(live, str) and live:
                handle = live
                xconfig.cache_handle(live)
            print("ACCOUNT:", handle)

            # ---- 1. the like, first and idempotently
            pre = await b.ev(sess, sub(PROBE_ARTICLE, SID=sid))
            if not isinstance(pre, str):
                print("REJECTED: probe failed: %s" % str(pre)[:200])
                return 3
            pd = json.loads(pre)
            if pd.get("err"):
                print("REJECTED: target not on page (%s)" % pd.get("err"))
                return 3
            if pd.get("unlike"):
                print("LIKE: ALREADY_LIKED")
            else:
                clicked = await b.ev(sess, sub(LIKE_CLICK, SID=sid))
                await asyncio.sleep(3.0)
                post = await b.ev(sess, sub(PROBE_ARTICLE, SID=sid))
                pdd = json.loads(post) if isinstance(post, str) else {}
                if pdd.get("unlike"):
                    print("LIKE: LIKED")
                else:
                    print("REJECTED: like did not confirm (%s)" % clicked)
                    return 4

            # ---- 2. the composer
            rc = await b.ev(sess, sub(REPLY_CLICK, SID=sid))
            print("reply click:", rc)
            await asyncio.sleep(6.0)
            en = await b.ev(sess, sub(ENUM_EDITORS, HANDLE=handle,
                                       PARENT=parent_hint, SID=sid))
            if not isinstance(en, str):
                print("REJECTED: editor enumeration failed: %s" % str(en)[:200])
                return 5
            ed = json.loads(en)
            print("EDITORS:", json.dumps(ed, ensure_ascii=False)[:600])
            if ed.get("nEd", 0) == 0:
                print("REJECTED: no editor mounted")
                return 5
            filled = [e for e in ed.get("eds", []) if e.get("len", 0) > 1]
            if filled:
                print("REJECTED: the composer already holds text (%s) -- "
                      "not ours to touch" % filled)
                return 6
            if ed.get("ownLinks", 0) > 0:
                print("REJECTED: the account's own links are already present")
                return 7
            # The composer must be bound to the PARENT. The reply control
            # navigates on some routes and mounts the MAIN composer, where
            # typing publishes a standalone post where a reply was meant --
            # and the parent post still being mounted is what tells the two
            # apart.
            if not (ed.get("parentMounted") or ed.get("bodyHasTarget")):
                print("REJECTED: the parent post is not mounted, so the "
                      "composer is not bound to it (route=%s)" % ed.get("route"))
                return 7

            # ---- 3. the copy
            ins = await b.ev(sess, INSERT)
            print("INSERT:", json.dumps(ins, ensure_ascii=False)[:300])
            if not isinstance(ins, dict) or not ins.get("ok"):
                print("REJECTED: the editor could not be focused for the copy")
                return 8
            # The copy goes in through CDP's Input.insertText: a real input
            # event, which is what the editor's own input path expects.
            await b.call("Input.insertText", {"text": copy}, session_id=sess)
            await asyncio.sleep(2.5)
            rr = await b.ev(sess, sub(REREAD, COPY=copy))
            print("REREAD:", json.dumps(rr, ensure_ascii=False)[:200])
            if not isinstance(rr, dict) or rr.get("domMatch") is not True:
                print("REJECTED: the copy did not survive the re-read")
                return 8

            blocks = await b.ev(sess, sub(BLOCKS, COPY=copy))
            if isinstance(blocks, dict) and blocks.get("nParas") is not None:
                print("PARAGRAPHS: editor=%s source=%s" % (
                    blocks.get("nParas"), blocks.get("wantParas")))
                if blocks.get("nParas") != blocks.get("wantParas"):
                    print("REJECTED: the editor holds %s paragraphs for %s in "
                          "the source -- the paragraph structure would be lost"
                          % (blocks.get("nParas"), blocks.get("wantParas")))
                    return 9
            else:
                print("PARAGRAPHS: unreadable (%s) -- the paragraph count "
                      "could not be checked" % blocks)

            # ---- 4. the send
            scope = await b.ev(sess, BTN_IN_DIALOG)
            if isinstance(scope, str):
                try:
                    scope = json.loads(scope)
                except ValueError:
                    scope = {}
            if not isinstance(scope, dict):
                scope = {}
            print("BUTTON SCOPE:", json.dumps(scope, ensure_ascii=False)[:400])
            if not scope.get("inDialog"):
                print("REJECTED: the composer is not inside a dialog, so the "
                      "send button cannot be told apart from the main "
                      "composer's -- refusing rather than risking a "
                      "standalone post")
                return 10
            if not scope.get("nEnabled"):
                print("REJECTED: no enabled button inside the reply dialog")
                return 10
            print("SCROLL:", await b.ev(sess, SCROLL_BTN))
            if dry_run:
                print("DRY RUN: the composer holds the copy, the like is "
                      "confirmed and the send button is the reply dialog's; "
                      "nothing was sent")
                return 0
            await asyncio.sleep(1.0)
            clicked = await b.ev(sess, CLICK_BTN)
            print("SEND CLICK:", clicked)
            if not str(clicked).startswith("CLICKED"):
                print("REJECTED: no enabled send button")
                return 10
            await asyncio.sleep(9.0)
            ps = await b.ev(sess, sub(POST_SEND, HANDLE=handle))
            own = json.loads(ps).get("own", []) if isinstance(ps, str) else []
            rid = None
            for href in own:
                if "/%s/status/" % handle in href and "analytics" not in href:
                    rid = href.rstrip("/").split("/")[-1]
            print("REPLY_ID: %s" % ("(found)" if rid else "(none)"))
            if not rid:
                print("REJECTED: no own status link appeared after the click")
                return 11
        finally:
            await b.close_tab(tid)

        # ---- 5. the landed post, on its own permalink
        tid2, s2 = await b.new_tab("https://%s/%s/status/%s"
                                    % (xconfig.site(), handle, rid))
        try:
            raw = None
            for _ in range(14):
                await asyncio.sleep(3.0)
                raw = await b.ev(s2, sub(OWN_READ, SID=rid))
                try:
                    d = json.loads(raw) if isinstance(raw, str) else {}
                except ValueError:
                    d = {}
                # The post's own text mounts BEFORE its link card. Stopping
                # on the text alone reads a half-hydrated post and calls a
                # landed link a lost one, so a reply that is up with its
                # card is reported as a rejection. When the copy carries
                # an address, the read waits for the card and the t.co.
                if d.get("nMine") and (not repo or link_ready(d)):
                    break
            if not isinstance(raw, str):
                print("REJECTED: the permalink read failed: %s" % str(raw)[:200])
                return 12
            d = json.loads(raw)
            if not d.get("nMine"):
                print("REJECTED: the reply did not mount on its own permalink; "
                      "last raw: %s" % str(raw)[:300])
                return 12
            # The reply is UP from here on: its own permalink rendered it.
            # The parent is answered whatever the address proof says, so a
            # later run skips it instead of replying to it a second time.
            stamp = time.strftime("%Y%m%d_%H%M%S")
            total = xstate.mark_answered(sid, backup_suffix=".bak_%s" % stamp)
            print("STATE: %d answered (the reply's own id is NOT recorded)" % total)
            landed = d.get("text", "")
            ok, detail = compare_prose(landed, copy, repo)
            print("PROSE:", json.dumps(detail, ensure_ascii=False))
            print("PROSE MATCH:", ok)
            if not ok:
                print("LANDED TEXT>>>")
                print(landed[:1500])
                print("REJECTED: the landed text is not the copy that was sent")
                return 13
            tco = d.get("tco") or []
            print("TCO:", tco)
            if repo:
                if not tco:
                    print("REJECTED: the link landed as no card and no t.co")
                    return 14
                if not d.get("hasCard"):
                    print("REJECTED: the link landed without a card")
                    return 14
                # The redirect names the place. The card's TITLE does not:
                # it carries the target page's own title, so it names the
                # repository only for a bare repository address.
                points, why = address_points_at(tco, repo)
                print("ADDRESS:", why)
                if points is False:
                    print("REJECTED: the link does not point at the address that was sent")
                    return 14
        finally:
            await b.close_tab(tid2)

        # ---- 6. one copy, and the thread it hangs from
        tid3, s3 = await b.new_tab("https://%s/%s/with_replies"
                                    % (xconfig.site(), handle))
        try:
            dup = None
            for _ in range(10):
                await asyncio.sleep(3.0)
                dup = await b.ev(s3, sub(DUP_COUNT, HANDLE=handle, RID=rid))
                try:
                    dd = json.loads(dup) if isinstance(dup, str) else {}
                except ValueError:
                    dd = {}
                if dd.get("nArts", 0) > 0:
                    break
            print("DUPLICATE ARTICLES:", dup)
        finally:
            await b.close_tab(tid3)

        tid4, s4 = await b.new_tab("https://%s/%s/status/%s"
                                    % (xconfig.site(), handle, rid))
        try:
            await asyncio.sleep(9.0)
            thread = await b.ev(s4, sub(THREAD_PROOF, WHO=who, PSID=sid,
                                        HANDLE=handle, RID=rid))
            print("THREAD:", thread)
        finally:
            await b.close_tab(tid4)

        # ---- 7. the state was already written when the reply was seen up
        # The receipt is the permalink, which the operator can open. The bare
        # id is not printed: it is redacted by the display layer, so a
        # transcript holding one is holding a token rather than an id.
        print("VERIFIED reply by @%s (candidate %d)" % (handle, index))
        print("URL: https://%s/%s/status/%s" % (xconfig.site(), handle, rid))
        return 0


def main(argv) -> int:
    path = None
    index = None
    copy_path = None
    repo = None
    dry_run = False
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--candidates":
            path = args[i + 1]; i += 2
        elif args[i] == "--index":
            index = int(args[i + 1]); i += 2
        elif args[i] == "--copy":
            copy_path = args[i + 1]; i += 2
        elif args[i] == "--repo":
            repo = args[i + 1]; i += 2
        elif args[i] == "--allow-no-repo":
            repo = None; i += 1
        elif args[i] == "--dry-run":
            dry_run = True; i += 1
        else:
            print("unknown argument: %s" % args[i])
            return 2
    if not (path and index is not None and copy_path):
        print(__doc__)
        return 2
    row = xcandidates.resolve(path, index)
    copy = Path(copy_path).read_text(encoding="utf-8").strip()
    if not copy:
        print("the copy file is empty")
        return 2
    problems = gate_copy(copy, repo)
    if problems:
        for p in problems:
            print("COPY GATE: %s" % p)
        return 2
    print("COPY: %d chars" % len(copy))
    # The binding hint is the PARENT's text, taken from the candidate. It is
    # what proves the composer opened on the parent and not on the account's
    # main composer.
    parent_hint = str(row.get("text", "")).strip()[:24]
    with xstate.Lock():
        return asyncio.run(run(index, row["sid"], row["who"], copy, repo,
                               parent_hint, dry_run=dry_run))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
