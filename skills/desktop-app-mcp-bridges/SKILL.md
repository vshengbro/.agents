---
name: desktop-app-mcp-bridges
description: "Use when wiring a desktop-app MCP bridge into Hermes."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [MCP, add-on, stdio, socket, Hermes, verification, skill-vendoring, Blender, TouchDesigner]
    related_skills: [hermes-agent, agent-skills-source-sync, install-mac-app]
---

# Desktop-app MCP bridges

## When to Use

Any task that connects Hermes to a third-party MCP server which is only useful while a **desktop application is running** — the server process is one half, an add-on/plugin hosted inside the app is the other. Trigger words: "install the X MCP", "connect Blender/TouchDesigner to Hermes", "set up the X addon bridge", "wire up the X plugin". Also use it when the deliverable includes vendoring that project's companion skill into `~/.agents`.

Not for: plain stdio MCP servers with no app-side half (use `hermes mcp add` directly), or using `bpy` headlessly with no bridge at all.

## The shape of the work

The class of work: a third-party project ships **two halves** — a server-side MCP process and an add-on/plugin hosted *inside* a running desktop app — and the two only talk when the app is up. Blender MCP, TouchDesigner's twozero.tox, and similar creative/CAD bridges all have this shape. Getting to a working state means both halves, and a verification that proves the loop is closed rather than assuming it.

`hermes mcp add` is a poor place to store durable knowledge (its reference lives in the bundled `hermes-agent` skill), so the Hermes-specific argument and diagnostics rules are pinned here.

## Procedure

1. **Read the upstream install docs for BOTH halves.** The server package and the app-side add-on are versioned and renamed independently; the server's own `--help` output is the most reliable source for its current entry point and any rename banner.
2. **Install the app-side add-on** with the server's installer subcommand, then re-run its "list my add-on paths" subcommand to confirm the file landed where the app actually looks. Do not hand-copy into a guessed directory.
3. **Enable the add-on in the app's saved preferences.** Most apps offer a headless/prefs mode that can enable a module and persist preferences without a GUI session. See `references/blender.md` for a working script and the two-run verification that actually proves persistence.
4. **Register the stdio server in Hermes**, with the runner's **absolute** path:
   ```bash
   printf 'Y\n' | hermes mcp add <name> --command /abs/path/to/runner \
       --env KEY=VALUE --args <package-name>
   ```
   Every flag goes **before** `--args`. Read the `mcp_servers.<name>` block back and confirm `env:` is a sibling of `args:`, not an item inside it.
5. **Verify with the ladder, in order.** All rungs, every time:
   - `hermes mcp list` — server present, `enabled`, transport resolved.
   - `hermes mcp test <name>` — stdio handshake and full tool inventory (this is the rung that proves the package actually runs).
   - `lsof -nP -iTCP:<port> -sTCP:LISTEN` — the app side is bound. Proves the two halves can meet.
   - **Call a real tool over the protocol** — the only rung that proves the loop is actually *closed* rather than merely reachable. A bound port means nothing if every tool errors on the first hop.
   `scripts/verify_mcp_bridge.sh <name> [port]` runs the first three and exits non-zero on the first failure. `scripts/probe_mcp_tools.py` runs the last one.
6. **Vendor the companion skill into `~/.agents`** (see below), then report: what is verified, what still needs a human action (typically "restart the app"), and what is uncommitted.

## Pitfalls

- **A bound port is not a working bridge.** Port-open is the strongest *static* signal available without calling anything, but a server can bind, list tools, and still fail on every invocation. Before reporting a bridge live, call one cheap read-only tool and show its real output — a scene listing, a status object, a byte count. "The port is open" is a weaker claim than "this returned this", and only the second survives a skeptical user.
- **Read the tool schema, never the companion skill's prose, when you need to call something.** Vendored skills are written against *some* release of a server that has since renamed tools; a doc naming `execute_python` when the live server only has `execute_blender_code` produces a plausible dead end. Dump the live schema first (rung 4), treat any vendored name as a hypothesis, and correct the vendored skill to match what the server actually serves.
- **Schema compliance is not behavior.** A tool can accept exactly the documented arguments and still fail, because the failure lives on the app side — a feature that is off by default, a lookup that needs an exact identifier. Call the tools, don't just read their signatures; the calls are where the real failure shapes appear.
- **Distinguish three failure shapes when reporting.** A missing required argument is a *schema* error (pydantic, `Field required`). A tool that reports a feature is switched off is a *state* condition, often phrased as a polite prose string rather than an exception — and one server may instead surface it as a transport-level "unknown command" error, which reads like a broken install. An exception escaping the client is a *transport* fault. Collapsing these into "it doesn't work" sends the user chasing the wrong bug.
- **`--args` is greedy.** `hermes mcp add` takes the remainder of the command line as server arguments, so a flag written after `--args` is silently consumed as an argument and lands in config under `args:`. Put every flag before it and read the config back.
- **The add command is interactive and silently cancels without a tty.** Its "enable all N tools? [Y/n/select]" prompt aborts and writes nothing when stdin is a pipe or a closed session. Pipe the answer explicitly, then confirm the block exists.
- **MCP tools do not appear in the session that added them.** Discovery runs at session start, so the correct deliverable after step 4 is a verified config plus the tool inventory — not a tool call. Do not spend the turn trying to call a tool that cannot exist yet.
- **An enabled add-on is not a listening socket.** These add-ons typically bind from a GUI-only startup hook that early-returns in headless mode, so no headless run can prove the port is open. Split the claim: headless proves *enabled*, the app proves *listening*.
- **Verifying persistence with the same factory-startup flag that made the change proves nothing.** A factory-startup run ignores the saved preferences, so a re-check that repeats it can only ever report the pre-existing default state. The re-check must omit the flag, and the two runs must be compared explicitly.
- **A running app may predate your config write and silently lack the feature.** Compare the process start time against the mtime of the preference file you just wrote; an older process holds stale in-memory state and will not pick the change up until restart. Surface both timestamps instead of guessing.
- **Do not restart the app yourself when it holds unsaved work.** Bring the start-time comparison to the user and let them restart after saving. Quitting a GUI app to satisfy a verification step destroys their work.
- **Use absolute runner paths, and pin the interpreter when the runner manages one.** MCP subprocesses inherit a filtered environment, and GUI-launched clients may not inherit the user's shell PATH at all. `UV_PYTHON_PREFERENCE=only-managed` (or the equivalent) keeps a managed interpreter from being shadowed by conda/pyenv/asdf/system Python.
- **Check the runner's help for a rename banner before writing config.** A renamed distribution often keeps the old name as a thin compatibility wrapper; configure the new name so the next person isn't maintaining a deprecation shim.

## Vendoring a companion skill into `~/.agents`

- Author the skill at `~/.agents/skills/<category>/<name>/` and expose it to Hermes with a **symlink** at `~/.hermes/skills/<category>/<name>` pointing at that path. Follow whatever the surrounding tree already does (symlink vs. real directory); do not copy the tree into both places.
- Keep upstream's `references/` next to its `SKILL.md`; do not flatten them.
- Extend the vendored frontmatter to the repo's full block (`version`, `author`, `license`, `platforms`, `compatibility`, `prerequisites`, `setup`, `metadata.hermes` with tags and `related_skills`). Upstream skills usually ship only `name` + `description`, which loads as a much weaker entry.
- **Never commit as a side effect.** These repos usually carry unrelated working-tree modifications; `git add -A` sweeps in someone else's work. Stage only the new path, and ask before committing.
- Reconcile the lock file with the repo's own reconciler script when it has one, rather than hand-editing inventory.
- **Reconcile the vendored skill against the live server before you call the work done.** Upstream prose is written against some earlier release; the server is the only authority for tool names, required arguments, and defaults. Walk the vendored tree, extract every backticked identifier that looks like a tool call, and diff that set against the live schema. Fix the file in place — edit the sentence that misleads rather than appending a correction note under it, and keep any stale name only inside a table whose purpose is to name the old thing.
- **An upstream skill that documents the tool surface should get a generated reference, not hand-transcribed one.** When a server exposes enough tools that reading them is a real cost, emit one `references/` file straight from the live schema, grouped by function, with a line saying the server wins on any conflict. This makes the next session a lookup instead of a re-derivation, and it is the only way the "verified" claim stays true after the server updates.

## Support files

- `references/blender.md` — the Blender MCP bridge specifically: package names, add-on paths and port, the headless enable + persistence-verify script, the restart requirement, the real tool names, and when to use the bridge versus plain headless `bpy`.
- `scripts/verify_mcp_bridge.sh <server-name> [port]` — runs the first three verification rungs and exits non-zero on the first failure.
- `scripts/probe_mcp_tools.py` — rung 4: dumps the live tool schema and calls tools over the real protocol, annotating each result as schema / state / transport so the three never look alike. Run via `uv run --with mcp python <path> --command <runner> --args <package> --dump`.
