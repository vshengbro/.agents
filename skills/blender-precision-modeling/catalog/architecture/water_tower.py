"""
water_tower -- elevated steel tank on four braced legs: a lathed cylindrical
tank with a conical roof and floor, a saddle skirt, a ring of staves, and a
lattice of computed braces.

Huge size class: 22 m to the tank roof. The structure is the read -- four legs,
X-bracing between them, and a tank that visibly overhangs its support. Leg
positions come from a computed square, braces from `grid_positions`.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=22000.0,
    leg_height=13000.0,
    leg_spacing=7000.0,     # square between leg centres
    leg_section=420.0,
    brace_bays=4,           # horizontal bracing levels per face
    tank_diameter=9000.0,
    tank_height=6000.0,
    tank_floor_diameter=4200.0,   # the conical floor tucks up inside
    roof_height=1600.0,
    stave_count=24,         # riveted staves round the tank
)

LH = SPEC["leg_height"]
LS = SPEC["leg_spacing"]
LG = SPEC["leg_section"]
TD = SPEC["tank_diameter"] / 2.0
TH = SPEC["tank_height"]
ROOF = SPEC["roof_height"]
TZ = LH                      # tank floor springs from here


def _lathe(name, profile, **kw):
    """`bkit.lathe` followed by a re-weld that works at this model's scale.

    `bkit.weld` defaults to dist_mm=0.0005 (5e-7 m), which is finer than the
    float32 precision of Blender's weld hash once a mesh sits more than about
    12 m up. The `segments` vertices a lathe emits at its pole then fail to
    merge, and the solid reports non-manifold edges at the apex. Welding again
    at 0.1 mm collapses the pole properly; 0.1 mm is three orders of magnitude
    below the smallest feature in this model.
    """
    ob = bkit.lathe(name, profile, **kw)
    bkit.weld(ob, 0.1)
    bkit.recalc(ob)
    return ob


def build():
    steel = bkit.preset("anodized")
    tank_mat = bkit.pbr("TankSteel", base=(0.48, 0.52, 0.55), metal=0.85,
                        rough=0.44)
    rivet = bkit.pbr("TankRivet", base=(0.40, 0.43, 0.46), metal=0.85,
                     rough=0.38)

    # ---- four legs on a computed square ----------------------------------
    legs = []
    for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        x, y = sx * LS / 2.0, sy * LS / 2.0
        legs.append((x, y))
        bkit.rounded_box("TowerLeg%d%d" % (sx > 0, sy > 0), LG, LG, LH, r=26.0,
                         segments=2, centre=(x, y, LH / 2.0), mat=steel)

    # ---- horizontal bracing + X-braces, all positions computed ----------
    bays = SPEC["brace_bays"]
    for lvl in range(1, bays + 1):
        z = LH * lvl / float(bays)
        for (i, j) in ((0, 1), (2, 3)):
            (x0, y0), (x1, y1) = legs[i], legs[j]
            _strut("BraceH%d%d" % (lvl, i), (x0, y0, z), (x1, y1, z), steel)
        for (i, j) in ((0, 2), (1, 3)):
            (x0, y0), (x1, y1) = legs[i], legs[j]
            _strut("BraceH%d%d" % (lvl, i), (x0, y0, z), (x1, y1, z), steel)
        # diagonals in each of the four faces
        for k, (a, b) in enumerate(((0, 2), (1, 3), (0, 1), (2, 3))):
            (x0, y0), (x1, y1) = legs[a], legs[b]
            z2 = LH * (lvl + 1) / float(bays) if lvl < bays else LH
            _strut("BraceD%d%d" % (lvl, k), (x0, y0, z),
                   (x1, y1, z2 if lvl < bays else LH), steel)

    # ---- tank: a lathed shell with a conical floor and a cone roof ------
    prof = [
        (0.0, TZ - ROOF * 0.9),          # apex of the floor cone, below
        (SPEC["tank_floor_diameter"] / 2.0, TZ),
        (TD - 260.0, TZ + 900.0),        # floor cone up to the shell
        (TD, TZ + 1400.0),
        (TD, TZ + TH - 200.0),
        (TD - 60.0, TZ + TH),            # top rim
        (TD - 300.0, TZ + TH),           # across the rim
        (TD - 300.0, TZ + TH - 300.0),   # down the inside
        (TD - 200.0, TZ + 1600.0),
        (SPEC["tank_floor_diameter"] / 2.0 + 200.0, TZ + 1100.0),
        (0.0, TZ + 700.0),               # inside face of the floor cone
    ]
    tank = _lathe("WaterTank", prof, segments=96, mat=tank_mat)

    # ---- conical roof ----------------------------------------------------
    roof = _lathe("TankRoof", [
        (0.0, TZ + TH - 300.0),
        (TD + 260.0, TZ + TH - 120.0),       # eave, slightly proud of the shell
        (TD + 300.0, TZ + TH - 60.0),
        (TD + 120.0, TZ + TH + 120.0),
        (TD * 0.55, TZ + TH + ROOF * 0.72),
        (TD * 0.20, TZ + TH + ROOF),
        (0.0, TZ + TH + ROOF),
    ], segments=96, mat=tank_mat)

    # ---- staves: the riveted plate joints round the shell ----------------
    ns = SPEC["stave_count"]
    st = bkit.rounded_box("TankStave", 60.0, 260.0, TH - 500.0, r=10.0,
                          segments=2, centre=(0.0, 0.0, 0.0), mat=rivet)
    bkit.array_radial(st, ns)
    bkit.move(st, TD + 10.0, 0.0, TZ + TH / 2.0)
    import bpy
    bpy.context.view_layer.update()

    # ---- skirt: the ring beam the tank sits on ---------------------------
    skirt = bkit.tube("TankSkirt", TD + 120.0, TD - 420.0, 700.0, segments=96,
                      centre=(0.0, 0.0, TZ + 500.0), mat=steel)

    return dict(spec=SPEC, parts=2 + 4 + ns, legs=4, staves=ns)


def _strut(name, p0, p1, mat, t=150.0):
    """A rectangular strut spanning two 3D points, oriented along the span."""
    import math as _m
    dx, dy, dz = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    length = _m.sqrt(dx * dx + dy * dy + dz * dz)
    ob = bkit.rounded_box(name, length, t, t, r=t * 0.3, segments=2,
                          centre=(p0[0] + dx / 2.0, p0[1] + dy / 2.0,
                                  p0[2] + dz / 2.0), mat=mat)
    ob.rotation_euler = (0.0, _m.asin(max(-1.0, min(1.0, dz / length))),
                         _m.atan2(dy, dx))
    import bpy
    bpy.context.view_layer.update()
    return ob


CHECKS = [
    dict(name="overall_height", mm=20600.0, tol=80.0, how="bbox_z"),
    dict(name="leg_height", mm=13000.0, tol=40.0, how="bbox_z", part="TowerLeg11"),
    dict(name="tank_diameter", mm=9000.0, tol=60.0, how="diameter", part="WaterTank"),
    dict(name="tank_floor_to_rim", mm=7440.0, tol=50.0, how="bbox_z",
         part="WaterTank"),
    dict(name="leg_section", mm=420.0, tol=20.0, how="bbox_x", part="TowerLeg11"),
]
