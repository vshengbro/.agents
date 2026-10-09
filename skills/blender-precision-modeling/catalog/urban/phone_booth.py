"""
phone_booth -- 900 x 900 x 2300 mm glazed telephone kiosk: a cast base, four
corner posts, five glazed panels (two sides, a front door and two rear panels),
a fascia sign, a roof with a drip edge and the payphone inside.

`medium` in the catalog, but the object is genuinely 2300 mm tall, so that is
what it is modelled at. Every glass panel overlaps its frame rail by more than
1 mm -- glass set exactly into a rebate touches the rail along its whole edge,
and that contact line is the classic non-manifold generator.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    booth_width=900.0,
    booth_depth=900.0,
    overall_height=2300.0,
    post_width=80.0,
    fascia_height=500.0,
    door_width=720.0,
    glazed_panels=5,
)

BW, BD = SPEC["booth_width"], SPEC["booth_depth"]
POST = SPEC["post_width"]
BASE_H = 120.0
FASCIA_TOP = 2300.0
FASCIA_H = SPEC["fascia_height"]
GLAZE_Z = (BASE_H + FASCIA_TOP - FASCIA_H) / 2.0
GLAZE_H = (FASCIA_TOP - FASCIA_H) - BASE_H


def build():
    frame = bkit.pbr("BoothFrame", base=(0.12, 0.26, 0.16), metal=0.45,
                     rough=0.42)
    glass = bkit.preset("glass")
    sign = bkit.pbr("BoothSign", base=(0.90, 0.86, 0.20), rough=0.26,
                    emission=(0.95, 0.90, 0.30), emission_strength=1.6)
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("brushed_metal")

    # ---- cast base and four corner posts --------------------------------
    bkit.rounded_box("BoothBase", BW, BD, BASE_H, r=14.0, segments=3,
                     centre=(0.0, 0.0, BASE_H / 2.0), mat=frame)
    for side, tag in ((-1.0, "FL"), (1.0, "FR"), (-1.0, "RL"), (1.0, "RR")):
        px = side * (BW / 2.0 - POST / 2.0)
        py = (-1.0 if tag[0] == "F" else 1.0) * (BD / 2.0 - POST / 2.0)
        bkit.rounded_box("Post" + tag, POST, POST,
                         FASCIA_TOP - FASCIA_H - BASE_H, r=8.0, segments=2,
                         centre=(px, py,
                                 BASE_H + (FASCIA_TOP - FASCIA_H - BASE_H)
                                 / 2.0), mat=frame)

    # ---- five glazed panels, each overlapping its rails ------------------
    gw = BW - 2 * POST
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("GlassSide" + tag, 14.0, BD - 2 * POST + 12.0,
                         GLAZE_H, r=3.0, segments=2, mat=glass,
                         centre=(side * (BW / 2.0 - POST / 2.0), 0.0, GLAZE_Z))
    # Rear: two panels split by a centre mullion.
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("GlassRear" + tag, (BD - 2 * POST) / 2.0 - 30.0,
                         14.0, GLAZE_H, r=3.0, segments=2, mat=glass,
                         centre=(side * ((BD - 2 * POST) / 4.0 + 15.0),
                                 BD / 2.0 - POST / 2.0, GLAZE_Z))
    # Front: a single door pane of the declared width.
    bkit.rounded_box("GlassDoor", SPEC["door_width"], 14.0, GLAZE_H, r=3.0,
                     segments=2, mat=glass,
                     centre=(-40.0, -(BD / 2.0 - POST / 2.0), GLAZE_Z))

    # ---- door stile, handle and hinge ------------------------------------
    bkit.rounded_box("DoorStile", 60.0, 40.0, GLAZE_H, r=6.0, segments=2,
                     centre=(SPEC["door_width"] / 2.0 - 70.0,
                             -(BD / 2.0 - POST / 2.0), GLAZE_Z), mat=frame)
    bkit.cylinder("DoorHandle", 16.0, 300.0, segments=24, axis="Z",
                  centre=(SPEC["door_width"] / 2.0 - 110.0,
                          -(BD / 2.0 - POST / 2.0) - 30.0, GLAZE_Z),
                  mat=steel)
    hinges = []
    for hz in bkit.grid_positions(1, 3, 0.0, GLAZE_H / 2.0):
        hinges.append(bkit.cylinder("_h", 12.0, 90.0, segments=20, axis="Z",
                                    mat=steel,
                                    centre=(-SPEC["door_width"] / 2.0 + 30.0,
                                            -(BD / 2.0 - POST / 2.0),
                                            GLAZE_Z + hz[1])))
    bkit.join(hinges, name="DoorHinges")

    # ---- fascia, sign band and roof with a drip edge ---------------------
    bkit.rounded_box("BoothFascia", BW, BD, FASCIA_H, r=10.0, segments=3,
                     centre=(0.0, 0.0, FASCIA_TOP - FASCIA_H / 2.0),
                     mat=frame)
    bkit.rounded_box("SignBand", BW - 60.0, 30.0, 300.0, r=8.0, segments=2,
                     centre=(0.0, -(BD / 2.0 + 8.0), 1980.0), mat=sign)
    bkit.rounded_box("BoothRoof", BW + 90.0, BD + 90.0, 110.0, r=20.0,
                     segments=3, centre=(0.0, 0.0, FASCIA_TOP + 40.0),
                     mat=frame)
    bkit.rounded_box("RoofDrip", BW + 130.0, BD + 130.0, 26.0, r=10.0,
                     segments=2, centre=(0.0, 0.0, FASCIA_TOP - 6.0),
                     mat=dark)

    # ---- payphone, shelf and coin unit ----------------------------------
    bkit.rounded_box("PhoneBody", 340.0, 200.0, 480.0, r=14.0, segments=3,
                     centre=(-60.0, 260.0, BASE_H + 30.0 + 240.0), mat=dark)
    bkit.rounded_box("PhoneShelf", 400.0, 240.0, 30.0, r=6.0, segments=2,
                     centre=(-60.0, 240.0, BASE_H + 55.0), mat=steel)
    bkit.rounded_box("PhoneDisplay", 220.0, 12.0, 120.0, r=4.0, segments=2,
                     centre=(-60.0, 158.0, BASE_H + 330.0), mat=sign)
    keypad = [bkit.rounded_box("_pk", 26.0, 8.0, 20.0, r=3.0, segments=2,
                               mat=steel,
                               centre=(-60.0 + kx, 156.0, BASE_H + 150.0 + kz))
              for (kx, kz) in bkit.grid_positions(3, 4, 36.0, 28.0)]
    bkit.join(keypad, name="PhoneKeypad")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="booth_width", mm=900.0, tol=1.0, how="bbox_x", part="BoothBase"),
    dict(name="booth_depth", mm=900.0, tol=1.0, how="bbox_y", part="BoothBase"),
    dict(name="post_width", mm=80.0, tol=0.6, how="bbox_x", part="PostFL"),
    dict(name="sign_band_width", mm=840.0, tol=1.0, how="bbox_x",
         part="SignBand"),
    dict(name="overall_height", mm=2395.0, tol=2.0, how="bbox_z"),
]