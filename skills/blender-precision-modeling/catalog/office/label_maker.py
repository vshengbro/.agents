"""
label_maker -- handheld label printer, 150 x 70 x 55 mm.

The label that makes it read is the strip coming out of the front slot: a thin
solid with real thickness, at the slot's height, not a decal on the face. The
keypad is laid out with grid_positions so no two keys share a coordinate.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=150.0,
    depth=70.0,
    height=55.0,
    label_width=12.0,
    label_thickness=0.4,
    slot_width=70.0,
)

W = SPEC["width"]
D = SPEC["depth"]
H = SPEC["height"]


def build():
    shell = bkit.pbr("LabelMakerShell", base=(0.72, 0.16, 0.14), rough=0.32,
                     coat=0.25)
    dark = bkit.preset("black_plastic")
    label_paper = bkit.pbr("LabelStrip", base=(0.95, 0.95, 0.92), rough=0.55)
    button = bkit.pbr("LabelMakerButton", base=(0.05, 0.30, 0.60), rough=0.30)

    body = bkit.rounded_box("LabelMakerBody", W, D, H, r=6.0, segments=4,
                            centre=(0, 0, H / 2.0), mat=shell)

    # ---- label exit slot on the front face --------------------------------
    slot = bkit.rounded_box("LabelMakerSlot", SPEC["slot_width"], 8.0, 6.0,
                            r=1.0, centre=(10.0, -D / 2.0 + 1.0, 9.0),
                            mat=dark)
    cutter = bkit.rounded_box("slot_cut", SPEC["slot_width"] + 4.0, 8.0, 3.4,
                              r=0.8, centre=(10.0, -D / 2.0 + 2.0, 9.0),
                              mat=None)
    bkit.boolean(body, cutter, "DIFFERENCE")

    # ---- the label itself, emerging from the slot -------------------------
    label = bkit.rounded_box("LabelMakerLabel", SPEC["label_width"], 26.0,
                             SPEC["label_thickness"], r=0.2,
                             centre=(10.0, -D / 2.0 - 12.0, 9.0),
                             mat=label_paper)

    # ---- keypad: 3 x 4, computed pitch ------------------------------------
    keys = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=4, rows=3,
                                                    pitch_x=15.0, pitch_y=13.0)):
        keys.append(bkit.rounded_box(
            "key%d" % i, 11.0, 9.0, 3.0, r=1.2,
            centre=(-20.0 + x, -4.0 + y, H + 0.5), mat=button))
    keypad = bkit.join(keys, name="LabelMakerKeys")

    # ---- display strip ----------------------------------------------------
    display = bkit.rounded_box("LabelMakerDisplay", 44.0, 16.0, 2.5, r=1.0,
                               centre=(42.0, 8.0, H + 0.4), mat=dark)
    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="width", mm=150.0, tol=0.6, how="bbox_x", part="LabelMakerBody"),
    dict(name="depth", mm=70.0, tol=0.6, how="bbox_y", part="LabelMakerBody"),
    dict(name="body_height", mm=55.0, tol=0.6, how="bbox_z",
         part="LabelMakerBody"),
    dict(name="label_thickness", mm=0.4, tol=0.3, how="bbox_z",
         part="LabelMakerLabel"),
]