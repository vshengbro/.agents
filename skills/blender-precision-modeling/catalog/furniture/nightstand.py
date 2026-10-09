"""
nightstand -- 450 x 400 mm two-drawer bedside cabinet, 550 mm high.

A nightstand sits beside a 500 mm bed, so it has to be roughly bed height:
450 mm of carcass under a 30 mm top puts the drawer pulls at 205 and 415 mm,
both within reach from a seated position. The two drawer fronts are laid out
with bkit.lay_out from their real 190 mm height plus a 20 mm reveal, which is
what keeps the gap between them even instead of eyeballed.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=450.0,
    depth=400.0,
    height=550.0,
    top_thickness=30.0,
    body_height=420.0,
    leg_section=50.0,
    leg_height=100.0,
    drawer_count=2,
    drawer_front_width=390.0,
    drawer_front_height=190.0,
    drawer_gap=20.0,
    drawer_front_thickness=20.0,
    knob_diameter=32.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
TOP_T = SPEC["top_thickness"]
BODY_H = SPEC["body_height"]
LEG = SPEC["leg_section"]
LEG_H = SPEC["leg_height"]
# body spans LEG_H..LEG_H+BODY_H = 100..520, top sits on top of that
BODY_Z0 = LEG_H
BODY_CZ = BODY_Z0 + BODY_H / 2.0
TOP_CZ = BODY_Z0 + BODY_H + TOP_T / 2.0
DF_W = SPEC["drawer_front_width"]
DF_H = SPEC["drawer_front_height"]
DF_T = SPEC["drawer_front_thickness"]
DF_Y = -D / 2.0 - DF_T / 2.0          # front panel flush with the carcass face
FRONT_Z = (BODY_Z0 + BODY_Z0 + BODY_H) / 2.0

CHECKS = [
    dict(name="overall_width", mm=450.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=550.0, tol=0.3, how="bbox_z"),
    dict(name="top_thickness", mm=30.0, tol=0.3, how="bbox_z", part="TableTop"),
    dict(name="drawer_front_width", mm=390.0, tol=0.3, how="bbox_x",
         part="DrawerFrontUpper"),
    dict(name="drawer_front_height", mm=190.0, tol=0.3, how="bbox_z",
         part="DrawerFrontUpper"),
    dict(name="leg_section", mm=50.0, tol=0.3, how="bbox_x", part="LegFrontLeft"),
]


def build():
    wood = bkit.pbr("NightstandWalnut", base=(0.34, 0.21, 0.11), metal=0.0,
                    rough=0.38)
    wood_dark = bkit.pbr("NightstandLeg", base=(0.26, 0.16, 0.08), metal=0.0,
                         rough=0.45)
    brass = bkit.preset("gold")

    bkit.rounded_box("TableTop", W, D, TOP_T, r=6.0, segments=3,
                     centre=(0, 0, TOP_CZ), mat=wood)
    bkit.rounded_box("Body", W, D, BODY_H, r=6.0, segments=3,
                     centre=(0, 0, BODY_CZ), mat=wood)

    leg_x = W / 2.0 - 35.0
    leg_y = D / 2.0 - 30.0
    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            bkit.rounded_box("Leg%s%s" % (yn, xn), LEG, LEG, LEG_H, r=4.0,
                             segments=2,
                             centre=(sx * leg_x, sy * leg_y, LEG_H / 2.0),
                             mat=wood_dark)

    # ---- drawer fronts: real height + real reveal, computed ----------------
    rows = bkit.lay_out([DF_H] * SPEC["drawer_count"],
                        gap=SPEC["drawer_gap"])
    for i, (dz, _w) in enumerate(rows):
        tag = "Lower" if i == 0 else "Upper"
        cz = FRONT_Z + dz
        bkit.rounded_box("DrawerFront%s" % tag, DF_W, DF_T, DF_H, r=4.0,
                         segments=3, centre=(0, DF_Y, cz), mat=wood)
        bkit.cylinder("Knob%s" % tag, SPEC["knob_diameter"] / 2.0, 30,
                      segments=32, centre=(0, DF_Y - DF_T / 2.0 - 15.0, cz),
                      axis="Y", mat=brass)

    return dict(spec=SPEC, parts=9)
