#!/usr/bin/env python3
"""Drive a stdio MCP server and dump / exercise its real tools.

Why this exists
---------------
`hermes mcp test` proves the server package *starts* and advertises tools. It
does NOT prove the tools work against the app, and it does NOT show you the
tool names or argument schemas you must call. Reading a server's own skill
prose is worse still: tool names drift silently across releases, and a doc
that says `execute_python` when the server only has `execute_blender_code`
sends you down a dead end with a plausible-looking error.

This script is the ground truth: it lists the live schema, and optionally
calls named tools so you can verify arguments instead of guessing them.

Usage
-----
  # dump the full live schema (no app needed beyond the server itself)
  probe_mcp_tools.py --dump

  # dump, then call specific tools with JSON args
  probe_mcp_tools.py \
      --tool get_scene_info:{"user_prompt":"verify"} \
      --tool execute_blender_code:{"code":"print(1)"}

  # one-liner status sweep: call every no-arg or status-ish tool
  probe_mcp_tools.py --call-zero-arg

Output is annotated per call with OK / ERR / EXC so a validation error, a
tool-level error, and a transport failure never look alike — those three mean
very different things when you are diagnosing a bridge.

Run it with any Python that has the mcp package, e.g.
  uv run --with mcp python probe_mcp_tools.py --dump
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys


def build_env(extra: list[str] | None) -> dict[str, str]:
    env = dict(os.environ)
    for pair in extra or []:
        if "=" in pair:
            k, v = pair.split("=", 1)
            env[k] = v
    return env


def render_dump(tools) -> str:
    out = []
    for t in sorted(tools, key=lambda x: x.name):
        schema = t.input_schema or {}
        req = set(schema.get("required", []))
        props = schema.get("properties") or {}
        if not props:
            out.append(f"{t.name}  (no args)")
            continue
        bits = []
        for key, v in props.items():
            mark = "*" if key in req else ""
            kind = v.get("type") or "any"
            if v.get("default") is not None:
                kind += f"={v['default']!r}"
            if v.get("enum"):
                kind += "[" + ",".join(str(e) for e in v["enum"])[:40] + "]"
            bits.append(f"{mark}{key}{mark}:{kind}")
        desc = (t.description or "").strip().replace("\n", " ")
        out.append(f"{t.name}\n    {' '.join(bits)}")
        if desc:
            out.append(f"    -> {desc[:160]}")
    return "\n".join(out)


async def call_one(session, name: str, args: dict) -> str:
    try:
        res = await session.call_tool(name, args)
    except Exception as exc:  # transport / spawn failure
        return f"[EXC] {name}  {type(exc).__name__}: {exc}"
    text = ""
    for c in res.content or []:
        if getattr(c, "type", "") == "text":
            text += c.text
        elif getattr(c, "type", "") == "image":
            text += f"[IMAGE {len(getattr(c, 'data', '') or '')} bytes]"
    if getattr(res, "isError", False):
        return f"[ERR] {name}\n     {text[:400]}"
    return f"[OK ] {name}\n     {text[:400]}"


def parse_tool_spec(spec: str) -> tuple[str, dict]:
    if ":" not in spec:
        return spec, {}
    name, _, raw = spec.partition(":")
    if not raw.strip():
        return name, {}
    return name, json.loads(raw)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--command", required=True, help="runner binary, absolute path preferred")
    ap.add_argument("--args", nargs=argparse.REMAINDER, default=[], help="server args after --args")
    ap.add_argument("--env", action="append", help="KEY=VALUE passed to the subprocess")
    ap.add_argument("--dump", action="store_true", help="print the live tool schema and exit")
    ap.add_argument("--tool", action="append", default=[], help="name or name:{\"json\":\"args\"}")
    ap.add_argument("--call-zero-arg", action="store_true",
                    help="call every tool that declares no required arguments")
    a = ap.parse_args()

    if not a.args:
        print("no --args given; pass them after a literal --args", file=sys.stderr)
        return 2

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=a.command, args=a.args, env=build_env(a.env))
    rc = 0
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools

            print(f"# {len(tools)} tools live on {a.command}")
            if a.dump:
                print(render_dump(tools))

            calls = [parse_tool_spec(s) for s in a.tool]
            if a.call_zero_arg:
                for t in tools:
                    if not (t.input_schema or {}).get("required"):
                        calls.append((t.name, {}))
            for name, cargs in calls:
                print(await call_one(session, name, cargs))
    return rc


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
