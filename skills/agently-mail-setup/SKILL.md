---
name: agently-mail-setup
description: "Use only when agently-cli is not installed, command not found, or its OAuth grant expired: npm install, auth login, re-auth. 邮箱命令行 安装 授权 失效。Never for reading or sending mail."
version: 0.3.0
license: MIT
metadata:
  hermes:
    related_skills: [agently-mail]
---

# agently-cli setup and reauthorization

Only setup, explicit CLI upgrades or expired OAuth grants. Reading/sending mail
uses [`agently-mail`](../agently-mail/SKILL.md). Inspect the current state first;
a normal mail request must not reinstall tools, replace skills or reset credentials.
## Index

§1 Check prerequisites and install only if needed · §2 Check the current credential namespace · §3 OAuth only when required · §4 Verify the actual account


## 1. Check prerequisites and install only if needed

```bash
command -v agently-cli
node --version
npm --version
```

Use the package's declared Node engine requirement rather than a remembered
version cutoff. If the CLI is absent or the user requested an upgrade:

```bash
npm install -g @tencent-qqmail/agently-cli
agently-cli --version
```

Check the exit status and actual version. A blocked security check is not a
successful install; report it rather than bypassing policy or installing an
untrusted mirror. Vendor setup reference: `https://agent.qq.com/doc/cli-setup.md`.
Read current authoritative instructions if package behavior differs.

**Do not run a skill installer as part of CLI setup.** This repository's mail
skill is locally curated. `npx skills add` can overwrite it; a vendor import or
replacement needs a separate explicit request, reviewed diff and verification.
Do not auto-link or replace another agent/profile's skills directories.

## 2. Check the current credential namespace

Run `agently-cli auth status` inside the agent that will use mail. Credentials
can be scoped by `AI_AGENT`; an agent-less shell's authorization error does not
prove the intended agent lost its grant. Check that identity before reauthorizing.
Never print session keys, tokens or credential files, and do not delete a working
grant merely because a different shell cannot see it.

## 3. OAuth only when required

Start `agently-cli auth login` as an interactive background PTY session, recording
its exact session/PID and cleanup immediately. Read its actual output; do not
fabricate an authorization URL or verification code.

Show the CLI's original authorization URL in a code block containing only that
unchanged URL, preceded by `请点击或复制以下链接在浏览器中完成授权：`.
Do not decode/rebuild its query, append punctuation, enter passwords/codes on the
user's behalf or ask the user to paste a code into chat. The user completes the
grant in their browser through the approved interactive flow.

Poll that exact session until it exits; failed/timed-out login is not success.
Report the error instead of automatically restarting OAuth or minting duplicate
requests. On cancellation or timeout stop the owned session and verify it and its
children exited; do not terminate another login session or the user's browser.

## 4. Verify the actual account

```bash
agently-cli +me
agently-cli auth status
```

Require successful CLI results and a real mailbox in the returned account/aliases.
Do not infer an email address from the OS login or an old session. Reply with the
actual account and authorization status, or the concrete failure; do not claim
mail delivery was tested because setup succeeded. No mail is sent during setup.

Temporary verification processes, tabs and files follow the
[resource lifecycle rule](../agent-skills-source-sync/SKILL.md#临时验证资源生命周期硬规则-3-细则).
Retain a resource only on explicit user request, with ownership and stop instructions.
