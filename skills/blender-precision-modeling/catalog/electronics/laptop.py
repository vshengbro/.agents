"""
laptop -- 13" notebook, 312 x 221 x 16 mm closed, modelled open at 105 degrees.

The lid is the whole problem. A laptop shell is a rounded-rectangle section of
a thickness far smaller than its corner radius, which a clamped uniform bevel
cannot express, so both halves are `extrude_profile` of a
`rounded_rect_section`. The lid is then built with its hinge edge at its own
mesh origin, rotated 105 degrees about X, and only then moved onto the hinge
axis -- rotating after the move would swing it about the world origin.

The keyboard is a 61-key main block plus 13 function keys, all 15 u wide and
all laid out from one pitch, so the key field is computed rather than typed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=312.0,
    depth=221.0,
    closed_thickness=16.0,
    base_thickness=9.0,
    lid_thickness=7.0,
    keys=74,
    pitch=19.05,
    cap_gap=1.4,
    open_deg=105.0,
)

L, D = SPEC["width"], SPEC["depth"]
BASE_T, LID_T = SPEC["base_thickness"], SPEC["lid_thickness"]
PITCH, GAP = SPEC["pitch"], SPEC["cap_gap"]
# The hinge belongs at the BACK of the deck, next to the keyboard's top row
# (function row at y = +80), i.e. +Y -- not at the user's edge (-Y), where the
# trackpad is. With the hinge at -Y the lid stood up out of the front of the
# machine and cut straight through the keyboard well.
HINGE_Y = D / 2.0 - 4.0
KEY_W = 275.0                       # the real key field of a 13" notebook
X0 = -KEY_W / 2.0


def build():
    # Anodised aluminium, not raw: metal=0.85 has no diffuse term to catch the
    # key light and the whole shell renders as a black slab.
    alu = bkit.pbr("LaptopAlu", base=(0.60, 0.61, 0.64), metal=0.45, rough=0.32)
    key = bkit.pbr("LaptopKey", base=(0.26, 0.26, 0.29), rough=0.38)
    glass = bkit.pbr("LaptopScreen", base=(0.030, 0.033, 0.042), rough=0.05,
                     coat=0.85)
    pad_mat = bkit.pbr("LaptopTrackpad", base=(0.42, 0.43, 0.46), rough=0.30,
                       coat=0.4)
    dark = bkit.pbr("LaptopDark", base=(0.10, 0.10, 0.12), rough=0.44)

    # ---- base ------------------------------------------------------------
    base = bkit.extrude_profile("LaptopBase",
                                bkit.rounded_rect_section(L, D, 14.0),
                                BASE_T, centre=(0, 0, BASE_T / 2.0),
                                mat=alu)
    bkit.bevel(base, 0.6, segments=2)

    # ---- keyboard well pressed into the base ------------------------------
    well = bkit.rounded_box("_well", KEY_W + 8.0, 116.0, 5.0, r=2.0,
                            segments=3, centre=(0, 28.0, BASE_T - 0.8))
    bkit.boolean(base, well, "DIFFERENCE")

    # ---- 61 main keys + 13 function keys, every row exactly 15 u --------
    keys = []
    rows = [([1.0] * 13 + [2.0]),                       # 1..= + Backspace
            ([1.5] + [1.0] * 12 + [1.5]),               # Tab + QWERTY + \
            ([1.75] + [1.0] * 11 + [2.25]),             # Caps + ASDF + Enter
            ([2.25] + [1.0] * 10 + [2.75]),             # Shift + ZXCV + Shift
            ([1.25, 1.25, 1.25, 5.5, 1.25, 1.25, 1.5, 1.75])]
    for r, widths_u in enumerate(rows):
        y = 66.0 - r * PITCH
        for (x, w) in bkit.lay_out([u * PITCH - GAP for u in widths_u],
                                   gap=GAP, centre=False):
            keys.append(bkit.rounded_box(
                "k%d_%d" % (r, len(keys)), w, w, 2.6, r=1.2, segments=2,
                centre=(X0 + x, y, BASE_T - 0.3), mat=key))
    # Function row: half-height keys sitting above the number row.
    for i, u in enumerate([0.0, 2.0, 3.0, 4.0, 5.0, 6.5, 7.5, 8.5, 9.5,
                           11.0, 12.0, 13.0, 14.0]):
        keys.append(bkit.rounded_box(
            "fk%d" % i, PITCH - GAP, 8.0, 2.6, r=1.0, segments=2,
            centre=(X0 + (u + 0.5) * PITCH, 80.0, BASE_T - 0.3), mat=key))
    bkit.join(keys, name="LaptopKeys")

    # ---- trackpad and hinge ---------------------------------------------
    bkit.rounded_box("LaptopTrackpad", 120.0, 78.0, 1.0, r=3.0, segments=3,
                     centre=(0, -62.0, BASE_T - 0.1), mat=pad_mat)
    bkit.cylinder("LaptopHinge", 6.0, 150.0, segments=32, axis="X",
                  centre=(0, HINGE_Y, BASE_T - 1.0), mat=dark)

    # ---- lid: hinge edge at its own mesh origin, then rotated ------------
    # The lid is built along -Y from its hinge edge (the hinge is at the back
    # of the deck, so "away from the user" is -Y) and then swung open about X.
    # open_deg is the angle between the deck and the lid, so the rotation that
    # opens it is (180 - open_deg) in the -Y sense: the lid tips up and back
    # over the hinge. Rotating by open_deg itself swung the lid down through the
    # keyboard well, which is what the render showed.
    lid_len = D - 8.0
    swing = 180.0 - SPEC["open_deg"]
    lid = bkit.extrude_profile("LaptopLid",
                               bkit.rounded_rect_section(L, lid_len, 14.0),
                               LID_T, centre=(0, -lid_len / 2.0, 0.0),
                               mat=alu)
    bkit.bevel(lid, 0.6, segments=2)
    # The screen sits on the lid's local -Z face, which is the one turned
    # toward the user once the lid has swung open.
    scr = bkit.extrude_profile(
        "LaptopScreen", bkit.rounded_rect_section(L - 18.0, lid_len - 26.0,
                                                  9.0),
        0.8, centre=(0, -lid_len / 2.0, -LID_T / 2.0 - 0.2), mat=glass)
    lid.rotation_euler = (math.radians(-swing), 0.0, 0.0)
    scr.rotation_euler = (math.radians(-swing), 0.0, 0.0)
    bkit.move(lid, 0, HINGE_Y, BASE_T - 1.0)
    bkit.move(scr, 0, HINGE_Y, BASE_T - 1.0)

    # ---- side ports, one computed row ------------------------------------
    ports = []
    for i, (y, w) in enumerate(bkit.lay_out([9.0, 5.0, 5.0], gap=9.0)):
        ports.append(bkit.rounded_box(
            "_p%d" % i, 3.0, w, 3.4, r=1.0, segments=2,
            centre=(L / 2.0 - 0.4, y + 30.0, 4.5), mat=dark))
    bkit.join(ports, name="LaptopPorts")

    return dict(spec=SPEC, parts=8, keys=len(keys))


CHECKS = [
    dict(name="width", mm=312.0, tol=0.8, how="bbox_x", part="LaptopBase"),
    dict(name="depth", mm=221.0, tol=0.8, how="bbox_y", part="LaptopBase"),
    dict(name="base_thickness", mm=9.0, tol=0.5, how="bbox_z",
         part="LaptopBase"),
    dict(name="overall_height", mm=207.2, tol=0.8, how="bbox_z"),
]
