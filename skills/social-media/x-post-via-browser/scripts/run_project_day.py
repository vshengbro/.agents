#!/usr/bin/env python3
"""Post the next project from the daily queue: one project's four languages.

A cron job runs this on the day schedule, so WHICH projects go out and WHEN is
the cron's business; this file only knows how to publish the next one properly.

The queue is a list of dicts, each one a project with its four versions:

    [{"repo": "euv-dev/euv",
      "langs": {"zh": "...", "en": "...", "ja": "...", "ko": "..."}}, ...]

One invocation publishes ONE project's zh/en/ja/ko in order, spaced by
--gap seconds, and records the project only after every one of them has been
read back off the timeline. A version that does not verify is NOT recorded, so
the next run retries that project rather than losing a language.

Every rule the publisher obeys is in the x-post-via-browser skill and enforced
by verify_no_unsafe_posting.py: no navigation, no clearing, no mouse, no
clipboard, one page load at most and only from ensure_browser.py.

  X_POST_STATE=/path/state.json python3 run_project_day.py 9240 [--dry-run]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLISH = HERE / "publish.py"
VERIFY = HERE / "verify_post.py"
WHOSE = HERE / "whose_posts.py"
QUEUE = Path(os.environ.get("X_QUEUE",
                            "/Users/sqs/.hermes/cache/scratch/x_queue.json"))
STATE = Path(os.environ.get(
    "X_POST_STATE", "/Users/sqs/.hermes/cache/scratch/x_project_state.json"))
# Minutes between the four language versions of one project. The cron's
# interval separates projects; this separates the versions inside one.
GAP = int(os.environ.get("X_GAP", "600"))


def run(script: Path, args: list[str], timeout: int = 600):
    p = subprocess.run([sys.executable, str(script)] + args,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except ValueError:
            pass
    return {"posted": [], "failed": {}}


def save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1))


def newest_status(port: str) -> str:
    """The id of my own most recent post — the page may show others'."""
    _, out = run(WHOSE, [port], timeout=240)
    for line in out.splitlines():
        if "MINE" in line:
            parts = line.split()
            return parts[1] if len(parts) > 1 else ""
    return ""


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "9240"
    dry = "--dry-run" in sys.argv
    queue = json.loads(QUEUE.read_text())
    state = load_state()
    done = set(state["posted"])

    if len(done) >= len(queue):
        print(f"queue is empty — all {len(queue)} projects already published")
        return 0

    idx = next(i for i in range(len(queue)) if i not in done)
    project = queue[idx]
    repo = project.get("repo", "?")
    langs = project.get("langs") or {}
    print(f"project {idx + 1}/{len(queue)}: {repo} "
          f"({', '.join(langs) or 'no languages'})")

    if dry:
        for code, body in langs.items():
            print(f"\n--- {code} ({len(body)} chars) ---\n{body}")
        return 0

    # A per-language copy file: publish.py reads a LIST of texts and takes an
    # index, so each version is published as index 0 of its own file. That
    # keeps one project's four languages in one queue entry and lets the
    # publisher's own refusal rules apply to each version unchanged.
    copy_path = STATE.parent / f".x_copy_{repo.replace('/', '_')}.json"
    copy_path.write_text(json.dumps([langs["zh"]] if "zh" in langs
                                    else [next(iter(langs.values()))]))

    published, results = [], []
    for n, (code, body) in enumerate(langs.items()):
        if n:
            print(f"  waiting {GAP // 60} min before {code}", flush=True)
            time.sleep(GAP)
        copy_path.write_text(json.dumps([body], ensure_ascii=False))

        _, out = run(PUBLISH, [port, "--post", "0", "--go"])
        tail = out.strip().splitlines()
        for line in tail[-14:]:
            print("  " + line, flush=True)

        if not any("CLICK tweetButton" in ln for ln in tail):
            print(f"  {code}: publisher did not click — stopping, "
                  f"{repo} stays queued so it is retried")
            return 0

        time.sleep(8)
        sid = newest_status(port)
        if not sid:
            print(f"  {code}: no status id on the page — NOT recording it")
            return 0
        _, v = run(VERIFY, [port, sid, str(copy_path), "0"], timeout=300)
        for line in v.strip().splitlines()[-6:]:
            print("  " + line, flush=True)
        if "VERIFIED" not in v:
            print(f"  {code}: verification failed — {repo} stays queued")
            return 0
        published.append({"lang": code, "sid": sid})
        results.append(f"{code}={sid}")

    state["posted"].append(idx)
    state.setdefault("failed", {})[repo] = None
    save_state(state)
    print(f"\npublished {repo}: {', '.join(results)} "
          f"({len(state['posted'])}/{len(queue)} projects done)")
    copy_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
