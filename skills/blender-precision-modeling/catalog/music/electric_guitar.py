"""
electric_guitar -- Stratocaster-style solid body, 920 mm long, six strings.

A solid-body electric is the opposite construction problem to an acoustic: the
outline is a flat plate with real thickness, not a lofted volume, so the body is
an `extrude_profile` of a hand-built double-cutaway silhouette. The silhouette
is the model -- a strat outline with the wrong waist or the wrong horn length
reads as a blob, so the control points are listed explicitly and closed in one
place.

Strings are six, evenly spaced by `bkit.lay_out`, running bridge -> nut, and
the twenty-two frets come from the 12th-root-of-two fret law against a real
648 mm scale, because evenly spaced frets are visible even at 720 px.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    total_length=895.0,
    body_length=400.0,
    body_width=326.0,
    body_depth=45.0,
    scale_length=648.0,
    nut_z=745.0,
    strings=6,
    string_gap=8.4,
    string_diameter=1.7,
    frets=22,
    bridge_z=97.0,
)

BODY_L = SPEC["body_length"]
NUT_Z = SPEC["nut_z"]
BRIDGE_Z = NUT_Z - SPEC["scale_length"]
STR_N = SPEC["strings"]

# Right half of the outline, tail (z=0) to neck joint (z=400). The waist is at
# z~232, the lower bout peaks at z~90, and the upper horn runs longer than the
# lower one -- that asymmetry is what separates a strat from a telecaster.
_HALF = [
    (60.0, 0.0), (135.0, 20.0), (163.0, 75.0), (160.0, 130.0),
    (128.0, 190.0), (104.0, 232.0), (126.0, 275.0), (138.0, 315.0),
    (128.0, 350.0), (96.0, 372.0), (70.0, 388.0), (64.0, 400.0),
]
_HALF_L = [(-64.0, 400.0), (-70.0, 388.0), (-96.0, 372.0), (-128.0, 350.0),
           (-140.0, 310.0), (-128.0, 268.0), (-104.0, 232.0), (-128.0, 190.0),
           (-160.0, 130.0), (-163.0, 75.0), (-135.0, 20.0), (-60.0, 0.0)]


def _rod(name, r, p0, p1, mat, segments=12):
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
    body_mat = bkit.pbr("ElecBody", base=(0.30, 0.34, 0.44), rough=0.22,
                        coat=0.6)
    neck_mat = bkit.pbr("ElecNeck", base=(0.44, 0.28, 0.13), rough=0.30)
    board = bkit.pbr("ElecBoard", base=(0.10, 0.07, 0.05), rough=0.42)
    hw = bkit.pbr("ElecHardware", base=(0.82, 0.82, 0.84), metal=0.85,
                  rough=0.20)
    chrome = bkit.pbr("ElecChrome", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.10)
    steel = bkit.pbr("ElecStrings", base=(0.74, 0.75, 0.78), metal=0.85,
                     rough=0.24)
    black = bkit.pbr("ElecBlack", base=(0.05, 0.05, 0.06), rough=0.36)
    guard = bkit.pbr("ElecGuard", base=(0.88, 0.86, 0.80), rough=0.20,
                     coat=0.5)
    cream = bkit.pbr("ElecCream", base=(0.85, 0.82, 0.72), rough=0.30)

    # ---- body: flat plate with real thickness, standing upright ------------
    # The outline is authored in ABSOLUTE z (0 at the tail, 400 at the neck
    # joint), and `extrude_profile`'s centre is an additive offset rather than a
    # recentring: passing BODY_L/2 here would shift the whole silhouette up by
    # 200 mm and put the tail in mid-air.
    outline = _HALF + _HALF_L
    body = bkit.extrude_profile("ElecBodyPlate", outline,
                                SPEC["body_depth"], centre=(0, 0, 0),
                                axis="Y", mat=body_mat)
    bkit.recalc(body)
    bkit.bevel(body, width_mm=3.0, segments=3, angle_deg=40)

    # Neck pocket: a real cut, one millimetre proud of the back face so the
    # cutter and the body surface cross instead of touching along an edge.
    bkit.boolean(body, bkit.rounded_box("_pocket", 66.0, SPEC["body_depth"] + 4.0,
                                        56.0, r=3.0, segments=2,
                                        centre=(0, 1.0, 372.0)), "DIFFERENCE")

    # ---- neck, fretboard, frets -------------------------------------------
    neck_t = 21.0
    face = -SPEC["body_depth"] / 2.0          # front of the instrument
    nk = []
    for i in range(6):
        t = i / 5.0
        z = 380.0 + t * (NUT_Z - 380.0)
        w = 56.0 + (43.0 - 56.0) * t
        ring = bkit.rounded_rect_section(w, neck_t, r=min(w, neck_t) * 0.40,
                                         per_corner=4)
        nk.append([(x, y + face - neck_t / 2.0, z) for (x, y) in ring])
    bkit.recalc(bkit.loft("ElecNeck", nk, mat=neck_mat))

    f22 = NUT_Z - SPEC["scale_length"] * (1.0 - 2.0 ** (-22.0 / 12.0))
    fb = []
    for z, w in ((f22, 57.0), (400.0, 55.0), (NUT_Z, 43.0)):
        ring = bkit.rounded_rect_section(w, 6.0, r=2.0, per_corner=3)
        fb.append([(x, y + face - 3.0, z) for (x, y) in ring])
    bkit.recalc(bkit.loft("ElecFretboard", fb, mat=board))

    frets = []
    for n in range(1, 23):
        z = NUT_Z - SPEC["scale_length"] * (1.0 - 2.0 ** (-n / 12.0))
        t = max(0.0, min(1.0, (z - f22) / (NUT_Z - f22)))
        w = 57.0 + (43.0 - 57.0) * t
        frets.append(bkit.box("ef%02d" % n, w - 0.5, 2.4, 1.3,
                              centre=(0.0, face - 6.0 - 0.5, z), mat=hw))
    bkit.join(frets, name="ElecFrets")
    bkit.box("ElecNut", 44.0, 7.0, 4.5, centre=(0.0, face - 6.5, NUT_Z + 2.0),
             mat=board)

    # ---- headstock and six inline machine heads ---------------------------
    hs = bkit.extrude_profile(
        "ElecHeadstock",
        [(-24.0, 0.0), (-28.0, 30.0), (-24.0, 92.0), (-16.0, 150.0),
         (16.0, 150.0), (24.0, 92.0), (28.0, 30.0), (24.0, 0.0)],
        13.0, centre=(0.0, face - 6.0, NUT_Z), axis="Y", mat=neck_mat)
    bkit.recalc(hs)
    bkit.bevel(hs, width_mm=1.5, segments=2)

    pegs = []
    for i in range(STR_N):
        z = NUT_Z + 26.0 + i * 21.0
        pegs.append(bkit.cylinder("ep%d" % i, 3.0, 22.0, segments=12,
                                  centre=(0.0, face - 6.0, z), axis="Y",
                                  mat=chrome))
        pegs.append(bkit.box("es%d" % i, 5.0, 12.0, 8.0,
                             centre=(20.0, face - 6.0, z), mat=chrome))
    bkit.join(pegs, name="ElecTuners")

    # ---- pickups, tremolo bridge, controls, jack, pickguard ---------------
    for tag, z in (("bridge", 150.0), ("middle", 215.0), ("neck", 300.0)):
        bkit.rounded_box("ElecPu%s" % tag, 82.0, 21.0, 15.0, r=2.5, segments=2,
                         centre=(0.0, face - 7.5, z), mat=black)
        for k in range(6):
            x = -33.0 + k * 13.2
            bkit.cylinder("ElecPp%s%d" % (tag, k), 2.6, 2.6, segments=10,
                          centre=(x, face - 15.4, z), axis="Y", mat=hw)

    bkit.rounded_box("ElecBridge", 82.0, 32.0, 12.0, r=2.0, segments=2,
                     centre=(0.0, face - 6.0, BRIDGE_Z), mat=chrome)
    for i in range(STR_N):
        bkit.box("ElecSaddle%d" % i, 6.0, 26.0, 3.0,
                 centre=(-26.0 + i * 10.4, face - 13.0, BRIDGE_Z), mat=hw)

    # Knobs and the switch sit in the treble-side rout, so they are laid out on
    # one gap rather than hand-placed.
    for i, (x, z) in enumerate(bkit.lay_out([17.0] * 4, gap=13.0)):
        bkit.cylinder("ElecKnob%d" % i, 7.5, 15.0, segments=18,
                      centre=(x + 96.0, face - 8.0, 214.0), axis="Y", mat=black)
    bkit.box("ElecSwitch", 7.0, 16.0, 32.0,
             centre=(96.0, face - 8.0, 262.0), mat=black)
    bkit.box("ElecJack", 30.0, 12.0, 34.0,
             centre=(104.0, SPEC["body_depth"] / 2.0 - 6.0, 150.0), mat=chrome)

    guard_poly = [(-120.0, 120.0), (-124.0, 250.0), (-96.0, 330.0),
                  (-40.0, 340.0), (60.0, 300.0), (118.0, 200.0),
                  (110.0, 120.0), (-30.0, 112.0)]
    pg = bkit.extrude_profile("ElecPickguard", guard_poly, 2.6,
                              centre=(0.0, face - 1.3, 0.0), axis="Y", mat=guard)
    bkit.recalc(pg)
    bkit.bevel(pg, width_mm=0.6, segments=2)

    # ---- strings: six, laid out on one gap, bridge -> nut ------------------
    d = SPEC["string_diameter"]
    strings = []
    for i, (x, _w) in enumerate(bkit.lay_out([d] * STR_N, gap=SPEC["string_gap"])):
        r = 0.60 + 0.17 * i
        strings.append(_rod("es%d" % i, r, (x, face - 14.0, BRIDGE_Z),
                            (x, face - 9.0, NUT_Z), steel))
    bkit.join(strings, name="ElecStrings")

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="body_length", mm=400.0, tol=0.6, how="bbox_z", part="ElecBodyPlate"),
    dict(name="body_width", mm=326.0, tol=0.6, how="bbox_x", part="ElecBodyPlate"),
    dict(name="body_depth", mm=45.0, tol=1.5, how="bbox_y", part="ElecBodyPlate"),
    dict(name="overall_length", mm=895.0, tol=1.5, how="bbox_z"),
]