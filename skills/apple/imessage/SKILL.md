---
name: imessage
description: "Use when sending or reading iMessage/SMS in Messages.app on macOS: imsg send, chats, history, watch. 苹果 信息 短信 收发。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [iMessage, SMS, Messages, macOS, Apple]
prerequisites:
  commands: [imsg]
---

# iMessage (macOS)

`imsg` reads the local Messages `chat.db` and sends through Messages.app
automation. Sibling skills: Notes → `apple-notes`, Reminders →
`apple-reminders`, device tracking → `findmy`.
## Index

Prerequisites · Workflow · Rules


## Prerequisites

- macOS 14+ with Messages.app signed in
- `brew install steipete/tap/imsg` (Homebrew tap is the supported install path)
- **Full Disk Access** for the terminal running `imsg` — it reads
  `~/Library/Messages/chat.db`; grant it in System Settings → Privacy & Security,
  then reopen the terminal
- **Automation → Messages** for sending; Contacts access is optional and only
  adds resolved names

Gate before claiming anything worked:

```bash
imsg chats --limit 3     # ok => database readable (FDA granted)
```

`unable to open database file` / `authorization denied` is a permission problem,
not a broken install.

## Workflow

### 1. Resolve the chat — never guess a number

```bash
imsg chats --limit 20 --json | jq -s
imsg group --chat-id 42 --json        # details for one chat
imsg chats --unread-only --json       # unread inbound only
```

### 2. Confirm, then send

Sending reaches a real person. State the resolved recipient and exact text back
to the user and get an explicit go-ahead — unless the request already authorized
this exact send ("给妈妈发一条说我会晚点到"), which *is* that authorization; don't
re-ask it and don't refuse it.

```bash
imsg send --to "+141****1212" --text "on my way"
imsg send --to "+141****1212" --text "see attached" --file ~/Desktop/note.pdf
imsg send --to "+141****1212" --text "hi" --service sms      # auto|imessage|sms
imsg send --chat-id 42 --text "same thread"                   # in-thread reply
```

`--to` takes a formatted number, an email address, or a contact name; `~`
expands in `--file`. SMS needs Text Message Forwarding on the paired iPhone, and
`imsg` cannot pick which of several Apple-ID numbers sends. Verify a file exists
before attaching it.

### 3. Read history

```bash
imsg history --chat-id 42 --limit 20 --json | jq -s
imsg history --chat-id 42 --limit 20 --attachments     # human-readable
imsg history --chat-id 42 --start 2026-05-01T00:00:00Z --end 2026-05-06T00:00:00Z
imsg history --chat-id 42 --participants "+141****1212,jane@example.com"
```

`--limit` (default 50) applies *after* date/participant filters. JSON always
includes attachment metadata; `--attachments` only affects display. A truncated
read is not the whole conversation — say so rather than presenting it as one.

### 4. Watch

```bash
imsg watch --chat-id 42 --json                     # streams until stopped
imsg watch --chat-id 42 --since-rowid 9000 --json # resume from a cursor
```

`--since-rowid` is exclusive; without it, watch starts at the newest message and
does not replay earlier ones (use `history` for those). Tapbacks are excluded
unless `--reactions` is passed.

**Watch is a process you spawned:** register its PID at launch, then kill that
exact PID when the user says stop or on failure, timeout, or cancellation. Never
`pkill imsg` — that also kills watches the user started.

## Rules

1. Resolve the chat before sending; never invent a number or recipient.
2. Confirm recipient and text unless the request already authorized this send —
   re-asking on a clearly authorized message blocks the user, while skipping the
   check on an unauthorized send is irreversible.
3. One recipient set per user instruction. No bulk messaging or spamming.
4. Only send where the user asked. Telegram/Discord/Slack/WhatsApp go through
   their gateway, not `imsg`. Group membership changes are out of scope.