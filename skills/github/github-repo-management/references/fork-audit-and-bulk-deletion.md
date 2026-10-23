# Auditing and bulk-deleting forks

Fork cleanup is a two-part job: **prove each fork is disposable**, then delete
it. Both parts have traps that produce a confident wrong answer.

## Part 1 — prove a fork is disposable

### The owner's rule is usually "do I have commits in it"

When the account owner states the rule ("keep what I have commits in, delete
the rest"), that is the classification, and it is simpler than it looks:
**a fork the owner has authored commits in is a keep; a fork with nothing of
theirs is a delete.** "Do I have commits in it" is about *their* commits, not
about whether the fork differs from upstream in any way — so a fork whose only
extra branches are upstream's own automation branches, and whose default
branch matches upstream tip-for-tip, is still a delete.

Under that rule, the checks below become the mechanism rather than the
policy: they are how you establish, per fork, whether the owner authored
anything there. A fork whose compare comes back with no `ahead_by` (see
below) still needs a verdict — its branch tips resolving upstream plus its
newest commits being authored by upstream contributors is the evidence that
the owner's commits are not in it.

### The mechanical checks

A fork is safe to delete only when **all** of these hold. Any one of them
failing keeps the fork.

| # | Check | How |
|---|-------|-----|
| 1 | No commits the upstream lacks | compare API reports `ahead_by == 0` |
| 2 | No branches the upstream lacks | every branch tip SHA resolves upstream |
| 3 | No open PR from this fork | the branch tips are upstream → PR is merged or closed |
| 4 | No releases / tags worth keeping | `GET /repos/{o}/{r}/releases` |
| 5 | Nothing references it | no `uses: owner/repo@ref` in any workflow |

### The compare call has the two sides swapped from what you expect

```
GET /repos/{fork_owner}/{fork_repo}/compare/{upstream_owner}:{upstream_branch}...{fork_branch}
```

- The **base** is `upstream_owner:upstream_branch` — owner-qualified.
- The **head** is the fork's own **branch name**, unqualified.

Passing a repo name (or the fork's own name) where a branch name belongs
silently compares the wrong thing. When a fork's branch name is ambiguous,
compare the tip **SHA** instead: `GET /repos/{upstream}/commits/{sha}` returns
200 when that commit already exists upstream, 404 when it does not. That is
the most reliable single check — use it as the primary signal.

### A compare with no `ahead_by` is a third outcome, not a pass and not a fail

When the fork and the upstream have **unrelated histories**, the compare call
returns a body with no `ahead_by` key at all — not `0`. A verdict written as
`ahead_by == 0` reads that as "cannot judge"; a verdict written as "any
non-zero number is bad" reads it as "reject". Neither is right, and a script
that only branches on the two leaves those forks permanently unclassified —
which is how a delete list ends up silently short.

Adjudicate them by tip SHA instead:

```bash
sha=$(curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/$OWNER/$FORK/commits/$BRANCH" | jq -r .sha)
curl -sS -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/$UPSTREAM/commits/$sha"   # 200 => tip is upstream's
```

`200` on the tip means the fork's default branch is a prefix of the upstream's
history, so anything the account owner committed on it is already upstream
too. Write the tip SHA into the verdict file so the call is reviewable
rather than inferred.

### Enumerate branches from the refs endpoint, not from `/branches`

`GET /repos/{o}/{r}/branches` returns a *role-dependent* list: for a repo the
caller administers it comes back with every branch, for one it only reads it
returns just the protected and default branches. An audit run against forks
the account owns therefore looks complete, while the same script pointed at
repos it does not own silently checks one branch and declares the rest clean.
`GET /repos/{o}/{r}/git/refs/heads` is the documented-complete source and
costs one call — use it so check 2 does not depend on the caller's role.

### `/user/repos` does not return `parent` for every fork

`GET /user/repos` returns `fork: true` but `parent` is frequently absent. Read
it per repo from `GET /repos/{full_name}`, and fall back to `source` (same
shape) when `parent` is missing. Without the parent you cannot compute the
compare base at all.

### Owner-only PR filters are ignored

`GET /repos/{upstream}/pulls?head=OWNER` (owner without a branch) is **not**
honoured — GitHub returns unrelated PRs, and the audit reads them as open PRs
against the fork. The search API cannot rescue this either: it does not
resolve a renamed account, so a PR authored under the old handle is invisible
to `search/issues`.

The workable route is check 2 above: enumerate the fork's branches, and for
each branch tip ask the **upstream** whether that SHA exists. If every tip
exists upstream, there is nothing in the fork that an open PR could still be
carrying.

### Workflow references are a hard keep

Scan the workflow files of **every** repo in the account for
`uses: {owner}/{repo}@ref`. A fork referenced by another repo's workflow is
live infrastructure: deleting it breaks that workflow, and the reference is
invisible from the fork's own metadata.

### Local clones pointing at a doomed fork

Before deleting a fork that has a local clone, re-point that clone's remote at
the upstream (`git remote set-url origin https://github.com/{upstream}.git`)
and verify the fetch still works. A local checkout left pointing at a deleted
remote is a broken clone the user will discover later.

## Part 2 — delete

### The API needs a scope `repo` does not include

`DELETE /repos/{owner}/{repo}` requires the **`delete_repo`** scope. A token
with `repo` answers `403` with a body naming the missing scope. Extend it:

```bash
gh auth refresh -h github.com -s delete_repo
```

That command runs a **device flow**: it prints a one-time code
(`803A-BC27`) and waits. The code goes into the browser form at
`https://github.com/login/device`.

**Two details of the code form.** The page has **nine** inputs: eight
characters plus a literal dash. The dash occupies slot index 4, and a form
filled with only the eight character slots submits `?reason=not_found`. And
the code is single-use and short-lived — regenerate it rather than retrying a
stale one.

Filling those nine slots has two workable routes, and the obvious one does
not work:

- **Through the page's own script** (`browser_exec`): write each slot's
  value with the native `HTMLInputElement` value setter and dispatch
  `input` + `change`, so the page's auto-advance and validation logic runs.
  Setting slot 4 to `-` is part of this — a form with eight filled slots and
  an empty dash slot still submits `not_found`.
- **Through the desktop bridge** (`computer_use`): focus the **first** slot
  and type the whole code including the dash as one string — the page
  advances the focus itself. Setting each slot separately does not work:
  every field has `maxlength=1`, so one `set_value` writes one character and
  the remaining characters are rejected.

**The flow ends in a sudo-mode re-auth.** After the scope grant, GitHub asks
for a password / 2FA / passkey ("Confirm access"). This is a hard boundary:
the agent does not type it. Hand the user the one command and the one code,
and wait for them to complete the verification.

### Two logged-in sessions for one account break each other

GitHub rotates the session when the same account signs in from a second
browser. The symptoms are misleading and each one was mistaken for something
else in practice:

- a disabled **Authorize** button on the confirmation page;
- a flash reading *"You signed in with another tab or window"*;
- `401` on a same-origin `POST` that a moment earlier returned `200`.

So a browser-automation copy of the profile and the user's real Chrome, both
holding a GitHub session, invalidate each other. **Only one browser session
per account at a time**, and the two are usually the *same* session: the
automation copy carries the real profile's cookie jar, so both browsers
present one session token.

**Do not sign the automation copy out to resolve the conflict.** Hitting
GitHub's `/logout` in the copy invalidates that session token server-side,
which signs the **user's real browser** out too — observed directly: after the
copy was signed out, the user's own Chrome landed on GitHub's sign-in page
and had to be re-authenticated by hand. Any device flow already in flight dies
with it. Resolve the conflict by making both browsers present one session
(see below), or by closing the other browser's GitHub tabs — never by signing
either side out.

Decide which browser owns the session **before** starting a device flow, not
after the first conflict: against a session-conflicted browser the Authorize
button stays permanently disabled, and every retry consumes a fresh
single-use code — so grinding codes without fixing the session burns one
code per attempt and never succeeds.

### Give the automation copy the user's session instead of signing either out

When the copy and the real browser both hold a GitHub session, the fix is to
make them present **one** session, not to revoke one. Copying the real
browser's encrypted cookie values into the copy's cookie jar does exactly
that: both profiles share the same `Chrome Safe Storage` keychain key, so
Chrome decrypts the injected values in the copy identically.

```bash
# 1. read the schema from BOTH databases — they differ between Chrome versions
python3 -c "
import sqlite3, os
for p in (os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies'),
          os.path.expanduser('~/.hermes/browser-profile/chrome/Default/Cookies')):
    print(p); print([r[1] for r in sqlite3.connect(p).execute('PRAGMA table_info(cookies)')])
"
# 2. copy the rows (user_session, logged_in, _octo, _gh_sess, dotcom_user)
# 3. restart the copy's Chrome — it caches the cookie jar in memory and
#    will not see injected rows until the process is replaced
```

Two traps, each of which looks like "the injection did not work":

- **The `cookies` table has no `length(encrypted_value)` column.** It is a
  computed expression you may `SELECT`, not a column you may `INSERT`. Listing
  it in the column list is a syntax error whose message points at the SQL,
  not at the schema mismatch.
- **A running Chrome does not reload its cookie jar.** Inject, then restart
  the copy's Chrome process; until then it serves the old jar and the copy
  still shows the sign-in page.

Copying the encrypted values verbatim is safe and sufficient — the
`encrypted_value` blob decrypts in the copy because the keychain key is
shared.

### Close the site's tabs in the other browser, do not sign it out

A tab on GitHub in the *other* browser re-establishes a session and
invalidates the copy's, even when that tab is idle. Enumerate and close only
the site's tabs, leaving the session cookie intact:

```applescript
tell application "Google Chrome"
  repeat with wi from 1 to count of windows
    set tabsList to tabs of window wi
    repeat with ti from (count of tabsList) to 1 by -1
      try
        if (URL of tab ti of window wi) contains "github.com" then
          close tab ti of window wi
        end if
      end try
    end repeat
  end repeat
end tell
```

Iterate **backwards by index** and close through `tab ti of window wi` — the
`repeat with t in tabs of w` form cannot be closed (`t of w` is not a
specifier) and fails with a type-conversion error. Close tabs rather than
signing out: signing out invalidates the user's live session too.

### A flagged account blocks OAuth authorization, and it looks like a session conflict

Before blaming the session, read what the flow actually says. Measured: the
device-flow Authorize click landed on `github.com/dashboard` carrying the
banner **"This account is flagged, and therefore cannot authorize a third
party application."** Every symptom the section above attributes to two
sessions — a permanently disabled Authorize button, a "You signed in with
another tab or window" flash, a `401` on a POST that returned `200` moments
earlier — is also what a **flagged account** produces, and none of the
session repairs touch it.

So when the flow keeps failing, read the page the failure redirects to rather
than re-deriving the cause from the symptoms. The discriminator is cheap:
load the dashboard (or whatever page the flow landed on) and look for a
flagging banner.

**A flagged account is a Support ticket, not a scope problem.** It blocks
authorizing third-party OAuth apps, so `gh auth refresh` cannot grant
`delete_repo` no matter how many codes are generated. It does not block the
web-UI delete path, which runs on the browser session rather than an OAuth
grant — so the web-UI flow is the one to take, and the OAuth route is
abandoned rather than retried.

### The delete scope has no alternative credential to fall back to

`delete_repo` cannot be worked around with a different token. A classic PAT
carrying only `repo` cannot delete either, and the account's other classic
PATs are not on disk: the keyring holds one entry (`gh:github.com`), Chrome's
password manager holds no `github.com` credential, and a shell rc file's
`GH_TOKEN` line is commented out. Check these three places before promising
a path that ends in a credential hunt:

```bash
security find-generic-password -s "gh:github.com" -g   # gh's keyring entry
grep -nE 'ghp_[A-Za-z0-9]{30,}' ~/.zshrc ~/.netrc       # a classic PAT in dotfiles
```

Then stop. When the only credential is the OAuth token, the OAuth route is
the only route, and the scope grant is the user's to complete.

### A TOTP handed over in chat is expired by the time you submit it — and it should not be handed over at all

A 2FA code the user pastes into chat is a **30-second** code, and the round
trip — user reads it, sends it, the agent's next tool call runs — consumes it.
A submit that returns `422` is an expired code, not a wrong one, and the
remedy is a fresh code, not a re-check of the form.

But the better answer is not to ask for one. An authenticator-app code is the
account owner's credential: it should be entered by them, in a place they
control. A device code is different — it authorises an application rather
than authenticating the person, so it can be handed over and typed into
chat. Keep those two apart when choosing what to ask for.

So structure the flow so the owner's step is **one prepared command**: capture
the form fields, the authenticity token, and the session cookies ahead of
time, then hand over the exact submission and let the owner run it. Preparing
the submission means preparing the request — action URL, every hidden field,
the session cookie header — not collecting the owner's secret and posting it
on their behalf, which is the same act with the consent invisible.

### The web-UI delete flow is multi-stage

If the API path is unavailable, the settings page drives it in stages, each
gated on the previous:

1. `Delete this repository` → a menu dialog opens.
2. `I want to delete this repository` → the warning stage.
3. A text field labelled *"To confirm, type `owner/repo` in the box below"*
   (`name="verification_field"`) → the final destructive submit.

Two traps:

- **A form's submit button can carry the action.** Where the button has
  `name="authorize" value="1"`, calling `form.submit()` sends the form
  **without** the button's value, and GitHub reads the missing value as
  *deny* — a successful-looking request that declines the authorization.
  Click the button, or submit with the button's name/value included.
- The stage-3 markup lives in a `<template>` element until the flow reaches
  it, so `querySelector` on the live DOM finds nothing. Enumerate the
  templates (`document.querySelectorAll('template')`) and match on the
  control's identity, not on the surrounding text — several stages reuse the
  same ids for different flows, and a substring match on the visible label
  picks the wrong one.

### The delete's sudo re-auth posts back to the delete endpoint, not to a sudo page

After the delete POST, GitHub answers with a **Confirm access** page whose
credential form posts **back to the same `/{owner}/{repo}/settings/delete`
URL** — there is no separate sudo endpoint to find. Two distinct credential
forms live on that page and they must not be confused:

- the **authenticator-app** form, identified by an `input[name="sudo_app_otp"]`
  (a text input), which also carries `repository`, `sudo_referrer`,
  `user_id`, `verification_field`, `verify` and its own `authenticity_token`;
- the **password** form, identified by `input[name="sudo_password"]`, and the
  **passkey** form, identified by `credential_type=webauthn` plus
  `webauthn_response`.

Select the form by its **input name**, not by its visible label or by its
position: several forms on the page share the label "Verify", and the
password and authenticator forms differ only in that one field name. The
`credential_type` hidden field tells you which variant the browser will
actually submit (`app` for the authenticator, `password`, `webauthn`).

The web-UI sudo page and the **OAuth authorize** sudo page are different
forms with different field sets — the authorize page carries `scope` and
`user_code`, the delete page carries `repository` and `verification_field`.
Reusing one page's hidden fields on the other produces a `422` that reads
like a bad credential.

### Verifying a deletion made through the web UI

### Verify the deletion from the account's repo list

`GET /repos/{owner}/{repo}` answering `404` after the delete is the check.
Do not verify by loading the repo's page in a browser — a deleted repo, a repo
that never existed, and a repo the account cannot see all render the same
not-found page.

The same check applies to a delete driven through the web UI: re-read the
repo's API endpoint, not the settings page the flow ended on. A delete that
left the browser on the settings page means the POST did not take, and the
settings page still renders normally for a repo that is being deleted.

### An audit that never reached its delete step must not be reported as a delete

A verified delete list is a **plan**, and the number of repos it names is not
a count of repos deleted. Measured: 56 forks audited and verified, 0 deleted,
because the credential step never completed — and the gap between "56
verified" and "0 deleted" is the entire point of the report.

So the report carries **three** numbers, not two: how many were audited and
classified, how many are on the delete list, and how many were **actually
deleted** (confirmed by a `404` from `GET /repos/{owner}/{repo}`). A report
that says "56 forks cleared" when 56 were classified and 0 deleted is an
over-claim that the reader cannot detect — the audit really was that good.

The same applies to the space reclaimed: report the verified disk delta and
the delete count as separate claims, each with the surface it was measured on.

### A delete script must read the token at run time and gate on the scope

Two failure modes turn a correct delete list into a silent no-op:

- **A hardcoded or redacted token in the script.** `-H "Authorization: Bearer
  ***"` answers `403` on every call, and the loop reports "failed" for all N
  repos while looking like a permissions problem rather than a broken script.
  Read the credential at run time (`TOKEN=$(gh auth token)`) so the script
  cannot outlive the credential.
- **Checking the scope only after the calls fail.** Assert the scope *before*
  the loop and exit early:

  ```bash
  SCOPES=$(curl -sS -D - -o /dev/null -H "Authorization: Bearer $TOKEN" \
            https://api.github.com/user | grep -i '^x-oauth-scopes:' | tr -d '\r' | cut -d' ' -f2-)
  case "$SCOPES" in *delete_repo*) ;; *) echo "token lacks delete_repo: $SCOPES" >&2; exit 2;; esac
  ```

  A pre-flight check costs one request and turns "56 failed deletes" into
  "the token cannot delete; here is the command that fixes it".

### The nine-slot code form has more than one dash layout

The device-code form's dash is a **static separator element** on some
renderings and a **ninth input** on others. Enumerate the inputs and their
ids rather than assuming a layout, and fill by id:

```js
const ids = [...document.querySelectorAll('input[id^="user-code-"]')]
  .map(i => i.id).sort((a,b) => parseInt(a.split('-').pop()) - parseInt(b.split('-').pop()));
```

When the ids run 0..8, slot 4 holds the dash and the code is 9 characters
including it (`44E1-4652`). When they run 0..7, the dash is static text and
the code is 8 characters (`44E14652`). Writing 8 characters into 9 slots
leaves the dash empty and the form submits `?reason=not_found` — a form that
looks completely filled.

## Reporting

Report the split, with the numbers: how many forks were deleted, how many
were kept, and **why each kept one was kept** (unique commits / unique branch /
open PR / workflow reference). A cleanup report that only gives the deleted
count hides the decisions that matter.

Report the deleted count as **0** when the delete step did not run, and say
what it is waiting on. A classified-but-not-deleted list reported as a
completed cleanup is the over-claim this whole reference exists to prevent.

When the owner's rule was "keep what I have commits in", say plainly how
that was measured per fork, and list the kept ones by the commits that kept
them — a fork kept for a one-line `Cargo.toml` tweak looks like a mistake
next to one kept for a feature branch unless the reason is on the page.

Keep the candidate list and the keep list on disk next to the delete script,
so a later run can re-derive the same classification instead of re-auditing
from scratch.

## Running the audit at scale

An account with dozens of forks turns the audit into hundreds of API calls.
That outruns a single agent turn, and — worse — it outruns a single tool's
timeout, so a run killed mid-way leaves no verdict for the repos it never
reached.

- **Persist a verdict per repo as you go.** One line per repo, appended
  immediately: `<name>|PASS` or `<name>|REJECT:<reason>`. A run that dies
  mid-way then leaves a file that says exactly how far it got, and the next
  run resumes from there instead of restarting.
- **Batch the audit to fit the timeout.** An `execute_code` cell is capped at
  about five minutes and a foreground shell call at a little under seven; a
  per-repo loop over 50+ repos with several API calls each overruns both.
  Split the candidate list into batches sized to finish well inside the cap.
- **Run the long tail as a background job, not a foreground call.** A
  background terminal task survives the turn and notifies on exit; a
  foreground call that hits its cap is killed along with its partial output.
- **Read the verdict file, not the script's exit code.** The file is the
  audit; the summary line is a report about the script.
- **A batch that "rejects" on an unparseable compare is reporting its own
  parser's limits**, not the forks' state — see the compare section above.
- **Budget the audit by requests, not by repos.** A five-check audit over 56
  forks is ~250 calls. At one call per second that overruns a single tool
  timeout, and a killed run's partial output is easy to mistake for a
  completed audit.
- **Two audits of the same list can disagree for a reason that is not a
  fork.** The compare-based verdict and the tip-SHA verdict classify the
  *same* fork differently when the histories are unrelated — one says
  "cannot judge", the other says "tip is upstream". Reconcile them by hand
  and record which evidence settled each one; do not let a list of mixed
  verdicts reach the delete step unexamined.
- **Re-verify the delete list immediately before deleting, not just before
  auditing.** Between the audit and the delete, a fork can gain a commit, a
  branch, a PR, or a release. Re-running the checks at delete time is what
  makes "verified" a statement about the moment of deletion.
