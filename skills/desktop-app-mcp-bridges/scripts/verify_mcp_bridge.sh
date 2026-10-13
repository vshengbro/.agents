#!/usr/bin/env bash
# Three-rung verification for an app-hosted MCP bridge.
#   rung 1  registered   hermes mcp list     -> present + enabled + transport resolved
#   rung 2  discovery    hermes mcp test     -> stdio handshake + tool inventory
#   rung 3  app socket   lsof -sTCP:LISTEN   -> the app side is bound (only proves the loop)
#
# Usage: verify_mcp_bridge.sh <server-name> [app-side-port]
# Exits non-zero on the first failing rung. See SKILL.md for what each rung can prove.

set -uo pipefail

name="${1:-}"
port="${2:-}"

if [[ -z "$name" ]]; then
    echo "usage: $(basename "$0") <server-name> [app-side-port]" >&2
    exit 2
fi

if ! command -v hermes >/dev/null 2>&1; then
    echo "FAIL: 'hermes' is not on PATH" >&2
    exit 1
fi

echo "== rung 1/3: registered =="
listing="$(hermes mcp list 2>&1)"
if ! printf '%s\n' "$listing" | grep -Eq "^[[:space:]]*${name}[[:space:]]"; then
    echo "FAIL: '${name}' is not listed by 'hermes mcp list'" >&2
    printf '%s\n' "$listing" >&2
    exit 1
fi
if ! printf '%s\n' "$listing" | grep -E "^[[:space:]]*${name}[[:space:]]" | grep -q "enabled"; then
    echo "FAIL: '${name}' is listed but not enabled" >&2
    exit 1
fi
printf '%s\n' "$listing" | grep -E "^[[:space:]]*${name}[[:space:]]"
echo "OK: registered and enabled"

echo
echo "== rung 2/3: stdio discovery =="
out=""
rc=0
out="$(hermes mcp test "$name" 2>&1)" || rc=$?
if [[ "$rc" -ne 0 ]]; then
    echo "FAIL: 'hermes mcp test ${name}' exited ${rc}" >&2
    printf '%s\n' "$out" >&2
    exit 1
fi
lines="$(printf '%s\n' "$out" | grep -c '[^[:space:]]' || true)"
if [[ "${lines:-0}" -lt 3 ]]; then
    echo "FAIL: no tool inventory returned (${lines} non-empty lines) — the server process" >&2
    echo "      did not complete handshake/discovery." >&2
    printf '%s\n' "$out" >&2
    exit 1
fi
echo "OK: handshake completed, ${lines} lines of tool inventory"

echo
echo "== rung 3/3: app socket =="
if [[ -z "$port" ]]; then
    echo "SKIP: no port given — the loop is NOT closed. Pass the app-side port."
else
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        lsof -nP -iTCP:"$port" -sTCP:LISTEN
        echo "OK: listening on ${port}"
    else
        echo "FAIL: nothing listening on ${port}." >&2
        echo "      The add-on is probably enabled but was never loaded by a GUI" >&2
        echo "      session of the app. Compare the app's process start time with the" >&2
        echo "      mtime of the preferences file you wrote, then have the user restart." >&2
        exit 1
    fi
fi

echo
echo "PASS: '${name}' bridge verified"
