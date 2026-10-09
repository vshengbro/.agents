#!/usr/bin/env python3
"""lint_rotation.py -- find parts that rotate about the world origin instead of
about themselves.

    blender -b --factory-startup --python lint_rotation.py -- <model.py> [...]
    blender -b --factory-startup --python lint_rotation.py -- --batch list.txt

`bkit.box()` bakes `centre` into the MESH DATA and leaves the object origin at
(0, 0, 0). That is deliberate -- it keeps `move()`, `array_linear(world=True)`
and the rest of the toolkit in one coordinate space -- but it means a plain

    ob.rotation_euler = (0, 0, radians(30))

swings that part around the WORLD origin, not around itself. A coffee machine
part 100 mm out is barely affected, which is exactly why this survives review;
the same line on a clock tower hand authored at z = 24284 mm throws it 10 m off
the dial.

So the displacement is reported directly: how far the rotation actually moves
this part's own centre. Zero means the rotation is harmless; a large number is a
part that is not where its author put it.

    ROTPIVOT  clock_tower  ClockHand1  centre 24.3 m from origin  moves 10.1 m

The fix is not to edit 267 call sites. It is to bake the rotation into the mesh
about the part's own centre (see `_fauna.bake_rot`), or to author the part in
world coordinates as the fauna helpers already do.
"""
import importlib.util
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

WORTH_REPORTING_M = 0.004      # 4 mm: below this the rotation is harmless here


def analyse_scene():
    out = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        rot = ob.rotation_euler
        if max(abs(rot.x), abs(rot.y), abs(rot.z)) < 1e-6:
            continue
        n = len(ob.data.vertices)
        if not n:
            continue
        c = Vector((0.0, 0.0, 0.0))
        for v in ob.data.vertices:
            c += v.co
        c /= n

        # Blender composes matrix_world as T(location) @ R @ S, so
        #     world_centre = location + R @ S @ local_centre
        # The ROTATION moves the part by R @ c_local - c_local, and by nothing
        # at all when c_local is the origin -- which is how `bkit.cylinder()` and
        # friends build: the centre lives in `obj.location`, the mesh sits on the
        # local origin, and rotating the object spins it about itself.
        #
        # An earlier version of this file rotated the WORLD centre instead, which
        # is not what Blender does. It reported every one of those correctly
        # behaving primitives as broken -- `clock_tower`'s dial as displaced
        # 34224 mm when the true figure is 103.6 mm, a 330x overstatement -- and
        # the prescribed fix destroyed good models: `sailboat`, `welder` and
        # `level_crossing` each fell from 55.0 to 22.5 on the objective gate when
        # their correct rotations were rewritten to pivot on the centroid.
        rotated = (Matrix.Rotation(rot.z, 4, "Z")
                   @ Matrix.Rotation(rot.y, 4, "Y")
                   @ Matrix.Rotation(rot.x, 4, "X"))
        moved = ((rotated @ c) - c).length
        # A part whose mesh is centred on its own local origin cannot move at
        # all: R @ 0 - 0 is zero, for any rotation. That is a proof rather than
        # an estimate, so such objects are skipped outright instead of being
        # reported at some sub-millimetre value. This is the common case --
        # `bkit.cylinder()`, `lathe()` and friends all build on the local origin
        # and carry their centre in `obj.location`.
        if c.length < 1e-3:
            continue
        if moved < WORTH_REPORTING_M:
            continue
        scale = ob.matrix_world.to_scale()
        if max(scale) > 1.001:
            # a non-uniform object scale makes the simple composition above an
            # approximation; say so rather than reporting a confident number
            note = "non-unit scale %s -- displacement is approximate" % (
                tuple(round(s, 3) for s in scale),)
        else:
            note = None
        out.append(dict(object=ob.name,
                        local_centre_mm=[round(c.x * 1000, 1),
                                         round(c.y * 1000, 1),
                                         round(c.z * 1000, 1)],
                        location_mm=[round(ob.location.x * 1000, 1),
                                     round(ob.location.y * 1000, 1),
                                     round(ob.location.z * 1000, 1)],
                        displacement_mm=round(moved * 1000, 1),
                        axis_deg=[round(math.degrees(a), 1)
                                  for a in (rot.x, rot.y, rot.z)],
                        note=note))
    return out


def run(model_path):
    s = importlib.util.spec_from_file_location("lint_model", model_path)
    mod = importlib.util.module_from_spec(s)
    sys.modules["lint_model"] = mod
    try:
        s.loader.exec_module(mod)
        mod.build()
    except Exception as exc:
        return dict(model=os.path.basename(model_path)[:-3],
                    error=str(exc)[:200], offenders=[])
    return dict(model=os.path.basename(model_path)[:-3],
                offenders=analyse_scene())


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    models = []
    if argv and argv[0] == "--batch":
        with open(argv[1]) as fh:
            models = [l.strip() for l in fh if l.strip()]
    else:
        models = argv

    rows = []
    for m in models:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        r = run(m)
        rows.append(r)
        for o in r["offenders"]:
            print("ROTPIVOT  %-24s %-22s local_centre=%-22s loc=%-20s "
                  "rotation moves it %9.1f mm  axis=%s"
                  % (r["model"], o["object"],
                     o["local_centre_mm"], o["location_mm"],
                     o["displacement_mm"], o["axis_deg"]), flush=True)

    bad = [r for r in rows if r["offenders"]]
    print("\n%d models checked, %d with a part rotating about the world origin, "
          "%d errored" % (len(rows), len(bad),
                          sum(1 for r in rows if r.get("error"))))
    dest = os.environ.get("ROTLINT_OUT", "/tmp/rotlint.json")
    with open(dest, "w") as fh:
        json.dump(rows, fh, indent=1)
    print("wrote %s" % dest)


main()
