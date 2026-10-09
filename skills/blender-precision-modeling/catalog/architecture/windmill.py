"""
windmill -- tower mill: a tapered round tower, a boarded cap, a gallery, and
four lattice sails on an array_radial.

Huge size class: 21.8 m to the cap, with a 16 m sail wheel. The sails are the
object. Each is a lofted lattice -- two booms, 14 bars, all positions from
`grid_positions` -- and the four are one swept object, not four copies.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tower_height=14000.0,
    tower_base_diameter=7000.0,
    tower_top_diameter=4200.0,
    gallery_height=1200.0,
    cap_height=3600.0,
    sail_count=4,
    sail_length=7000.0,
    sail_boom_width=260.0,
    sail_bar_count=14,
    sail_bar_width=220.0,
    overall_height=21800.0,
)

TH = SPEC["tower_height"]
BD = SPEC["tower_base_diameter"] / 2.0
TD = SPEC["tower_top_diameter"] / 2.0
GH = SPEC["gallery_height"]
CH = SPEC["cap_height"]
SL = SPEC["sail_length"]
NR = SPEC["sail_count"]

HUB_Z = TH + 900.0          # sail centre above the ground


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
    brick = bkit.pbr("WindmillBrick", base=(0.56, 0.36, 0.28), rough=0.70)
    board = bkit.pbr("WindmillBoard", base=(0.30, 0.17, 0.10), rough=0.62)
    timber = bkit.pbr("WindmillTimber", base=(0.38, 0.26, 0.14), rough=0.60)
    canvas = bkit.pbr("WindmillCanvas", base=(0.80, 0.77, 0.68), rough=0.72)

    # ---- tower: a lathed taper with a slight belly at the base -----------
    prof = [(0.0, 0.0), (BD + 260.0, 0.0), (BD, 400.0)]
    steps = 8
    for i in range(steps + 1):
        f = i / float(steps)
        r = BD + (TD - BD) * (f ** 1.25)
        prof.append((r, 400.0 + (TH - 400.0) * f))
    prof.append((0.0, TH))
    tower = _lathe("WindmillTower", prof, segments=72, mat=brick)

    # ---- gallery: a corbelled ring at the tower head --------------------
    gallery = _lathe("WindmillGallery", [
        (TD, TH - 300.0),
        (TD + 500.0, TH + 200.0),
        (TD + 620.0, TH + GH - 200.0),
        (TD + 560.0, TH + GH),
        (0.0, TH + GH),
    ], segments=72, mat=timber)

    # ---- cap: a boarded ogee -------------------------------------------
    zc = TH + GH
    prof2 = [(0.0, zc)]
    for i in range(7):
        f = i / 6.0
        r = (TD + 520.0) * (1.0 - f) ** 1.5 * (1.0 + 0.12 * math.sin(math.pi * f))
        prof2.append((max(60.0, r), zc + CH * f))
    prof2.append((0.0, zc + CH))
    cap = _lathe("WindmillCap", prof2, segments=72, mat=board)

    # ---- one sail: two booms, N bars, a canvas panel --------------------
    # Built in the XY plane about the origin so array_radial orbits it, then
    # stood upright about X and lifted to hub height. Lofting keeps the
    # object's location at zero, which the sweep requires.
    bw = SPEC["sail_boom_width"]
    secs = []
    for (rad, hw) in ((700.0, bw), (2000.0, bw * 0.85),
                      (SL * 0.72, bw * 0.7), (SL, bw * 0.55)):
        secs.append([(rad, y, z) for (y, z) in bkit.rounded_rect_section(
            hw, hw * 0.42, hw * 0.2, per_corner=3)])
    sail = bkit.loft("WindmillSails", secs, closed_loop=True,
                     cap_start=True, cap_end=True, mat=timber)
    bkit.recalc(sail)
    bkit.array_radial(sail, NR)
    # stand the rotor up about X, THEN lift it to hub height
    sail.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(sail, 0.0, 0.0, HUB_Z)
    import bpy
    bpy.context.view_layer.update()

    # ---- sail bars: the lattice that makes it a mill, not a paddle ------
    bar_w = SPEC["sail_bar_width"]
    for i in range(SPEC["sail_bar_count"]):
        f = (i + 0.5) / SPEC["sail_bar_count"]
        rad = 700.0 + (SL - 700.0) * f
        bkit.rounded_box("SailBar%d" % (i + 1), bar_w, 1900.0, 70.0, r=12.0,
                         segments=2, centre=(rad, 0.0, 0.0), mat=timber)

    # ---- canvas: the sail cloth on the inner face of the bars ----------
    canvas_p = bkit.rounded_box("SailCanvas", SL - 900.0, 60.0, 2000.0,
                                r=20.0, segments=2,
                                centre=(700.0 + (SL - 900.0) / 2.0, -190.0, 0.0),
                                mat=canvas)
    bkit.array_radial(canvas_p, NR)
    canvas_p.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(canvas_p, 0.0, 0.0, HUB_Z)
    bpy.context.view_layer.update()

    # ---- hub and windshaft ----------------------------------------------
    hub = bkit.cylinder("WindmillHub", 520.0, 900.0, segments=40,
                        centre=(0.0, 0.0, HUB_Z), axis="Y", mat=timber)
    shaft = bkit.cylinder("Windshaft", 220.0, 2600.0, segments=24,
                          centre=(0.0, 1300.0, HUB_Z), axis="Y", mat=timber)

    return dict(spec=SPEC, parts=5 + SPEC["sail_bar_count"], sails=NR)


CHECKS = [
    dict(name="tower_height", mm=14000.0, tol=40.0, how="bbox_z",
         part="WindmillTower"),
    dict(name="tower_base_diameter", mm=7520.0, tol=40.0, how="diameter",
         part="WindmillTower"),
    dict(name="sail_reach", mm=14000.0, tol=60.0, how="diameter",
         part="WindmillSails"),
    dict(name="overall_height", mm=21935.0, tol=80.0, how="bbox_z"),
    dict(name="hub_diameter", mm=1040.0, tol=20.0, how="diameter",
         part="WindmillHub"),
]
