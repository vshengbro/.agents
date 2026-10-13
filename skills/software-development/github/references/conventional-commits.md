# Conventional Commits Quick Reference

Format: `type(scope): description`

## Types

| Type | When to use | Example |
|------|------------|---------|
| `feat` | New feature or capability | `feat(auth): add OAuth2 login flow` |
| `fix` | Bug fix | `fix(api): handle null response from /users endpoint` |
| `refactor` | Code restructuring, no behavior change | `refactor(db): extract query builder into separate module` |
| `docs` | Documentation only | `docs: update API usage examples in README` |
| `test` | Adding or updating tests | `test(auth): add integration tests for token refresh` |
| `ci` | CI/CD configuration | `ci: add Python 3.12 to test matrix` |
| `chore` | Maintenance, dependencies, tooling | `chore: upgrade pytest to 8.x` |
| `perf` | Performance improvement | `perf(search): add index on users.email column` |
| `style` | Formatting, whitespace, semicolons | `style: run black formatter on src/` |
| `build` | Build system or external deps | `build: switch from setuptools to hatch` |
| `revert` | Reverts a previous commit | `revert: revert "feat(auth): add OAuth2 login flow"` |

## Scope (optional)

Short identifier for the area of the codebase: `auth`, `api`, `db`, `ui`, `cli`, etc.

## Breaking Changes

Add `!` after type or `BREAKING CHANGE:` in footer:

```
feat(api)!: change authentication to use bearer tokens

BREAKING CHANGE: API endpoints now require Bearer token instead of API key header.
Migration guide: https://docs.example.com/migrate-auth
```

## Multi-line Body

Wrap at 72 characters. Use bullet points for multiple changes:

```
feat(auth): add JWT-based user authentication

- Add login/register endpoints with input validation
- Add User model with argon2 password hashing
- Add auth middleware for protected routes
- Add token refresh endpoint with rotation

Closes #42
```

## Linking Issues

In the commit body or footer:

```
Closes #42          ← closes the issue when merged
Fixes #42           ← same effect
Refs #42            ← references without closing
Co-authored-by: Name <email>
```

## Quick Decision Guide

- Added something new? → `feat`
- Something was broken and you fixed it? → `fix`
- Changed how code is organized but not what it does? → `refactor`
- Only touched tests? → `test`
- Only touched docs? → `docs`
- Updated CI/CD pipelines? → `ci`
- Updated dependencies or tooling? → `chore`
- Made something faster? → `perf`

## Project-Specific Conventions

Inspect the project's merged history BEFORE writing your first commit on a project with strict CI. The repo's `.github/workflows/*.yml`, the last 5–10 merge commits, and the PR template (if any) are authoritative — they tell you what trailers, scopes, and changelog conventions are expected. Mirror them; do not invent your own shape.

Patterns to look for:

- **Version-bump trailers.** Some repos (e.g. monorepos with workspace-wide semver) fold the version bump into the same commit as the fix, with body trailers like:
  ```
  fix(api): correct token refresh race
  
  [...explanation...]
  
  * chore: bump version to 1.4.2
  * chore: sync workspace versions to 1.4.2
  ```
  Check with `git log --oneline -- '*Cargo.toml'` or similar — if version bumps always appear inside fix commits, yours should too. A standalone `chore: bump version` commit will get squash-merged away, but the trailers inside the squashed commit become part of the canonical history.

  **Two commit types coexist in many monorepos** — distinguish them from the
  actual commit subject, not from PR squash messages:
  - `chore: bump version to X.Y.Z` — touches ONLY the root crate's
    `[package].version` (often one line in the root manifest).
  - `chore: sync all package versions to X.Y.Z` — touches every workspace
    member and the root `[workspace.dependencies]` table.
  When fixing a bug, the trailer goes inside the fix commit and matches the
  `bump` shape, NOT the `sync` shape — the sync commit is a separate concern
  performed by a release process or by a maintainer. Inspect
  `git log --format='%s' -- '*Cargo.toml'` for the last 20 commits; the
  subject line tells you which shape applies to fix commits on this project.

- **Changelog scopes.** Some projects require a `BREAKING CHANGE:` footer, a `Refs #N` line, or a custom `Signed-off-by:` trailer. Read one or two to copy the shape; don't paste a generic Conventional Commits template if the project uses something specific.

- **Branching model.** Conventional Commits do not dictate branch names. Check `git branch -a` and recent merge commits — if everything goes through `fix/scope-description` branches and squash-merges, follow that; if the project uses `release/*` long-lived branches, do not invent your own.

When the project's history is ambiguous (no recent commits, fresh repo), fall back to the standard format and document your assumption in the PR body so reviewers can correct it before merge.
