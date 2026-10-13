# Worked example: hand-off recipe across a multi-site change

Case: user moved a static-asset directory, every image 404s, and asked for
steps to make the build honour the new location — explicitly "don't change it,
I'll do it".

## Step 1 — measure before writing anything

The user asked about "the files that reference the images". The actual broken
thing was elsewhere. Build first, then classify:

- `public/` moved out of the location the build reads → **0 assets copied**.
  The symptom (every image 404) had nothing to do with the reference syntax.
- Only 22 of 1182 references were path-relative and therefore fragile; the
  other 1160 were site-root-relative or external and survived the move intact.

Reporting "here are the 22 lines to change" without the second fact would have
implied the whole site was broken when 97% of it was fine.

## Step 2 — find every site the change must land in

The failure mode for this class of task is fixing the *reported* site and
missing a second one. Grep for the behaviour, not just the path:

| Site | Role |
|---|---|
| `build.rs` `copy_dir(public, www)` | build-time copy |
| `src/bin/.../fn.rs` `copy_public_assets(src, out)` | post-build copy into `--out` |
| `copy_doc_assets` | sibling-asset walk, with a skip rule for the `public` dir |
| CI workflow | invokes the CLI; must gain the new flag or the fix never ships |
| caller's build script | passes the new flag |

"Only site 1 is changed" and "CI is unchanged" both produce a build that looks
correct locally and is broken in production. Name these explicitly in the
recipe.

## Step 3 — prefer the backward-compatible shape

Adding `--assets <DIR>` (defaulting to the old `<src>/public`) beats changing
the default: other consumers of the tool keep working, and the regression test
is "run it without the flag and confirm the old behaviour". Say which way you
lean and why in one line, then let the user override.

## Step 4 — write steps that match the existing code

Before quoting a constant or a signature, read the file. Match its conventions
(doc comments, naming, `if`/`match` structure, where constants live). In this
codebase `MSG_FLAG_REQUIRES_VALUE` is already shared between two flags — the
consistent move is to reuse it, and the recipe should say so and explain why,
rather than have the user invent a fourth constant.

## Step 5 — end with the verification, and the numbers

```
./build.sh
ls dist/markdown-images | wc -l    # expect 119
ls dist/img | wc -l                 # expect 9
```

A step list whose last line is "then it should work" is not verifiable. Give
the command and the expected value so the user can tell pass from fail without
asking you.

## Step 6 — flag what is easy to miss

- The CI workflow needs the same flag, or the fix works locally and ships broken.
- A reference rewrite must not touch sample output inside fenced code blocks.
- The blocker (which directory is correct) may be a decision that is theirs.

State all three inline rather than as a footnote — a step list is read top to
bottom and executed from the top.
