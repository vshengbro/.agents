# GitHub auth: scope gates, sudo re-auth, device-flow forms

Reference for the failure modes that hit `gh auth refresh` and the REST API's
per-endpoint scope gates. The entry point (`SKILL.md`) keeps the shortest
working path; this file keeps the diagnostics.

## Scope gates are per-endpoint, not per-account

`DELETE /repos/{owner}/{repo}` needs `delete_repo`, which `repo` does not
imply — a `403` whose body names the missing scope is the whole answer.
Extend with:

```bash
gh auth refresh -h github.com -s delete_repo
```

## `gh auth refresh` ends in a sudo-mode re-auth

The device flow grants the scope, then GitHub asks for a password / 2FA /
passkey before it takes effect. That re-auth is the account owner's to
complete: hand over the command and the one-time code, then wait. Do not
drive the browser through a credential prompt, and do not accept the
credential in chat.

Where the surrounding work must be prepared around that hand-off, prepare the
**submission** (the exact URL, the hidden fields, the session cookie) so the
owner's step is one command. Do not prepare it by taking their code and
submitting it on their behalf: that is the same act with the consent
invisible, and it also fails — a TOTP is valid about 30 seconds, so the chat
round trip spends it before it can be used.

## A flagged account cannot authorize a third-party app at all

The symptoms are the ones a session conflict also produces: a permanently
disabled Authorize button, a "You signed in with another tab or window" flash,
a `401` on a POST that returned `200` a moment earlier. The tell is a banner
on the page the flow redirects to — "This account is flagged, and therefore
cannot authorize a third party application." Read the page the failure lands
on before re-deriving the cause from the symptoms; no amount of session repair
clears a flag, and it needs GitHub Support.

## The device-code form's dash may be a slot or may be static text

A form filled with only the character slots submits `?reason=not_found` while
looking completely filled. Enumerate the inputs and fill by id rather than
assuming a layout — on some renderings the ids run 0..8 with slot 4 holding
the dash (9 characters including it), on others 0..7 with the dash as a
static separator (8 characters). The code is single-use and short-lived —
regenerate rather than resubmit a stale one.

Filling the slots is the harder half: drive them through the page's own
script (write each value with the native `HTMLInputElement` setter and
dispatch `input` + `change`, dash included), or type the whole code into the
**first** slot and let the page advance the focus. Setting the slots one at a
time does not work — each has `maxlength=1`, so one write fits one character.

## Two browsers, one account

Give the second browser the user's session cookie (one session, two browsers)
or close the site's tabs in the other browser — do **not** sign either out,
which invalidates the token the user's live browser holds.

## Symptom table

| Symptom | Cause | Action |
|---|---|---|
| `gh auth refresh` never completes | the browser needs a sudo-mode password/2FA re-auth | that step is the user's; surface the code and wait |
| the device flow's Authorize click lands on the dashboard and nothing happens | the account is **flagged** and cannot authorize third-party apps | the dashboard banner says so; it needs GitHub Support, and no session repair clears it |
| a submitted 2FA code is rejected with `422` | the code expired — a TOTP lives ~30s and the chat round trip spends it | do not accept a TOTP in chat; have the owner complete the re-auth in their own browser, with the submission pre-staged so their step is one command |
| GitHub pages show "You signed in with another tab or window" | a second browser holds a session for the same account | give the copy the user's session cookie (one session, two browsers) or close the site's tabs in the other browser — do **not** sign either out, which invalidates the token the user's live browser holds; one account, one session |
