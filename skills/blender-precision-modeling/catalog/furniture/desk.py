"""
desk -- 1400 x 700 mm writing desk with two drawer pedestals, 750 mm high.

A pedestal desk is two 400 mm masses with a 600 mm knee hole between them, so
the widths are not a style choice -- 400 + 600 + 400 is the 1400 mm top, and
the six drawer fronts are three 190 mm rows in each pedestal. Both banks are
laid out with bkit.lay_out from their real 190 mm height and a 20 mm reveal,
which is what keeps the pedestal drawers level with each other.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=1400.0,
    depth=700.0,
    height=750.0,
    top_thickness=35.0,
    pedestal_width=400.0,
    pedestal_depth=680.0,
    pedestal_height=655.0,
    plinth_height=60.0,
    knee_hole_width=600.0,
    drawer_count=3,           # per pedestal
    drawer_front_width=360.0,
    drawer_front_height=190.0,
    drawer_front_thickness=20.0,
    drawer_gap=20.0,
    modesty_panel_height=400.0,
    handle_length=140.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
TOP_T = SPEC["top_thickness"]
TOP_Z0 = H - TOP_T                            # 715
PED_W, PED_D, PED_H = (SPEC["pedestal_width"], SPEC["pedestal_depth"],
                       SPEC["pedestal_height"])
PLINTH_H = SPEC["plinth_height"]
PED_Z0 = PLINTH_H                             # 60
PED_CZ = PED_Z0 + PED_H / 2.0                 # 387.5
# Pedestal centre x: half the 600 mm knee hole plus half a 400 mm pedestal puts
# the inner face at the knee-hole edge; the 10 mm is the top's side overhang.
PED_CX = W / 2.0 - 10.0 - PED_W / 2.0         # 490
DF_W = SPEC["drawer_front_width"]
DF_H = SPEC["drawer_front_height"]
DF_T = SPEC["drawer_front_thickness"]
DF_Y = -PED_D / 2.0 - DF_T / 2.0              # -350

CHECKS = [
    dict(name="overall_width", mm=1400.0, tol=0.4, how="bbox_x"),
    dict(name="overall_height", mm=750.0, tol=0.3, how="bbox_z"),
    dict(name="top_thickness", mm=35.0, tol=0.3, how="bbox_z", part="DeskTop"),
    dict(name="pedestal_width", mm=400.0, tol=0.3, how="bbox_x",
         part="PedestalLeft"),
    dict(name="pedestal_height", mm=655.0, tol=0.3, how="bbox_z",
         part="PedestalLeft"),
    dict(name="drawer_front_width", mm=360.0, tol=0.3, how="bbox_x",
         part="DrawerFrontLeft0"),
    dict(name="drawer_front_height", mm=190.0, tol=0.3, how="bbox_z",
         part="DrawerFrontLeft0"),
]


def build():
    wood = bkit.pbr("DeskOak", base=(0.50, 0.33, 0.17), metal=0.0, rough=0.36)
    wood_dk = bkit.pbr("DeskPlinth", base=(0.33, 0.20, 0.10), metal=0.0,
                       rough=0.45)
    brass = bkit.preset("gold")

    bkit.rounded_box("DeskTop", W, D, TOP_T, r=8.0, segments=4,
                     centre=(0, 0, TOP_Z0 + TOP_T / 2.0), mat=wood)

    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Pedestal%s" % tag, PED_W, PED_D, PED_H, r=5.0,
                         segments=3, centre=(sx * PED_CX, 0, PED_CZ), mat=wood)
        bkit.rounded_box("Plinth%s" % tag, PED_W - 40.0, PED_D - 60.0, PLINTH_H,
                         r=3.0, segments=2,
                         centre=(sx * PED_CX, 0, PLINTH_H / 2.0), mat=wood_dk)

        # ---- drawer bank, identical in both pedestals --------------------
        for i, (dz, _w) in enumerate(
                bkit.lay_out([DF_H] * SPEC["drawer_count"], gap=SPEC["drawer_gap"])):
            cz = PED_CZ + dz
            name = "%s%d" % (tag, i)
            bkit.rounded_box("DrawerFront%s" % name, DF_W, DF_T, DF_H, r=4.0,
                             segments=3, centre=(sx * PED_CX, DF_Y, cz), mat=wood)
            bkit.cylinder("Handle%s" % name, 8.0, SPEC["handle_length"],
                          segments=24,
                          centre=(sx * PED_CX, DF_Y - DF_T / 2.0 - 14.0, cz),
                          axis="X", mat=brass)

    bkit.rounded_box("ModestyPanel", SPEC["knee_hole_width"] - 20.0, 25.0,
                     SPEC["modesty_panel_height"], r=4.0, segments=2,
                     centre=(0, PED_D / 2.0 - 15.0, TOP_Z0 - SPEC["modesty_panel_height"] / 2.0),
                     mat=wood_dk)

    return dict(spec=SPEC, parts=17)
