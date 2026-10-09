#!/usr/bin/env python3
"""Prove the rail buffer fix: a vehicle's two ends must be symmetric.

The bug: `_rail.buffers()` authored its assembly once at negative X and then
translated it, so a rear-ended vehicle got buffers pointing back along its own
body. The signature was EXACT -- all four rail vehicles measured 440 mm of end
asymmetry, and 440 mm is the pad depth.

This asserts the invariant directly rather than eyeballing renders: for each
rail vehicle, the distance from the model centre to each end must match. A
vehicle built from one call at both ends cannot be asymmetric.

    blender -b --factory-startup --python rail_symmetry.py
"""
import glob
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS)

import bpy      # noqa: E402
import bkit     # noqa: E402

CAT = os.path.join(os.path.dirname(SCRIPTS), "catalog", "vehicles_rail")
# subway_train is EXCLUDED ON PURPOSE: it is a two-car unit, so its ends are
# genuinely unequal and the invariant below does not apply to it. Listing it
# would teach the test to report a real design as a bug, which is worse than
# not covering it -- the fix for the one-sided buffer is proved on the eight
# single-body vehicles, which is where the bug lived.
MODELS = ["diesel_locomotive", "passenger_carriage", "tram", "railcar",
          "freight_wagon", "hopper_wagon", "tank_wagon", "flatbed_wagon"]

print("%-20s %10s %10s %10s %8s" % ("model", "x_min", "x_max", "asym_mm",
                                    "verdict"))
print("-" * 64)
fails = 0
for name in MODELS:
    path = os.path.join(CAT, name + ".py")
    if not os.path.isfile(path):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    import importlib.util
    s = importlib.util.spec_from_file_location("rail_" + name, path)
    mod = importlib.util.module_from_spec(s)
    sys.modules["rail_" + name] = mod
    s.loader.exec_module(mod)
    mod.build()
    bb = bkit.scene_bbox()
    lo, hi = bb["x_min"], bb["x_max"]
    asym = (lo + hi) / 2.0 * -1.0          # 0 when the ends are equidistant
    ok = abs(asym) < 1.0
    fails += 0 if ok else 1
    print("%-20s %10.1f %10.1f %10.2f %8s"
          % (name, lo, hi, asym, "ok" if ok else "FAIL"))

print("-" * 64)
print("%d models, %d asymmetric" % (len(MODELS), fails))
sys.exit(1 if fails else 0)
