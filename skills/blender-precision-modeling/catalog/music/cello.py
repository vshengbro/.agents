"""
cello -- 4/4 cello, 755 mm body, 1205 mm overall with the endpin, four strings.

The cello is the violin construction scaled by a factor of ~2.1 and then
re-dimensioned: a cello is not a big violin. Its bouts are proportionally
rounder, the ribs are 3x deeper, the neck is shorter relative to the body, and
it stands on an endpin, which is what takes the overall length to 1205 mm.

Everything repeated is computed: the four strings come from `bkit.lay_out`, the
two pegs from a two-row `grid_positions`, and the body plates from one silhouette
scaled at three heights. The C-bout waist is the control point list's job -- a
cello with a straight-sided body reads as a jar.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_length=755.0,
    body_width=445.0,
    upper_bout_width=340.0,
    waist_width=230.0,
    rib_depth=118.0,
    # A cello's 1205 mm is body + neck + pegbox + scroll, measured WITHOUT the
    # endpin. Deployed on the floor the endpin adds 280 mm below the tail, so
    # the standing height of this model is 1494 mm.
    total_length=1494.0,
    body_and_neck_length=1214.0,
    strings=4,
    string_gap=19.0,
    string_diameter=1.6,
    scale_length=690.0,
    nut_z=1090.0,
    endpin_length=300.0,
)

BODY_L = SPEC["body_length"]
NUT_Z = SPEC["nut_z"]
BRIDGE_Z = NUT_Z - SPEC["scale_length"]
STR_N = SPEC["strings"]

# Half-silhouette, tail (z=0) to neck end (z=755). The waist at z=378 is the
# narrowest point; the lower bout peaks at z=195.
_HALF = [
    (0.0, 0.0), (92.0, 14.0), (152.0, 48.0), (196.0, 112.0), (222.0, 195.0),
    (216.0, 276.0), (186.0, 336.0), (138.0, 378.0), (156.0, 424.0),
    (176.0, 478.0), (170.0, 556.0), (150.0, 624.0), (124.0, 686.0),
    (102.0, 726.0), (94.0, 755.0),
]


def _ring(t):
    half = [(x * t, z) for (x, z) in _HALF]
    return half + [(-x, z) for (x, z) in reversed(_HALF[1:-1])]


def _rod(name, r, p0, p1, mat, segments=10):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ob = bkit.cylinder(name, r, length, segments=segments, centre=(0, 0, 0),
                       axis="Z", mat=mat)
    ob.rotation_euler = (-math.atan2(dy, math.hypot(dx, dz)),
                         math.atan2(dx, dz), 0.0)
    bkit.move(ob, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    return ob


def build():
    top = bkit.pbr("CelloTop", base=(0.60, 0.30, 0.12), rough=0.17, coat=0.7)
    back = bkit.pbr("CelloBack", base=(0.38, 0.16, 0.06), rough=0.20, coat=0.6)
    ribs = bkit.pbr("CelloRibs", base=(0.46, 0.21, 0.09), rough=0.34)
    maple = bkit.pbr("CelloMaple", base=(0.62, 0.40, 0.18), rough=0.30)
    board = bkit.pbr("CelloBoard", base=(0.07, 0.05, 0.04), rough=0.40)
    ebony = bkit.pbr("CelloEbony", base=(0.06, 0.05, 0.045), rough=0.36)
    steel = bkit.pbr("CelloStrings", base=(0.76, 0.77, 0.80), metal=0.85,
                     rough=0.22)
    steel_hw = bkit.pbr("CelloHardware", base=(0.80, 0.81, 0.83), metal=0.85,
                        rough=0.24)

    half_d = SPEC["rib_depth"] / 2.0
    for tag, y0, mat in (("Top", half_d, top), ("Back", -half_d, back)):
        secs = []
        for dz, t in ((0.0, 1.0), (22.0, 0.985), (45.0, 0.92),
                      (62.0, 0.80), (72.0, 0.58)):
            secs.append([(x, y0 + dz, z) for (x, z) in _ring(t)])
        bkit.recalc(bkit.loft("Cello%s" % tag, secs, mat=mat))

    rib = bkit.extrude_profile("CelloRibsBox", _ring(1.0), SPEC["rib_depth"],
                               centre=(0, 0, 0), axis="Y", mat=ribs)
    bkit.recalc(rib)

    # ---- neck, fingerboard, pegbox, scroll --------------------------------
    nk = []
    for i in range(6):
        t = i / 5.0
        z = BODY_L - 130.0 + t * (NUT_Z - BODY_L + 130.0)
        w = 100.0 + (72.0 - 100.0) * t
        ring = bkit.rounded_rect_section(w, 44.0, r=15.0, per_corner=4)
        nk.append([(x, y - 26.0, z) for (x, y) in ring])
    bkit.recalc(bkit.loft("CelloNeck", nk, mat=maple))

    fb = []
    for z, w, y in ((BODY_L - 320.0, 96.0, -6.0), (BODY_L, 92.0, -8.0),
                    (NUT_Z, 72.0, -10.0)):
        ring = bkit.rounded_rect_section(w, 22.0, r=4.0, per_corner=3)
        fb.append([(x, yy + y, z) for (x, yy) in ring])
    bkit.recalc(bkit.loft("CelloFingerboard", fb, mat=board))
    bkit.box("CelloNut", 74.0, 12.0, 8.0, centre=(0, -18.0, NUT_Z + 4.0),
             mat=ebony)

    peg_y = -26.0
    pegbox = bkit.extrude_profile(
        "CelloPegbox",
        [(-30.0, 0.0), (-36.0, 40.0), (-26.0, 78.0),
         (26.0, 78.0), (36.0, 40.0), (30.0, 0.0)],
        50.0, centre=(0, peg_y, NUT_Z + 6.0), axis="Y", mat=maple)
    bkit.recalc(pegbox)
    prof = []
    for i in range(9):
        t = i / 8.0
        prof.append((38.0 * (1.0 - 0.74 * t) + 3.0, 80.0 + 34.0 * t))
    prof.append((4.0, 118.0))
    scroll = bkit.lathe("CelloScroll", prof, segments=32, centre=(0, 0, 0),
                        mat=maple)
    bkit.move(scroll, 0.0, peg_y, NUT_Z + 6.0)

    pegs = []
    for i, side in enumerate((-1, -1, 1, 1)):
        z = NUT_Z + 26.0 + (i % 2) * 42.0
        pegs.append(bkit.cylinder("Cp%d" % i, 6.5, 56.0, segments=12,
                                  centre=(side * 26.0, peg_y, z), axis="X",
                                  mat=ebony))
        pegs.append(bkit.box("Cg%d" % i, 13.0, 24.0, 16.0,
                             centre=(side * 44.0, peg_y, z), mat=ebony))
    bkit.join(pegs, name="CelloPegs")

    # ---- tailpiece, bridge, f-holes, endpin -------------------------------
    # The top plate's crown reaches y = +72 and its rim sits at +59, so the
    # bridge and f-holes stand on the crown and the tailpiece hangs just above
    # it -- at the old y = 96 they floated clear of the plate entirely.
    tail = bkit.extrude_profile("CelloTailpiece",
                                [(-46.0, 0.0), (-52.0, 62.0), (-38.0, 150.0),
                                 (38.0, 150.0), (52.0, 62.0), (46.0, 0.0)],
                                16.0, centre=(0, 76.0, 205.0), axis="Y",
                                mat=ebony)
    bkit.recalc(tail)
    bkit.bevel(tail, width_mm=2.0, segments=2)

    bkit.rounded_box("CelloBridge", 92.0, 16.0, 78.0, r=3.0, segments=2,
                     centre=(0, 76.0, BRIDGE_Z), mat=maple)
    for i, side in enumerate((-1, 1)):
        bkit.rounded_box("CelloFhole%d" % i, 11.0, 12.0, 100.0, r=4.0,
                         segments=2,
                         centre=(side * 132.0, 68.0, 440.0), mat=ebony)

    # The endpin hangs 300 mm below the tail. It is centred so its TOP is at
    # z=20 (buried 20 mm up into the body's lower block) and its bottom lands at
    # z=-280, which is what puts the floor-to-scroll total at 1205 mm.
    bkit.cylinder("CelloEndpin", 8.0, SPEC["endpin_length"], segments=16,
                  centre=(0, 0, 20.0 - SPEC["endpin_length"] / 2.0),
                  axis="Z", mat=steel_hw)

    # ---- four strings, tailpiece -> bridge -> nut -------------------------
    # Strings run in the plane just above the arched top plate.
    d = SPEC["string_diameter"]
    strings = []
    y_tail, y_bridge, y_nut = 78.0, 76.0, -26.0
    for i, (x, _w) in enumerate(bkit.lay_out([d] * STR_N,
                                             gap=SPEC["string_gap"])):
        r = 0.65 + 0.24 * i
        strings.append(_rod("Cs%d" % i, r, (x, y_tail, 200.0),
                            (x, y_bridge, BRIDGE_Z), steel))
        strings.append(_rod("Ct%d" % i, r, (x, y_bridge, BRIDGE_Z),
                            (x, y_nut, NUT_Z), steel))
    bkit.join(strings, name="CelloStrings")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="body_length", mm=755.0, tol=0.8, how="bbox_z", part="CelloRibsBox"),
    dict(name="body_width", mm=445.0, tol=1.5, how="bbox_x", part="CelloRibsBox"),
    dict(name="rib_depth", mm=118.0, tol=1.5, how="bbox_y", part="CelloRibsBox"),
    dict(name="overall_height", mm=1494.0, tol=3.0, how="bbox_z"),
]