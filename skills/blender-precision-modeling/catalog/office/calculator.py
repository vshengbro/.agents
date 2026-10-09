"""
calculator -- desktop calculator, 155 x 78 x 12 mm.

Flat slab, which is right: this is the office item where the silhouette is
least informative and the surface detail does all the work. 5 rows x 4 columns
of keys laid out on one computed pitch, plus a recessed display window.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=155.0,
    depth=78.0,
    height=12.0,
    key_size=11.0,
    key_height=2.2,
    rows=5,
    cols=4,
)

W = SPEC["width"]
D = SPEC["depth"]
H = SPEC["height"]


def build():
    shell = bkit.pbr("CalcShell", base=(0.30, 0.32, 0.36), rough=0.34,
                     coat=0.25)
    key_mat = bkit.pbr("CalcKeys", base=(0.90, 0.90, 0.88), rough=0.42)
    op_mat = bkit.pbr("CalcOpKeys", base=(0.90, 0.45, 0.12), rough=0.40)
    screen = bkit.pbr("CalcScreen", base=(0.58, 0.72, 0.58), rough=0.12,
                      coat=0.6)

    body = bkit.rounded_box("CalculatorBody", W, D, H, r=4.0, segments=4,
                            centre=(0, 0, H / 2.0), mat=shell)

    # ---- display window: a real recess with the LCD sitting in it ---------
    well = bkit.rounded_box("disp_cut", 58.0, 22.0, 6.0, r=1.5,
                            centre=(0, 24.0, H - 1.0), mat=None)
    bkit.boolean(body, well, "DIFFERENCE")
    display = bkit.rounded_box("CalculatorDisplay", 56.0, 20.0, 2.0, r=1.0,
                               centre=(0, 24.0, H - 2.0), mat=screen)

    # ---- keypad: one computed pitch, no hand-placed coordinates ----------
    pitch_x = 15.0
    pitch_y = 11.5
    keys = []
    for i, (x, y) in enumerate(bkit.grid_positions(
            cols=SPEC["cols"], rows=SPEC["rows"],
            pitch_x=pitch_x, pitch_y=pitch_y)):
        mat = op_mat if i >= SPEC["cols"] * (SPEC["rows"] - 1) else key_mat
        keys.append(bkit.rounded_box(
            "k%d" % i, SPEC["key_size"], 8.0, SPEC["key_height"], r=1.4,
            centre=(x, -30.0 + y, H + SPEC["key_height"] / 2.0 - 0.4),
            mat=mat))
    keypad = bkit.join(keys, name="CalculatorKeys")
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="width", mm=155.0, tol=0.6, how="bbox_x", part="CalculatorBody"),
    dict(name="depth", mm=78.0, tol=0.6, how="bbox_y", part="CalculatorBody"),
    dict(name="height", mm=12.0, tol=0.6, how="bbox_z", part="CalculatorBody"),
    dict(name="key_height", mm=2.2, tol=0.5, how="bbox_z",
         part="CalculatorKeys"),
]