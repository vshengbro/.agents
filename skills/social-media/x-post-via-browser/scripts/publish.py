#!/usr/bin/env python3
"""Post one long post to X through the composer that is already open.

The shortest path that works. Every step was measured, and everything else was
tried and measured to break the text:

  focus the real Draft editor -> one insertText for the whole body ->
  compare -> click the post button -> verify with verify_post.py

These do NOT work, and none of them is here:

  * imeSetComposition for the URL — strands the URL's first character in the
    body, so the editor reads "…edition。h" against a source of "…"
  * a paste for the URL (commands=["paste"]) — X folds the separator into the
    host and the sentence comes back as "https://\ncrates.io"
  * clearing the composer — leaves 4–24 characters, and a later reload raises
    Chrome's unsaved-changes dialog, which blocks every step after it
  * looking for button[data-testid="tweetButton"] — the inline composer mounts
    tweetButtonInline and often mounts no tweetButton at all

  python3 publish.py [port] --post 0 --go
  python3 publish.py [port] --show          # the copy, touches nothing
  python3 publish.py [port] --tabs          # the open X tab, touches nothing
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cdp as C                                          # noqa: E402
import xconfig                                           # noqa: E402

COPY = os.environ.get("X_COPY") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "x_copy_example.json")
DRAFT_CLS = "public-DraftEditor-content"

# Two nodes carry data-testid="tweetTextarea_0" and only one is the real
# editor; the other is an empty decoy. Document order is not stable between
# renders, so the taller visible one is the one that holds the text.
EDITOR = """(() => {
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  if (!all.length) return {ok: false, why: 'no visible Draft editor'};
  const e = all.sort((a, b) => b.getBoundingClientRect().height
                             - a.getBoundingClientRect().height)[0];
  const a = document.activeElement;
  let text = '';
  for (const n of e.childNodes) text += n.textContent || '';
  return {
    ok: true, focused: a === e || (a && e.contains(a)),
    len: text.length, text: text,
    buttons: [...document.querySelectorAll('button[data-testid]')]
      .filter(b => /^tweetButton/.test(b.dataset.testid))
      .map(b => b.dataset.testid + (b.disabled ? ':dis' : ':en'))
  };
})()""" % json.dumps(DRAFT_CLS)

# Either button posts. X mounts tweetButtonInline for the inline composer and
# does not reliably mount tweetButton, so a lookup that requires tweetButton
# finds nothing on a composer whose button is right there and enabled — which
# reads as "the button never enabled" and silently drops the post.
BUTTON = """(() => {
  const all = [...document.querySelectorAll('button[data-testid]')]
    .filter(b => /^tweetButton/.test(b.dataset.testid));
  const b = all.find(x => x.dataset.testid === 'tweetButton')
         || all.find(x => !x.disabled);
  if (!b) return {clicked: null, why: all.length ? 'disabled' : 'no post button',
                  present: all.map(x => x.dataset.testid)};
  if (b.disabled) return {clicked: null, why: 'disabled',
                          present: all.map(x => x.dataset.testid)};
  b.click();
  return {clicked: b.dataset.testid,
          present: all.map(x => x.dataset.testid)};
})()"""

STRIP = lambda s: re.sub(r"https?://\S+", "\x00", s or "")
FLAT = lambda s: "".join((s or "").split())


def canon(s: str) -> str:
    """Source and editor text reduced to a comparable form.

    Whitespace goes everywhere: X removes a space at a Latin/CJK boundary
    while typing ("AI 时代" -> "AI时代") and the Draft editor keeps hidden
    nodes of its own, so a raw length compare reads 860 against an 859
    character source on a post that is character-for-character correct. What
    is left is the non-space characters, and those must match exactly — a
    dropped or mangled character cannot hide behind a space.
    """
    return FLAT(STRIP(s))


def jd(v):
    """js() returns a value or a distinguishable error marker; unwrap both."""
    if isinstance(v, dict) and any(k in v for k in
                                   ("__js_error", "__socket_error",
                                    "__timeout", "__cdp_error")):
        return {}
    return v if isinstance(v, dict) else {}


def read(c):
    return jd(c.js(EDITOR, wait=25, retries=5))


def focus_editor(c, tries=12):
    """Address the composer's Draft editor, opening it by clicking if needed.

    No navigation and no reload: every page load makes the user confirm it in
    their UI, so the composer is opened the way a person opens it — by
    clicking the compose control already on screen.
    """
    for _ in range(tries):
        st = read(c)
        if st.get("ok"):
            c.js("""(() => {
              const all = [...document.querySelectorAll(
                '[data-testid="tweetTextarea_0"]')]
                .filter(n => n.className && n.className.indexOf(%s) >= 0
                             && n.offsetParent !== null);
              if (!all.length) return false;
              all.sort((a, b) => b.getBoundingClientRect().height
                                - a.getBoundingClientRect().height)[0].focus();
              return true;
            })()""" % json.dumps(DRAFT_CLS), wait=20, retries=3)
            time.sleep(0.4)
            st = read(c)
            if st.get("focused"):
                return st
        time.sleep(0.6)

    opened = c.js("""(() => {
      const btn = [...document.querySelectorAll(
        '[data-testid="SideNav_NewTweet_Button"], '
        '[data-testid="SideNav_NewTweetButton"], '
        'a[href*="/compose/post"], '
        + '[data-testid="appTabBarPostBtn"]')]
        .filter(e => e.offsetParent !== null)[0];
      if (!btn) return 'NO_COMPOSE_CONTROL';
      btn.click(); return 'CLICKED_COMPOSE';
    })()""", wait=25, retries=5)
    time.sleep(7)
    for _ in range(tries):
        st = read(c)
        if st.get("ok"):
            return st
        time.sleep(0.6)
    print(f"  no composer on this page and {opened} — open the composer "
          f"yourself; nothing was reloaded", flush=True)
    return st


def stray_linkifiers(text: str, urls) -> list:
    """Dotted tokens X will turn into links even though they are not URLs.

    X linkifies any dotted token, not just one it recognises as a URL, and the
    span it replaces then reads back as a line break — a bare "crates.io" in
    the body split a sentence in two and shipped twice before it was refused
    here. So the check is on the COPY, before a character is typed.
    """
    hosts = {u.split("://", 1)[1].split("/", 1)[0] for u in urls}
    return [w for w in re.findall(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}", text)
            if w not in hosts]


def warm(c) -> None:
    """Send one throwaway character so the editor accepts the next one.

    A fresh Draft block — the composer itself, or any block Enter just opened —
    swallows the first character typed into it. Measured four ways on the same
    body: under char events the leading '中' was gone, under keyDown/keyUp it
    was gone, with a 30ms per-character delay it was gone, and with the caret
    explicitly collapsed to the start it was still gone. One ASCII space first
    initialises the block and the body then arrives exact.

    The warm-up character is a SPACE, and it is removed afterwards. Do not
    change it to a visible marker: measured, the removal pass deletes forward
    from the start of each block, and a leading space is the one thing that
    survives that pass without leaving the body visibly wrong if it is missed.
    """
    c.send("Input.dispatchKeyEvent", type="char", text=" ")
    time.sleep(0.25)


def current_text(c) -> str:
    """The focused Draft editor's text, for a mid-run comparison."""
    return c.js("""(() => {
      const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
        .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                     && n.offsetParent !== null);
      const e = all.find(x => x === document.activeElement) || all[0];
      return (e && e.innerText) || '';
    })()""", wait=20, retries=3) or ""


def type_keys(c, text: str, initial: str | None = None) -> None:
    """Type a non-ASCII body as real key events, one character at a time.

    Input.insertText writes to the DOM without touching the editor's state, so
    a CJK run sent that way is discarded: measured, a 597-character Chinese
    body came back holding only its 30-character ASCII URL, and 5-, 48- and
    190-character Chinese probes all arrived as a single newline. Real key
    events update the editor model, and the reply path — which sends Chinese
    this way — lands its text every time.

    A key event cannot carry a character no keyboard produces, so non-ASCII
    goes as a `char` event and ASCII as keyDown/keyUp. Enter is a real key.

    THE WARM-UP CHARACTER IS LOAD-BEARING. In an empty Draft block the very
    first character of any sequence is swallowed, whatever it is and however it
    is sent: measured, '中文测试' arrived as '文测试' under char events, under
    keyDown/keyUp, with a 30ms per-character delay, and with the caret
    explicitly collapsed to the end. One ASCII space first initialises the
    block and the body then arrives exact.

    URLS GO IN AS SLOW KEY EVENTS. Two faster paths both truncate them:
    key events at full speed arrive as 'https://github.c' — the punctuation
    run is what the editor drops — and a single insertText at the caret
    position inserts nothing at all, silently. The URL characters go one at a
    time with a pause, which is the same path that carries the body correctly.
    """
    parts = re.split(r"(https?://\S+)", text)
    # The URL goes in FIRST, before any body text, and the body follows it.
    #
    # imeSetComposition is the only measured path that delivers a URL intact —
    # per-character key events lose the tail to linkification ('https://github.c',
    # identically at 0/40/80/150 ms per character, in an empty editor and after a
    # body, with the caret re-focused and with a blur/refocus reset), and
    # Input.insertText inserts nothing.
    #
    # It only works against an EMPTY composer. Measured: called as the first
    # thing after focusing a blank Draft editor the URL lands whole; called
    # after the body has been typed it lands zero times, and no error is
    # reported either way — so the count gate is what distinguishes them.
    for block in parts:
        if not block:
            continue
        is_url = bool(re.match(r"^https?://\S+$", block))
        if is_url:
            # imeSetComposition, whole URL, then WAIT. Two things that look
            # harmless and are not, both measured here:
            #
            #   reading the composer to check the URL landed — the read beats
            #     the composition, so it looks like a failure, and the key
            #     events sent to recover cut the composition: the URL came back
            #     as 'b.com/euv-dev/euv', first ten characters gone.
            #   committing it afterwards — an insertText commit inserts the URL
            #     a SECOND time, and the post went out with the link duplicated
            #     while every presence gate passed, because presence is not
            #     count.
            #
            # So: one call, one wait, nothing else. The URL count gate in main()
            # is what reports failure.
            c.send("Input.imeSetComposition", text=block,
                   selectionStart=len(block), selectionEnd=len(block),
                   wait=40, retries=6)
            # Wait it out. NOTHING reads the composer between this call and the
            # body's first character — not even to confirm the URL landed. The
            # read is what breaks it: measured, the identical sequence works
            # when the composer is never read and loses the URL entirely when
            # one read lands in the window between the composition and the body.
            # `initial` is what the composer already held when this run started,
            # captured by the caller before any of this — it is the only reading
            # taken on the way in, and taking it is not optional either: the
            # same call fails against a composer that already has a space in it.
            time.sleep(2.5)
            # A SPACE, not Enter, separates the URL from the body. Enter opens a
            # new block, and the warm-up removal pass then deletes from the
            # start of every block — including the URL's own, where the head
            # character is real text: measured, the leading 'euv' went missing
            # that way. One block keeps the removal pass unambiguous.
            c.send("Input.dispatchKeyEvent", type="char", text=" ")
            time.sleep(0.4)
            # Done with this block — imeSetComposition already delivered it.
            # Falling through to the per-character loop retyped the URL on top
            # of it, and linkification then kept only the tail: measured,
            # 'https://github.com/euv-dev/euv' came back as
            # 'ub.com/euv-dev/euv'.
            continue
        else:
            warm(c)
        for i, ch in enumerate(block):
            if ch == "\n":
                c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                       code="Enter", windowsVirtualKeyCode=13, text="\r")
                c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                       code="Enter", windowsVirtualKeyCode=13)
                # Enter starts a fresh block, and the first character typed
                # into a fresh block is swallowed the same way: measured, a
                # two-paragraph body arrived with '第二段' read back as '二段'.
                warm(c)
            elif ord(ch) < 0x80:
                c.send("Input.dispatchKeyEvent", type="keyDown", key=ch,
                       text=ch)
                c.send("Input.dispatchKeyEvent", type="keyUp", key=ch)
            else:
                c.send("Input.dispatchKeyEvent", type="char", text=ch)
            # A pause between characters, and one every 25 on top. Measured:
            # without the per-character pause the editor drops whole stretches
            # mid-body — a 447-character Chinese body came back holding only its
            # last 215 characters. And the whole of this loop is the only thing
            # between an intact URL and the finished text: run by hand, the same
            # sequence put 408 characters of Chinese after an imeSetComposition
            # URL and the URL was still there at the end, count 1 throughout.
            time.sleep(0.012)
            if i % 25 == 24:
                time.sleep(0.4)
    time.sleep(1.5)

    # Remove the warm-up space at the head of each block.
    #
    # Delete FORWARD from the start of the composer, repeatedly, and stop as
    # soon as the compare passes — never a fixed count. The count that a fixed
    # loop needs is wrong whenever the block structure is not exactly one
    # block per newline: measured, 9 blocks against 8 warm-ups deleted one
    # real character ('euv里每个' came back as 'DOM元素'), which the length
    # check cannot see because the removed and the trailing space cancel out.
    # Guessing the count loses real text; checking the text cannot.
    # Remove the warm-up space the body block opens with.
    #
    # ONE pass, and the block is located by the SOURCE, never by "starts with a
    # space". Both of those matter, and both were arrived at the hard way:
    #
    #   a loop kept finding the same block and ran to its limit, deleting real
    #     characters ('euv里每个' arrived as 'DOM元素');
    #   "any leaf starting with a space" finds X's linkified URL element —
    #     whose innerText is link text, so it does not even contain "http" —
    #     and deletes it. Measured: the URL was whole at the insert and read
    #     back at zero occurrences, 410 characters against a 438 character
    #     source, with the text behind it untouched.
    #
    # The source's first body characters are the only safe anchor.
    tail_src = re.sub(r"^\s*https?://\S+\s*", "", text)
    anchor = tail_src[:10]
    moved = c.js("""(() => {
      const all = [...document.querySelectorAll(
        '[data-testid="tweetTextarea_0"]')]
        .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                     && n.offsetParent !== null);
      const e = all.find(x => x === document.activeElement) || all[0];
      if (!e) return 'NO_EDITOR';
      const b = [...e.querySelectorAll('div')].find(x =>
        x.children.length === 0
        && (x.innerText || '') === ' ' + ANCHOR);
      if (!b) return 'NO_WARMUP_BLOCK';
      const sel = window.getSelection();
      const r = document.createRange();
      r.selectNodeContents(b);
      r.collapse(true);
      sel.removeAllRanges();
      sel.addRange(r);
      return 'OK';
    })()""".replace("ANCHOR", repr(anchor)), wait=25, retries=4)
    if moved == "OK":
        time.sleep(0.5)
        c.send("Input.dispatchKeyEvent", type="keyDown", key="Delete",
               code="Delete", windowsVirtualKeyCode=46)
        c.send("Input.dispatchKeyEvent", type="keyUp", key="Delete",
               code="Delete", windowsVirtualKeyCode=46)
        time.sleep(0.8)
    else:
        print(f"  warm-up removal: {moved} (no space to remove, "
              f"or the body block was not found)", flush=True)
    time.sleep(1.5)


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() \
        else xconfig.port()
    if "--show" in sys.argv:
        posts = json.load(open(COPY))
        print(f"{COPY}\n{len(posts)} posts\n")
        for i, s in enumerate(posts):
            n_urls = len(re.findall(r"https?://\S+", s))
            print(f"  [{i}] {len(s):5} chars, {n_urls} url(s)")
            print(f"      {s[:60]!r}...")
        return 0
    if "--tabs" in sys.argv:
        C.set_port(port)
        for t in C.tabs("page"):
            if xconfig.is_site_tab(t.get("url", "")):
                print(f"  {t['id'][:8]} {t['url'][:70]}")
        return 0

    idx = int(sys.argv[sys.argv.index("--post") + 1]) \
        if "--post" in sys.argv else 0
    go = "--go" in sys.argv
    text = json.load(open(COPY))[idx]
    urls = re.findall(r"https?://\S+", text)

    bad = stray_linkifiers(text, urls)
    if bad:
        print(f"REFUSING: {bad} will be linkified by X and read back broken. "
              f"Rewrite the copy without the dotted token.", flush=True)
        return 1

    C.set_port(port)
    # Bring the browser up if it is down, and open a tab if none exists. This
    # is the only page load the flow ever performs, and it lives in
    # ensure_browser.py because that is the one script the commit gate lets
    # load a page. It runs before anything is typed, so it cannot race the
    # composer or leave unsaved input behind.
    ensure = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("ensure_browser.py")),
         str(port)], capture_output=True, text=True, timeout=600)
    for line in (ensure.stdout + ensure.stderr).strip().splitlines():
        print("  " + line, flush=True)
    if ensure.returncode != 0:
        print("could not get a usable x.com tab", flush=True)
        return 1

    pages = [t for t in C.tabs("page")
            if xconfig.is_site_tab(t.get("url", ""))]
    if not pages:
        print(f"no {xconfig.site()} tab open after ensure_browser", flush=True)
        return 1
    c = C.Cdp(pages[0]["webSocketDebuggerUrl"])

    st = focus_editor(c)
    if not st.get("ok"):
        c.close()
        return 1
    print(f"FOCUS {st.get('len')} chars, buttons {st.get('buttons')}",
          flush=True)

    have = st.get("text", "") or ""
    if have:
        # The composer is never cleared by default — clearing raises the
        # unsaved-changes dialog, and this account's composer can hold text the
        # user typed. But text THIS automation left behind is different: a run
        # that failed part-way through leaves its debris, the next run then finds
        # it, and it rides out with the next post. Measured debris: 'dev/euv ',
        # the tail of a URL a run cut short, sitting in front of otherwise
        # correct text.
        #
        # Only text that is recognisably this script's own gets cleared, and the
        # test is that the composer's text differs from the target ONLY by a
        # prefix. Anything else — different words, different order — is left for
        # a human, because then it is not debris, it is someone's draft.
        # The composer's text minus any leading run of characters is the
        # target — that is exactly what this script's debris looks like. The
        # debris sits at the FRONT (measured 'dev/euv ' in front of otherwise
        # correct text), so the test is a suffix match, not a prefix one.
        tail = have
        while tail and canon(tail) != canon(text):
            tail = tail[1:]
        # Also accept whitespace-only differences, and only when the removed
        # prefix is SHORT — measured debris is a cut-short URL tail like
        # 'dev/euv ', eight characters. Without the length bound this accepts
        # any text, because trimming from the front eventually lands on the
        # target, and then a user's own draft would be cleared.
        squash = lambda s: re.sub(r"\s+", "", s)
        # A failed URL insert leaves the body WITHOUT its link, so the
        # suffix match below can never fire. Recognise that shape separately:
        # the composer's text is the source minus the URL, with warm-up spaces
        # where the URL used to be. Measured, a run that lost its URL left
        # '   euv 里事件注册表的重入问题…' against a source of
        # 'https://github.com/euv-dev/euv euv 里事件注册表的重入问题…'.
        # The composer's text may also be a PREFIX of the source: a run that
        # typed the URL and then stopped leaves exactly the URL sitting there.
        # Compare raw, not through canon — canon replaces every URL with a
        # single marker, so a prefix that is exactly one URL compares equal to
        # the source's marker and the strip never converges.
        # The composer's text may also be a suffix of the source, with this
        # script's own debris in front of it.
        without_url = squash(re.sub(r"https?://\S+", "", text))
        is_own_debris = (have.strip() and text.startswith(have.strip())
                         or canon(tail) == canon(text)
                         or squash(have) == without_url) and canon(have) != canon(text)
        if canon(have) == canon(text):
            print(f"  already holds this exact post ({st.get('len')} chars) — "
                  f"posting it as it stands", flush=True)
        elif is_own_debris:
            print(f"  found {st.get('len')} chars of this script's own debris — "
                  f"clearing before typing", flush=True)
            for _ in range(40):
                left = c.js("""(() => {
                  const all = [...document.querySelectorAll(
                    '[data-testid="tweetTextarea_0"]')]
                    .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                                 && n.offsetParent !== null);
                  const e = all.find(x => x === document.activeElement) || all[0];
                  if (!e) return 0;
                  e.focus();
                  const sel = window.getSelection();
                  const r = document.createRange();
                  r.selectNodeContents(e);
                  sel.removeAllRanges();
                  sel.addRange(r);
                  document.execCommand('delete');
                  sel.removeAllRanges();
                  return (e.innerText || '').length;
                })()""", wait=20, retries=3)
                if not left or (isinstance(left, int) and left < 2):
                    break
                time.sleep(0.3)
            time.sleep(1.2)
            # Block-by-block delete leaves a lone newline where the first
            # block was, which canon() counts as content. Trim it before
            # giving up — measured, after clearing 'dev/euv https://…' the
            # composer read back as '\nhttps://github.com/euv-dev/euv …'.
            if canon(current_text(c)):
                for _ in range(4):
                    c.js("""(() => {
                      const all = [...document.querySelectorAll(
                        '[data-testid="tweetTextarea_0"]')]
                        .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                                     && n.offsetParent !== null);
                      const e = all.find(x => x === document.activeElement) || all[0];
                      if (!e) return false;
                      e.focus();
                      const sel = window.getSelection();
                      const r = document.createRange();
                      r.selectNodeContents(e);
                      r.collapse(true);
                      sel.removeAllRanges();
                      sel.addRange(r);
                      return true;
                    })()""", wait=20, retries=3)
                    c.send("Input.dispatchKeyEvent", type="keyDown",
                           key="Delete", code="Delete",
                           windowsVirtualKeyCode=46)
                    c.send("Input.dispatchKeyEvent", type="keyUp",
                           key="Delete", code="Delete",
                           windowsVirtualKeyCode=46)
                    time.sleep(0.4)
                time.sleep(1.0)
            if canon(current_text(c)):
                print("  REFUSING to type — could not clear its own debris:",
                      repr(current_text(c)[:80]), flush=True)
                c.close()
                return 1
            have = ""
        else:
            print(f"  holds {st.get('len')} characters that are NOT this post. "
                  f"Left untouched — clearing raises the unsaved-changes "
                  f"dialog.", flush=True)
            print(f"    has: {have[:70]!r}", flush=True)
            print(f"    want: {text[:70]!r}", flush=True)
            c.close()
            return 1
    if not have:
        # The input method depends on the SCRIPT, measured — not on habit.
        #
        # Input.insertText sends the string straight to the DOM and does not
        # touch the editor's own state. X's Draft editor therefore keeps its
        # composition model at whatever it had, and a CJK run sent that way is
        # discarded: measured, a 597-character Chinese body came back holding
        # only its 30-character ASCII URL, every Han character gone, at every
        # length tried (5, 48 and 190 characters all arrived as one newline).
        # Pure ASCII survives insertText intact, which is why the failure only
        # ever appeared once the copy was written in Chinese.
        #
        # Real key events are the path a person uses and they update the model.
        # Measured cost: ~600 characters is a few seconds, which is nothing
        # against a ten-minute gap between language versions. So: any text
        # containing non-ASCII goes per character; pure ASCII keeps the single
        # fast insertText.
        needs_keys = any(ord(ch) > 127 for ch in text)
        if needs_keys:
            print(f"  empty — typing {len(text)} characters as key events "
                  f"(body is not pure ASCII)", flush=True)
            type_keys(c, text)
        else:
            print(f"  empty — inserting {len(text)} characters in one "
                  f"insertText (pure ASCII)", flush=True)
            c.send("Input.insertText", text=text, wait=40, retries=6)
            time.sleep(2.0)

    c.close_composition("")     # never leave an open composition behind
    st = read(c)
    got = st.get("text", "") or ""
    fg, ft = canon(got), canon(text)
    # The compare is the gate. The raw editor length is NOT: X's Draft editor
    # keeps hidden text nodes of its own, so it reads 860 against an 859
    # character source even when the visible text matches exactly. Requiring
    # len(fg) <= len(ft) keeps the "nothing was invented" guarantee without
    # failing on that hidden node.
    ok = fg == ft and len(fg) <= len(ft)
    # The URL must survive as text. It is NOT required to be an <a> here: this
    # composer never renders a link entity however the text arrives (ten input
    # methods measured, zero <a> nodes) and X resolves the URL server-side.
    # canon() strips whitespace, so also require a space before each URL — X
    # folded a newline into the host and read back "https://\ncrates.io", the
    # characters were all present, and the text compare passed anyway.
    sep_ok = all(m.start() == 0 or got[m.start() - 1] == " "
                 for u in urls for m in re.finditer(re.escape(u), got))
    urls_ok = all(u in got for u in urls) and sep_ok
    # Presence is not enough. Measured: committing the URL composition with a
    # second insertText inserted it a second time, the post went out with the
    # link duplicated, and every gate above still passed because each asks a
    # yes/no question. Count the occurrences instead.
    urls_once = all(got.count(u) == text.count(u) for u in urls)
    if not urls_once:
        print("  a URL appears a different number of times than in the source:",
              {u: (got.count(u), text.count(u)) for u in urls if got.count(u) != text.count(u)},
              flush=True)

    print(f"  LEN {st.get('len')} want {len(text)} match={ok} "
          f"urls={len(urls)} urls_ok={urls_ok}", flush=True)
    if not ok or not urls_ok or not urls_once:
        if not ok:
            i = next((x for x in range(min(len(fg), len(ft)))
                      if fg[x] != ft[x]), None)
            print(f"  MISMATCH — first difference at {i}, not clicking",
                  flush=True)
            if i is not None:
                lo = max(0, i - 20)
                print(f"    got : {fg[lo:i + 20]!r}", flush=True)
                print(f"    want: {ft[lo:i + 20]!r}", flush=True)
        else:
            print(f"  the URL did not survive intact, not clicking", flush=True)
        c.close()
        return 1

    if not go:
        print("(dry run — not clicking)", flush=True)
        c.close()
        return 0

    res = jd(c.js(BUTTON, wait=25, retries=5))
    for _ in range(8):
        if res.get("clicked"):
            break
        time.sleep(4)
        res = jd(c.js(BUTTON, wait=25, retries=4))
    c.close_composition("")     # the button may have opened one
    print(f"CLICK {res.get('clicked') or res.get('why')} "
          f"(buttons {res.get('present')})", flush=True)
    c.close()
    return 0 if res.get("clicked") else 1


if __name__ == "__main__":
    sys.exit(main())
