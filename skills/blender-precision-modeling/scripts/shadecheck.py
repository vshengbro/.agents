#!/usr/bin/env python3
"""Does shade_smooth() actually smooth, or does it silently fall back?

    blender -b --factory-startup --python shadecheck.py

`shade_smooth()` calls `bpy.ops.object.shade_auto_smooth()`, which in Blender 4.x
is implemented by linking a "Smooth by Angle" geometry-nodes asset from the
install's datafiles. This Blender was patched and re-signed to run headless on a
GPU-less host, and the run log is full of:

    Error: No asset found at path ".../4.5/datafiles/assets/geometry_nodes/
           smooth_by_angle.blend/NodeTree/Smooth by Angle"

The call still returns without raising, so the `except` fallback never fires and
nothing reports a problem -- but the cylinders stay faceted. A vision round
independently reported "vertical banding / stair-stepped silhouettes on
cylinders" in 4 of 12 models, which is what faceting looks like.

This measures the actual outcome instead of trusting the call: build a
48-segment cylinder, shade it, and count how many of its polygons are set to
flat. If shade_smooth is working, a cylinder's side faces are smooth and only
the caps are flat.
"""
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS)

import bpy      # noqa: E402
import bkit     # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
bkit.reset()
cyl = bkit.cylinder("Cyl", 20.0, 60.0, segments=48, centre=(0, 0, 30),
                    mat=bkit.preset("steel"))
flat_before = sum(1 for p in cyl.data.polygons if not p.use_smooth)
bkit.shade_smooth(cyl)
flat_after = sum(1 for p in cyl.data.polygons if not p.use_smooth)
total = len(cyl.data.polygons)

print("cylinder: %d polygons (%d segments -> %d side + 2 caps)"
      % (total, 48, total - 2))
print("flat before shade_smooth: %d" % flat_before)
print("flat after  shade_smooth: %d" % flat_after)

ok = flat_after <= 4          # caps (or a small rim) may legitimately stay flat
print("\nVERDICT: %s"
      % ("shade_smooth works -- side faces are smooth"
         if ok else "shade_smooth is NOT smoothing -- %d of %d faces are flat"
         % (flat_after, total)))

# also report whether the 4.x operator itself is usable here
try:
    bpy.context.view_layer.objects.active = cyl
    bpy.ops.object.shade_auto_smooth(angle=0.5)
    print("bpy.ops.object.shade_auto_smooth: callable")
except Exception as exc:
    print("bpy.ops.object.shade_auto_smooth raised: %s" % exc)

sys.exit(0 if ok else 1)
