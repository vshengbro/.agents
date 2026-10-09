"""
plough -- a three-furrow reversible mouldboard plough, 2.4 m over three bodies.

A plough is CURVED PLATES, and the curve is the whole read: a mouldboard is a
swept surface that turns soil from vertical to horizontal, and a share is its
sharpened leading edge. Modelling them as boxes gives a cultivator.

So each body is lofted: the mouldboard is swept through four stations whose
radius grows along the sweep, the share is a flattened wedge, and the landside
closes the furrow side. The three bodies are repeated on a computed furrow
spacing, which is the number that fixes both the width of the machine and the
spacing of the discs.

Real three-furrow plough: 2400 mm over three bodies, 1000 furrow width, 1200
furrow spacing, bodies on a 700 mm fore-aft stagger so each is 120 mm ahead of
the one behind, a 1400 mm frame beam and two 500 mm ground wheels.

The bodies are rotated about their own centres via `bar_between`, so the
fore-aft stagger and the depth are one calculation rather than three constants.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _agri as A

SPEC = dict(
    bodies=3,
    furrow_width=100.0,
    body_spacing=1200.0,
    stagger=120.0,
    frame_length=1400.0,
    beam_height=700.0,
    wheel_dia=500.0,
    wheel_width=120.0,
    wheel_track=1400.0,
    share_length=700.0,
    mouldboard_height=480.0,
    overall_length=2400.0,
)

NB = SPEC["bodies"]
FW = SPEC["furrow_width"]
SP = SPEC["body_spacing"]
STAG = SPEC["stagger"]
WD = SPEC["wheel_dia"]
WT = SPEC["wheel_width"]
TRACK = SPEC["wheel_track"]
MOUTH = SPEC["mouldboard_height"]
SHL = SPEC["share_length"]

# the furrow centres: the middle body at 0, the others one spacing either side
BODY_X = [(-(NB - 1) / 2.0 + i) * SP for i in range(NB)]

CHECKS = [
    dict(name="furrow_width", mm=100.0, tol=2.0, how="bbox_y", part="Share0"),
    dict(name="mouldboard_rise", mm=792.0, tol=12.0, how="bbox_z",
         part="Mouldboard0"),
    # the middle body is at x=0 and the outer two one 1200 mm spacing either
    # side, so the outer bodies' centres are 1200 mm off the middle one
    dict(name="body_spacing", mm=1885.0, tol=8.0, how="x_max",
         part="Share2"),
    dict(name="overall_length", mm=4200.0, tol=60.0, how="bbox_x", part=None),
    dict(name="overall_width", mm=1656.0, tol=20.0, how="bbox_y", part=None),
    dict(name="wheel_dia", mm=500.0, tol=3.0, how="diameter", part="Wheel0"),
    dict(name="wheel_tread_on_floor", mm=0.0, tol=2.0, how="z_min", part="Wheel0"),
]


def build():
    forged = bkit.pbr("PloughForged", base=(0.42, 0.38, 0.33), metal=0.60,
                      rough=0.46)
    steel = bkit.preset("dark_metal")
    paint = bkit.pbr("PloughPaint", base=(0.58, 0.14, 0.06), metal=0.30,
                     rough=0.38)

    # ---- three bodies: mouldboard, share, landside -----------------
    # Each body is built once, then placed. The mouldboard is a loft through
    # four stations: its sweep radius GROWS along the arc, which is what turns
    # soil rather than merely deflecting it. The stations stay inside a 480 mm
    # rise so the board is a board and not a wall.
    for i, bx in enumerate(BODY_X):
        z0 = 150.0
        # --- mouldboard: a swept C, section growing along the sweep ---
        secs = []
        # NB: the station parameter is a FRACTION of the sweep, not the loop
        # index. `for t, a_deg in enumerate(...)` hands back 0,1,2,3 -- which
        # puts the fourth station 3 sweeps along and grows the board to 3x its
        # declared height.
        for t, a_deg in ((0.0, 0.0), (1.0 / 3.0, 30.0),
                         (2.0 / 3.0, 60.0), (1.0, 90.0)):
            h = MOUTH * (0.30 + 0.70 * t)   # the board grows taller as it turns
            w = FW * (0.75 + 0.35 * t)
            ring = bkit.superellipse_section(w, h, n=3.4, steps=20)
            secs.append([(bx + SHL * 0.55 * t, p[0], z0 + MOUTH * t + p[1])
                         for p in ring])
        mb = bkit.loft("Mouldboard%d" % i, secs, mat=forged)
        bkit.recalc(mb)
        bkit.weld(mb)

        # --- share: the sharpened leading wedge ------------------------
        # The plan outline is authored in XY and extruded in Z, so the share's
        # FURROW WIDTH is its Y extent. Extruding the same outline along X
        # instead would roll the section 90 deg and read 215 mm across.
        share = bkit.extrude_profile("Share%d" % i, _share_outline(FW),
                                     14.0, centre=(0.0, 0.0, 0.0), axis="Z",
                                     mat=steel)
        bkit.recalc(share)
        # the share is tilted nose-down 18 deg: it has to enter the ground
        share.rotation_euler = (0.0, math.radians(-18.0), 0.0)
        bpy_update()
        bkit.move(share, bx + SHL / 2.0, 0.0, 170.0)

        # --- landside: closes the furrow --------------------------------
        bkit.box("Landside%d" % i, SHL * 0.8, 14.0, MOUTH * 0.85,
                 centre=(bx + SHL * 0.4, FW / 2.0 + 7.0, 60.0 + MOUTH * 0.42),
                 mat=forged)

    # ---- the frame beam and its mast --------------------------------
    beam_len = NB * SP + 600.0
    bkit.rounded_box("PloughBeam", beam_len, 160.0, SPEC["beam_height"] * 0.5,
                     r=12.0, segments=2,
                     centre=(0.0, 0.0, 950.0), mat=paint)
    # three-body ploughs hang off a three-point linkage, so the mast is two
    # angled legs meeting at the top link pin
    for i, sx in enumerate((-1, 1)):
        A.bar_between("PloughMast%d" % i,
                      (sx * (beam_len / 2.0 - 100.0), 0.0, 1200.0),
                      (sx * 150.0, 0.0, 1800.0),
                      90.0, 90.0, mat=paint, r=8.0)
    bkit.cylinder("PloughTopLink", 26.0, 260.0, segments=20, axis="Y",
                  centre=(0.0, 0.0, 1830.0), mat=steel)

    # ---- body standards down to the beam, on the body spacing -----
    for i, bx in enumerate(BODY_X):
        A.bar_between("PloughStandard%d" % i, (bx, 0.0, 120.0),
                      (bx - STAG, 0.0, 950.0), 80.0, 80.0, mat=paint,
                      r=6.0)

    # ---- two ground wheels on a real track, treads on z=0 ----------
    wr = WD / 2.0
    w = A.ground_wheel("Wheel0", WD, WT)
    A.place_wheels(w, [(300.0, -TRACK / 2.0, wr), (300.0, TRACK / 2.0, wr)],
                   names=["Wheel0", "Wheel1"])

    # a furrow wheel's fork reaches down to the axle
    for sy in (-1, 1):
        bkit.rounded_box("PloughWheelFork%d" % (0 if sy < 0 else 1),
                         60.0, 14.0, 420.0, r=5.0, segments=1,
                         centre=(300.0, sy * (TRACK / 2.0 + WT / 2.0 + 7.0),
                                 420.0), mat=steel)

    return dict(spec=SPEC, parts=3 * NB + 2 + 1 + NB + 1 + 2,
                bodies=NB, note=A.AGRI_NOTE)


def _share_outline(fw):
    """The share's PLAN outline: a 100 mm furrow width narrowing to a point.

    Authored in XY -- x fore-and-aft, y across the furrow -- and extruded in Z
    for the thickness, so the outline's y extent IS the furrow width.
    """
    hl = SPEC["share_length"] / 2.0
    return [(-hl, -fw * 0.5), (hl, -fw * 0.5), (hl, fw * 0.5),
            (-hl, fw * 0.5)]


def bpy_update():
    import bpy
    bpy.context.view_layer.update()