#!/usr/bin/env python3
"""Post the next item from a queue, once. Idempotent — one item per invocation.

A cron job runs this every minute, so the spacing between posts is the cron's
interval rather than anything here. It picks the first item not yet posted,
publishes it, and records the result only when the publisher actually clicked,
so a missed or failed tick does not repost and a duplicate tick does not
double-post. When the queue empties it says so and does nothing, which is how
a single nightly run knows it is finished.

Every rule the publisher obeys is in the x-post-via-browser skill and enforced
by verify_no_unsafe_posting.py. Nothing here opens a tab, navigates, reloads
or clears the composer: the browser tab must already be on x.com, and if it is
not the publisher says so and posts nothing.

  X_COPY=/path/to.json X_POST_STATE=/path/to/state.json \
      python3 run_queue_tick.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PUBLISH = HERE / "publish.py"
VERIFY = HERE / "verify_post.py"
WHOSE = HERE / "whose_posts.py"

# Every value below is resolved INSIDE the function that reads it. A
# module-level constant is frozen at import, which is a live bug here and not
# a style preference: a cron wrapper commonly exports X_POST_STATE or X_PORT
# after this module is in the import chain, and a frozen constant silently
# ignores it — the run then reads and writes the wrong state file, or drives a
# different browser than the caller asked for, with nothing in the output that
# says so.


def copy_file() -> Path:
    """X_COPY, else the example copy beside these scripts."""
    return Path((os.environ.get("X_COPY") or "").strip()
                or str(HERE / "x_copy_example.json")).expanduser()


def state_file() -> Path:
    """X_POST_STATE, else a state file beside the scripts.

    Beside the scripts and not under one developer's home directory: a path
    that only exists on the machine it was written on makes every other
    machine silently start from an empty queue, which republishes items that
    were already posted.
    """
    return Path((os.environ.get("X_POST_STATE") or "").strip()
                or str(HERE / "x_post_state.json")).expanduser()


def run(script: Path, args: list[str], timeout: int = 420) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(script)] + args,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except ValueError:
            pass
    return {"posted": []}


def save_state(path: Path, s: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(s, ensure_ascii=False, indent=1))


def newest_status(port: str) -> str:
    """The id of my own most recent post, or "" — the page may show others'."""
    rc, out = run(WHOSE, [port], timeout=180)
    for line in out.splitlines():
        if "MINE" in line:
            parts = line.split()
            return parts[1] if len(parts) > 1 else ""
    return ""


def main() -> int:
    import xconfig

    port = str(int(sys.argv[1])) if len(sys.argv) > 1 else str(xconfig.port())
    copy = copy_file()
    state_path = state_file()
    posts = json.loads(copy.read_text())
    state = load_state(state_path)
    done = set(state["posted"])

    if len(done) >= len(posts):
        print(f"queue is empty — all {len(posts)} items already posted")
        return 0

    idx = next(i for i in range(len(posts)) if i not in done)
    head = posts[idx].splitlines()[0][:56]
    print(f"posting {idx + 1}/{len(posts)}: {head}")

    rc, out = run(PUBLISH, [port, "--post", str(idx), "--go"])
    print(out.strip()[-1200:])

    # The publisher exits 0 even when it declines to click, so the decision is
    # made on its own words. CLICKED is not proof either — the timeline is.
    if "CLICK tweetButton" not in out and "CLICK tweetButtonInline" not in out:
        print("publisher did not click; leaving this item queued for the next "
              "tick rather than marking it done")
        return 0

    time.sleep(8)
    sid = newest_status(port)
    if not sid:
        print("no status id found on the page; NOT recording it as posted — "
              "the queue stays where it is rather than losing the item")
        return 0

    rc, v = run(VERIFY, [port, sid, str(copy), str(idx)], timeout=240)
    print(v.strip()[-900:])
    if "VERIFIED" not in v:
        print("verification did not pass; leaving it queued so the failure is "
              "visible instead of silently counted as done")
        return 0

    state["posted"].append(idx)
    save_state(state_path, state)
    print(f"recorded {idx} as posted ({len(state['posted'])}/{len(posts)})  "
          f"status {sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
