#!/usr/bin/env python3
"""Publish one standalone post, and prove the address is on it.

THE LANDED POST IS THE ONLY PROOF

A click on the send button is a button press. On two separate nights a post
went out having passed every composer-side gate -- the text matched the
source, the URL was present -- and carried NO address at all, because the
loss happened after the click. A version that does not verify is not
counted, and a version that fails is not replaced: three more damaged public
posts is worse than one.

So this script reads the landed post back, on its own permalink, and prints
one verdict:

    LINK OK                       the post is up and its card names the repo
    LINK PRESENT BUT NOT PROVEN   the post is up with a rewritten link and no
                                  card naming the repo -- a FAILURE
    LINK LOST                     the post is PUBLIC WITHOUT ITS ADDRESS
    NO POST ON PAGE               nothing was established

A TRAILING ADDRESS LANDS AS A CARD

When the last token is a URL, X promotes it to a link card and the raw URL
string is then ABSENT from the post's text. A substring check for the URL
reads false on a perfectly landed link, so the proof is the card text plus
the t.co redirect, and the prose is compared as the span before the card.

Usage:
    xpost.py --copy post.txt --repo https://github.com/owner/repo
    xpost.py --copy post.txt --repo https://github.com/owner/repo --dry-run
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402
import xstate                                             # noqa: E402
from xcdp import Browser, sub                             # noqa: E402

# The composer on the page, with its context.
ENUM_EDITORS = """(() => {
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
  return JSON.stringify({nEd: info.length, eds: info, btns: btns,
    vh: window.innerHeight, route: location.pathname});
})()"""

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

REREAD = """(() => {
  const eds = [...document.querySelectorAll("div[data-testid='tweetTextarea_0'], div[contenteditable='true']")];
  const best = eds.map(e => ({e: e, len: (e.innerText||'').trim().length})).sort((a,b)=>b.len-a.len)[0];
  if (!best) return {err:'no-editor'};
  const txt = (best.e.innerText||'').replace(/\\s+$/,'');
  const flat = txt.split(' ').join('').split('\\n').join('').split('\\t').join('');
  const want = __COPY__.split(' ').join('').split('\\n').join('').split('\\t').join('');
  return {domLen: txt.length, domMatch: flat === want, head: txt.slice(0,40),
          hasUrl: txt.indexOf(__REPO__) >= 0};
})()"""

BTN_STATE = """(() => {
  const btns = [...document.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")];
  return JSON.stringify(btns.map(b => {
    const r = b.getBoundingClientRect();
    return {tid: b.getAttribute('data-testid'), disabled: b.getAttribute('aria-disabled'),
            top: Math.round(r.top), bottom: Math.round(r.bottom), vh: window.innerHeight};
  }));
})()"""

SCROLL_BTN = """(() => {
  const btns = [...document.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")]
    .filter(b => b.getAttribute('aria-disabled') !== 'true');
  if (!btns.length) return JSON.stringify({err:'no-enabled-button'});
  const b = btns[0];
  let r = b.getBoundingClientRect();
  const vh = window.innerHeight;
  let scroller = null, p = b.parentElement;
  while (p && p !== document.body) {
    const st = getComputedStyle(p);
    if ((st.overflowY === 'auto' || st.overflowY === 'scroll') && p.scrollHeight > p.clientHeight + 20) { scroller = p; break; }
    p = p.parentElement;
  }
  if (scroller) scroller.scrollTop += (r.top - 0.6 * vh);
  else window.scrollBy(0, r.top - 0.5 * vh);
  r = b.getBoundingClientRect();
  return JSON.stringify({tid: b.getAttribute('data-testid'), hasScroller: !!scroller,
    top: Math.round(r.top), bottom: Math.round(r.bottom), vh: vh,
    ok: r.top > 40 && r.bottom < vh - 40});
})()"""

CLICK_BTN = """(() => {
  const btns = [...document.querySelectorAll("[data-testid='tweetButton'],[data-testid='tweetButtonInline']")]
    .filter(b => b.getAttribute('aria-disabled') !== 'true');
  if (!btns.length) return 'NO_ENABLED_BUTTON';
  btns[0].click();
  return 'CLICKED ' + btns[0].getAttribute('data-testid');
})()"""

# The account's own status links after the click.
POST_SEND = """(() => {
  const H = __HANDLE__;
  const own = [...document.querySelectorAll("a[href*='/" + H + "/status/']")]
    .map(a => a.getAttribute('href'));
  return JSON.stringify({route: location.pathname, own: own.slice(0,6),
    toast: (document.body.innerText||'').indexOf('你的帖子已发送') >= 0});
})()"""

# The landed post, read on its OWN permalink.
#
# The whole ARTICLE's innerText is NOT the post: it carries the link card,
# the "来自 github.com" line and the engagement chrome, none of which are in
# the source copy -- so comparing the article against the source reads false
# on a perfectly landed post. The post's own text element is read instead,
# and the card is read separately.
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
    const ext = [...a.querySelectorAll('a[href^="http"]')].map(x => x.href)
      .filter(h => !/x\\.com|twitter\\.com/.test(h));
    return JSON.stringify({nMine: 1, len: body.length, text: body,
      cardText: card ? (card.innerText || '') : '',
      hasCard: !!card, tco: tco, ext: ext});
  }
  return JSON.stringify({err: 'no-mine', nArts: arts.length});
})()"""


def canon(text: str) -> str:
    """Text reduced to the part that must match exactly.

    Two normalisations, both learned from a false result. X rewrites the
    URL as a t.co shortener, so the URL span is REMOVED from both sides
    rather than looked for -- the address is proved by the card, not by a
    substring. And the renderer reflows the body, putting a line break
    between tokens that were space-separated in the source, so all
    whitespace goes. What is left is the non-space characters, which is the
    part that must match exactly.
    """
    text = re.sub(r"\S*(?:https?://\S+|t\.co/\S+)", "\x00", text or "")
    return "".join(text.split())


def strip_chrome(raw: str) -> str:
    """The post's own prose, without the author block and the engagement chrome.

    The handle comes from the live account, never from a constant, so the
    script carries no account in it.
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
    chrome = {"·", "查看", "回复", "转发", "喜欢", "分享", "书签", "广告", "显示更多"}
    while body and (body[-1] in chrome or body[-1].isdigit()):
        body.pop()
    return "\n".join(body)


def gate_copy(copy: str, repo: str) -> list:
    """Reasons the post may not be published. Empty list means it may.

    X linkifies any dotted token, not just one it recognises as a URL, and
    the span it replaces then reads back as a line break -- a bare
    "crates.io" in the body split a sentence in two and shipped twice
    before it was refused. So the check is on the COPY, before a character
    is typed.

    The check is on a LETTER-SUFFIXED TOKEN, and nothing else. A version
    number ends in digits, X does not linkify it, and a post about a
    release is mostly version numbers.
    """
    problems = []
    if not repo:
        return ["no repository address given"]
    if not (10 <= len(copy) <= 3000):
        problems.append("length %d outside 10-3000" % len(copy))
    if copy.count(repo) != 1:
        problems.append("the address must appear exactly once, found %d"
                        % copy.count(repo))
    elif not copy.rstrip().endswith(repo):
        problems.append("the address must END the post")
    elif (" " + repo) not in copy:
        problems.append("the address must be preceded by exactly one space")
    elif any(ln.strip() == repo for ln in copy.rstrip().split("\n")):
        problems.append("the address must not be alone on its own line")
    dotted = [w for w in re.findall(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}", copy)
              if not w.startswith("github")]
    if dotted:
        problems.append("dotted tokens: %s" % dotted)
    if copy.count("�"):
        problems.append("replacement character in the copy")
    return problems


async def run(copy: str, repo: str, dry_run: bool) -> int:
    handle = xconfig.handle()
    if not handle:
        print("REJECTED: the account handle is unknown")
        return 1
    async with Browser() as b:
        tid, sess = await b.new_tab("https://%s/compose/post" % xconfig.site())
        try:
            await b.wait_for(
                sess,
                "document.querySelectorAll(\"div[data-testid='tweetTextarea_0'], div[contenteditable='true']\").length > 0",
                timeout=45)
            en = await b.ev(sess, ENUM_EDITORS)
            if not isinstance(en, str):
                print("REJECTED: the composer enumeration failed: %s"
                      % str(en)[:200])
                return 2
            ed = json.loads(en)
            print("COMPOSER:", json.dumps(ed, ensure_ascii=False)[:500])
            if ed.get("nEd", 0) == 0:
                print("REJECTED: no composer mounted")
                return 2
            filled = [e for e in ed.get("eds", []) if e.get("len", 0) > 1]
            if filled:
                print("REJECTED: the composer already holds text (%s)" % filled)
                return 3

            ins = await b.ev(sess, INSERT)
            print("INSERT:", json.dumps(ins, ensure_ascii=False)[:300])
            if not isinstance(ins, dict) or not ins.get("ok"):
                print("REJECTED: the composer could not be focused for the copy")
                return 4
            # The copy goes in through CDP's Input.insertText: a real input
            # event, which is what the composer's own input path expects.
            await b.call("Input.insertText", {"text": copy}, session_id=sess)
            await asyncio.sleep(2.5)
            rr = await b.ev(sess, sub(REREAD, COPY=copy, REPO=repo))
            print("REREAD:", json.dumps(rr, ensure_ascii=False)[:250])
            if not isinstance(rr, dict) or rr.get("domMatch") is not True:
                print("REJECTED: the copy did not survive the re-read")
                return 4
            if not rr.get("hasUrl"):
                print("REJECTED: the address is not in the composer text")
                return 4
            if dry_run:
                print("DRY RUN: the composer holds the copy and the address")
                return 0

            print("BUTTONS:", await b.ev(sess, BTN_STATE))
            print("SCROLL:", await b.ev(sess, SCROLL_BTN))
            await asyncio.sleep(1.0)
            clicked = await b.ev(sess, CLICK_BTN)
            print("SEND CLICK:", clicked)
            if not str(clicked).startswith("CLICKED"):
                print("REJECTED: no enabled post button")
                return 5
            await asyncio.sleep(10.0)
            ps = await b.ev(sess, sub(POST_SEND, HANDLE=handle))
            own = json.loads(ps).get("own", []) if isinstance(ps, str) else []
            sid = None
            for href in own:
                if "/%s/status/" % handle in href and "analytics" not in href:
                    sid = href.rstrip("/").split("/")[-1]
            print("POST SID: %s" % ("(found)" if sid else "(none)"))
            if not sid:
                print("NO POST ON PAGE")
                return 6
        finally:
            await b.close_tab(tid)

        # ---- the landed post, on its own permalink
        tid2, s2 = await b.new_tab("https://%s/%s/status/%s"
                                    % (xconfig.site(), handle, sid))
        try:
            raw = None
            for _ in range(14):
                await asyncio.sleep(3.0)
                raw = await b.ev(s2, sub(OWN_READ, SID=sid))
                try:
                    d = json.loads(raw) if isinstance(raw, str) else {}
                except ValueError:
                    d = {}
                if d.get("nMine"):
                    break
            if not isinstance(raw, str):
                print("NO POST ON PAGE")
                return 6
            d = json.loads(raw)
            if not d.get("nMine"):
                print("NO POST ON PAGE; last raw: %s" % str(raw)[:300])
                return 6
            landed = d.get("text", "")
            card_text = d.get("cardText", "")
            tco = d.get("tco") or []
            ext = d.get("ext") or []
            print("LANDED LEN:", d.get("len"))
            print("CARD TEXT:", card_text[:120])
            print("TCO:", tco)
            print("EXT LINKS:", ext)
            # The prose is compared with the URL span removed from BOTH
            # sides: X rewrites the address as a t.co, so looking for the
            # address in the text reads false on a landed link. The address
            # is proved by the card naming the repository.
            ok = canon(landed) == canon(copy)
            print("PROSE MATCH:", ok)
            if not tco:
                print("LANDED LINK LOST - the post is up without its address")
                return 7
            if not d.get("hasCard"):
                print("LANDED LINK PRESENT BUT NOT PROVEN - no card on the post")
                return 8
            repo_name = repo.rstrip("/").split("/")[-1]
            if repo_name and repo_name.lower() not in card_text.lower():
                print("LANDED LINK PRESENT BUT NOT PROVEN - the card does not "
                      "name the repository")
                return 8
            if not ok:
                print("LANDED TEXT>>>")
                print(landed[:1500])
                print("LANDED LINK PRESENT BUT NOT PROVEN - the prose differs")
                return 8
        finally:
            await b.close_tab(tid2)

    xstate.record_published({
        "date": time.strftime("%Y-%m-%d"),
        "repo": repo,
        "kind": "promotion",
        "url": "https://%s/%s/status/%s" % (xconfig.site(), handle, sid),
    })
    print("LANDED LINK OK")
    print("URL: https://%s/%s/status/%s" % (xconfig.site(), handle, sid))
    return 0


def main(argv) -> int:
    copy_path = None
    repo = None
    dry_run = False
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--copy":
            copy_path = args[i + 1]; i += 2
        elif args[i] == "--repo":
            repo = args[i + 1]; i += 2
        elif args[i] == "--dry-run":
            dry_run = True; i += 1
        else:
            print("unknown argument: %s" % args[i])
            return 2
    if not (copy_path and repo):
        print(__doc__)
        return 2
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
    with xstate.Lock():
        return asyncio.run(run(copy, repo, dry_run))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
