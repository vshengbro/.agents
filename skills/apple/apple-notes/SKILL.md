---
name: apple-notes
description: "Use when creating, searching, editing, or exporting Apple Notes on macOS via memo. 苹果 备忘录 笔记。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
prerequisites:
  commands: [memo]
---

# Apple Notes

`memo` drives Notes.app over AppleScript. Notes sync to iPhone/iPad through
iCloud.
## Index

Prerequisites · When NOT to use · Command surface · Workflow · Limitations and rules


## Prerequisites

- macOS with Notes.app
- `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Automation access to Notes.app when prompted (System Settings → Privacy →
  Automation)
- `$EDITOR` exported — `memo` composes note bodies in it, so `-a` and `-e` do
  not work headless without one

Confirm the tool matches this machine before relying on it:

```bash
memo --help && memo notes --help
```

## When NOT to use

- Bear or another notes app — this drives Notes.app only.
- Agent-internal notes that never need to sync → the memory tool.

## Command surface

```bash
memo notes                        # list notes
memo notes -f "Folder Name"       # limit to a folder
memo notes -s "query"             # fuzzy search
memo notes -fl                    # list folders and subfolders
memo notes -v 3                   # print note N from the listing

memo notes -a                     # add a note: opens $EDITOR
memo notes -a -f "Folder Name"    # add into a specific folder
memo notes -e [-f "Folder"]       # pick a note, edit it in $EDITOR
memo notes -m                     # move a note to another folder
memo notes -d [-f "Folder"]       # delete a note
memo notes -ex [-f "Folder"]      # export to HTML/Markdown on the Desktop
```

`-a/--add`, `-e`, `-d`, and `-m` are bare flags: they open an editor or an
interactive picker, they take no title argument. Pass a folder with
`-f/--folder`; there is no `--title`.

## Workflow

1. Scope first — `memo notes -fl`, then `memo notes -f "<Folder>"` or
   `memo notes -s "<query>"`.
2. Capture the identifying detail (`-v N`) so the note you act on is provably
   the one the user meant before any `-e`, `-m`, or `-d`.
3. Compose or edit content in `$EDITOR`, save, quit. `memo` writes the note back
   through AppleScript.
4. Re-run the same listing command and confirm the change landed.

## Limitations and rules

- Notes containing images cannot be edited in place. Inline images survive as
  `[MEMO_IMG_N]` placeholders in the editor: keep the placeholder to preserve
  the image, remove it to drop the image. AppleScript appends preserved images
  at the end of the note regardless of placeholder position.
- Interactive picking needs a real terminal: run with `pty=true` if a prompt
  can't render.
- `-d` deletes. Show the user the note you identified and get a go-ahead before
  running it — deletion is not recoverable through this CLI.
- Interactive selection is not an id: if a listing changed between your read
  and your write, re-list instead of reusing a stale index.