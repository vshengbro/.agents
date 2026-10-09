"""
hourglass -- 150 mm turned-end hourglass with sand in the lower bulb.

An hourglass is two turned end caps, three turned columns and two glass
bulbs -- and the two things that make it read as an hourglass are the waist
between the bulbs and the sand, so both are modelled. The bulb profile is one
lathe: a wide shoulder, a narrow waist at mid height, and a second shoulder,
which is why a single revolved profile is enough for both halves.

The columns are three at 120 degrees, swept by array_radial about the
hourglass's own axis, which is the third time in this catalog where the array
centre is the difference between a cage and a tripod that has spilled.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

H = 150.0
CAP_R = 36.0
CAP_H = 14.0
BULB_R = 32.0
BULB_H = 122.0
WAIST_R = 6.0
GLASS_T = 1.6
COL_R = 3.6
COL_N = 3
COL_ORBIT = 30.0
SAND_H = 40.0
FINIAL_R = 8.0

SPEC = dict(height=H, cap_diameter=2.0 * CAP_R, cap_height=CAP_H,
            bulb_diameter=2.0 * BULB_R, bulb_height=BULB_H,
            waist_diameter=2.0 * WAIST_R, column_count=COL_N,
            column_diameter=2.0 * COL_R, sand_height=SAND_H)


def build():
    wood = bkit.pbr("GlassWood", base=(0.34, 0.18, 0.08), metal=0.0, rough=0.34,
                    coat=0.5)
    glass = bkit.pbr("HourglassGlass", base=(0.88, 0.92, 0.96), metal=0.0, rough=0.04,
                     transmission=0.6, ior=1.5)
    sand = bkit.pbr("HourglassSand", base=(0.86, 0.72, 0.44), metal=0.0, rough=0.88)

    # ---- the two turned end caps -------------------------------------------
    caps = []
    for (z, flip) in ((CAP_H / 2.0, 1.0), (H - CAP_H / 2.0, -1.0)):
        prof = [(0.0, 0.0), (CAP_R - 3.0, 0.0), (CAP_R, 3.0),
                (CAP_R, CAP_H - 5.0), (CAP_R - 5.0, CAP_H),
                (14.0, CAP_H), (10.0, CAP_H - 4.0), (0.0, CAP_H - 4.0)]
        prof = [(r, z + (zz - CAP_H / 2.0) * 1.0) for (r, zz) in prof]
        c = bkit.lathe("EndCaps", prof, segments=64,
                       centre=(0.0, 0.0, z), mat=wood)
        if flip < 0:
            c.rotation_euler = (math.radians(180.0), 0.0, 0.0)
        bkit.recalc(c)
        caps.append(c)
    bkit.join(caps, name="EndCaps")

    # ---- the glass: one waist, two shoulders --------------------------------
    # Profile from the lower cap's neck up over the waist to the upper neck.
    # Both ends terminate on a short neck of the same radius, so the closed
    # loop has no axis-to-axis segment and no zero-area faces.
    z0 = CAP_H - 2.0
    z1 = H - CAP_H + 2.0
    glass_ob = bkit.lathe(
        "Bulbs",
        [(WAIST_R + GLASS_T, z0),
         (BULB_R * 0.72, z0 + (z1 - z0) * 0.12),
         (BULB_R, z0 + (z1 - z0) * 0.26),
         (BULB_R * 0.70, z0 + (z1 - z0) * 0.40),
         (WAIST_R + GLASS_T, z0 + (z1 - z0) * 0.5),
         (BULB_R * 0.70, z0 + (z1 - z0) * 0.60),
         (BULB_R, z0 + (z1 - z0) * 0.74),
         (BULB_R * 0.72, z0 + (z1 - z0) * 0.88),
         (WAIST_R + GLASS_T, z1),
         (WAIST_R, z1),
         (WAIST_R, z0),
         (WAIST_R + GLASS_T, z0)],
        segments=72, cap_ends=False, mat=glass)

    # ---- three turned columns, swept about the axis ------------------------
    col = bkit.cylinder("Columns", COL_R, H - 2.0 * CAP_H + 8.0, segments=20,
                        centre=(COL_ORBIT, 0.0, H / 2.0), mat=wood)
    bkit.array_radial(col, COL_N, centre=(0.0, 0.0, H / 2.0))

    # ---- the sand: a cone in the lower bulb, and a funnel above the waist ---
    pile = bkit.lathe(
        "Sand",
        [(0.0, z0 + 2.0), (BULB_R * 0.42, z0 + SAND_H * 0.55),
         (WAIST_R + 0.6, z0 + SAND_H), (0.0, z0 + SAND_H)],
        segments=48, mat=sand)
    running = bkit.lathe(
        "SandStream",
        [(0.0, z0 + SAND_H * 0.5), (2.0, z0 + SAND_H * 0.75),
         (2.0, z0 + (z1 - z0) * 0.5 + 2.0), (0.0, z0 + (z1 - z0) * 0.5 + 2.0)],
        segments=20, mat=sand)

    # ---- finial discs top and bottom ---------------------------------------
    finials = []
    for z in (0.0, H):
        finials.append(bkit.lathe(
            "Finials",
            [(0.0, 0.0), (FINIAL_R, 1.5), (FINIAL_R, 4.0), (FINIAL_R - 4.0, 6.0),
             (0.0, 6.0)],
            segments=40, centre=(0.0, 0.0, z - (6.0 if z > H / 2.0 else 0.0)),
            mat=wood))
    bkit.join(finials, name="Finials")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="height", mm=157, tol=0.3, how="bbox_z",
         part=None),
    dict(name="cap_diameter", mm=72.0, tol=0.2, how="diameter", part="EndCaps"),
    dict(name="bulb_diameter", mm=64.0, tol=0.2, how="diameter", part="Bulbs"),
    # the waist is a Z feature between two 32 mm bulbs, so it is not expressible
    # as a bounding box on the glass; the bulb pair's own height is
    dict(name="bulb_height", mm=126.0, tol=0.3, how="bbox_z",
         part="Bulbs"),
    dict(name="column_count_span", mm=7.2, tol=0.1, how="bbox_x",
         part="Columns"),
    dict(name="sand_height", mm=38, tol=0.2, how="bbox_z",
         part="Sand")
]