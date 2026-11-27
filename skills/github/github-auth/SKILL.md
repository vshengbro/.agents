---
name: github-auth
description: 'Use when GitHub access fails or auth must be set up: gh CLI login, personal access tokens, SSH keys, and the keyring/env traps that make gh report "not logged in" when a token exists.'
license: MIT
---
# github-auth

Get GitHub working, then verify with a real command — not with `gh auth status`
alone. Auth setup is a prerequisite for `github-code-review`,
`github-repo-management` and `gh-pr-creation-workflow`, but those skills assume
it already works; load this one when it does not.
## Index

§1 gh CLI (preferred) · §2 Token without gh · §3 SSH · §4 Git identity is separate from GitHub auth


## Detect first

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>&1 | head -5
git config --global --get credential.helper || echo "no credential helper"
```

`gh auth status` printing a scope list does **not** prove API calls work.
Proof is `gh api user --jq .login` (or a `git ls-remote`).

## 1. gh CLI (preferred)

```bash
gh auth login                       # interactive: GitHub.com → HTTPS → browser
gh auth login --with-token < token.txt
gh auth setup-git                   # wires the git credential helper
```

**Device flow, when interactive login is impractical** (agent-driven session,
headless). gh's public OAuth client id, so no app registration is needed:

```bash
RESP=$(curl -s -X POST -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a&scope=repo,read:org,gist" \
  https://github.com/login/device/code)
USER_CODE=$(sed -nE 's/.*"user_code":"([^"]*)".*/\1/p' <<<"$RESP")
echo "Go to https://github.com/login/device and enter: $USER_CODE"
# poll /login/oauth/access_token with the device_code; handle
# authorization_pending (keep polling), slow_down (+5s), expired_token, access_denied.
# Pipe the token straight into gh; never echo or log it.
gh auth login --with-token <<<"$TOKEN"
```

`repo,read:org,gist` is the documented minimum; add `workflow` only when you
push workflow files. Later: `gh auth refresh -h github.com -s write:discussion`.

**Scope gates are per-endpoint, not per-account.** `DELETE /repos/{owner}/{repo}`
needs `delete_repo`, which `repo` does not imply — a `403` whose body names
the missing scope is the whole answer. Extend with
`gh auth refresh -h github.com -s delete_repo`.

**Ask for a device code, never for a 2FA/TOTP.** The device code is a routing
token, not a secret — it authorises an application, it does not authenticate
the person, and it can be pasted into chat. An authenticator-app code *is* the
person's credential, and asking for one in chat crosses a line the tooling
draws deliberately: a code that authenticates the account should be entered
by the account owner, in a place the owner controls. So when the sudo
re-auth needs a second factor, the ask is for the **owner to complete it** —
run the command, finish the prompt in their own browser, then report back —
not for them to hand the code over.

Where the surrounding work must be prepared around that hand-off, prepare the
**submission** (the exact URL, the hidden fields, the session cookie) so the
owner's step is one command. Do not prepare it by taking their code and
submitting it on their behalf: that is the same act with the consent
invisible, and it also fails — a TOTP is valid about 30 seconds, so the chat
round trip spends it before it can be used.

A flagged account cannot authorize a third-party app at all, and the device
form's dash may be a slot or may be static text — both failure modes, plus
the symptom table, are in
[references/scope-gates-and-device-flow.md](references/scope-gates-and-device-flow.md).

**Headless keyring hang.** On keyring-less hosts (VPS, containers) `gh auth
login --with-token` can block forever waiting on a secret service, even with
`--insecure-storage` and no output. Wrap it in `timeout 20 …`; on exit 124
write the credential store directly instead:

```bash
mkdir -p ~/.config/gh
printf 'github.com:\n    users:\n        %s:\n            oauth_token: %s\n    git_protocol: https\n    oauth_token: %s\n    user: %s\n' \
  "$LOGIN" "$TOKEN" "$TOKEN" "$LOGIN" > ~/.config/gh/hosts.yml
chmod 600 ~/.config/gh/hosts.yml
gh auth status && gh auth setup-git
```

`gh auth status` and `setup-git` read that file without touching the keyring,
so they work immediately.

**When a PTY is involved** (Windows agent sessions), answer prompts with
`process(submit)` — a bare `\n` via `process(write)` is not delivered as a line
terminator on a ConPTY, and `gh`'s blocking "Press Enter" prompt never returns.

## 2. Token without gh

```bash
git config --global credential.helper store          # or: store --file=<path>
git ls-remote https://github.com/<user>/<repo>.git   # prompt: username + token as password
```

GitHub disabled password auth: the token **is** the password. Scopes:
`repo`, `workflow`, `read:org` (private orgs). Never embed the token in a
remote URL — it leaks into `.git/config`, shell history and process listings.

Read the token back out of the credential store with the helper script
(`scripts/git-credential-token.py`, pass the store path explicitly when
`credential.helper` is `store --file=…`), or set `GITHUB_TOKEN` directly.

## 3. SSH

```bash
ls ~/.ssh/id_*.pub 2>/dev/null || ssh-keygen -t ed25519 -C "$EMAIL" -f ~/.ssh/id_ed25519 -N ""
ssh -T git@github.com      # "Hi <user>! You've successfully authenticated"
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

On this host `gh auth status` reports protocol `ssh` — SSH is the working push
path, which also sidesteps the HTTPS-push stall described in
`gh-pr-creation-workflow/references/network-and-api-fallbacks.md`.

## 4. Git identity is separate from GitHub auth

Auth gets you access; `user.name` / `user.email` decide the commit author.
They are a separate concern, governed by `git-standards` §4 — set once in the
global config, never per commit.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `gh auth status` says not logged in while the user has a working `GH_TOKEN` | the token lives in `~/.bashrc` / `~/.profile`, and a non-interactive agent shell never sources them | `source ~/.bashrc ~/.profile` in the same call, or wrap the command: `source ~/.bashrc ~/.profile; exec <cmd>` |
| `git push` asks for a password | password auth is disabled | paste the PAT instead |
| `remote: Permission denied` | token lacks `repo`, or the repo needs `read:org` | check `gh auth status` scopes; regenerate |
| `ssh: connect to host github.com port 22: Connection refused` | port 22 blocked | add to `~/.ssh/config`: `Host github.com` / `Port 443` / `Hostname ssh.github.com` |
| `gh pr edit --body-file` fails with a scopes error | GraphQL needs `read:org`; the token has only `repo` | use REST: `gh api -X PATCH repos/<o>/<r>/pulls/<N> -f body=…` |
| `fatal: could not read Username` in CI | workflow token/secret missing | add the `permissions:` block; `gh secret list` |
| `gh auth refresh` refuses | `GH_TOKEN` is set in the environment | clear it for the refresh call, or have the user regenerate the token |
| Two GitHub accounts | one credential store | separate `~/.ssh/config` host aliases, or per-repo credential URLs |
