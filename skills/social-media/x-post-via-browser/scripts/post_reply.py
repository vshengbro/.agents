#!/usr/bin/env python3
"""Reply to a post through the reply box that its own reply control opens.

The path is the one a person takes: find the post on the open page, click the
reply control on that post, type into the box that appears, send. Clicking a
reply control opens the box in place, so this loads no page, opens no tab and
takes no focus — which is why the commit gate allows this file alongside
no-page-load.

Two things went wrong before, and both are refused now rather than retried:

- Choosing the editor by height picked the main composer on a timeline, and
  643 characters went into the standalone post box and were published as a new
  post. The reply box is now identified by what appeared after the click, and
  sending is refused unless the editor holding the text sits in a reply dialog.
- Choosing the first enabled tweet button on the page sent through whatever
  composer happened to be on screen. The send control is now looked up inside
  the same dialog as the editor that took the text.

Nothing counts as sent until the reply is found under its own target.

  python3 post_reply.py 9240 <status_id> <reply_text_or_file>
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as C                                          # noqa: E402
import org_repos                                          # noqa: E402

DRAFT_CLS = "public-DraftEditor-content"
# The member reply cap. The 280 that free accounts get does not apply here,
# and checking against it once meant trimming drafts to a fifth of an answer.
REPLY_LIMIT = 25000
ME = "eastspire_sheng"

SNAPSHOT = """(() => {
  window.__seenEditors = new Set(
    [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
      .filter(n => n.className && n.className.indexOf(%s) >= 0
                   && n.offsetParent !== null));
  return window.__seenEditors.size;
})()""" % json.dumps(DRAFT_CLS)

# Bring the target into view first. A post can sit in the DOM 31000px below
# the fold, where its reply control is off-screen and a click lands on
# nothing — which is why opening once succeeded and produced no box. A scroll
# is not a navigation, so the rest of the rules still stand.
SCROLL_INTO_VIEW = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => x.getAttribute('href').split('/').pop() === SID
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (!own) continue;
    // The reply control sits at the bottom of a post, so a post whose top is
    // technically in view can still have its control below the fold. Scroll
    // the control, not the article.
    const btn = a.querySelector('[data-testid="reply"]');
    const box = btn ? btn.getBoundingClientRect() : a.getBoundingClientRect();
    const vh = window.innerHeight;
    if (box.top > 40 && box.bottom < vh - 40) {
      return JSON.stringify({moved: false, top: Math.round(box.top)});
    }
    a.scrollIntoView({block: 'center', behavior: 'instant'});
    const after = (a.querySelector('[data-testid="reply"]')
                   || a).getBoundingClientRect();
    return JSON.stringify({moved: true, top: Math.round(after.top),
                           vh: vh});
  }
  return JSON.stringify({moved: false, why: 'not on page'});
})()"""

# Click the reply control on the article that OWNS this status id. Matching any
# status link picks up a quoted post or a reply context instead, which is how a
# reply once targeted a stranger's post.
# Open the reply box the way a pointer does, without a pointer.
# element.click() only fires `click`, and X's controls act on the
# mousedown/mouseup pair — so the first version reported CLICKED and opened
# nothing. Dispatching that sequence on the element needs no coordinates and
# takes neither the user's mouse nor the OS keyboard, which is exactly what
# the no-mouse-keyboard rule protects. Clicking a stale position straight
# after a scroll is what raised the draft prompt, so the caller waits first.
REPLY_POINT = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => x.getAttribute('href').split('/').pop() === SID
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (!own) continue;
    const btn = a.querySelector('[data-testid="reply"]');
    if (!btn) return JSON.stringify({why: 'no reply button'});
    const box = btn.getBoundingClientRect();
    if (!box.width) return JSON.stringify({why: 'reply button has no size'});
    if (box.top < 0 || box.top > window.innerHeight) {
      return JSON.stringify({why: 'reply control is off screen',
                            top: Math.round(box.top)});
    }
    const at = {bubbles: true, cancelable: true, view: window,
                clientX: box.left + box.width / 2,
                clientY: box.top + box.height / 2, button: 0};
    btn.dispatchEvent(new MouseEvent('mousedown', at));
    btn.dispatchEvent(new MouseEvent('mouseup', at));
    btn.dispatchEvent(new MouseEvent('click', at));
    return JSON.stringify({opened: true, top: Math.round(box.top)});
  }
  return JSON.stringify({why: 'target not on page'});
})()"""

# The reply editor is the one that was not on the page before the click. The
# send control is found by walking up from that editor, never by taking the
# first enabled tweet button on the page.
STATE = """(() => {
  const now = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  const seen = window.__seenEditors || new Set();
  const fresh = now.filter(n => !seen.has(n));
  // A leftover "keep your draft" prompt can sit on top of the reply box, and
  // the first dialog on the page is then the wrong one. Scope by which dialog
  // holds a visible editor, not by which came first.
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  const inDialog = (list) => list.filter(n => dialogs.some(
    d => d === n.closest('[role="dialog"]')));
  const e = inDialog(fresh)[0] || fresh[0] || inDialog(now)[0] || now[0];
  if (!e) return {ok: false, why: 'no visible editor'};
  e.focus();
  let text = '';
  for (const n of e.childNodes) text += n.textContent || '';
  let scope = dialogs.find(d => d.contains(e)) || e.closest('form')
              || e.parentElement;
  let send = null;
  while (scope && scope !== document.body) {
    send = [...scope.querySelectorAll('button[data-testid]')]
      .find(b => /^tweetButton/.test(b.dataset.testid));
    if (send) break;
    scope = scope.parentElement;
  }
  return {ok: true, len: text.length, text: text,
          in_dialog: !!e.closest('[role="dialog"]'), is_new: fresh.includes(e),
          editors: now.length, send: send ? send.dataset.testid : null,
          enabled: !!(send && !send.disabled)};
})()""" % json.dumps(DRAFT_CLS)

CLOSE = """(() => {
  const d = [...document.querySelectorAll('[role="dialog"]')]
    .filter(x => x.offsetParent !== null
                 && x.querySelector('[data-testid="tweetTextarea_0"]'))[0];
  if (!d) return 'no dialog with an editor';
  const btn = d.querySelector('[data-testid="app-bar-close"]');
  if (!btn) return 'no close button';
  btn.click();
  return 'closed';
})()"""

SEND = """(() => {
  const now = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  // Same scoping as STATE: the dialog that holds a visible editor, not
  // whichever dialog the page happens to list first.
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  const e = now.find(n => dialogs.some(d => d === n.closest('[role="dialog"]')))
          || now[0];
  if (!e) return {sent: null, why: 'reply editor is gone'};
  let scope = dialogs.find(d => d.contains(e)) || e.closest('form')
              || e.parentElement;
  while (scope && scope !== document.body) {
    const btn = [...scope.querySelectorAll('button[data-testid]')]
      .find(b => /^tweetButton/.test(b.dataset.testid) && !b.disabled);
    if (btn) { btn.click(); return {sent: btn.dataset.testid}; }
    scope = scope.parentElement;
  }
  return {sent: null, why: 'no enabled send button inside the reply box'};
})()""" % json.dumps(DRAFT_CLS)

# Verified where a reply actually appears: carrying the same text prefix, written
# by this account, and marked as a reply.
#
# The original template demanded that the TARGET id be a status link inside the
# article. On this build a sent reply renders as a top-level article whose own
# time link carries its OWN id, and the "@target" name it replies to is plain
# text, not a link — so the target id was nowhere in the article and the search
# never matched. The reply had landed, and was reported NOT VERIFIED every time.
# So match on the three things the timeline really does show: the author, the
# body prefix, and the 回复 label.
VERIFIED = """(() => {
  const out = [];
  for (const a of document.querySelectorAll('article')) {
    const who = a.querySelector("a[href^='/']");
    if (!who || who.getAttribute('href').split('/').pop() !== WHO) continue;
    let body = '';
    const walk = (n) => {
      let s = '';
      for (const k of n.childNodes) {
        if (k.nodeType === 3) s += k.textContent;
        else if (k.nodeName === 'BR') s += '\\n';
        else s += walk(k);
      }
      return s;
    };
    const box = a.querySelector('[data-testid="tweetText"]');
    if (box) body = walk(box);
    if (!body) continue;
    const full = (a.innerText || '');
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    out.push({sid: st ? st.getAttribute('href').split('/').pop() : '',
              text: body.replace(/\\s+/g, ' ').trim(),
              is_reply: /回复|Replying to/.test(full.slice(0, 200)),
              // A reply long enough to be collapsed shows only its first few
              // words plus a 显示更多 control, so a prefix match against the
              // source reads as "no such reply" on a reply that is in fact
              // complete and sitting right there.
              collapsed: /显示更多|Show more|顯示更多/.test(
                  full.slice(0, 400))});
  }
  return JSON.stringify({rows: out});
})()"""

canon = lambda s: "".join(re.sub(r"https?://\S+", "\x00", s or "").split())


# Expand a collapsed reply, in place. The control is a SPAN with a click
# handler, not a link, so this is the same act as clicking 显示更多 and it
# loads nothing. Scoped to ONE status id on purpose: the feed's other posts have
# their own 显示更多 controls, and expanding those would rewrite text that is
# being compared for other reasons.
EXPAND = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === SID);
    if (!st) continue;
    const more = [...a.querySelectorAll('span, div, [role="button"], a')]
      .filter(e => {
        const t = (e.textContent || '').trim();
        return (t === '显示更多' || t === 'Show more' || t === '顯示更多')
               && !e.querySelector('*');
      });
    if (!more.length) return {expanded: false, why: 'nothing to expand'};
    more[0].click();
    return {expanded: true};
  }
  return {expanded: false, why: 'status not on page'};
})()"""


def same_body(got: str, want: str) -> bool:
    """Compare what the editor holds against the source, ignoring whitespace.

    An exact compare can never pass for a multi-line reply. X renders each
    newline as an element (a div or a br), so the text nodes hold the lines
    with nothing between them: a 476-character source with 6 newlines came back
    as 470 characters, and the script called that a mismatch and refused to
    send a reply that was in fact correct and complete. publish.py already
    reduces both sides to their non-space characters for the same reason, and
    the editor's raw length is not trustworthy either — Draft keeps hidden
    text nodes of its own, so it can read high on text that matches.

    So the guarantee is the non-space characters, exactly as publish.py states
    it: a dropped or mangled character cannot hide behind a space.
    """
    return canon(got) == canon(want)


def js(c, tpl, sid=None):
    """Evaluate a template, always handing back a dict.

    cdp.js returns whatever the expression produced, or an error marker string.
    Callers here ask structured questions and then read the answer, so a bare
    string has to stay visible as a failure instead of disappearing into a dict
    the caller forgets to check.

    A template that ends in JSON.stringify() returns a STRING, not an object,
    and the templates here are split across both styles. Wrapping it as _raw
    made every question asked of one of them read as "no" — REPLY_POINT
    answered {"opened":true} and the caller saw {"_raw": '{"opened":true}'},
    so a reply box that had opened was reported as NOT SENDING with no reason,
    every single time, while the box was in fact sitting there focused and
    ready. Parse a JSON object out of a string before giving up on it.
    """
    r = c.js(tpl.replace("SID", json.dumps(sid or ""))
              .replace("WHO", json.dumps(ME)), wait=25, retries=5)
    if isinstance(r, str):
        try:
            r = json.loads(r)
        except ValueError:
            pass
    if isinstance(r, dict):
        return {k: v for k, v in r.items() if not k.startswith("__")}
    return {"_raw": str(r)[:160]}


PICK = """(() => {
  const out = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => x.getAttribute('href').split('/').pop()
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (!own) continue;
    const sid = own.getAttribute('href').split('/').pop();
    if (seen.has(sid)) continue;
    seen.add(sid);
    const who = a.querySelector("a[href^='/']");
    const box = a.querySelector('[data-testid="tweetText"]');
    out.push({sid: sid,
              who: who ? who.getAttribute('href').split('/').pop() : '?',
              text: box ? box.innerText.replace(/\\s+/g, ' ').trim() : ''});
  }
  return JSON.stringify(out);
})()"""

# Pick a target on the page that is actually about AI, tooling or code, and is
# written by someone else. The account's own posts are never a reply target.
AI_WORDS = ("rust", "agent", "llm", "token", "context", "cargo", "wasm",
            "compile", "macro", "mcp", "tool call", "code", "model", "prompt",
            "inference", "编程", "模型", "编译", "工具", "宏", "上下文", "智能体")


def pick_target(c, want=""):
    """Find the post on the page that a reply was written for.

    The status id comes from this read, never from a file written by an
    earlier scroll: the timeline replaces posts continuously, so an id read
    minutes ago names something no longer on screen. When the reply names its
    target, only that post qualifies — searching for a keyword instead is how
    a reply ends up under the wrong post.
    """
    r = c.js(PICK, wait=30, retries=5)
    rows = json.loads(r) if isinstance(r, str) else r
    if not isinstance(rows, list):
        return "", None
    for row in rows:
        if row.get("who") == ME or not row.get("text"):
            continue
        if want:
            if row["sid"] == want:
                return row["sid"], row
            continue
        if any(w in row["text"].lower() for w in AI_WORDS):
            return row["sid"], row
    return "", None


def main() -> int:
    port, sid, arg = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    text = open(arg, encoding="utf-8").read() if os.path.exists(arg) else arg
    for_sid = ""
    m = re.search(r"^#\s*target-status:\s*(\d{15,25})\s*$", text, re.M)
    if m:
        for_sid = m.group(1)
        text = re.sub(r"^#.*$\n?", "", text, flags=re.M)
    C.set_port(port)
    tabs = [t for t in C.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab", flush=True)
        return 1
    c = C.Cdp(tabs[0]["webSocketDebuggerUrl"])

    # A reply here has two jobs: it has to answer the post it sits under, and
    # it has to carry a repository this account owns. A github.com link to
    # somewhere else is not a promotion of this account's work, so the owners
    # are matched rather than the host.
    repo = org_repos.find_repo(text)
    if not repo:
        print("REFUSING - %s" % org_repos.check(text), flush=True)
        c.close()
        return 1
    if len(text) > REPLY_LIMIT:
        print("REFUSING - %d characters, over the %d limit"
              % (len(text), REPLY_LIMIT), flush=True)
        c.close()
        return 1
    print("  carries %s, %d characters" % (repo, len(text)), flush=True)

    # X linkifies any dotted token and the replaced span reads back as a line
    # break, which splits the sentence. Refuse before typing, not after.
    stray = [w for w in re.findall(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}", text)
             if not w.startswith("github")]
    if stray:
        print("REFUSING: %s will be linkified and read back broken" % stray,
              flush=True)
        c.close()
        return 1

    if sid == "auto":
        sid, row = pick_target(c, for_sid)
        if not sid:
            if for_sid:
                # Say which post is missing. "nothing relevant" would send
                # the reader looking for a topic problem that is not there.
                print("NOT ON THE PAGE - this reply is written for %s and "
                      "that post is not in view; scroll to it and run again"
                      % for_sid, flush=True)
            else:
                print("NO TARGET - the reply names no post, and nothing on "
                      "the page matches the AI/tooling vocabulary", flush=True)
            c.close()
            return 1
        # A reply is written for one post. A reply file says which, and the
        # post on screen has to be that one. "auto" once answered a post about
        # quant trading with an argument about compile-time checks, so the
        # target is chosen from the reply rather than the other way round.
        if for_sid and for_sid != sid:
            print("NOT THE POST THIS REPLY WAS WRITTEN FOR", flush=True)
            print("  reply targets  %s" % for_sid, flush=True)
            print("  page shows     %s @%s" % (sid, row["who"]), flush=True)
            c.close()
            return 1
        print("target: @%s %s%s" % (
            row["who"], sid, " (declared)" if for_sid else ""), flush=True)
        print("  %s" % row["text"][:140], flush=True)

    for _ in range(3):
        pos = js(c, SCROLL_INTO_VIEW, sid)
        if pos.get("why"):
            break
        time.sleep(1.2)
        if not pos.get("moved"):
            break
    if pos.get("moved"):
        print("  scrolled the post into view (top %s)" % pos.get("top"),
              flush=True)

    c.js("""(() => {
      for (const d of document.querySelectorAll('[role="dialog"]')) {
        if (d.offsetParent === null) continue;
        if (d.querySelector('[contenteditable="true"]')) continue;
        const b = d.querySelector('[data-testid="app-bar-close"]');
        if (b) b.click(); else d.remove();
      }
    })()""", wait=25, retries=4)
    time.sleep(1.0)

    c.js(SNAPSHOT, wait=25, retries=4)
    # A scroll needs time to settle. The virtual list re-renders, and a click
    # into the old position is read as leaving the editor — the prompt that
    # appeared when this was done in one step.
    time.sleep(2.0)      # let a scroll settle before aiming at the control
    pt = js(c, REPLY_POINT, sid)
    print("open reply:", pt, flush=True)
    if not pt.get("opened"):
        print("NOT SENDING -", pt.get("why"), flush=True)
        c.close()
        return 1
    opened = pt
    time.sleep(2.5)
    # The draft prompt appears after the click, so clear overlays again.
    c.js("""(() => {
      for (const d of document.querySelectorAll('[role="dialog"]')) {
        if (d.offsetParent === null) continue;
        if (d.querySelector('[contenteditable="true"]')) continue;
        const b = d.querySelector('[data-testid="app-bar-close"]');
        if (b) b.click(); else d.remove();
      }
    })()""", wait=25, retries=4)
    time.sleep(1.0)
    probe = js(c, STATE)
    if not probe.get("ok") or not probe.get("in_dialog"):
        print("NOT SENDING - the reply box did not open. Measured on this "
              "browser: a synthesised mousedown/mouseup on the control "
              "changes nothing, and with the overlays gone focus does land "
              "on it but X ignores a synthesised Enter and Space. Only a "
              "real click opens it. Open the reply box yourself and the "
              "typing, the exact length check and the verification below "
              "all still work.", flush=True)
        c.close()
        return 1
    # Nothing is typed when the target is not on this page: a missing reply
    # control once let the flow fall through to the main composer.
    if not opened.get("opened"):
        print("NOT SENDING - target post is not on the open page", flush=True)
        c.close()
        return 1

    time.sleep(3)
    st = {}
    for _ in range(10):
        st = js(c, STATE)
        if st.get("ok"):
            break
        time.sleep(1.5)
    if not st.get("ok"):
        print("reply composer did not appear:", st, flush=True)
        c.close()
        return 1
    print("  reply box: new=%s in_dialog=%s editors=%s send=%s:%s" % (
        st.get("is_new"), st.get("in_dialog"), st.get("editors"),
        st.get("send"), "en" if st.get("enabled") else "dis"), flush=True)
    if not st.get("in_dialog"):
        print("  NOT SENDING - no reply box opened; the only editor is the "
              "main composer", flush=True)
        c.close()
        return 1

    # A leftover draft from a previous run is appended to rather than replaced,
    # and the result posts as somebody else's sentence. Start from empty.
    if st.get("len", 0) != 0:
        # A leftover draft must not be edited, appended to, or deleted: the
        # composer is the user's, and clearing it is exactly what the gate
        # forbids. Close this box and open a fresh one instead — a new reply
        # composer starts empty.
        print("  reply box already holds %s characters, reopening a clean one"
              % st.get("len"), flush=True)
        js(c, CLOSE)
        time.sleep(2.0)
        st = {}
        for _ in range(8):
            js(c, REPLY_POINT, sid)
            time.sleep(1.5)
            st = js(c, STATE)
            if st.get("ok") and st.get("len", 0) == 0:
                break
        if not st.get("ok") or st.get("len", 0) != 0:
            print("  NOT SENDING - no empty reply box could be opened, and "
                  "the existing draft is not ours to touch", flush=True)
            c.close()
            return 1
        print("  clean reply box open", flush=True)

    # insertText writes to the DOM without touching the editor state, so the
    # send button lights up while the handler behind it still sees an empty
    # draft and posts nothing. Real key events are the path a person uses.
    print("  typing %d characters" % len(text), flush=True)
    for i, ch in enumerate(text):
        if ch == "\n":
            c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13, text="\r")
            c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13)
        elif ord(ch) < 0x80:
            c.send("Input.dispatchKeyEvent", type="keyDown", key=ch, text=ch)
            c.send("Input.dispatchKeyEvent", type="keyUp", key=ch)
        else:
            # No keyboard key produces an em dash or any CJK character, so a
            # key event drops it. `char` is the event that carries text with
            # no key behind it.
            c.send("Input.dispatchKeyEvent", type="char", text=ch)
        if i % 25 == 24:
            time.sleep(0.4)
    time.sleep(2.5)

    st = js(c, STATE)
    # Newlines are elements in the editor, not characters in its text, so the
    # compare is on the non-space characters rather than the raw strings.
    ok = same_body(st.get("text") or "", text)
    print("  LEN %s want %s exact=%s" % (st.get("len"), len(text), ok),
          flush=True)
    if not ok:
        print("  text does not match, not sending", flush=True)
        c.close()
        return 1
    if not st.get("in_dialog"):
        print("  NOT SENDING - the editor holding the text is not a reply "
              "box", flush=True)
        c.close()
        return 1

    res = js(c, SEND)
    for _ in range(8):
        if res.get("sent"):
            break
        time.sleep(3)
        res = js(c, SEND)
    c.close_composition("")
    print("SEND", res, flush=True)
    if not res.get("sent"):
        c.close()
        return 1

    time.sleep(6)
    # WHO goes through js(), which substitutes it; JSON.stringify then hands
    # the answer back as a string, and js() parses that into the dict this loop
    # reads. Leaving WHO unsubstituted made the template throw, and the throw
    # arrives as a dict — so "not a list" was the only thing the loop saw, and
    # it reported NOT VERIFIED on a reply that had just landed.
    #
    # Scrolling to the top first is part of the same fix. A reply that has just
    # been sent appears at the TOP of the timeline, and this script scrolls
    # down to reach the target before typing — so the feed was left scrolled
    # past the very post it was about to verify. One run sent a reply,
    # scrolled to the top, found it there, and reported NOT VERIFIED. A scroll
    # is not a navigation, so every other rule still stands.
    prefix = canon(text)[:60]
    for _ in range(6):
        c.js("window.scrollTo(0, 0); true", wait=20, retries=3)
        time.sleep(2.5)
        rows = js(c, VERIFIED).get("rows") or []
        if isinstance(rows, list):
            # A reply that landed is identified by its own text prefix, by this
            # account, and by being marked a reply. Requiring the target's id
            # to be a link inside the article was the bug: X renders a sent
            # reply as its own top-level article and leaves the replied-to
            # name as plain text.
            for row in rows:
                if canon(row.get("text", "")).startswith(prefix):
                    print("VERIFIED reply by @%s: %s reply_marked=%s"
                          % (ME, row.get("sid", ""), row.get("is_reply")),
                          flush=True)
                    c.close()
                    return 0
                # The prefix may be missing only because X collapsed the text
                # behind 显示更多, which leaves only the first few words
                # showing. Expand that one reply and read it again — a
                # 329-character Japanese reply was reported NOT VERIFIED
                # because the timeline showed 14 characters of it.
                if row.get("collapsed") and row.get("sid"):
                    ex = js(c, EXPAND.replace("SID",
                                              json.dumps(row["sid"])))
                    print("  collapsed reply %s, expanding: %s"
                          % (row["sid"], ex), flush=True)
                    if ex.get("expanded"):
                        time.sleep(2.5)
                        again = js(c, VERIFIED).get("rows") or []
                        for r2 in again if isinstance(again, list) else []:
                            if r2.get("sid") == row["sid"] and canon(
                                    r2.get("text", "")
                            ).startswith(prefix):
                                print("VERIFIED reply by @%s: %s "
                                      "reply_marked=%s (expanded)"
                                      % (ME, r2.get("sid", ""),
                                         r2.get("is_reply")), flush=True)
                                c.close()
                                return 0
        time.sleep(5)
    print("NOT VERIFIED - no reply from this account carries this text",
          flush=True)
    c.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
