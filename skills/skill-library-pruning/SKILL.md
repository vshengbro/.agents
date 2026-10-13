---
name: skill-library-pruning
description: Use when auditing or pruning a Hermes skill library.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [skills, cleanup, audit, pruning, hermes]
    related_skills: [hermes-agent]
---

# Skill Library Pruning

## When to Use

Auditing or pruning a Hermes skill library where a git source repo (e.g. `~/.agents/skills`) feeds the active root (`~/.hermes/skills`): finding modeling/unused/duplicate skills, deleting user-named victims, or sweeping orphan scripts. Deletion is destructive but git-recoverable — the user's convention is **real deletion, no backup dirs, direct commit to master, no PR** for this repo.

## Procedure

1. **Build the true active set.** `~/.hermes/skills` mixes symlinks and plain-directory copies; a plain `find` misses everything behind a symlink. Use `find -L ~/.hermes/skills -name SKILL.md`, then `os.path.realpath()` each hit: symlink target inside the source repo = installed-from-source; anything else = bundled/copy (deleting the source skill does NOT remove a copy — remove it explicitly if the skill is being retired).
2. **Rank by usage.** Read `~/.hermes/skills/.usage.json`: `use_count` / `last_used_at` per skill, keyed by `name` or `category:name`. Present candidates grouped — not-installed, zero-use, duplicate pairs — with `du -sh` sizes. The user picks victims from that list; never unilaterally delete a high-use skill.
3. **Reference-scan before deleting.** Grep every victim name across the whole library (`*.md`, `*.py`, `*.sh`, `*.json`): `related_skills:` frontmatter lists, routing tables, prose pointers, and external consumers (`~/.git-hooks`, `~/.hermes/scripts`, cron configs). Fix every hit in survivors in the same commit.
4. **Salvage what survivors still reference.** If a surviving skill's doc or script points at a file inside a victim (template, script, reference doc), copy it into the survivor's own directory and repoint the reference before `git rm`. Check the victim's whole directory for operational assets, not just the one file you saw referenced.
5. **Delete and clean the registries.** `git rm -r` the source paths; remove matching `.skill-lock.json` entries (match on the `skillPath` field, prefix-aware for category dirs); unlink the symlink or `rmtree` the copy under `~/.hermes/skills` for every victim. A whole-**category** symlink (`~/.hermes/skills/euv -> .agents/skills/euv`) dies with the source automatically; a **per-skill** symlink does not and must be `rm`'d explicitly. Finish with `find -L ~/.hermes/skills -type l` = zero dangling links.
6. **Commit under real hooks, then push.** Stage only the deletions + lock + reference fixes + salvaged files; leave pre-existing uncommitted work in unrelated skills untouched and unstaged. **Never bypass the repo's hooks** (`-c core.hooksPath=/dev/null`, `--no-verify`) to get the commit through, however safe the change looks — a docs-only diff does not exempt it, because the question is the principle, not the blast radius. If you already bypassed, `git reset --soft HEAD~1` and redo it. If `git push` to github.com:22 fails, retry once or use `ssh://git@ssh.github.com:443/<owner>/<repo>.git`.

## Pitfalls

- **Scan at both full-filename and stem level** — prose cites skills without the extension (`depub_consts`, not `depub_consts.py`), so basename-only grep reports false orphans. Run a word-boundary stem grep as a second pass before calling anything unused.
- **Directory-driven consumption defeats name grep** — fixtures loaded via `FIXTURES = HERE / "fixtures" / <case>` + `copytree`, or configs found via `iterdir()` + suffix filter, never appear by name in any file. Read the consumer's discovery code before deleting fixture/config files; a name that appears nowhere can still be load-bearing.
- **English-word filenames false-match prose** — `allowed.yml` / `bump.yml` word-boundary-match ordinary sentences ("allowed to", "version bump"). Verify each rescue hit is actually about the file, not the word.
- **Duplicate skills diverge — compare by SECTION, not by file** — two installs of one name can differ by a single `related_skills` line, or the *less-used* copy can carry whole sections the popular one lacks, because they are separate source directories that stopped tracking each other. `diff -rq` tells you they differ; a heading-level diff tells you what to keep:

  ```bash
  comm -13 <(grep -E '^## ' popular/SKILL.md | sort) <(grep -E '^## ' other/SKILL.md | sort)
  ```

  Salvage those sections into the survivor *before* `git rm`, anchoring the insertion on the heading text so a re-run does not append a second copy. Deleting the lower-use copy is the right call and silently discarding content inside it is not.
- **Duplicates are not always symlink-vs-copy — `readlink` both.** A same-named skill can be installed twice as two symlinks pointing at two *different* source directories (`~/.hermes/skills/computer-use -> .agents/skills/computer-use` and `~/.hermes/skills/autonomous-ai-agents/computer-use -> .agents/skills/autonomous-ai-agents/computer-use`). Resolving realpaths and assuming "one of these is a copy" sends you to edit the wrong tree.
- **Usage keys are namespaced, so ranking by name undercounts.** One installed skill has two `.usage.json` entries — a bare `name` and a `category:name` — and they can differ by an order of magnitude. Look up BOTH forms and sum them, or the "least used" pick is an artifact of which key you happened to read.
- **A heavily-referenced skill missing from the active root is an installation gap, not a prune candidate.** A source-repo skill that cron jobs, hooks and scripts reference by name but that has no install under the active root is broken wiring, not redundancy — report it as "should be installed", never group it with the unused.
- **`git add -A -- <already-git-rm'd path>` fails with a pathspec error.** That is the expected outcome, not a problem: `git rm` already staged the deletion. Stage only the paths that still exist on disk.
- **`.pyc` under `scripts/` is cache, not source** — check `git ls-files` first: untracked means plain `rm`, tracked means `git rm`; add `*.pyc` to `.gitignore` so it never gets committed. `.gitignore` does NOT stop on-disk regeneration: any recurring caller that imports repo python modules (global git hooks running verifier scripts, cron dispatchers) re-creates `__pycache__` on every run — kill it at the source with `export PYTHONDONTWRITEBYTECODE=1` in that caller, otherwise the sweep has to be repeated forever.
- **Ambiguous victim names need one clarification, not a guess** — a name can be both a standalone skill and a category dir with used children (e.g. `frontend-dev`). Ask once; if unanswered, delete the conservative subset (the zero-use member) and disclose the interpretation in the report so the user can widen it with one word.
- **Do not sweep the user's uncommitted work into the cleanup commit** — stage explicit paths (`git add -A -- skills .skill-lock.json ':!path/to/their/work'`), never bare `git add -A`.

## Library shape rule

The library is deliberately small and high-signal; the user prunes aggressively. Do not create new skills during ordinary task work — new skills only on explicit user request or in a designated library-maintenance pass.

**`~/.hermes/skills` is a symlink layer and nothing else.** `~/.agents/skills` is the single source of truth: every skill is authored, edited and committed there, and a plain directory under `~/.hermes/skills` carrying its own `SKILL.md` is a violation — including the case where it is the *only* copy. "This skill exists nowhere else" is the case to migrate into the source repo, not the case to keep.

So the assertion after any migration is `find ~/.hermes/skills -name SKILL.md | wc -l` = **0**, and it must be run **without** `-L`: following symlinks makes a healthy layer read as empty and the check then passes for the wrong reason. Anything sitting directly under `~/.hermes/skills` that is not a symlink is Hermes metadata (`.usage.json`, `.curator_state`, `.bundled_manifest`, …), not a skill.
