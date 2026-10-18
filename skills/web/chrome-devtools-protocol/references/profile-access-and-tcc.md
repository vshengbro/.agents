# Browser profile access: real-profile consent, TCC, and locks

Depth notes for the "attaching to a logged-in browser" section of SKILL.md.
Read when the browser profile is unreadable, or when the task needs the user's
real logins.

## 1. Ask the toolchain before improvising

In Hermes, signed-in browsing is configured, not hand-rolled. The supported
setting is the `browser` toolset with real-profile consent:

```bash
hermes config set browser.use_real_profile true   # consent: browse with real logins
hermes config get browser.use_real_profile        # read back
```

`use_real_profile` does **not** attach to the user's daily Chrome window — that
would fight the running instance for the profile lock. It snapshots the
default-Chromium profile into a Hermes-owned copy
(`~/.hermes/browser-profile/<browser>`), launches the **real system browser
binary** on that copy, and re-syncs the auth databases per fresh session. Two
consequences worth stating before you promise anything:

- The copy deliberately omits `--use-mock-keychain` / `--password-store=basic`,
  so macOS keychain-encrypted cookies decrypt and the session is genuinely
  signed in. A dev/automation Chrome that *does* pass those flags shares no
  login state at all — the usual reason an "already signed in" page looks logged
  out to the agent.
- Turning the key back off deletes `~/.hermes/browser-profile/`, so revoking
  consent also removes the copied credentials. Check that path is gone rather
  than assuming no credential copies remain.

Config changes to tools take effect on a new session (`/reset`), not
mid-conversation. Signed-in browser work goes through `browser_exec`, not
`computer_use` — the typed desktop browser route and its `grant_existing_profile`
opt-in were removed from Hermes, and a leftover key in config.yaml is ignored.

## 2. TCC denial vs a real profile lock

These produce the same `PermissionError` and have opposite fixes, so never
trust the message text. The distinction is mechanical: **a real lock has a
`SingletonLock` symlink; a TCC denial does not.** Run the probe *before*
advising the user to quit their browser — telling someone to close Chrome when
the actual cause is a privacy grant wastes their time and fixes nothing.

```bash
python3 ../scripts/diagnose_chrome_profile_access.py [chrome|chromium|brave|edge]
# 0 readable/absent, 1 TCC privacy grant, 2 real lock
```

The probe decides TCC vs lock, sweeps sibling directories to show the boundary,
and walks the process ancestry to name the app that actually needs the grant.
What it checks:

- `os.listdir()` on the profile raising `PermissionError` with `errno == 1`
  (EPERM) is **TCC**, not Unix permissions. A Unix denial surfaces as
  `errno == 13` (EACCES).
- `stat` shows the profile owned by the invoking user with mode `0700` while
  the shell reads neighbouring directories fine — TCC is a per-app policy, not a
  filesystem mode.
- The denial is **selective across sibling app-data directories**: profiles
  denied while `Library/Preferences` is readable means an App Data privacy
  grant, not a broken browser.
- `os.path.isfile()` on a TCC-denied path returns `False` rather than raising.
  Code that branches on `isfile()` before opening silently treats "denied" as
  "absent" and reports a missing profile.

## 3. Who to grant, and why you can't grant it yourself

TCC is evaluated per **responsible application**, and a shell-launched agent
inherits the grant of whatever launched it (a terminal, a GUI terminal emulator,
an IDE). The grant must go to that ancestor app — not to Chrome, and not to a
`launchctl asuser` wrapper. Find the real holder by walking the ancestry (the
probe prints it):

```bash
PID=$$; for i in $(seq 8); do
  P=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' '); [ -z "$P" ] && break
  echo "$PID -> $P : $(ps -o comm= -p "$P" 2>/dev/null)"; PID=$P
done
```

The remediation is a user action in System Settings → Privacy & Security → Full
Disk Drive Access, granting the ancestor app, followed by a full quit and
relaunch of that app so the new grant is picked up. A grant cannot be issued
from the terminal — `tccutil` only resets entries, it cannot add them — so stop
and hand this to the user rather than attempting it.

## 4. When the user cannot relaunch Chrome

If the user is away from the keyboard and Chrome is already running without
`--remote-debugging-port`, **do not assume you can start a fresh Chrome on the
user's profile from Hermes**. Two paths both fail on recent macOS:

- `--user-data-dir=$HOME/Library/Application Support/Google/Chrome
  --profile-directory=Default`: the child Chrome inherits TCC restrictions from
  the Hermes process tree and exits immediately after launch — no listener
  appears. The block is on the user-data-dir itself; children inherit it.
- `launchctl asuser <uid> /Applications/Google Chrome.app/...`: same failure.
  `asuser` only changes uid context, not TCC inheritance.

Verifying the failure (cheap): launch with the flag, wait 3–8 s, then
`curl -s --max-time 3 http://localhost:9222/json/version`. An empty response
plus a live Chrome process that is not listening means TCC killed the
profile read while the launch itself succeeded.

Do not loop on launch attempts — each one confirms the same TCC boundary and
burns time. After two attempts, the remaining options are (a) the user
relaunching Chrome with the debug flag, (b) a token the user can paste into a
non-interactive input, or (c) an unauthenticated fallback the task actually
permits (public endpoints via `web_extract`, `blocked-page-recovery`).

## 5. Reusing an already-running agent-browser Chrome

If a previous `agent-browser open ...` left a Chrome for Testing alive with a
random `--remote-debugging-port=0`, find the port without relaunching:

```bash
PID=$(pgrep -f "agent-browser-chrome" | head -1)
lsof -p $PID 2>/dev/null | awk '/LISTEN/{print $9}'
```

Connect to it with raw CDP — but note the profile is empty, so it carries **no
user login cookies**. It is a functional headless Chromium, nothing more. If you
need the user's session, use the real-profile path in section 1 instead.
