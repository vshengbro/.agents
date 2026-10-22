# The dedicated browser and the state directory

## Why a dedicated browser

The harness browser answers 403 on x.com. It identifies as
HeadlessChrome, and the same URL answers 200 with an ordinary user agent
from the same address in the same second, so overriding the user agent
fixes the 403 — but the harness's own profile carries no x.com session,
so the page then redirects to the login screen. Fixing one breaks the
other.

`xbrowser.py` resolves both: it copies the session cookies out of the
user's real Chrome profile and launches a headless Chrome against the
COPY, in a private profile under the state directory.

- **The copy is a read-only sqlite backup**, not a file copy. Copying the
  `Cookies` file while a Chrome is running can miss a page still in the
  WAL, and the result is a profile that looks fine and is not signed in.
- **The real profile is never written to.** It is input, never output.
- **No window the user can see**, and no OS focus taken: the user can
  keep typing while a run works.
- **An already-running instance is adopted, not replaced.** The port file
  names the endpoint, and a scan of the skill's port range confirms a
  live one before anything is launched. Replacing a running instance
  deletes the profile the live one is using.
- **The private profile is rebuilt only when it has no session cookie.**
  If it already carries an `auth_token`, it is reused — rebuilding it
  under a running browser is what loses the session.

## Why the state directory and not scratch

`~/.hermes/state/x-post/` holds the browser endpoint, the account handle,
the answered ids, the publication record and the lock.

**It is deliberately not the scratch directory.** The daily cleanup
removes scratch files older than a day, and a port file that disappears
between two runs is a job that cannot find its own browser: the run
starts a second instance, and the two fight over one account.

**The state file is written atomically** — a temporary file, renamed over
the target, read back before the call returns. A bare `open(path, "w")`
truncates the moment it is called, so a write that raises afterwards
leaves a zero-byte file and every prior run's record gone. The rename is
what makes it atomic; the read-back is what makes it honest.

**The lock is advisory and per-process.** Two jobs on a schedule can
overlap, and a reply that lands under the wrong post is the result, so a
run that cannot take the lock waits and says so rather than proceeding.

**Every environment value is read at call time.** The state directory,
the browser endpoint, the account handle and the code directory live in
`xconfig.py` and are resolved when a script runs, never as module-level
constants. A constant is stale the moment the environment changes, and
the stale value is what a run uses.

**The account handle is discovered from the live page.** It is not
written down anywhere, so a rename of the account does not silently
point the scripts at the wrong identity.
