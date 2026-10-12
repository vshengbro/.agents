#!/usr/bin/env python3
"""Attach an image or a video to the NEXT post, through the composer, and stop.

This file stages media and nothing else. It opens the composer, hands X a
file, watches the preview appear, optionally types alt text, and then LEAVES
the composer holding all of it. publish.py (a new post) or post_reply.py (a
reply) is what sends, and the send is verified there. A script that attached
media AND published it could no longer tell "the attachment went out" from
"the post went out", which is the same class of mistake this skill has already
made in other shapes — and media is the one thing where it costs the most,
because a post that shipped without its picture still reads as a successful
post in a log.

THE FILE IS HANDED OVER THROUGH CDP, AND THAT IS THE ONLY ROUTE LEFT.

    X mounts a real input[type=file] behind the composer's media button, and
    the only way to put a path into it from outside the page is
    DOM.setFileInputFiles with the input's nodeId. Everything else was taken
    off the table by the skill's own rules before this file was written:
    pbcopy/pbpaste and the clipboard are banned because paste hangs here and
    bypasses Draft's own input path; an OS file dialog is not ours to drive at
    all; Input.dispatchMouseEvent is banned because the user's pointer is
    never taken; Page.bringToFront is banned for the same reason. So the
    route is: click the media control that is already on screen, find the
    input X mounted because of that click, and set its files over CDP.

  * Three selectors in this file are UNVERIFIED, and all three are the ones
    that carry the whole route: MEDIA_TESTID ("media") is the media button,
    the ALT selectors are the alt-text control and its field, and the
    reliance on X mounting a DOM-addressable input[type=file] inside the
    composer has never been measured on this build. Nothing in this skill has
    ever attached a file. They are written so that being wrong is legible
    rather than silent — a button that is not found dumps every control the
    composer really carries, and a file input that is not found is a refusal
    (NO FILE INPUT), never a continue.

  * The file is validated before the browser is touched at all, and the two
    refusals are hard: NO SUCH FILE and UNSUPPORTED TYPE. A typo that reached
    the page would leave the media button doing nothing and the run reporting
    a composer that mysteriously refused the file; it costs nothing to catch
    here, so it is caught here. --check prints the plan and stops there, and
    it still enforces the type: the extension is wrong regardless of what the
    caller intended to do with it.

  * A file that does not attach is NOT ATTACHED and exits non-zero, and a
    file that attaches without its requested alt text is ALT NOT SET and also
    exits non-zero. An unattached file that a later publish.py then posts
    without its picture is the worst outcome available to this script, so
    every failure says which of the two states the composer is actually in
    and no failure path is allowed to stay quiet.

  * Scoping the media to the composer's own dialog is not tidiness. A bare
    input[type=file] query over the whole page finds the avatar uploader on
    some surfaces, and setting files on THAT starts an avatar change on the
    account. The file input is only taken from inside the composer, and the
    one page-wide fallback is allowed only when exactly one file input exists
    and no other dialog is open, which is a condition written to be unlikely
    rather than a condition written to be convenient.

  * Nothing here sends, navigates, reloads, opens a tab, clears a composer,
    takes the mouse, takes the OS keyboard, or touches the clipboard, which is
    what lets the commit gate allow the file at all.

  python3 x_media.py PATH [--alt TEXT] [--video] [--check]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit                                                # noqa: E402

# What each kind accepts. X's own accept strings are narrower than this and
# wider on different surfaces, so the list is the union the skill is willing
# to try, and everything else is refused before the browser is opened.
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif")
VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm")


# --- the composer's own box --------------------------------------------
# The composer box is the visible [role="dialog"] holding a visible Draft
# editor, else the editor's own form — the same scope xkit.SEND_IN_BOX picks
# the send control in, so the media is staged in the box that would send it.
# Reached through xkit.DRAFT_CLS rather than a copy of the class name.
SCOPE_JS = """\
  const scope = () => {
    const cls = %s;
    const dialogs = [...document.querySelectorAll('[role="dialog"]')]
      .filter(d => d.offsetParent !== null
                   && d.querySelector('[data-testid="tweetTextarea_0"]'));
    const eds = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
      .filter(n => n.className && n.className.indexOf(cls) >= 0
                   && n.offsetParent !== null);
    if (dialogs.length) {
      return eds.length ? (dialogs.find(d => d.contains(eds[0])) || dialogs[0])
                        : dialogs[0];
    }
    return eds.length ? (eds[0].closest('form') || eds[0].parentElement) : null;
  };
  // offsetParent is null for a position:fixed node, and the desktop side
  // bar's controls are fixed, so a rect test is added beside it rather than
  // instead of it.
  const shown = (n) => {
    if (!n) return false;
    if (n.offsetParent !== null) return true;
    const r = n.getBoundingClientRect();
    return r.width > 0 && r.height > 0
           && r.bottom > 0 && r.top < window.innerHeight;
  };""" % json.dumps(xkit.DRAFT_CLS)

# The three compose controls, in publish.py's order, picking the first VISIBLE
# one. Clicking a control that is already on screen is allowed; a page load is
# not, and this loads nothing.
OPEN_COMPOSER = """(() => {
  const shown = (n) => {
    if (!n) return false;
    if (n.offsetParent !== null) return true;
    const r = n.getBoundingClientRect();
    return r.width > 0 && r.height > 0
           && r.bottom > 0 && r.top < window.innerHeight;
  };
  const want = ['[data-testid="SideNav_NewTweet_Button"]',
                '[data-testid="SideNav_NewTweetButton"]',
                'a[href*="/compose/post"]',
                '[data-testid="appTabBarPostBtn"]'];
  for (const s of want) {
    const hit = [...document.querySelectorAll(s)].filter(shown)[0];
    if (!hit) continue;
    const r = hit.getBoundingClientRect();
    if (r.top < 0 || r.top > window.innerHeight) {
      // Scrolled rather than clicked: a control 31000px below the fold takes
      // a click on nothing, which is how an open once and produced no box.
      window.scrollTo(0, Math.max(0,
        window.scrollY + r.top - window.innerHeight / 2));
      return {clicked: false, why: s + ' was off screen, scrolled to it'};
    }
    hit.click();
    return {clicked: true, which: s};
  }
  return {clicked: false, why: 'no compose control on this page'};
})()"""


# --- the media button (UNVERIFIED testid) -------------------------------
# UNVERIFIED: "media" is the composer's add-photos control, taken from the
# browser-automation reference notes. No script in this skill has clicked one.
# The aria-label patterns are the same guess by another route (X labels the
# control 添加照片和视频 / Add photos and video), so the two agreeing is not
# two pieces of evidence. GIF and poll controls sit in the same row and are
# NOT wanted here, so the image label is tried before the video one and the
# hit is reported back so a wrong pick is visible in the log.
MEDIA_TESTID = "media"
MEDIA_BUTTON = """(() => {
  __SCOPE__
  const sc = scope();
  if (!sc) return {clicked: false, why: 'no composer box on this page'};
  const nodes = [...sc.querySelectorAll(
    'button, [role="button"], [data-testid]')].filter(shown);
  const label = (n) => ((n.getAttribute('aria-label') || '') + ' '
    + (n.getAttribute('data-tooltip-content') || '')).toLowerCase();
  const bytestid = nodes.find(n => n.dataset.testid === %s);
  const byimage = nodes.find(n => /照片|图片|图像|photo|image|media/
                                  .test(label(n)));
  const byvideo = nodes.find(n => /视频|video/.test(label(n)));
  const hit = bytestid || byimage || byvideo;
  if (!hit) {
    return {clicked: false, why: 'no media button in this composer',
      testids: [...new Set([...sc.querySelectorAll('[data-testid]')]
                .map(n => n.dataset.testid))].slice(0, 24),
      labels: [...sc.querySelectorAll('[aria-label]')]
                .map(n => n.getAttribute('aria-label'))
                .filter(Boolean).slice(0, 24)};
  }
  const r = hit.getBoundingClientRect();
  if (r.top < 0 || r.top > window.innerHeight) {
    window.scrollTo(0, Math.max(0,
      window.scrollY + r.top - window.innerHeight / 2));
    return {clicked: false,
            why: 'the media button was off screen, scrolled to it'};
  }
  hit.click();
  return {clicked: true, which: hit.dataset.testid || label(hit) || '?',
          aria: hit.getAttribute('aria-label') || ''};
})()"""


# --- the file input ----------------------------------------------------
# Mark ONE input so the CDP query below can address it by attribute instead
# of by position. setAttribute is not clearing anything; the marker is removed
# on the way out.
MARK_FILE_INPUT = """(() => {
  __SCOPE__
  document.querySelectorAll('[data-x-media-target]').forEach(
    n => n.removeAttribute('data-x-media-target'));
  const all = [...document.querySelectorAll('input[type="file"]')];
  const sc = scope();
  let pick = null, tier = '';
  if (sc) {
    pick = all.filter(n => sc.contains(n))[0] || null;
    if (pick) tier = 'inside the composer';
  }
  if (!pick) {
    const form = sc ? sc.closest('form') : null;
    if (form) {
      pick = [...form.querySelectorAll('input[type="file"]')][0] || null;
      if (pick) tier = "inside the composer's form";
    }
  }
  if (!pick && all.length === 1) {
    // The page-wide fallback exists only when it cannot be a second input:
    // an avatar or DM uploader is reachable only with its own dialog open, so
    // a lone input with no other dialog mounted is this composer's.
    const other = [...document.querySelectorAll('[role="dialog"]')]
      .filter(d => d.offsetParent !== null
                   && !d.querySelector('[data-testid="tweetTextarea_0"]'));
    if (!other.length) { pick = all[0]; tier = 'the only input on the page'; }
  }
  if (!pick) {
    return {ok: false, why: all.length
      ? ('no file input inside the composer; the page has ' + all.length
         + ' elsewhere and they are not ours to fill')
      : 'no input[type=file] anywhere on this page', total: all.length};
  }
  pick.setAttribute('data-x-media-target', '1');
  return {ok: true, tier: tier, total: all.length,
          accept: pick.getAttribute('accept') || '',
          multiple: pick.multiple === true};
})()"""

# A media preview inside the composer: a rendered blob-backed image, a video,
# or any element whose testid reads like an attachment. The file input is NOT
# evidence — it stays in the DOM whether or not X accepted the file, which is
# exactly the thing that must not be read as success.
PREVIEW = """(() => {
  __SCOPE__
  const sc = scope();
  if (!sc) return JSON.stringify({found: false, why: 'no composer box'});
  const img = [...sc.querySelectorAll('img[src^="blob:"]')].filter(shown)[0];
  const vid = [...sc.querySelectorAll('video')].filter(shown)[0];
  const named = [...sc.querySelectorAll('[data-testid]')].filter(n =>
    shown(n) && /photo|video|media|attachment|player/i.test(n.dataset.testid));
  const hit = img || vid || named[0];
  if (!hit) {
    return JSON.stringify({found: false, why: 'no preview element',
      testids: [...new Set([...sc.querySelectorAll('[data-testid]')]
                .map(n => n.dataset.testid))].slice(0, 24),
      inputs: sc.querySelectorAll('input[type="file"]').length});
  }
  return JSON.stringify({found: true,
    kind: img ? 'image' : (vid ? 'video' : 'element'),
    which: hit.dataset ? (hit.dataset.testid || hit.nodeName)
                       : hit.nodeName,
    src: (hit.getAttribute && hit.getAttribute('src') || '').slice(0, 40),
    testids: [...new Set(named.map(n => n.dataset.testid))].slice(0, 8)});
})()"""


# --- alt text (UNVERIFIED selectors) -----------------------------------
# UNVERIFIED: no script here has opened X's alt-text dialog. X labels the
# control 添加替代文字 / Add alt text and prints ALT on the preview; the dialog
# it opens holds a textarea on some builds and a Draft editor on others, so
# both are accepted and what was actually typed into is READ BACK afterwards
# rather than assumed.
ALT_CONTROL = """(() => {
  __SCOPE__
  const sc = scope();
  if (!sc) return {clicked: false, why: 'no composer box on this page'};
  const text = (n) => ((n.innerText || '') + ' '
    + (n.getAttribute('aria-label') || '') + ' '
    + (n.getAttribute('data-tooltip-content') || '')).toLowerCase();
  const nodes = [...sc.querySelectorAll(
    'button, [role="button"], [data-testid], div')].filter(shown);
  const hit = nodes.find(n => /添加替代文字|添加替代文本|替代文字|替代文本/
                              .test(text(n)))
             || nodes.find(n => /(^|\\s)alt(\\s|$)/.test(text(n)))
             || nodes.find(n => /add alt text|alt text/.test(text(n)));
  if (!hit) {
    return {clicked: false, why: 'no alt-text control on the preview',
      testids: [...new Set([...sc.querySelectorAll('[data-testid]')]
                .map(n => n.dataset.testid))].slice(0, 24),
      labels: [...sc.querySelectorAll('[aria-label]')]
                .map(n => n.getAttribute('aria-label'))
                .filter(Boolean).slice(0, 24)};
  }
  hit.click();
  return {clicked: true, which: (hit.innerText || '').trim().slice(0, 24)
                          || hit.getAttribute('aria-label') || '?'};
})()"""

# The alt dialog is the newest visible dialog that is NOT the composer and
# holds a text field; the composer's own editor is excluded by its testid.
ALT_FIELD = """(() => {
  const ds = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && !d.querySelector('[data-testid="tweetTextarea_0"]'))
    .filter(d => d.querySelector('textarea')
                 || d.querySelector('[contenteditable="true"]'));
  const d = ds[ds.length - 1];
  if (!d) return {found: false, why: 'no alt-text dialog is open'};
  const ta = d.querySelector('textarea');
  const ce = [...d.querySelectorAll('[contenteditable="true"]')][0];
  const f = ta || ce;
  if (!f) return {found: false, why: 'the alt dialog has no text field'};
  f.focus();
  return {found: true, tag: f.nodeName.toLowerCase(),
          text: ta ? (ta.value || '') : (f.innerText || '')};
})()"""

# The alt dialog applies on its own confirm control; typing into the field
# alone leaves the text unapplied and the dialog covering the composer.
ALT_CONFIRM = """(() => {
  const ds = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && !d.querySelector('[data-testid="tweetTextarea_0"]'));
  const d = ds[ds.length - 1];
  if (!d) return {clicked: false, why: 'the alt dialog already closed'};
  const txt = (n) => ((n.innerText || '') + ' '
    + (n.getAttribute('aria-label') || '')).toLowerCase();
  const hit = [...d.querySelectorAll('button, [role="button"]')]
    .filter(n => n.offsetParent !== null)
    .find(n => /完成|保存|应用|确定|done|save|apply|ok/.test(txt(n)));
  if (!hit) return {clicked: false,
                    why: 'the alt dialog has no confirm control',
                    buttons: [...d.querySelectorAll('button')]
                      .map(n => (n.innerText || '').trim()).slice(0, 12)};
  hit.click();
  return {clicked: true, which: (hit.innerText || '').trim()
                          || hit.getAttribute('aria-label') || '?'};
})()"""

ALT_STILL_OPEN = """(() => {
  const ds = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && !d.querySelector('[data-testid="tweetTextarea_0"]'))
    .filter(d => d.querySelector('textarea')
                 || d.querySelector('[contenteditable="true"]'));
  return ds.length > 0;
})()"""


# --- plumbing -----------------------------------------------------------

def tpl(text: str) -> str:
    """A template with the composer-scope helpers spliced in."""
    return text.replace("__SCOPE__", SCOPE_JS)


def cdp_ok(res) -> bool:
    """True when a raw cdp.send() returned a result and not an error marker."""
    return isinstance(res, dict) and not any(
        k in res for k in ("__socket_error", "__cdp_error", "__timeout"))


def cdp_why(res) -> str:
    """Why a raw send() failed, named. A dict printed raw reads as noise."""
    if isinstance(res, dict):
        for k in ("__cdp_error", "__socket_error", "__timeout"):
            if k in res:
                return "%s: %s" % (k[2:], str(res[k])[:140])
    return "no reply to the CDP call (timeout)" if res is None \
        else str(res)[:140]


def validate(raw: str, want_video: bool):
    """The file, checked with zero browser contact, or None after printing why.

    Existence first, then the extension: the extension is what X will reject,
    and a path that does not exist cannot have a type worth discussing. The
    order is also what makes the two verification cases read the way they do —
    /etc/hosts.jpg never gets far enough to be called an image.
    """
    path = os.path.expanduser(raw)
    ext = os.path.splitext(path)[1].lower()
    if not os.path.exists(path):
        print("NO SUCH FILE %s" % path, flush=True)
        return None
    if not os.path.isfile(path):
        print("NOT A FILE %s" % path, flush=True)
        return None
    if not os.access(path, os.R_OK):
        print("NOT READABLE %s" % path, flush=True)
        return None
    allowed = VIDEO_EXTS if want_video else IMAGE_EXTS
    if ext not in allowed:
        print("UNSUPPORTED TYPE %s — images: %s / video: %s"
              % (ext or "(no extension)", " ".join(IMAGE_EXTS),
                 " ".join(VIDEO_EXTS)), flush=True)
        return None
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        print("NOT READABLE %s — %s" % (path, exc), flush=True)
        return None
    return {"path": os.path.abspath(path), "ext": ext, "size": size,
            "kind": "video" if want_video else "image"}


def open_composer(c) -> dict:
    """Open the composer by clicking the control already on screen."""
    got = xkit.js(c, OPEN_COMPOSER)
    if not got.get("clicked"):
        # It may have been below the fold, which the click scrolls to and then
        # answers. One more pass, and nothing is clicked twice.
        time.sleep(1.2)
        again = xkit.js(c, OPEN_COMPOSER)
        got = again if again.get("clicked") else got
    return got


def set_files(c, info: dict) -> dict:
    """Mark the composer's file input, then put the path into it over CDP.

    The attribute mark is what makes the nodeId lookup unambiguous: a page
    query for input[type=file] by index would be answering a question about
    the DOM order, and X re-renders the composer freely, so the node this
    script measured seconds ago may not be the node the next call addresses.
    """
    marked = xkit.js(c, tpl(MARK_FILE_INPUT))
    if not marked.get("ok"):
        return {"ok": False, "why": marked.get("why") or "no file input"}

    doc = c.send("DOM.getDocument", depth=1, wait=25)
    if not cdp_ok(doc):
        return {"ok": False, "why": "DOM.getDocument — %s" % cdp_why(doc)}
    root = (doc.get("root") or {}).get("nodeId")
    if not root:
        return {"ok": False, "why": "DOM.getDocument returned no root node"}

    found = c.send("DOM.querySelectorAll", wait=25, nodeId=root,
                   selector='[data-x-media-target]')
    if not cdp_ok(found):
        return {"ok": False, "why": "DOM.querySelectorAll — %s"
                                  % cdp_why(found)}
    ids = found.get("nodeIds") or []
    if not ids:
        # The mark was set through Runtime and the tree was pushed after it,
        # so a miss here means the attribute never landed; once more, from a
        # fresh document.
        doc2 = c.send("DOM.getDocument", depth=1, wait=25)
        if cdp_ok(doc2):
            root2 = (doc2.get("root") or {}).get("nodeId")
            if root2:
                again = c.send("DOM.querySelectorAll", wait=25, nodeId=root2,
                               selector='[data-x-media-target]')
                if cdp_ok(again):
                    ids = again.get("nodeIds") or []
    if not ids:
        return {"ok": False, "why": "the marked file input is not in the "
                                    "pushed document tree"}

    # The ONE call that does the work. No clipboard, no OS dialog, no mouse.
    done = c.send("DOM.setFileInputFiles", wait=40, files=[info["path"]],
                  nodeId=ids[0])
    if not cdp_ok(done):
        return {"ok": False, "nodeId": ids[0],
                "why": "DOM.setFileInputFiles — %s" % cdp_why(done)}
    return {"ok": True, "tier": marked.get("tier"),
            "accept": marked.get("accept"), "multiple": marked.get("multiple"),
            "nodeId": ids[0]}


def wait_preview(c, tries: int = 25, pause: float = 0.8):
    """A rendered preview inside the composer, or the last thing it did show."""
    last = {"found": False, "why": "not looked at"}
    for _ in range(tries):
        last = xkit.js(c, tpl(PREVIEW))
        if last.get("found"):
            return last
        time.sleep(pause)
    return last


def set_alt(c, alt: str) -> dict:
    """Type alt text into X's alt dialog and apply it. One dict, always.

    Every branch returns {"ok": bool, "why": str, ...} so a caller cannot
    read a success out of a tuple it unpacked wrongly.
    """
    clicked = xkit.js(c, tpl(ALT_CONTROL))
    if not clicked.get("clicked"):
        return {"ok": False, "which": clicked.get("which"),
                "why": clicked.get("why") or "no alt-text control on the "
                                           "preview",
                "testids": clicked.get("testids"),
                "labels": clicked.get("labels")}

    field = {}
    for _ in range(12):
        field = xkit.js(c, ALT_FIELD)
        if field.get("found"):
            break
        time.sleep(0.7)
    if not field.get("found"):
        return {"ok": False, "which": clicked.get("which"),
                "why": field.get("why") or "the alt dialog never opened"}

    # xkit's normal key-event path, unmodified: ASCII goes in as one
    # insertText, anything else per character. The warm-up space and the
    # first-character swallow are that helper's problem and are not re-derived
    # here; the read-back below is what catches it if the helper is wrong.
    xkit.type_body(c, alt, existing=field.get("text") or "")

    after = {}
    for _ in range(8):
        after = xkit.js(c, ALT_FIELD)
        if after.get("found") and \
                xkit.canon(after.get("text") or "") == xkit.canon(alt):
            break
        time.sleep(0.7)
    if xkit.canon((after or {}).get("text") or "") != xkit.canon(alt):
        return {"ok": False, "which": clicked.get("which"),
                "why": "the alt field reads back as %r, not %r — the text did "
                       "not land" % ((after or {}).get("text") or "", alt)}

    confirmed = xkit.js(c, ALT_CONFIRM)
    still = True
    for _ in range(8):
        still = bool(xkit.js_raw(c, ALT_STILL_OPEN))
        if not still:
            break
        time.sleep(0.7)
    return {"ok": True, "which": clicked.get("which"),
            "confirm": confirmed.get("which") if confirmed.get("clicked")
            else None, "still_open": still,
            "why": "" if not still else
            "the alt text is typed but the dialog is still open — confirm it "
            "by hand"}


def run(c, args, info: dict, me: str) -> int:
    """Everything after the file is known good. Returns 0 only if it is in."""
    who = me or "(handle not readable)"
    opened = open_composer(c)
    if not opened.get("clicked"):
        return xkit.die("NO COMPOSER - open the composer yourself and re-run"
                        "\n  last click attempt: %s" % opened.get("why"))

    ed = xkit.the_editor(c, tries=10, pause=1.5)     # ~15s
    if not ed:
        return xkit.die("NO COMPOSER - open the composer yourself and re-run")

    print("  composer open for @%s (editor holds %s characters, in a dialog: "
          "%s)" % (who, ed.get("len"), ed.get("in_dialog")), flush=True)

    btn = xkit.js(c, tpl(MEDIA_BUTTON).replace("%s", json.dumps(
        MEDIA_TESTID)))
    if not btn.get("clicked"):
        print("  MEDIA BUTTON NOT FOUND — the composer's real controls are: "
              "testids=%s labels=%s"
              % (btn.get("testids") or [], btn.get("labels") or []),
              flush=True)
        print("  UNVERIFIED selector %r did not match; attaching anyway is "
              "refused rather than guessed at" % MEDIA_TESTID, flush=True)
        return xkit.die("NO FILE INPUT - the media button was not found, so X "
                        "was never asked to mount a file input\n"
                        "  attach the file by hand and re-run")
    print("  media control clicked (%s%s)" % (btn.get("which"),
                                              (" / " + btn["aria"])
                                              if btn.get("aria") else ""),
          flush=True)

    # X mounts the input when the media control is used; give it a moment
    # before asking, because a query run too early reads as "X has no file
    # input" and that is a different failure from the real one.
    time.sleep(1.5)
    put = set_files(c, info)
    if not put.get("ok"):
        return xkit.die("NO FILE INPUT - X did not mount an input[type=file] in "
                        "the composer; attach the file by hand and re-run"
                        "\n  %s" % put.get("why"))
    print("  file handed to node %s (%s%s)" % (put.get("nodeId"),
                                               put.get("tier") or "?",
                                               ", accepts " + put["accept"]
                                               if put.get("accept") else ""),
          flush=True)

    prev = wait_preview(c)
    if not prev.get("found"):
        print("  composer holds: testids=%s, file inputs=%s"
              % (prev.get("testids") or [], prev.get("inputs")), flush=True)
        return xkit.die("NOT ATTACHED - the file did not appear in the "
                        "composer\n  %s" % (prev.get("why") or "no preview"))

    if args.alt:
        alt = set_alt(c, args.alt)
        if not alt.get("ok"):
            print("  alt control: %s" % (alt.get("which") or "not found"),
                  flush=True)
            if alt.get("testids"):
                print("  composer testids: %s" % alt["testids"], flush=True)
            if alt.get("labels"):
                print("  composer labels: %s" % alt["labels"], flush=True)
            # The attachment DID land and is still staged; the alt text did
            # not. Both facts are printed, and the exit code is non-zero
            # because an alt text that was asked for and not set is a silent
            # failure at the far end of the pipeline.
            print("ATTACHED %s (%s)" % (info["path"], info["kind"]), flush=True)
            return xkit.die("ALT NOT SET - %s\n  the media IS attached and "
                            "still in the composer; publish.py can send it "
                            "without alt text, or type the alt by hand"
                            % alt.get("why"))
        print("  alt dialog: control %s, confirm %s"
              % (alt.get("which"), alt.get("confirm") or "NOT FOUND"),
              flush=True)
        if alt.get("still_open"):
            print("  NOTE - %s" % alt.get("why"), flush=True)
        print("ALT SET %s" % args.alt, flush=True)

    # The marker this script set is cleared at the start of every run by the
    # same template that sets it, so a stale one can never be found by a
    # later run and the composer is left holding nothing but the media.
    print("ATTACHED %s (%s)" % (info["path"], info["kind"]), flush=True)
    print("  staged only — nothing was sent. publish.py / post_reply.py send "
          "it and verify the post.", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Attach an image or video to the NEXT post, in the "
                    "composer. Does not send.")
    ap.add_argument("path", help="the media file to attach")
    ap.add_argument("--alt", help="alt / accessibility text for the media")
    ap.add_argument("--video", action="store_true",
                    help="treat the file as video; otherwise as an image")
    ap.add_argument("--check", action="store_true",
                    help="validate the file, print the plan, touch nothing")
    args = ap.parse_args()

    # Every refusal happens here, before a browser connection exists. A gate
    # that costs nothing should not cost a connection, and a typo must never
    # reach the page — including under --check, where the type is still wrong
    # whatever the caller meant to do with it.
    info = validate(args.path, args.video)
    if info is None:
        return 1

    if args.check:
        print("CHECK OK — nothing was touched, no composer was opened.")
        print("  file  %s" % info["path"])
        print("  size  %d bytes" % info["size"])
        print("  type  %s (%s)" % (info["kind"], info["ext"]))
        print("  alt   %s" % ("given: %r" % args.alt if args.alt
                              else "not given — the media will post with no "
                                   "alt text"))
        return 0

    # xkit.connect prints why it could not and returns None; the guard around
    # it is here because a browser that is not running answers the port with a
    # refused connection, which must not reach the caller as a traceback.
    try:
        c, _tab, me = xkit.connect()
    except Exception as exc:
        print("  %s: %s" % (type(exc).__name__, str(exc)[:90]), flush=True)
        return xkit.die("NOT ATTACHED %s — cannot reach the browser to drive "
                        "it.\n  %s" % (info["path"], xkit.no_browser()))
    if c is None:
        return xkit.die("NOT ATTACHED %s" % info["path"])

    try:
        return run(c, args, info, me)
    except Exception as exc:
        return xkit.die("NOT ATTACHED %s — aborted on %s: %s\n  the composer "
                        "was left as it was; nothing is claimed about the "
                        "attachment"
                        % (info["path"], type(exc).__name__, str(exc)[:120]))
    finally:
        try:
            c.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(0 if main() == 0 else 1)
