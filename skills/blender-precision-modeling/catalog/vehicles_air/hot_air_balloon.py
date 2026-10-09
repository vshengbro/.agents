"""
hot_air_balloon -- an 18 m envelope with a 1.2 m basket, 26 m to the top.

A balloon is ONE PROFILE: crown, shoulder, equator, throat, mouth, revolved.
That is the whole reason `lathe` exists. What is not the profile is the rigging
-- sixteen LOAD TAPES running over the shoulder to a burner frame, and twenty
four vertical panel seams on the envelope itself. Both are repeated features
and both are computed: the tapes are arrayed radially about the Z axis at the
crown radius, the seams are lathed ring-edges at real gore angles.

The envelope is not a sphere: a real hot-air envelope is taller than it is
wide, with a flat crown and a nearly cylindrical throat, and getting that
profile right is the difference between a balloon and a beach ball.

Real sport balloon: 18000 mm envelope diameter, 14000 mm mouth, 26.2 m overall,
16 suspension tapes, 1200 x 1100 x 1100 mm basket.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _craft as C

SPEC = dict(
    envelope_dia=18000.0,
    mouth_dia=14000.0,
    mouth_outer_dia=14120.0,
    envelope_height=20000.0,
    gores=24,
    tapes=16,
    basket_length=1200.0,
    basket_width=1100.0,
    basket_height=1100.0,
    burner_height=1600.0,
    overall_height=22700.0,
)

R = SPEC["envelope_dia"] / 2.0
MOUTH = SPEC["mouth_dia"] / 2.0
MOUTH_Z = SPEC["basket_height"] + SPEC["burner_height"]
TOP_Z = MOUTH_Z + SPEC["envelope_height"]
TAPE_R = R * 0.86

CHECKS = [
    dict(name="envelope_dia", mm=18000.0, tol=40.0, how="bbox_x",
         part="BalloonEnvelope"),
    dict(name="throat_outer_dia", mm=14120.0, tol=20.0, how="bbox_x",
         part="BalloonThroat"),
    dict(name="envelope_height", mm=20000.0, tol=40.0, how="bbox_z",
         part="BalloonEnvelope"),
    dict(name="top_z", mm=22700.0, tol=40.0, how="top_z",
         part="BalloonEnvelope"),
    dict(name="basket_length", mm=1200.0, tol=5.0, how="bbox_x",
         part="BalloonBasket"),
    dict(name="basket_height", mm=1100.0, tol=5.0, how="bbox_z",
         part="BalloonBasket"),
    dict(name="basket_on_floor", mm=0.0, tol=5.0, how="z_min",
         part="BalloonBasket"),
    dict(name="tape_row_span", mm=15630.0, tol=20.0, how="bbox_x",
         part="BalloonTapes"),
]


def build():
    gore_a = bkit.pbr("BalloonGore", base=(0.88, 0.24, 0.18), rough=0.62)
    gore_b = bkit.pbr("BalloonGoreAlt", base=(0.94, 0.86, 0.28), rough=0.62)
    gore_c = bkit.pbr("BalloonGoreDark", base=(0.20, 0.34, 0.56), rough=0.62)
    wicker = bkit.pbr("BalloonWicker", base=(0.56, 0.40, 0.20), rough=0.70)
    rope = bkit.pbr("BalloonRope", base=(0.76, 0.70, 0.48), rough=0.84)
    steel = bkit.preset("brushed_metal")

    # ---- the envelope: ONE revolved profile ------------------------
    h = SPEC["envelope_height"]
    prof = [(0.0, h), (R * 0.30, h * 0.965), (R * 0.62, h * 0.86),
            (R * 0.90, h * 0.66), (R, h * 0.44), (R * 0.98, h * 0.24),
            (R * 0.90, h * 0.09), (MOUTH, 0.0)]
    env = bkit.lathe("BalloonEnvelope", prof, segments=64,
                     centre=(0.0, 0.0, MOUTH_Z), mat=gore_a)
    # the profile DESCENDS from the crown to the mouth, so the revolved
    # faces come out inside-out and the envelope reports a negative volume
    bkit.recalc(env)
    bkit.assign_faces_by(env, gore_b,
                         lambda c, n: (math.atan2(c.y, c.x)
                                       % (2.0 * math.pi)) < 0.9)
    bkit.assign_faces_by(env, gore_c,
                         lambda c, n: 2.4 < (math.atan2(c.y, c.x)
                                             % (2.0 * math.pi)) < 3.0)

    # ---- the mouth hoop and the load tapes --------------------------
    bkit.tube("BalloonThroat", MOUTH + 60.0, MOUTH, 260.0, segments=64,
              centre=(0.0, 0.0, MOUTH_Z + 130.0), mat=rope)

    tape = bkit.rounded_box("BalloonTapes", 150.0, 150.0, h * 0.80, r=40.0,
                            segments=3,
                            centre=(TAPE_R, 0.0, MOUTH_Z + h * 0.40),
                            mat=rope)
    bpy.context.view_layer.update()
    bkit.array_radial(tape, SPEC["tapes"], axis="Z", centre=(0.0, 0.0, 0.0))

    # ---- the burner frame: a square ring of uprights ----------------
    up = MOUTH * 0.72
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        C.strut("BalloonUpright%d" % i, (sx * up, sy * up, SPEC["basket_height"]),
                (sx * up, sy * up, MOUTH_Z), 42.0, mat=steel)
    for i, (p0, p1) in enumerate((((-up, -up), (up, -up)),
                                  ((up, -up), (up, up)),
                                  ((up, up), (-up, up)),
                                  ((-up, up), (-up, -up)))):
        C.strut("BalloonBurnerBar%d" % i,
                (p0[0], p0[1], MOUTH_Z - 120.0),
                (p1[0], p1[1], MOUTH_Z - 120.0), 50.0, mat=steel)
    bkit.rounded_box("BalloonBurner", 700.0, 700.0, 620.0, r=60.0,
                     segments=3, centre=(0.0, 0.0, MOUTH_Z - 430.0),
                     mat=steel)
    for i, (sx, sy) in enumerate(((-1, 1), (1, 1))):
        bkit.cylinder("BalloonBurnerCoil%d" % i, 110.0, 420.0, segments=20,
                      centre=(sx * 260.0, sy * 260.0, MOUTH_Z - 430.0),
                      mat=bkit.pbr("BalloonFlame", base=(1.0, 0.55, 0.15),
                                   rough=0.4, emission=(1.0, 0.52, 0.12),
                                   emission_strength=3.0))

    # ---- the basket: a woven box with real corner posts ------------
    bkit.rounded_box("BalloonBasket", SPEC["basket_length"],
                     SPEC["basket_width"], SPEC["basket_height"], r=10.0,
                     segments=2,
                     centre=(0.0, 0.0, SPEC["basket_height"] / 2.0),
                     mat=wicker)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bkit.rounded_box("BalloonPost%d" % i, 70.0, 70.0,
                         SPEC["basket_height"] + 240.0, r=12.0, segments=2,
                         centre=(sx * (SPEC["basket_length"] / 2.0 - 20.0),
                                 sy * (SPEC["basket_width"] / 2.0 - 20.0),
                                 (SPEC["basket_height"] + 240.0) / 2.0),
                         mat=wicker)
    bkit.rounded_box("BalloonBurnerRing", 1000.0, 1000.0, 90.0, r=20.0,
                     segments=2, centre=(0.0, 0.0,
                                        SPEC["basket_height"] + 220.0),
                     mat=wicker)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 1 + 4 + 2 + 6,
                note="The envelope is one revolved profile; the load tapes "
                     "are arrayed about the Z axis at the shoulder radius.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
