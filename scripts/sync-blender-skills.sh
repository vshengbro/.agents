#!/usr/bin/env bash
# Vendor arjun988/blender-skills with exact tree and provenance checks.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/sync_blender_skills.py" "$@"
