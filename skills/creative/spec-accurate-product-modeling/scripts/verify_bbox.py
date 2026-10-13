"""Bounding-box assertion gate for a spec-accurate model.

Run after EVERY geometry edit, before rendering. Exits non-zero when any axis
misses the target by more than TOL_MM, so it can gate a build.

Adapt the constants at the top, then:
    blender --background --python verify_bbox.py

Measures EVALUATED bounds (live modifiers applied), never raw .dimensions --
only the evaluated bounds are what actually render.
"""

import sys

# --- adapt these per project -------------------------------------------------
TARGET_CM = (19.7, 19.7, 9.5)   # W, D, H from the vendor spec sheet
TOL_MM = 0.5
EXCLUDE = {"Floor", "Backdrop", "BounceL", "BounceR"}   # set dressing
# ----------------------------------------------------------------------------

# Blender fills this in; a non-Blender tool can instead assign
# [(name, minx, miny, minz, maxx, maxy, maxz), ...] to BOUNDS before calling.
BOUNDS = None


def measure_blender():
    import bpy
    from mathutils import Vector

    deps = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name in EXCLUDE:
            continue
        ev = obj.evaluated_get(deps)
        for corner in ev.bound_box:
            wc = ev.matrix_world @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], wc[i])
                hi[i] = max(hi[i], wc[i])
    return lo, hi


def main():
    if BOUNDS is not None:
        rows = BOUNDS
        lo = [min(r[i + 1] for r in rows) for i in range(3)]
        hi = [max(r[i + 4] for r in rows) for i in range(3)]
    else:
        lo, hi = measure_blender()

    size = [hi[i] - lo[i] for i in range(3)]
    print("BBOX_MIN_CM  %8.4f %8.4f %8.4f" % tuple(lo))
    print("BBOX_MAX_CM  %8.4f %8.4f %8.4f" % tuple(hi))
    print("BBOX_SIZE_CM %8.4f %8.4f %8.4f" % tuple(size))

    ok = True
    for axis, got, want in zip("XYZ", size, TARGET_CM):
        delta_mm = (got - want) * 10.0
        bad = abs(delta_mm) > TOL_MM
        ok = ok and not bad
        print("  %s  got %8.4f cm  want %8.4f cm  delta %+0.3f mm  %s"
              % (axis, got, want, delta_mm, "FAIL" if bad else "ok"))

    print("VERIFY_OK" if ok else "VERIFY_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
