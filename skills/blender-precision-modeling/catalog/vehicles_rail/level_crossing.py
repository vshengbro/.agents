"""
level_crossing -- automatic half-barrier crossing with two boom arms raised.

Geometry of a level crossing, which is the thing that is easy to get wrong:
the ROAD runs across the TRACK, and the barriers are set back ALONG the track
on each side of the road, not out beside the rails. The arms therefore lie
across the road -- parallel to the track when lowered -- and swing UP about a
horizontal pivot on top of their post.

So: track along X at y = +/-752.5, road along Y, posts at x = +/-2,100 with
the arms pivoting at 1,180 mm over rail and standing up at 72 degrees. Each
boom is built along +X and rotated about Y, and the RIGHT one also gets a 180
degree spin about Z: rotate both the same way about Y and the right-hand boom
swings DOWN into the ballast, which then drags the whole assembly up when
`sit_on_floor()` seats it on the phantom.

Every part sits at or above z=0 -- timbers on the ground, deck flush with the
railhead at 372 -- so the seat offset is zero and the top_z checks read
straight off the model.

Each boom is alternating red and white segments joined into ONE arm, which is
the single most recognisable crossing cue there is.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bpy
import bkit
import _rail as R

SPEC = dict(
    road_deck_length=5600.0,      # across the road, i.e. along the track
    road_deck_width=5200.0,       # along the road
    post_spacing=4000.0,
    pivot_height_above_rail=1180.0,
    boom_length=2200.0,
    boom_angle_deg=72.0,
    boom_tip_z=3310.0,
    rail_height=172.0,
    rail_crown_z=372.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="road_deck_length", mm=5600.0, tol=4.0, how="bbox_x",
         part="CrossDeck"),
    dict(name="road_deck_width", mm=5200.0, tol=4.0, how="bbox_y",
         part="CrossDeck"),
    dict(name="rail_length", mm=5600.0, tol=4.0, how="bbox_x",
         part="CrossRailL"),
    dict(name="rail_crown_z", mm=372.0, tol=3.0, how="top_z", part="CrossRailL"),
    dict(name="post_height", mm=1208.0, tol=4.0, how="top_z",
         part="CrossPostL"),
    dict(name="boom_tip_z", mm=3310.0, tol=4.0, how="top_z",
         part="CrossBoomL"),
    dict(name="cabinet_height", mm=1100.0, tol=4.0, how="bbox_z",
         part="CrossCabinet"),
]

DECK_X = 5600.0
DECK_Y = 5200.0
DECK_T = 112.0
DECK_TOP = 372.0                    # flush with the railhead
TIMBER_H = 200.0
RAIL_Z0 = TIMBER_H
RAIL_H = 172.0
POST_X = 2000.0
PIVOT_Z = R.above_rail(1180.0)
BOOM_L = 2200.0
BOOM_RAISE = 72.0


def _boom(name, sign, red, white, steel):
    """One boom arm: alternating segments, built along +X then swung up.

    Built at the pivot so the rotation is about the pivot itself; rotating a
    boom that has already been moved out to its post swings it round the world
    origin instead and lands it metres away.
    """
    segs = []
    n = 6
    seg = BOOM_L / n
    for i in range(n):
        segs.append(bkit.rounded_box("%s_Seg%d" % (name, i), seg - 16.0, 110.0,
                                     150.0, r=18.0, segments=2,
                                     centre=(seg * (i + 0.5), 0.0, 0.0),
                                     mat=red if i % 2 == 0 else white))
    segs.append(bkit.rounded_box(name + "_Skirt", BOOM_L - 60.0, 40.0, 240.0,
                                 r=15.0, segments=2,
                                 centre=(BOOM_L / 2.0, 0.0, -160.0),
                                 mat=steel))
    ob = bkit.join(segs, name)
    bkit.recalc(ob)
    R.freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    # Ry(-raise) sends local +X up and +X. The right-hand boom also needs a
    # half turn about Z so its length runs toward -X instead of back across
    # the left-hand post.
    ob.rotation_euler = (0.0, math.radians(-BOOM_RAISE),
                         0.0 if sign > 0 else math.pi)
    bpy.context.view_layer.update()
    bkit.move(ob, sign * POST_X, 0.0, PIVOT_Z)
    return ob


def build():
    asphalt = bkit.pbr("CrossAsphalt", base=(0.15, 0.15, 0.16), rough=0.86)
    concrete = bkit.pbr("CrossConcrete", base=(0.55, 0.54, 0.51), rough=0.80)
    steel = bkit.preset("dark_metal")
    red = bkit.preset("red_paint")
    white = bkit.preset("white_plastic")
    yellow = bkit.preset("yellow_paint")

    # --- timbered formation and the road deck ------------------------------
    R.sleeper_row("CrossTimbers", 7, 700.0, 2600.0, sx=240.0, sz=TIMBER_H,
                  z0=0.0, mat=concrete)
    deck = bkit.rounded_box("CrossDeck", DECK_X, DECK_Y, DECK_T, r=25.0,
                            segments=2,
                            centre=(0.0, 0.0, DECK_TOP - DECK_T / 2.0),
                            mat=asphalt)
    for i, x in enumerate(R.evenly(9, 4200.0)):
        bkit.rounded_box("CrossRoadMark%d" % i, 260.0, 1400.0, 8.0, r=4.0,
                         segments=1, centre=(x, 0.0, DECK_TOP + 3.0),
                         mat=white)

    # --- the railway itself, kerbed through the deck -----------------------
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        R.rail("CrossRail" + tag, DECK_X, y=s * R.RAIL_Y, z0=RAIL_Z0,
               h=RAIL_H, mat=steel)
        bkit.rounded_box("CrossKerb" + tag, DECK_X, 300.0, 90.0, r=20.0,
                         segments=2,
                         centre=(0.0, s * (R.RAIL_Y + 160.0),
                                 DECK_TOP + 45.0), mat=concrete)

    # --- posts, pivots and warning lamps ------------------------------------
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        bkit.rounded_box("CrossPost" + tag, 420.0, 420.0, PIVOT_Z, r=70.0,
                         segments=3, centre=(s * POST_X, 0.0, PIVOT_Z / 2.0),
                         mat=yellow)
        bkit.rounded_box("CrossPivot" + tag, 560.0, 300.0, 320.0, r=80.0,
                         segments=3,
                         centre=(s * POST_X, 0.0, PIVOT_Z + 60.0), mat=steel)
        bkit.cylinder("CrossLamp" + tag, 150.0, 260.0, segments=20, axis="X",
                      centre=(s * (POST_X - 300.0), 0.0, PIVOT_Z + 330.0),
                      mat=bkit.pbr("CrossLampMat", base=(0.45, 0.03, 0.03),
                                   rough=0.25,
                                   emission=(1.0, 0.12, 0.06),
                                   emission_strength=1.2))
    _boom("CrossBoomL", 1.0, red, white, steel)
    _boom("CrossBoomR", -1.0, red, white, steel)

    # --- equipment cabinet and the drive rod -------------------------------
    bkit.rounded_box("CrossCabinet", 520.0, 380.0, 1100.0, r=50.0, segments=3,
                     centre=(-POST_X + 1000.0, 1600.0, DECK_TOP + 550.0),
                     mat=yellow)
    bkit.rounded_box("CrossCabinetPlinth", 640.0, 500.0, 220.0, r=30.0,
                     segments=2,
                     centre=(-POST_X + 1000.0, 1600.0, DECK_TOP + 110.0),
                     mat=concrete)
    R.strut("CrossDriveRod", (-POST_X, 0.0, PIVOT_Z - 260.0),
            (-POST_X + 1000.0, 1600.0, DECK_TOP + 260.0), 60.0, steel, seg=12)

    return dict(spec=SPEC, parts=14)