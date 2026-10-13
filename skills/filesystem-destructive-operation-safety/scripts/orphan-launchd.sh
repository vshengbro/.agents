#!/bin/bash
# Read-only scanner: launchd jobs whose target executable no longer exists.
# Deletes nothing. Prints one line per job: OK / ORPHAN.
#
#   bash orphan-launchd.sh                 # scan all four launchd dirs
#   bash orphan-launchd.sh sogou ClashX    # only jobs matching a substring
#
# An ORPHAN line means the plist is registered but its Program is gone, so
# launchd respawns into "program not found" on every trigger. Unregister with
#   sudo launchctl bootout system/<label>   # or: launchctl remove <label>
# BEFORE deleting the plist, or the error persists until reboot.
set -u

DIRS=(/Library/LaunchDaemons /Library/LaunchAgents
      "$HOME/Library/LaunchAgents" "$HOME/Library/LaunchDaemons")

filters=("$@")
matches() {  # empty filter list matches everything
  [ ${#filters[@]} -eq 0 ] && return 0
  local f
  for f in "${filters[@]}"; do
    case "$1" in *"$f"*) return 0 ;; esac
  done
  return 1
}

orphans=0; checked=0
for d in "${DIRS[@]}"; do
  [ -d "$d" ] || continue
  for plist in "$d"/*.plist; do
    [ -e "$plist" ] || continue
    matches "$plist" || continue

    # Plists express the target as either :Program or :ProgramArguments:0.
    prog=$(/usr/libexec/PlistBuddy -c "Print :Program" "$plist" 2>/dev/null)
    [ -z "$prog" ] && \
      prog=$(/usr/libexec/PlistBuddy -c "Print :ProgramArguments:0" "$plist" 2>/dev/null)
    [ -z "$prog" ] && continue      # no program key: not a resolvable job

    label=$(/usr/libexec/PlistBuddy -c "Print :Label" "$plist" 2>/dev/null)
    label=${label:-$(basename "$plist" .plist)}
    checked=$((checked + 1))

    if [ -e "$prog" ]; then
      printf '  OK      %-52s -> %s\n' "$label" "$prog"
    else
      printf '  ORPHAN  %-52s -> %s (MISSING)\n' "$label" "$prog"
      orphans=$((orphans + 1))
    fi
  done
done

echo "RESULT: checked=$checked orphans=$orphans"
[ "$orphans" -gt 0 ] && exit 1 || exit 0
