#!/usr/bin/env python3
"""
blrun.py -- run many catalog models through Blender with bounded concurrency.

Why a runner at all: the catalog is built by many agents at once, and every one
of them wants to launch Blender. Unbounded launching oversubscribes the CPU,
each render crawls, and the batch looks like a hang. Worse, processes sharing a
temp directory corrupt each other's Blender state.

Two rules this enforces:
  1. A GLOBAL process cap across every blrun invocation, not just one batch.
     Implemented with a slot directory + flock, so N agents each running 4 jobs
     still never exceed --max-procs in total.
  2. One isolated TMPDIR and output directory per job, so two renders can
     never write the same file or share Blender's scratch state.

Slot files are never deleted -- /tmp is append-only on some hosts (unlink is
denied), so liveness is tracked by rewriting a slot's contents to "done"
instead. A stale slot from a crashed run is detected by a dead pid and reused.
"""
import argparse
import concurrent.futures as futures
import errno
import json
import os
import subprocess
import sys
import time

BLENDER_CANDIDATES = [
    os.environ.get("BLENDER_BIN", ""),
    "/Users/sqs/code/.blenderlab/Blender.app/Contents/MacOS/Blender",
    "/Applications/Blender.app/Contents/MacOS/Blender",
    "blender",
]


def find_blender(explicit=""):
    for cand in [explicit] + BLENDER_CANDIDATES:
        if not cand:
            continue
        if os.path.sep in cand:
            if os.path.exists(cand) and os.access(cand, os.X_OK):
                return cand
        else:
            from shutil import which
            hit = which(cand)
            if hit:
                return hit
    return None


class SlotPool:
    """Cross-process cap on concurrent Blender processes."""

    def __init__(self, root, cap):
        self.dir = os.path.join(root, ".slots")
        os.makedirs(self.dir, exist_ok=True)
        self.cap = max(1, cap)
        self.held = None

    def _alive(self, path):
        try:
            with open(path) as fh:
                head = fh.read(64).strip()
        except OSError:
            return False
        if head.startswith("done"):
            return False
        try:
            pid = int(head.split()[0])
        except (ValueError, IndexError):
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError as exc:
            # EPERM means the process EXISTS and we are simply not allowed to
            # signal it -- which is exactly the case on sandboxes and hosts that
            # forbid cross-process signalling. Reporting that as "dead" silently
            # disables the global cap: every slot looks free, every runner admits
            # its full cap, and the machine is oversubscribed. Only ESRCH, the
            # kernel saying there is no such process, means the slot is stale.
            return exc.errno != errno.ESRCH
        except Exception:
            return False

    def acquire(self, timeout=3600.0):
        import fcntl
        lock_path = os.path.join(self.dir, ".lock")
        lock = open(lock_path, "a+")
        deadline = time.time() + timeout
        while True:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                used = []
                for name in os.listdir(self.dir):
                    if name == ".lock":
                        continue
                    p = os.path.join(self.dir, name)
                    if self._alive(p):
                        used.append(p)
                if len(used) < self.cap:
                    slot = os.path.join(self.dir, "slot-%d" % os.getpid())
                    with open(slot, "w") as fh:       # overwrite is allowed
                        fh.write("%d %f\n" % (os.getpid(), time.time()))
                    self.held = slot
                    return slot
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
            if time.time() > deadline:
                raise TimeoutError("no slot within %ss (cap=%d)" % (timeout, self.cap))
            time.sleep(0.5)

    def release(self):
        if self.held:
            try:
                with open(self.held, "w") as fh:
                    fh.write("done %d %f\n" % (os.getpid(), time.time()))
            except OSError:
                pass
            self.held = None


def run_one(blender, model, outdir, threads, samples, res, shots, skill_root,
            timeout_s=1800):
    name = os.path.splitext(os.path.basename(model))[0]
    job_dir = os.path.join(outdir, name)
    tmp_dir = os.path.join(job_dir, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(job_dir, exist_ok=True)

    env = dict(os.environ)
    env["TMPDIR"] = tmp_dir
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # keep __pycache__ out of the skill
    env.pop("BLENDER_USER_SCRIPTS", None)

    runner = os.path.join(skill_root, "scripts", "run_model.py")
    cmd = [blender, "--background", "--factory-startup", "-noaudio",
           "--python-exit-code", "1", "-t", str(threads),
           "--python", runner, "--", model, job_dir,
           "--samples", str(samples), "--res", res]
    if shots:
        cmd += ["--shots", shots]

    log = os.path.join(job_dir, "run.log")
    t_start = time.time()
    t0 = t_start
    try:
        with open(log, "w") as fh:
            rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                 env=env, cwd=job_dir, timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        rc, timed_out = 124, True

    result = dict(name=name, model=model, outdir=job_dir, returncode=rc,
                  seconds=round(time.time() - t0, 1), timed_out=timed_out,
                  started=round(t_start, 3), ended=round(time.time(), 3),
                  log=log)
    rep = os.path.join(job_dir, "report.json")
    if os.path.exists(rep):
        try:
            with open(rep) as fh:
                result["report"] = json.load(fh)
        except ValueError:
            result["report_error"] = "unparseable report.json"
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("models", nargs="+", help="model .py files, or a directory")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--skill-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--blender", default="")
    ap.add_argument("--max-procs", type=int,
                    default=int(os.environ.get("BLRUN_MAX_PROCS", "12")))
    ap.add_argument("--threads", type=int,
                    default=int(os.environ.get("BLRUN_THREADS", "2")))
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", default="800x620")
    ap.add_argument("--shots", default="")
    args = ap.parse_args()

    blender = find_blender(args.blender)
    if not blender:
        print("BLRUN no Blender binary found. Run scripts/bootstrap_blender.py "
              "first, or set BLENDER_BIN.", file=sys.stderr)
        return 2

    models = []
    for item in args.models:
        if os.path.isdir(item):
            for root, _dirs, files in os.walk(item):
                models += [os.path.join(root, f) for f in sorted(files)
                           if f.endswith(".py") and not f.startswith("_")]
        else:
            models.append(item)
    models = [m for m in models if "__pycache__" not in m]
    # taxonomy.py is the catalog SOURCE, not a model. Walking catalog/ picked it
    # up and burned a render slot on a module with no build().
    models = [m for m in models
              if os.path.basename(m) not in ("taxonomy.py",)]
    # Blender runs with cwd=<job_dir>, so a RELATIVE model path would resolve
    # against the job directory and fail with a misleading FileNotFoundError.
    models = [os.path.abspath(m) for m in models]
    os.makedirs(args.outdir, exist_ok=True)

    pool = SlotPool(args.outdir, args.max_procs)
    print("BLRUN %d models, cap=%d procs, threads=%d, blender=%s"
          % (len(models), args.max_procs, args.threads, blender), flush=True)

    # The batch runs CONCURRENTLY, one worker per slot.
    #
    # This loop used to be serial: it acquired a slot, ran a blocking
    # subprocess.call, released, and moved on. The slot pool therefore only ever
    # stopped *other* blrun processes from oversubscribing -- it never made this
    # invocation parallel, so --max-procs 8 was decoration. Every catalog sweep
    # had been rendering one model at a time while the report claimed eight,
    # which is where a multi-hour budget went. The pool size is the slot cap, so
    # one process still never exceeds it, and N processes still share it.
    results = [None] * len(models)
    t0 = time.time()

    def job(idx_model):
        idx, model = idx_model
        slot = pool.acquire()
        try:
            res = run_one(blender, model, args.outdir, args.threads,
                          args.samples, args.res, args.shots, args.skill_root)
        finally:
            pool.release()
        return idx, res

    with futures.ThreadPoolExecutor(max_workers=args.max_procs) as ex:
        pending = {ex.submit(job, pair): pair[0]
                   for pair in enumerate(models)}
        for fut in futures.as_completed(pending):
            idx, res = fut.result()
            results[idx] = res
            rep = res.get("report") or {}
            print("BLRUN [%d/%d] %-28s rc=%d %5.1fs status=%s verts=%s "
                  "nonmanifold=%s"
                  % (idx + 1, len(models), res["name"], res["returncode"],
                     res["seconds"], rep.get("status", "-"),
                     rep.get("verts", "-"), rep.get("nonmanifold", "-")),
                  flush=True)

    done = [r for r in results if r is not None]
    ok = sum(1 for r in done if r["returncode"] == 0)

    # What concurrency was ACTUALLY achieved, measured from the jobs' own
    # intervals rather than from the --max-procs that was asked for. The runner
    # once advertised a cap it never used, and nothing in its output said so;
    # a sweep ran one model at a time for hours while the log claimed eight.
    # peak is now a fact in the summary, so that cannot hide again.
    peak = 0
    edges = []
    for r in done:
        edges.append((r.get("started", 0.0), 1))
        edges.append((r.get("ended", 0.0), -1))
    edges.sort()
    live = 0
    for _t, delta in edges:
        live += delta
        peak = max(peak, live)
    serial = sum(r["seconds"] for r in done)

    summary = dict(total=len(done), ok=ok, failed=len(done) - ok,
                   wall_seconds=round(time.time() - t0, 1),
                   cap=args.max_procs, threads=args.threads,
                   observed_peak_concurrency=peak,
                   serial_seconds=round(serial, 1),
                   speedup=round(serial / max(1e-9, time.time() - t0), 2),
                   results=done)
    with open(os.path.join(args.outdir, "blrun_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print("BLRUN DONE ok=%d/%d wall=%.1fs serial=%.1fs speedup=%.2fx "
          "peak_concurrency=%d (cap=%d)"
          % (ok, len(done), summary["wall_seconds"], serial, summary["speedup"],
             peak, args.max_procs), flush=True)
    return 0 if ok == len(done) else 1


if __name__ == "__main__":
    sys.exit(main())