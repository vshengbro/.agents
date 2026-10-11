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

  python3 run_project_day.py [--dry-run]
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

# Where the project record lived before xconfig. Read once, then migrated.
_LEGACY_STATE = Path("~/.hermes/cache/scratch/x_project_state.json")


# Resolved inside main(), never at import: a cron wrapper that exports
# X_QUEUE or X_POST_STATE after this module is already loaded would otherwise
# be ignored, and the run would read — and then rewrite — the wrong queue.

def queue_file() -> Path:
    """X_QUEUE, else the queue beside the scripts."""
    return Path((os.environ.get("X_QUEUE") or "").strip()
                or str(HERE / "x_queue.json")).expanduser()


def state_file() -> Path:
    """X_POST_STATE, else the project state beside the scripts.

    Beside the scripts, not under one developer's home directory: a path that
    only exists where it was written makes every other machine start from an
    empty record and republish projects that already went out.

    A record already written under the pre-xconfig location is still READ from
    there when the new one is absent, and the next successful save migrates
    it. Dropping it silently would empty `posted`, which is not a cosmetic
    loss: it re-publishes projects whose four languages already went out.
    """
    raw = (os.environ.get("X_POST_STATE") or "").strip()
    if raw:
        return Path(raw).expanduser()
    target = HERE / "x_project_state.json"
    if target.exists():
        return target
    legacy = _LEGACY_STATE.expanduser()
    return legacy if legacy.is_file() else target


def migrate_state(legacy: Path, target: Path) -> None:
    """Copy a pre-xconfig state record to the new location, once."""
    if legacy == target or not legacy.is_file() or target.exists():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(legacy.read_text())
        print(f"migrated project state {legacy} -> {target}", flush=True)
    except OSError as exc:
        print(f"could not migrate project state {legacy}:", exc, flush=True)


def gap_seconds() -> int:
    """X_GAP, else the ten minutes between a project's language versions."""
    raw = (os.environ.get("X_GAP") or "").strip()
    try:
        return int(raw) if raw else 600
    except ValueError:
        return 600


def run(script: Path, args: list[str], timeout: int = 600):
    p = subprocess.run([sys.executable, str(script)] + args,
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except ValueError:
            pass
    return {"posted": [], "failed": {}}


def save_state(path: Path, s: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(s, ensure_ascii=False, indent=1))


def newest_status(port: str) -> str:
    """The id of my own most recent post — the page may show others'."""
    _, out = run(WHOSE, [port], timeout=240)
    for line in out.splitlines():
        if "MINE" in line:
            parts = line.split()
            return parts[1] if len(parts) > 1 else ""
    return ""


def main() -> int:
    import xconfig

    port = str(int(sys.argv[1])) if len(sys.argv) > 1 \
        and sys.argv[1].isdigit() else str(xconfig.port())
    dry = "--dry-run" in sys.argv
    state_path = state_file()
    queue = json.loads(queue_file().read_text())
    state = load_state(state_path)
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
    copy_path = state_path.parent / f".x_copy_{repo.replace('/', '_')}.json"
    copy_path.write_text(json.dumps([langs["zh"]] if "zh" in langs
                                    else [next(iter(langs.values()))]))

    published, results = [], []
    gap = gap_seconds()
    for n, (code, body) in enumerate(langs.items()):
        if n:
            print(f"  waiting {gap // 60} min before {code}", flush=True)
            time.sleep(gap)
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
    save_state(state_path, state)
    migrate_state(_LEGACY_STATE.expanduser(), HERE / "x_project_state.json")
    print(f"\npublished {repo}: {', '.join(results)} "
          f"({len(state['posted'])}/{len(queue)} projects done)")
    copy_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
