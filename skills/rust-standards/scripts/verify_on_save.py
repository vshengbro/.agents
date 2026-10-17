#!/usr/bin/env python3
"""Check a saved Rust/TOML file against the rust-standards verifiers.

The pre-commit hook already blocks a commit that introduces a violation, and
`rust_pre_commit.py` already runs the full pipeline. Neither fires while the file
is being written, so a rule like "no comments in mod.rs (§2.5)" is only discovered
at commit time — after the violation has been written, staged, and explained in a
message. Wiring this into an editor save hook puts the failure on the line that
caused it.

The pre-commit hook stays authoritative: it is what actually blocks. This is a
fast local signal, not a second source of truth, so it reports and never edits.

The verifiers under `scripts/` take a DIRECTORY and recurse, so this runs each one
against the saved file's parent and keeps only the findings that name that file.
That keeps a save cheap and keeps the message about the file just written.

Usage:
    python3 verify_on_save.py <repo_root> <file> [<file> ...]

Exit codes:
    0 - no violation in the given files
    1 - at least one violation; the message names the rule, file and line
    2 - usage error
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Verifiers worth running per save. Each is a fast recursive read and maps to one
# rule an editor author actually trips.
VERIFIERS = [
    ("verify_no_toml_mod_comments.py", "§2.5 no comments in *.toml / mod.rs"),
    ("verify_no_import_rename.py", "§6.5 no `use ... as ...` import renaming"),
    ("verify_no_allow_lints.py", "§14 no #[allow(...)]"),
    ("verify_doc_comment_format.py", "§2.2 doc-comment Arguments/Returns"),
]

# Verifier output prefixes its findings with the absolute path; match on the tail
# so a finding is attributed to the saved file regardless of how it was spelled.
def _names_file(line: str, target: Path) -> bool:
    return line.startswith(str(target)) or line.startswith(target.name + ":")


def check_file(target: Path) -> list[str]:
    """Return one message per violation this verifier reports for `target`."""
    directory = target.parent if target.is_file() else target
    findings: list[str] = []
    for script, rule in VERIFIERS:
        verifier = SCRIPTS_DIR / script
        if not verifier.is_file() or not directory.is_dir():
            continue
        try:
            proc = subprocess.run(
                ["python3", str(verifier), str(directory)],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            findings.append(f"{target}: {rule} — verifier timed out")
            continue
        if proc.returncode == 0:
            continue
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            if _names_file(line, target):
                # Strip the leading path so the editor shows a short message.
                detail = line[len(str(target)) :].lstrip(": ") if line.startswith(str(target)) else line
                findings.append(f"{target}: {rule} — {detail}")
    return findings


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--stdin"]
    if len(args) < 2:
        sys.stderr.write(__doc__ or "")
        return 2
    repo = Path(args[0]).resolve()
    files = []
    for item in args[1:]:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = repo / candidate
        files.append(candidate)

    # Only Rust sources and manifests carry these rules, so saving a README or a
    # lockfile costs nothing.
    targets = [f for f in files if f.suffix in {".rs", ".toml"}]
    if not targets:
        return 0

    findings: list[str] = []
    for target in targets:
        findings.extend(check_file(target))

    if not findings:
        return 0

    sys.stderr.write(f"rust-standards (on save) — {len(findings)} finding(s):\n")
    for finding in findings:
        sys.stderr.write(f"  {finding}\n")
    sys.stderr.write("\nThese block `git commit`. Fix now rather than at commit time.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
