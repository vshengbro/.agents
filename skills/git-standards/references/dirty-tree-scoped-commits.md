# Committing into a tree that already has uncommitted work

A dirty tree is the normal state of a long-lived skills or tooling repo, and
your change often lands in a file that ALREADY carries someone else's
uncommitted edits. `git add <file>` then commits both, which hands you credit
for work you did not write and can silently ship it broken.

## Stage the file's HEAD version plus only your own hunks

Read the other uncommitted work, keep it in the working tree, and stage a
version that does not contain it:

```bash
# 1. your edit, and the other party's edit, are both in the working tree
git diff <file>                       # separate the two: which hunks are yours?

# 2. build a file that is HEAD + only your hunks, stage it, then restore
cp <file> "$TMPDIR/<file>.mine"        # keep the full working-tree copy
git show HEAD:<file> > <file>           # start from HEAD
#    apply only your hunks to <file>
git add <file>                         # staged = HEAD + yours
cp "$TMPDIR/<file>.mine" <file>        # working tree = yours + theirs, still uncommitted
git diff --cached <file>               # read back: only your hunks may be staged
```

## When another agent may be writing to the same file, stage through the INDEX

The recipe above temporarily overwrites the file on disk, which is a race with
a live writer: their edit lands in the window between your restore and their
next write, and one of them is lost. Building the blob and pointing the index
at it stages the same content while every file on disk stays exactly as it
was:

```bash
git show HEAD:<file> > "$TMPDIR/<file>.mine"   # HEAD + only your hunks
#    apply only your hunks to $TMPDIR/<file>.mine
blob=$(git hash-object -w --stdin < "$TMPDIR/<file>.mine")
mode=$(git ls-tree HEAD <file> | awk '{print $1}')
git update-index --cacheinfo "$mode,$blob,<file>"
```

`git add` cannot express "my hunks of this one file", and `git add -p` is
interactive and fragile. Read back both sides before committing: the staged
diff must show only your hunks, and the unstaged diff must still show the
other party's — the second going empty means you swallowed their work. The
`refusing-to-own-another-agents-silent-overwrite` skill covers attributing the
hunks and reporting the collision.

When your change and the other party's touch the SAME file, verify the staged
version is coherent on its own — that is the version that will be committed and
later checked out by someone who has none of the other party's work:

```bash
git stash push -- <file> && git stash pop   # confirm the pair is not entangled
```

If the two edits overlap in the same region, they are one change: either take
both or neither, and say which in the commit message. Do not fabricate a
synthetic base to make the split look clean.

## Sometimes the split is impossible, and the commit has to carry both

The other party's change may be exactly what their own untracked test asserts,
so staging only your hunks leaves a test that fails against the committed tree
— the split produces a broken checkout, which is worse than a wide commit.
Take both, and NAME the extra content in the commit message: the reader has
to know the commit also carries someone else's work and what that work was,
because the message is the only place that says so. Stage the other party's
untracked files too, or the test they wrote is not in the commit and the tree
is still broken.

## Prove the scoped commit is self-contained before pushing it

A commit that depends on uncommitted work elsewhere in the tree is broken for
everyone else. Check the staged set in isolation:

```bash
git clone --no-hardlinks --depth 1 <repo> "$TMPDIR/probe"
cp <your-staged-files> "$TMPDIR/probe/<paths>"
cd "$TMPDIR/probe" && <the project's own self-test or gate>
```

A skill repo's self-tests are the right instrument: the scoped commit must
pass them against HEAD's version of everything else.

## Restore the working tree afterwards and prove it

After staging, the other party's uncommitted work must still be there,
uncommitted and unmodified:

```bash
git diff --stat            # their hunks still present
git diff --cached --stat   # only yours staged
```

Commit only the paths you staged. Never `git add -A` in a tree that was dirty
before you arrived.
