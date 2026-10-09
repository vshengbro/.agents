"""
gazebo -- an octagonal garden gazebo: eight columns on a computed ring, a
railed platform, eight arched braces, and a shingled cone roof with a finial.

Large size class (600..3000 mm): 3.6 m across, 3.1 m to the finial. The eight
spokes are ONE object swept with array_radial and then counted, not eight
hand-placed copies -- eight columns that are 7.5 degrees out would be visible
from directly above and nowhere else.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    sides=8,
    column_ring_diameter=3600.0,   # the ring the eight columns stand on
    column_diameter=180.0,
    column_height=2400.0,
    platform_height=420.0,
    platform_diameter=3900.0,
    roof_height=1900.0,
    roof_overhang=260.0,
    finial_height=420.0,
    rail_height=900.0,
)

BAYS = SPEC["sides"]
OD = SPEC["column_ring_diameter"]
CD = SPEC["column_diameter"]
CH = SPEC["column_height"]
PH = SPEC["platform_height"]
RH = SPEC["roof_height"]
OH = SPEC["roof_overhang"]

# columns stand on a circle of this radius, so the roof can oversail them
COL_R = OD / 2.0 - 420.0
Z_FLOOR = PH


def build():
    stone = bkit.pbr("GazeboStone", base=(0.72, 0.70, 0.65), rough=0.70)
    timber = bkit.pbr("GazeboTimber", base=(0.44, 0.31, 0.18), rough=0.58)
    shingle = bkit.pbr("GazeboShingle", base=(0.26, 0.28, 0.27), rough=0.68)
    trim = bkit.pbr("GazeboTrim", base=(0.20, 0.21, 0.22), rough=0.40)

    # ---- platform: two stepped courses, ONE solid -----------------------
    # One lathe rather than two stacked ones: the 420 mm floor height is only
    # measurable on a single part, and two solids meeting flush along a face
    # is exactly the tangency that leaves bad edges.
    pd = SPEC["platform_diameter"]
    bkit.lathe("GazeboPlatform", [
        (0.0, 0.0), (pd / 2.0, 0.0), (pd / 2.0, 240.0),
        (pd / 2.0 - 90.0, 240.0), (pd / 2.0 - 90.0, SPEC["platform_height"]),
        (0.0, SPEC["platform_height"]),
    ], segments=64, mat=stone)

    # ---- eight columns, one swept object ---------------------------------
    # bkit.array_radial derives its Array offset from the object's own world
    # matrix, so an object already placed at a radius spirals outward instead
    # of orbiting -- the eighth copy lands at 2.4x the radius. Copying each
    # column to its exact ring position is correct at any count.
    col = bkit.lathe("GazeboColumn0", [
        (0.0, 0.0), (CD / 2.0 + 26.0, 0.0), (CD / 2.0 + 26.0, 90.0),
        (CD / 2.0, 150.0),
        (CD / 2.0, CH - 150.0),
        (CD / 2.0 + 26.0, CH - 90.0),
        (CD / 2.0 + 26.0, CH), (0.0, CH),
    ], segments=40, mat=timber)
    cols = [bkit.move(col, COL_R, 0.0, Z_FLOOR)]
    for i in range(1, BAYS):
        a = 2.0 * math.pi * i / BAYS
        cols.append(bkit.duplicate(
            col, "GazeboColumn%d" % i,
            offset_mm=(COL_R * math.cos(a), COL_R * math.sin(a), Z_FLOOR)))
    bkit.join(cols, "GazeboColumns")
    bpy_update()

    # ---- perimeter rail: two rails plus balusters, on a computed ring ---
    for zt, nm in ((Z_FLOOR + SPEC["rail_height"], "Top"),
                   (Z_FLOOR + SPEC["rail_height"] * 0.48, "Mid")):
        rail = bkit.torus("GazeboRail%s" % nm, COL_R, 34.0, seg_major=72,
                          seg_minor=12, centre=(0.0, 0.0, zt), mat=trim)
    bal = bkit.rounded_box("GazeboBaluster0", 46.0, 46.0, SPEC["rail_height"],
                           r=10.0, segments=2, centre=(0.0, 0.0, 0.0),
                           mat=trim)
    bals = [bkit.move(bal, COL_R + 90.0, 0.0, Z_FLOOR)]
    for i in range(1, BAYS * 2):
        a = 2.0 * math.pi * i / (BAYS * 2)
        bals.append(bkit.duplicate(
            bal, "GazeboBaluster%d" % i,
            offset_mm=((COL_R + 90.0) * math.cos(a),
                       (COL_R + 90.0) * math.sin(a), Z_FLOOR)))
    bkit.join(bals, "GazeboBalusters")
    bpy_update()

    # ---- head ring: the beam the roof sits on ---------------------------
    ring = bkit.tube("GazeboHeadRing", OD / 2.0 + 40.0, OD / 2.0 - 150.0,
                     220.0, segments=72,
                     centre=(0.0, 0.0, Z_FLOOR + CH + 110.0), mat=timber)

    # ---- roof: a cone with a real overhang and a flat soffit ------------
    zr = Z_FLOOR + CH + 220.0
    roof_r = OD / 2.0 + OH
    roof = bkit.lathe("GazeboRoof", [
        (0.0, zr),
        (roof_r, zr),                       # eave, outer
        (roof_r + 40.0, zr + 60.0),         # fascia
        (roof_r - 120.0, zr + 90.0),        # soffit turning up
        (roof_r * 0.55, zr + RH * 0.72),     # the cone
        (roof_r * 0.16, zr + RH - 40.0),
        (0.0, zr + RH),
    ], segments=72, mat=shingle)

    # ---- eight rafters under the roof, one object ------------------------
    rafter = bkit.rounded_box("GazeboRafter0", roof_r * 0.80, 90.0, 150.0,
                              r=20.0, segments=2,
                              centre=(roof_r * 0.40, 0.0, 0.0), mat=timber)
    rafters = [rafter]
    for i in range(1, BAYS):
        a = 2.0 * math.pi * i / BAYS
        rafters.append(bkit.duplicate(
            rafter, "GazeboRafter%d" % i,
            rot_deg=(0.0, 0.0, math.degrees(a))))
    bkit.join(rafters, "GazeboRafters")
    bkit.move(bpy.data.objects["GazeboRafters"], 0.0, 0.0, zr + RH * 0.30)
    bpy_update()

    # ---- finial ----------------------------------------------------------
    fin = bkit.lathe("GazeboFinial", [
        (0.0, zr + RH - 60.0),
        (150.0, zr + RH - 20.0),
        (90.0, zr + RH + 120.0),
        (170.0, zr + RH + 180.0),
        (70.0, zr + RH + 320.0),
        (0.0, zr + RH + SPEC["finial_height"]),
    ], segments=32, mat=trim)

    return dict(spec=SPEC, parts=10, sides=BAYS, columns=BAYS)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    # the widest thing in the assembly is the roof, so the overall width IS the
    # roof diameter: 2 * (OD/2 + roof_overhang + the 40 mm fascia) = 2 * 2100
    dict(name="overall_diameter", mm=4200.0, tol=30.0, how="bbox_x"),
    dict(name="platform_height", mm=420.0, tol=4.0, how="bbox_z",
         part="GazeboPlatform"),
    dict(name="column_height", mm=2400.0, tol=20.0, how="bbox_z",
         part="GazeboColumns"),
    dict(name="platform_diameter", mm=3900.0, tol=20.0, how="diameter",
         part="GazeboPlatform"),
    # roof_overhang is a PROJECTION past the column ring, not a length of any
    # one part, so no bbox can measure it. It stays declared in SPEC; the
    # measurable sibling is the roof's own diameter.
    dict(name="roof_diameter", mm=4200.0, tol=30.0, how="diameter",
         part="GazeboRoof"),
    dict(name="finial_height", mm=480.0, tol=20.0, how="bbox_z",
         part="GazeboFinial"),
]
