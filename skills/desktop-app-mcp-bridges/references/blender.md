# Blender MCP bridge

Two halves: a Python MCP server process, and a single-file add-on (`blender_mcp.py`, ~250KB) hosted inside Blender that owns a localhost socket.

## Names and entry points

- Current package: **`mcp-for-blender`**. The older PyPI name `blender-mcp` still installs, but it is a compatibility wrapper that prints a rename banner on every run — configure the new name.
- Server subcommands: `install-addon` (copies the add-on into Blender's user add-ons dir, keeping a `.bak`), `addon-paths` (lists discovered add-on dirs, marking each `(exists)` / `(missing)` and printing any existing install).
- Hermes registration:
  ```bash
  printf 'Y\n' | hermes mcp add blender \
      --command /abs/path/to/uvx \
      --env UV_PYTHON_PREFERENCE=only-managed \
      --args mcp-for-blender
  ```
  `install-addon` and `addon-paths` are subcommands of the same console script, so the absolute runner path from the MCP config works for both.
- Add-on destination: `~/Library/Application Support/Blender/<version>/scripts/addons/blender_mcp.py` — the dir is created on first install, so `addon-paths` reporting `(missing)` before install is normal, not a failure.
- Add-on registers under the **Interface** category, with `bl_info` version `(1, 7)` and add-on protocol version 11 on Blender 4.5 LTS. The add-on file itself is a compatibility pin: an older server package talking to a newer add-on (or vice versa) fails at handshake, so upgrade both halves together.

## Port and auto-start

- Socket port **9876**, exposed as a scene property (`blendermcp_port`, min 1024 / max 65535).
- Auto-start is a scene property defaulting to on (`blendermcp_auto_start_server`), and the startup hook registers a persistent timer. It early-returns when `bpy.app.background` is true — **the socket only binds in a GUI session**.
- If the port already has a listener the add-on prints a skip message rather than stealing the port, and reports the server as not running. Check for a stray listener before blaming the enable step.

## Headless enable, and how to actually verify it

Enable the module and persist preferences in one headless run:

```python
# enable_mcp.py — run: Blender -b --factory-startup --python enable_mcp.py
import bpy, addon_utils
try:
    bpy.ops.preferences.addon_enable(module="blender_mcp")
    print("ENABLED_OK")
except Exception as e:
    print("ENABLE_FAIL", repr(e))
print("enabled_in_prefs:", "blender_mcp" in bpy.context.preferences.addons)
bpy.ops.wm.save_userpref()
print("SAVED_PREFS")
```

Verification is **two runs**, because the flag matters:

1. `Blender -b --python-expr "import bpy; print('ADDONS:', sorted(a.module for a in bpy.context.preferences.addons))"` — no factory-startup. `blender_mcp` must appear in the list. Confirm the `config/userpref.blend` mtime advanced on the enable run; that file is the real artifact.
2. `lsof -nP -iTCP:9876 -sTCP:LISTEN` — will be empty until a GUI session runs. A headless run can only ever prove *enabled*.

## Restart requirement

A GUI Blender launched **before** the enable write keeps stale in-memory state and never opens the socket, with no error surfaced. Diagnose by comparing `ps -o lstart -p <pid>` with the mtime of `userpref.blend`; if the process is older, the add-on is not loaded in it. The fix is a user-initiated restart — do not quit an app holding unsaved work on the user's behalf.

## Real tool names (measured, not from docs)

The server exposes 36 tools. Upstream skill prose predates a rename and names two of
them wrongly, so treat the live schema as the only source:

| Prose says | Real name | Required args |
|---|---|---|
| `execute_python` | `execute_blender_code` | `code` |
| `screenshot` | `get_viewport_screenshot` | none (`max_size` optional, default 1000) |
| `get_scene_info` | `get_scene_info` | **`user_prompt`** |

`get_scene_info` is the **only** tool where `user_prompt` is mandatory, and omitting it
returns a pydantic `Field required` error rather than an empty scene. Every other tool
accepts `user_prompt` as optional with default `''` — pass the user's real request text,
since it costs nothing and improves results. Other required args that bite:
`get_object_info` -> `object_name`; `export_scene` -> `filepath`; `set_texture` ->
`object_name` + `texture_id`; `import_generated_asset_tripo` -> `request_id` + `name`.
Note `download_sketchfab_model` requires `target_size` while `download_polypizza_model`
only defaults it — do not assume the sibling tools share an arity.

`export_scene` works and is preferable to hand-rolling `bpy.ops.export_scene.gltf(...)`;
it returns `{"path", "bytes", "exported": [...], "selection_only"}`.

`bpy_api_lookup` needs an **exact type identifier**, not prose. `"bevel modifier"`
returns `{"error": "Unknown type: ...", "did_you_mean": []}` with no suggestion, so
there is no recovery path — use the real `bl_idname` (`"BEVEL"`,
`"ShaderNodeTexNoise"`), or fall back to `describe_node_type` with the `bl_idname`,
which does work and returns the label, host tree, and property list.

## Asset integrations ship disabled

All six external services (PolyHaven, Sketchfab, PolyPizza, Hyper3D Rodin, Hunyuan3D,
Tripo) report "disabled" out of the box, and **no env var, config file, or MCP argument
turns them on** — the toggle lives in the add-on UI only (3D Viewport `N` -> MCP for
Blender panel -> per-service checkbox; `scene.blendermcp_use_polyhaven` for PolyHaven
defaults to `False`). Tripo is different in kind: it reports availability only under
MCP for Blender **Premium**, which is a paywall, not a setting.

**Gate every search on the matching status tool.** A disabled service fails in two
distinct shapes, and the second is the dangerous one because it reads like a broken
install rather than an off switch:

- `get_sketchfab_status` -> clean prose: "Sketchfab integration is currently disabled..."
- `search_sketchfab_models` -> transport error:
  `Communication error with Blender: Unknown command type: search_sketchfab_models`

Reporting that second shape as "Sketchfab is broken" would send the user reinstalling
something that only needed a checkbox.

## Bridge versus plain headless `bpy`

Use the MCP bridge when you need to act on a **live GUI session** the user is looking at: inspect the current scene, run `execute_python` in their open file, screenshot the viewport, or pull PolyHaven / Sketchfab / Rodin / Hunyuan3D / Tripo assets.

For building a model from scratch, batch export, or anything that should not touch the user's session, prefer a headless `bpy` script invoked directly against the Blender binary — no add-on, no socket, no restart dependency, and reproducible. Bridge sessions are also the wrong place for large exports: the MCP call path times out, so drive export from a separate headless process and import the result.
