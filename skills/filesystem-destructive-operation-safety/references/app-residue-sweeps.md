# App-residue sweeps on macOS

Recipe for "delete what X left behind", and the request it usually grows into:
"…and the leftovers from other programs too". The rules in SKILL.md (evidence
before names, liveness checks, allowlist scripting, verify functionally) all
apply. The SCOPE rule is in SKILL.md under *App-residue sweeps*: an app absent
from `/Applications` is not an uninstalled app, so measure the real footprint
across every install root before reporting a size.

## 1. The location map

A single vendor leaves state in a dozen places, and the ones that hold the
megabytes are not the ones people check first.

| Location | Holds | Notes |
|---|---|---|
| `/Library/Input Methods/*.app` | **the whole IME payload** | not an app bundle in `/Applications` |
| `/Library/PrivilegedHelperTools/` | root helper binaries | one per vendor, one per product |
| `/Library/LaunchDaemons/*.plist` | root jobs (startup, `StartInterval`) | `LaunchAgent`s too |
| `~/Library/LaunchAgents/*.plist` | per-user jobs | |
| `/Library/Application Support/<vendor>` | shared data | often Apple, see §5 |
| `~/Library/Application Support/<id>` | per-app data, incl. hidden dirs | a dot-dir can be the biggest item |
| `~/Library/Caches/`, `~/Library/HTTPStorages/` | caches, cookies | |
| `~/Library/Preferences/*.plist` | settings | needs `cfprefsd` restart after |
| `~/Library/Containers/`, `Group Containers/` | sandboxed state | match by bundle id |
| `~/Library/WebKit/<id>` | per-site storage | easy to miss, tens of MB |
| `~/Library/Mobile Documents/iCloud~<v>~<app>` | cloud container | daemon-pinned, §6 |
| `/var/db/receipts/` (`pkgutil --pkgs`) | installer receipts | no uninstaller; benign to leave |

First pass, cheap and read-only:

```bash
v=sogou   # vendor substring, lowercased
ls -d /Library/Input\ Methods/*[Ss]ogou* ~/Library/*{[Ss]ogou,clashx}* 2>/dev/null
du -shc ~/Library/Application\ Support/*[Ss]ogou* 2>/dev/null | tail -1
sfltool dumpbtm 2>/dev/null | grep -i -A6 "$v"     # background items
pkgutil --pkgs | grep -i "$v"                      # installer receipts
```

`sfltool dumpbtm` beats `launchctl list` for coverage: it lists every
registered background item with its `URL` and `Executable Path`, including jobs
that are registered but not currently loaded. `launchctl list` shows the loaded
subset only, so a residue sweep built on it under-reports.

## 2. Bulk removal is one allowlist script, and liveness is re-checked per entry

The scan and the delete are minutes apart; something can open a cache in
between. Order inside the script: unload first, then delete, then flush prefs.

```bash
set -u
removed=0; skipped=0; failed=0

# 1. Unregister the job BEFORE its binary disappears, else launchd respawns
#    into "program not found" on every StartInterval tick.
for label in com.example.Agent com.example.Service; do
  launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1 \
    && launchctl bootout "gui/$(id -u)/$label" 2>/dev/null \
    && echo "UNLOADED $label"
done

# 2. Per-entry liveness re-check, immediately before the delete.
for p in "$@"; do
  [ -e "$p" ] || continue
  if lsof 2>/dev/null | grep -qF "$p"; then
    echo "SKIP (in use): $p"; skipped=$((skipped+1)); continue
  fi
  rm -rf "$p" 2>/dev/null \
    && { echo "removed: $p"; removed=$((removed+1)); } \
    || { echo "FAILED: $p"; failed=$((failed+1)); }
done

# 3. Commit the Preferences deletions; cfprefsd caches the old plist.
killall -u "$(id -u)" cfprefsd 2>/dev/null
echo "RESULT: removed=$removed skipped=$skipped failed=$failed"
```

Report the counts and print every skipped path — the user can only object to a
keep they can see. A `FAILED` line is a finding to investigate, not a retry:
root-owned paths failing as a non-root user is the expected, correct outcome.

## 3. The privilege split: script it, hand it over

Root-owned items are usually the majority of the bytes, and a non-interactive
agent cannot authenticate them. Write the root half to a script and give the
user one line to run — a list of paths to delete by hand is work you are
delegating back to them.

```bash
sudo bash /path/to/rm_root_residue.sh
```

Report the two halves separately with their sizes. "Removed ~115 MB now,
~520 MB pending your sudo" is a real number the user can plan around; a single
blended figure is not.

## 4. Vendor-family collisions: prove the survivor is independent

One vendor, several products, shared identifier prefix — so "the app that
replaced it" may or may not still call the orphan's root helper. Resolve it by
scanning the survivor's binary:

```bash
strings "/Applications/<Survivor>.app/Contents/MacOS/<survivor>" \
  | grep -i -E "com\.vendor\.OldProduct|HelperName" | sort -u
```

Empty = the orphan is genuinely orphaned. Non-empty = you have found a live
dependency; keep it. Also compare the helpers themselves: a survivor with a
*different, Apple-signed* helper and no reference to the old one is the clean
case.

## 5. Names in `/Library/Application Support` prove nothing

Root-owned entries there are frequently Apple's own and load-bearing:

- `livefsd/settings.plist` carries the Developer `CoreDevice` `DeviceFS` mount
  records. Read it — a `mountedOn` path is a keep by evidence.
- `BTServer/` holds GarageBand/Logic/Keynote sound-library content that
  installed Apple apps still read.

```bash
/usr/libexec/PlistBuddy -c Print "/Library/Application Support/<name>/settings.plist" 2>/dev/null
codesign -dv "/Library/Application Support/<name>" 2>&1 | grep -iE "identifier|team"
```

An `0B` directory is not proof of disuse — the same trap as a simulator
runtime volume. A daemon-held or mount-managed `0B` entry is exactly the case
where the byte count understates what the directory controls.

## 6. Cloud containers: a `Permission denied` is the answer

An empty `iCloud~<vendor>~<app>` container returns `Permission denied` even to
its owner — the iCloud daemon pins the directory, and a plain file count shows
`0`. Confirm it is empty, leave it, and name it in the report as a known
leftover. `rm -rf` under a forced path fights the OS and is not worth it; iCloud
reclaims the shell on its own. Deleting a *non-empty* container is a real
sync-delete of cloud data, so never widen to that case without asking.

## 7. Recency beats presence, for CLI tools with no app bundle

A CLI installed outside `/Applications` with no `PATH` entry is not a residue
candidate, and "no `.app`" is not a keep signal either. Its own state directory
carries the liveness proof:

```bash
d="$HOME/Library/Application Support/<Tool>"
cat "$d"/*install.lock.pid 2>/dev/null | xargs -I{} ps -p {} -o pid,etime,command
stat -f "%Sm  %N" -t "%F %H:%M" "$d"     # mtime today == used today
ls -la "$d" | tail -5                     # config/log rewritten each run
```

A stale lock **PID** proves nothing — the file survives the process. The
state directory's mtime plus a same-day log write is the real evidence. A
89 MB CLI that ran an hour ago is a working tool; reporting it as residue
because it has no `.app` is the exact failure this check exists to prevent.

## 8. Verify with a negative scan, not an absence of errors

Re-run the location map after the sweep and show it empty. Also positively
confirm the tools you kept working, so a "clean" report is not a report that
broke something:

```bash
find ~/Library -maxdepth 3 -iname "*<vendor>*"        # expect: no output
defaults read com.apple.HIToolbox AppleEnabledInputSources   # inputs intact
for d in <installed-app-state-dirs>; do
  [ -e "$HOME/Library/Application Support/$d" ] && echo "  OK  $d"
done
launchctl list | grep -cE "<jobs you expect still loaded>"
```

A false "clean" is worse than an admitted leftover, so the verification step
must be able to fail.

## 9. Report shape

Bytes reclaimed per privilege tier; the exact `sudo` line for the pending half;
`removed=N skipped=N failed=M`; the kept items **with the evidence that kept
them** (lock-file mtime, plist naming a live mount, binary scan finding no
reference); and any leftover you could not remove, named with why. Findings
that emerged from the scan — a second vendor's orphaned helper worth 91 MB, a
full app payload hiding outside `/Applications` — usually matter more to the
user than the bytes and belong in the report, not just the tally.
