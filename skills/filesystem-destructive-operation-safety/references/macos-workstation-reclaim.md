# macOS workstation disk reclaim

Recipe for "clean up disk junk" on a macOS dev host. The rules in SKILL.md
(evidence-based triage, liveness checks, allowlist scripting, verify
functionally) all apply; this file is the macOS-specific candidate map.

## 1. Lead with the real number, on the real volume

`/` on macOS is a read-only system snapshot reporting a small, meaningless
figure. The live data volume is `/System/Volumes/Data`.

```bash
df -h / /System/Volumes/Data
```

State the real headroom before deleting anything. A request to "clean disk
junk" is often best answered by reporting the disk was never tight, then
reclaiming only what is provably stale — that framing is what makes the
remainder of the pass safe to approve.

## 2. Candidate map

```bash
du -sh ~/Library/Caches ~/Library/Developer ~/.cache /private/tmp \
       ~/.hermes/cache/scratch ~/Library/Containers 2>/dev/null
for d in ~/Library/Caches ~/.cache /private/tmp ~/.hermes/cache/scratch; do
  du -sh "$d"/* 2>/dev/null | sort -rh | head -10
done
```

Recurring offenders on a Rust/macOS host: per-experiment `target/` siblings,
`/private/tmp` build dirs from throwaway runs, per-app updater caches, rotated
logs, agent scratch dirs, simulator device data, VM images.

## 3. Resolve the live cache from config, delete only the siblings

A build tool's cache is pinned by config, so its name tells you nothing. Check
`~/.cargo/config.toml` (`build.target-dir`) *and* the shell rc files, because
`CARGO_HOME` / `CARGO_TARGET_DIR` can only be expressed as env.

```bash
grep -rn "target-dir\|CARGO_HOME\|CARGO_TARGET_DIR" \
     ~/.cargo/config.toml ~/.zshenv ~/.zshrc ~/.profile 2>/dev/null
```

Whatever the config points at is a **keep**. The `target-<suffix>` siblings
beside it are one-off experiment residue and are usually the bulk of the
reclaim. `CACHEDIR.TAG` at a root marks a real build cache.

## 4. Simulator data: drive `simctl`, never `rm -rf`

`simctl` owns the device data layout, so reclaim through it. `erase` keeps the
device listed; only its data goes.

```bash
xcrun simctl list devices | grep Booted
xcrun simctl shutdown <udid> && xcrun simctl erase <udid>
du -sh ~/Library/Developer/CoreDevice/DeviceFS     # tens of GB -> ~1M
xcrun simctl boot <udid>                            # functional check
```

`shutdown` before `erase`: a booted device makes the erase ineffective, which
reads as a no-op bug rather than a wrong state.

Do **not** touch the runtime disk images (`xcrun simctl runtime list`) — see
the mounted-from-elsewhere trap in SKILL.md. Erase the device; keep the
runtime.

## 5. Docker Desktop's VM disk when the daemon is stopped

Desktop runs a Linux VM whose disk lives in the app container, not
`/var/lib/docker`. With the backend down the bytes are inert image data.

```bash
pgrep -f com.docker.backend || echo "daemon down"
du -sh ~/Library/Containers/com.docker.docker/Data/vms
```

Deleting it is a local state reset, not an uninstall — the app stays installed
and re-pulls on next start. Confirm the backend is down first; when it is up,
use `docker system df` instead.

## 6. uv / `uvx` caches: prefer the tool, and accept a lock skip

`uv cache prune` only drops unreferenced entries, so prefer it to `rm -rf`. It
**blocks on `.lock`** when long-lived `uvx`-spawned tool servers (MCP bridges)
are running — a 300s timeout there is the expected outcome, not a reason to
`--force`. Treat the cache as a keep, report it, and move on.

## 7. Report shape

Report before/after `df` on `/System/Volumes/Data` and bytes actually
reclaimed; `removed=N skipped=N failed=M` plus the *names* of what was kept and
why; findings that emerged from the scan (a hung build pinning a cache lock
often matters more to the user than the bytes); and any self-correction, stated
plainly. Never leave a bare `FAIL` from a misdirected check standing as if the
cleanup had broken something.
