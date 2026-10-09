"""
run_model.py -- the single entrypoint every catalog generator is executed through.

    blender -b --factory-startup -noaudio -t 4 --python run_model.py -- \\
        <model_script.py> <outdir> [--samples N] [--res WxH] [--no-render]

The model script must define build() and may define SPEC (a dict of real-world
dimensions in millimetres). Everything else -- staging, camera framing, renders,
the machine-readable report -- happens here, so 100+ generators stay uniform
and comparable, and no generator can accidentally ship a render made with a
different lighting recipe than everyone else.

Writes to <outdir>:
    report.json      geometry facts + spec deltas (what verify.py scores)
    <shot>.png       hero / three_quarter / side / top / rear / front
"""
import argparse
import importlib.util
import json
import os
import sys
import time
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import bpy            # noqa: E402
import bkit           # noqa: E402


def load_module(path):
    spec = importlib.util.spec_from_file_location("catalog_model", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["catalog_model"] = mod
    spec.loader.exec_module(mod)
    return mod


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("outdir")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--res", default="1100x850")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--shots", default="")
    return ap.parse_args(argv)


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    w, h = (int(x) for x in args.res.lower().split("x"))
    t_start = time.time()

    status = "ok"
    error = None
    spec = {}
    try:
        # reset() first: it calls read_factory_settings, which destroys every
        # datablock. A model that binds a material at module scope
        # (`MAT = bkit.preset("steel")`) would otherwise have it silently deleted
        # before build() ever runs.
        bkit.reset()
        mod = load_module(args.model)
        spec = dict(getattr(mod, "SPEC", {}) or {})
        # Pull the catalog entry for this file so scoring can check the declared
        # size class and so build status is traceable back to the enumeration.
        item_id = os.path.splitext(os.path.basename(args.model))[0]
        try:
            cat_path = os.path.join(os.path.dirname(SCRIPT_DIR), "catalog",
                                    "catalog.json")
            with open(cat_path) as fh:
                entry = next((i for i in json.load(fh)["items"]
                              if i["id"] == item_id), None)
            if entry:
                spec["_size_class"] = entry["size_class"]
                spec["_domain"] = entry["domain"]
                spec["_display_name"] = entry["name"]
        except Exception:
            pass
        built = mod.build()
        if isinstance(built, dict):
            spec.update(built)
        # Seat the model on z=0 before anything is measured or rendered: a model
        # authored hanging below the origin is buried by the studio backdrop and
        # renders as a truncated stump while still reporting a perfect bbox.
        data_offset = bkit.sit_on_floor()
    except Exception:
        status = "error"
        error = traceback.format_exc()
        print(error, flush=True)

    data = bkit.report(spec=spec or None)
    data["status"] = status
    data["error"] = error
    data["model_script"] = os.path.abspath(args.model)
    data["build_seconds"] = round(time.time() - t_start, 2)

    # Evaluate the model's declared CHECKS by measuring the real geometry. The
    # model says HOW to measure; the harness does the measuring, so a dimension
    # claim cannot be satisfied by simply asserting it.
    if status == "ok":
        checks = getattr(sys.modules.get("catalog_model"), "CHECKS", None) or []
        results = []
        for c in checks:
            entry = dict(name=c.get("name", "?"), want=c.get("mm"),
                         how=c.get("how", "bbox_z"), part=c.get("part"))
            try:
                got = bkit.measure(entry["part"], entry["how"])
                tol = float(c.get("tol", max(0.4, 0.01 * float(entry["want"]))))
                entry["got"] = round(got, 3)
                entry["tol"] = tol
                entry["error"] = round(abs(got - float(entry["want"])), 3)
                entry["ok"] = entry["error"] <= tol
            except Exception as exc:
                entry["error"] = "measurement failed: %s" % exc
                entry["ok"] = False
            results.append(entry)
        data["checks"] = results
        data["checks_passed"] = sum(1 for r in results if r["ok"])
        data["checks_total"] = len(results)
    if "data_offset" in dir():
        data["seated_offset_mm"] = data_offset

    if status == "ok" and not args.no_render:
        try:
            bpy.context.scene.render.resolution_x = w
            bpy.context.scene.render.resolution_y = h
            bb = data["bbox"]
            target = ((bb["x_min"] + bb["x_max"]) / 2.0,
                      (bb["y_min"] + bb["y_max"]) / 2.0,
                      (bb["z_min"] + bb["z_max"]) / 2.0)
            rad = max(data["radius_mm"] * bkit.MM, 1e-4)
            bkit.studio(rad)
            shots = None
            if args.shots:
                shots = [tuple(s.split(":")) for s in args.shots.split(",")]
                shots = [(n, float(a), float(e), float(l)) for (n, a, e, l) in shots]
            t0 = time.time()
            paths = bkit.render_shots(args.outdir, target, rad, shots=shots,
                                      samples=args.samples, res=(w, h))
            data["renders"] = [os.path.basename(p) for p in paths]
            data["render_seconds"] = round(time.time() - t0, 2)
        except Exception:
            data["render_error"] = traceback.format_exc()
            print(data["render_error"], flush=True)

    bkit.dump(data, os.path.join(args.outdir, "report.json"))
    print("RUN_MODEL %s status=%s objects=%d verts=%d faces=%d nonmanifold=%d"
          % (os.path.basename(args.model), status, data.get("objects", 0),
             data.get("verts", 0), data.get("faces", 0), data.get("nonmanifold", 0)),
          flush=True)
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
