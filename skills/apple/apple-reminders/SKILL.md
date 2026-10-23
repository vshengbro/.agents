---
name: apple-reminders
description: "Use when creating or managing Apple Reminders items on macOS via remindctl: due dates, lists, alarms, complete. 苹果 提醒事项 待办清单。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Reminders, tasks, todo, macOS, Apple]
prerequisites:
  commands: [remindctl]
---

# Apple Reminders

`remindctl` reads and updates the same reminders Reminders.app shows, through
public EventKit APIs, so they stay in sync on every device. Sibling skills:
Notes → `apple-notes`, messages → `imessage`, location → `findmy`.
## Index

Prerequisites · When NOT to use · Workflow · Verification and rules


## Prerequisites

- macOS 14+ with Reminders.app
- `brew install steipete/tap/remindctl`
- Reminders permission for the terminal that runs it

```bash
remindctl status          # permission state
remindctl authorize       # request it (macOS may not prompt on first run)
remindctl doctor --for-agent   # diagnose permissions + store access
```

If no prompt appears, trigger it once from the same terminal:
`osascript -e 'tell application "Reminders" to get name of reminders'`, then allow
access in System Settings → Privacy & Security → Reminders and re-run
`remindctl status`.

## When NOT to use

- "Remind me at 9am" as an **agent** alert → the cronjob tool, not Reminders.
  Ask which one is meant when the phrasing is ambiguous.
- Calendar events → Calendar tooling. Project tracking → the project's issue
  tracker.
- Native Reminders sections, tags/smart lists, file attachments, and the Urgent
  toggle are not reachable — EventKit doesn't expose them.

## Workflow

### Read

```bash
remindctl today            # also: tomorrow | week | overdue | upcoming | all
remindctl 2026-01-04       # a specific date
remindctl list             # lists; `remindctl list Work` shows one list's items
remindctl search "invoice" --list Work
remindctl info 4A83 --json # one reminder by index or ID prefix
remindctl today --json     # parse this way, not by scraping the pretty output
```

Output flags are global: `--json`, `--plain` (TSV), `--quiet`, `--format table`,
`--no-color`, `--no-input`. Reminders sort by due date, then title, then stable
ID, so use IDs — not numeric indexes — whenever the list can change under you.

### Create

Confirm the title, list, and due date back to the user before creating; a request
that already states them ("明天下午取快递") is itself that confirmation.

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
remindctl add --title "Take vitamins" --due tomorrow --repeat daily
```

`--due` and `--alarm` are different fields, which is the classic mistake here:

```bash
remindctl add --title "Hairdresser" --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
remindctl edit 87354 --alarm "2026-05-15 13:30"
remindctl edit 87354 --clear-alarm
```

`--due` is the deadline; `--alarm` is the notification. Reminders.app may group
or display the item by the alarm time, so **verify with `remindctl today --json`
and read `dueDate` vs `alarmDate`** rather than assuming the due time moved.
Changing only `--due` leaves existing alarms untouched.

Accepted dates: `today`/`tomorrow`/`yesterday`, `YYYY-MM-DD`,
`YYYY-MM-DD HH:mm`, ISO 8601 with offset. Date-only is all-day; date-time is
timed. Impossible dates and trailing text are rejected, not normalized.

### Update

```bash
remindctl edit 87354 --title "New title"
remindctl edit 87354 --list Office          # or --list-id 7A12
remindctl complete 1 2 3
remindctl delete 4A83 --force
```

`edit`/`complete`/`delete` take indexes from the current listing or an ID prefix.

## Verification and rules

1. Re-read with `--json` after every mutation; report the actual `id`, `dueDate`,
   and `alarmDate`, not the values you intended to set.
2. `Reminder is missing a calendar` means EventKit saved it but could not attach
   a list — check Reminders.app before retrying, or you create a duplicate.
3. Confirm content and due date before creating unless the request already
   specified them.
4. `delete` is irreversible: confirm the target by title first.