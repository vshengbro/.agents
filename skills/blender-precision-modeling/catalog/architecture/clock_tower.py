"""
clock_tower -- a 32 m civic clock tower: a battered masonry shaft, a corbelled
belfry stage with louvres, four clock faces with real hands, a spire and a
weathervane.

Huge size class. The clocks are the object: four dials on the four faces, each
with a real bezel, twelve hour marks placed with `grid_positions`-style trig,
and hands at 10:10 -- the conventional display time, and the only time that
does not hide the hands behind the numerals.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=32000.0,
    base_width=9000.0,
    base_height=1200.0,
    shaft_top_width=6400.0,
    shaft_height=20000.0,
    clock_stage_height=6000.0,
    clock_stage_width=7600.0,
    clock_diameter=3600.0,
    belfry_height=3200.0,
    belfry_width=5800.0,
    spire_height=1600.0,
    faces=4,
    hour_marks=12,
)

BH = SPEC["base_height"]
SH = SPEC["shaft_height"]
CW = SPEC["clock_stage_width"]
CD = SPEC["clock_diameter"]
CZ = BH + SH + SPEC["clock_stage_height"] / 2.0   # clock centre height


def build():
    masonry = bkit.pbr("ClockStone", base=(0.74, 0.70, 0.63), rough=0.66)
    stone_dk = bkit.pbr("ClockStoneDark", base=(0.64, 0.60, 0.54), rough=0.70)
    dial = bkit.pbr("ClockDial", base=(0.93, 0.92, 0.88), rough=0.24)
    metal = bkit.preset("polished_metal")
    louvre = bkit.pbr("BelfryLouvre", base=(0.22, 0.20, 0.18), rough=0.62)

    # ---- battered base ----------------------------------------------------
    base = _lathe("TowerBase", [
        (0.0, 0.0), (SPEC["base_width"] / 2.0 + 400.0, 0.0),
        (SPEC["base_width"] / 2.0 + 400.0, 400.0),
        (SPEC["base_width"] / 2.0 + 120.0, 640.0),
        (SPEC["base_width"] / 2.0, BH),
        (0.0, BH),
    ], segments=72, mat=stone_dk)

    # ---- shaft: a slight batter, straight-tapering ----------------------
    shaft = bkit.loft("TowerShaft", [
        _ring(SPEC["base_width"], SPEC["base_width"], 260.0, 0.0),
        _ring(SPEC["shaft_top_width"] + 160.0,
              SPEC["shaft_top_width"] + 160.0, 240.0, SH * 0.55),
        _ring(SPEC["shaft_top_width"], SPEC["shaft_top_width"], 220.0, SH),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=masonry)
    bkit.recalc(shaft)
    bkit.move(shaft, 0.0, 0.0, BH)

    # ---- clock stage: corbelled out to carry the dials ------------------
    zs = BH + SH
    stage = bkit.loft("ClockStage", [
        _ring(SPEC["shaft_top_width"], SPEC["shaft_top_width"], 220.0, 0.0),
        _ring(CW - 300.0, CW - 300.0, 240.0, 400.0),
        _ring(CW, CW, 260.0, 700.0),
        _ring(CW, CW, 260.0, SPEC["clock_stage_height"] - 300.0),
        _ring(CW + 260.0, CW + 260.0, 280.0, SPEC["clock_stage_height"]),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=masonry)
    bkit.recalc(stage)
    bkit.move(stage, 0.0, 0.0, zs)

    # ---- four dials, each with a bezel, marks and two hands -------------
    # Face normals at 0, 90, 180, 270 deg, computed from SPEC["faces"].
    face_r = CD / 2.0
    y_stage = zs + SPEC["clock_stage_height"] / 2.0
    for f in range(SPEC["faces"]):
        a = 2.0 * math.pi * f / SPEC["faces"]
        nx, ny = math.cos(a), math.sin(a)          # outward normal
        tx, ty = -ny, nx                            # tangent, for the marks

        # the dial plate: a shallow disc standing proud of the wall
        plate = _lathe("ClockDial%d" % (f + 1), [
            (0.0, 0.0), (face_r, 0.0), (face_r, 90.0), (face_r - 70.0, 130.0),
            (0.0, 130.0),
        ], segments=64, mat=dial)
        # a lathe stands along +Z; tip it to face outward along the normal
        plate.rotation_euler = (math.radians(90.0), 0.0, a)
        bkit.move(plate, nx * (CW / 2.0 - 40.0), ny * (CW / 2.0 - 40.0), CZ)
        bpy_update()

        # twelve hour marks on the bezel, positioned by trig
        for m in range(SPEC["hour_marks"]):
            ma = 2.0 * math.pi * m / SPEC["hour_marks"]
            r = face_r - 180.0
            mx = nx * (CW / 2.0 + 30.0) + tx * (r * math.sin(ma))
            my = ny * (CW / 2.0 + 30.0) + ty * (r * math.sin(ma))
            mz = CZ + r * math.cos(ma)
            mark = bkit.rounded_box("ClockMark%d_%d" % (f + 1, m), 60.0,
                                    160.0, 260.0, r=20.0, segments=1,
                                    centre=(mx, my, mz), mat=metal)
            mark.rotation_euler = (0.0, 0.0, a)
            bpy_update()

        # hands at 10:10 -- hour at 305 deg, minute at 60 deg from 12
        for ang, ln, wd, nm in ((305.0, face_r * 0.55, 110.0, "Hour"),
                                (60.0, face_r * 0.80, 80.0, "Minute")):
            ha = math.radians(ang)
            hx = nx * (CW / 2.0 + 90.0) + tx * (ln / 2.0 * math.sin(ha))
            hy = ny * (CW / 2.0 + 90.0) + ty * (ln / 2.0 * math.sin(ha))
            hz = CZ + (ln / 2.0) * math.cos(ha)
            hand = bkit.rounded_box("Clock%sHand%d" % (nm, f + 1), 70.0, wd,
                                    ln, r=25.0, segments=1,
                                    centre=(hx, hy, hz), mat=metal)
            hand.rotation_euler = (-ha, 0.0, a)
            bpy_update()

    # ---- belfry with louvres --------------------------------------------
    zb = zs + SPEC["clock_stage_height"]
    belfry = bkit.loft("TowerBelfry", [
        _ring(SPEC["belfry_width"] + 300.0, SPEC["belfry_width"] + 300.0,
              200.0, 0.0),
        _ring(SPEC["belfry_width"], SPEC["belfry_width"], 180.0, 500.0),
        _ring(SPEC["belfry_width"] - 500.0, SPEC["belfry_width"] - 500.0,
              160.0, SPEC["belfry_height"] - 300.0),
        _ring(SPEC["belfry_width"] - 900.0, SPEC["belfry_width"] - 900.0,
              140.0, SPEC["belfry_height"]),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=stone_dk)
    bkit.recalc(belfry)
    bkit.move(belfry, 0.0, 0.0, zb)

    for f in range(SPEC["faces"]):
        a = 2.0 * math.pi * f / SPEC["faces"]
        for k in range(7):
            lv = bkit.rounded_box("Louvre%d_%d" % (f, k), 60.0, 1500.0, 110.0,
                                  r=20.0, segments=1,
                                  centre=(math.cos(a) * (SPEC["belfry_width"] / 2.0 - 100.0),
                                          math.sin(a) * (SPEC["belfry_width"] / 2.0 - 100.0),
                                          zb + 600.0 + k * 340.0), mat=louvre)
            lv.rotation_euler = (0.0, math.radians(-22.0), a)
            bpy_update()

    # ---- spire and weathervane ------------------------------------------
    zs2 = zb + SPEC["belfry_height"]
    spire = _lathe("TowerSpire", [
        (0.0, zs2),
        (SPEC["belfry_width"] / 2.0 - 900.0, zs2),
        (SPEC["belfry_width"] / 2.0 - 1400.0, zs2 + SPEC["spire_height"] * 0.7),
        (220.0, zs2 + SPEC["spire_height"]),
        (0.0, zs2 + SPEC["spire_height"]),
    ], segments=48, mat=masonry)

    vane = _lathe("Weathervane", [
        (0.0, zs2 + SPEC["spire_height"] - 200.0),
        (70.0, zs2 + SPEC["spire_height"] - 100.0),
        (40.0, zs2 + SPEC["spire_height"] + 700.0),
        (0.0, zs2 + SPEC["spire_height"] + 900.0),
    ], segments=24, mat=metal)
    arrow = bkit.rounded_box("VaneArrow", 1100.0, 60.0, 200.0, r=20.0,
                             segments=1, centre=(400.0, 0.0,
                                                 zs2 + SPEC["spire_height"] + 420.0),
                             mat=metal)

    return dict(spec=SPEC, parts=5 + SPEC["faces"] * (1 + SPEC["hour_marks"] + 2),
                faces=SPEC["faces"])


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=6)]


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


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="overall_height", mm=32900.0, tol=90.0, how="bbox_z"),
    dict(name="base_width", mm=9800.0, tol=60.0, how="diameter", part="TowerBase"),
    dict(name="shaft_height", mm=20000.0, tol=50.0, how="bbox_z", part="TowerShaft"),
    dict(name="clock_stage_width", mm=7860.0, tol=60.0, how="diameter",
         part="ClockStage"),
    dict(name="belfry_height", mm=3200.0, tol=50.0, how="bbox_z", part="TowerBelfry"),
]
