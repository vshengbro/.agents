---
name: findmy
description: "Use when locating an Apple device, item, or AirTag through Find My on macOS. 查找 定位 设备 位置。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
---

# Find My (Apple)

Apple ships no Find My CLI or API, and FindMy.app has **no AppleScript
dictionary** (no `.sdef`, no `OSAScriptingDefinition` — verified on this
machine). The only route is UI automation plus reading the screen. Do not write
AppleScript that "tells FindMy to do something" — it exposes no commands.

Sibling skills: Notes → `apple-notes`, Reminders → `apple-reminders`,
messages → `imessage`.
## Index

Prerequisites · Method A — screenshot + vision (no extra tools) · Method B — peekaboo (preferred when installed) · Switching Devices ↔ Items · Rules · Resource lifecycle


## Prerequisites

* macOS with Find My installed and iCloud signed in, with the devices/AirTags
  already enrolled in Find My
* Screen Recording permission for the terminal that captures the window
  (System Settings → Privacy & Security → Screen Recording), granted and the
  terminal reopened
* Optional but better: `brew install openclaw/tap/peekaboo` for AX-driven
  clicking and annotated captures

```bash
pgrep -x FindMy                          # already running?
ls -d /System/Applications/FindMy.app     # bundle id: com.apple.findmy
```

## Method A — screenshot + vision (no extra tools)

```bash
open -a FindMy
screencapture -o -l <windowid> "$TMPDIR/findmy.png"   # -o drops the window shadow
```

Take `<windowid>` from `peekaboo window list --app FindMy --json`, or use
`screencapture -i` for manual selection. Then read the pixels:

```
vision_analyze(image_url="<path>", question="Which device or item is selected, and what location, address, timestamp, and accuracy does Find My show?")
```

Quote the accuracy figure and the timestamp in your answer. "Found near the
office" without them is a guess.

## Method B — peekaboo (preferred when installed)

```bash
peekaboo see --app FindMy --annotate --path "$TMPDIR/findmy-ui.png" --json
peekaboo click --on <element_id> --app FindMy      # ids come from the `see` JSON
peekaboo see --app FindMy --path "$TMPDIR/findmy-detail.png" --json
```

Then `vision_analyze` the detail capture with the question above. Peekaboo needs
Screen Recording for pixels and Accessibility for the element map; without both,
element detection returns nothing.

Generic macOS UI automation unrelated to Find My belongs to `computer-use`.

## Switching Devices ↔ Items

AirTags live under **Items**; iPhones, iPads, and Macs under **Devices**. Click
the tab through peekaboo's element tree. Do not hand-roll
`click button "Devices" of toolbar 1` — FindMy.app's accessibility hierarchy is
not stable across macOS versions and that selector silently stops matching.

## Rules

1. Track only devices and items the user owns or is authorized to locate.
   Location data is sensitive: capture no wider a view than the question needs,
   and do not keep screenshots around.
2. Never invent a location. If the capture shows no fix, an old timestamp, or
   poor accuracy, report exactly that.
3. AirTag positions refresh only while Find My is open and online. A stale or
   offline marker is the expected failure, not something to work around.
4. Every screenshot is a file you created: write under `$TMPDIR` or scratch,
   never into the user's Documents, and delete it when the task ends.

## Resource lifecycle

* `peekaboo` — record the exact PID; on completion, failure, timeout, or cancel,
  kill that PID (or `peekaboo daemon stop` for a daemon you started). Never
  `pkill peekaboo` — a daemon or session the user owns is not yours.
* `screencapture` finishes on its own; nothing to reap, but do delete its PNGs.
* A long "watch this AirTag" loop is a background process you spawned: register
  its PID and stop that exact PID when the user says stop. Prefer a `cronjob`
  over a hand-rolled `while true` sleep loop.
* Don't leave Find My frontmost for the user — quit it if you launched it and
  they didn't ask for it to stay open.
