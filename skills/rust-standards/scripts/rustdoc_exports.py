#!/usr/bin/env python3
"""Public item names a crate root binds through its glob imports.

The rustdoc JSON records a glob re-export as a `use` entry whose `source` is
the module it re-exports. The target module may be stripped (no items listed),
so the re-exported names are recovered from the `paths` map: the items whose
path is `<module>, <kind>, <Name>` belong to that module.

Only names that are actually reachable from the crate root count.
"""

from __future__ import annotations

import json
from pathlib import Path


def crate_root_exports(payload: dict) -> set[str]:
    """Names the crate root re-exports, directly or through a glob."""
    index = payload.get("index", {})
    paths = payload.get("paths", {})
    root_id = str(payload.get("root"))
    root_entry = index.get(root_id, {})
    items = root_entry.get("items", [])
    if not items:
        items = root_entry.get("inner", {}).get("module", {}).get("items", [])

    # module id -> exported item names, taken from the paths map.
    by_module: dict[int, set[str]] = {}
    module_id_by_name: dict[str, int] = {}
    for path_id, path in paths.items():
        segments = path.get("path", [])
        if len(segments) < 3:
            continue
        kind = segments[-2]
        name = segments[-1]
        if kind not in {"struct", "enum", "type", "trait", "union", "constant"}:
            continue
        module = segments[-3]
        by_module.setdefault(module, set()).add(name)
        module_id_by_name.setdefault(module, int(path_id))

    names: set[str] = set()
    for child in items:
        child_entry = index.get(str(child), {})
        use = child_entry.get("inner", {}).get("use")
        if not use:
            name = child_entry.get("name", "")
            if name and name[0].isupper():
                names.add(name)
            continue
        source = use.get("source", "")
        if use.get("is_glob"):
            names |= by_module.get(source, set())
        else:
            name = use.get("name", "")
            if name and name[0].isupper():
                names.add(name)
    return {n for n in names if n and n[0].isupper()}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    root = Path("/Users/vshengbro/code/hyperlane/target/doc")
    for stem in ("http_type", "http_request", "hyperlane_core", "hyperlane_cli",
                 "http_compress", "http_constant"):
        doc = root / f"{stem}.json"
        if not doc.is_file():
            print(f"{stem}: (no payload)")
            continue
        names = crate_root_exports(load(doc))
        print(f"{stem}: {len(names)} root exports")
        for probe in ("Request", "Response", "Method", "Error", "TcpStream",
                      "TokenStream", "Result", "Ident", "Stream"):
            if probe in names:
                print(f"    {probe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
