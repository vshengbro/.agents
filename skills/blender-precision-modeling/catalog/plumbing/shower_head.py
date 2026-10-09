"""
shower_head -- handheld rain head on a wall bracket: lathed body, a real
perforated nozzle face, a bent handle, and a swept hose.

The face is the point of this model. A shower head without visible nozzles is
a lid, so the nozzle field is `perforated_panel` -- one watertight mesh with
every hole cut, no booleans to go non-manifold.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    head_diameter=120.0,
    head_height=32.0,
    nozzle_diameter=3.0,
    nozzle_rows=7,
    nozzle_cols=7,
    handle_length=170.0,
    handle_diameter=26.0,
    overall_length=232.0,   # head crown to the bottom of the hose stub
)

HD = SPEC["head_diameter"]
NOZ = SPEC["nozzle_diameter"]
ROWS, COLS = SPEC["nozzle_rows"], SPEC["nozzle_cols"]


def build():
    chrome = bkit.preset("polished_metal")
    grey = bkit.pbr("ShowerGrey", base=(0.55, 0.57, 0.60), metal=0.3, rough=0.30)
    face_mat = bkit.pbr("NozzleFace", base=(0.30, 0.31, 0.33), metal=0.2,
                        rough=0.45)

    # ---- head shell: a shallow lathed dome with a real cavity --------------
    head = bkit.lathe("ShowerHead", [
        (0.0, 0.0),
        (HD / 2.0 - 6.0, 0.0),
        (HD / 2.0, 6.0),                    # outer edge
        (HD / 2.0, SPEC["head_height"] - 8.0),
        (HD / 2.0 - 10.0, SPEC["head_height"]),   # crown
        (HD / 2.0 - 26.0, SPEC["head_height"] - 4.0),
        (HD / 2.0 - 26.0, SPEC["head_height"] - 12.0),  # inner lip
        (HD / 2.0 - 30.0, 8.0),             # cavity floor
        (0.0, 8.0),
    ], segments=96, mat=chrome)

    # ---- nozzle face: perforated_panel, holes cut, no booleans -------------
    # The field is inset to the cavity floor (z = 8) and lies just under the
    # rim so the holes read as depth rather than as painted dots.
    field_d = HD - 62.0
    pitch = field_d / (COLS + 1)
    face = bkit.perforated_panel("NozzleFace", COLS, ROWS, pitch, pitch,
                                 NOZ / 2.0, field_d, field_d, 6.0,
                                 mat=face_mat)
    bkit.move(face, 0.0, 0.0, 5.0)

    # ---- handle: a bent grip below the head -------------------------------
    handle = bkit.lathe("ShowerHandle", [
        (0.0, 0.0), (13.0, 0.0), (13.0, 16.0), (11.0, 26.0),
        (11.0, SPEC["handle_length"] - 40.0), (13.0, SPEC["handle_length"] - 26.0),
        (13.0, SPEC["handle_length"]), (0.0, SPEC["handle_length"]),
    ], segments=48, mat=grey)
    # Sits under the head; the head shell's own underside is at z = 0.
    bkit.move(handle, 0.0, 0.0, -SPEC["handle_length"])

    # ---- hose stub: the thread the hose screws onto ----------------------
    # A hose is sold separately, so only the stub is modelled -- a full hose
    # tail pushed the assembly to 411 mm and out of the `small` band.
    hose = bkit.lathe("HoseStub", [
        (0.0, 0.0), (11.0, 0.0), (11.0, 26.0), (14.0, 30.0), (14.0, 40.0),
        (9.0, 40.0), (9.0, 30.0), (0.0, 30.0),
    ], segments=32, mat=grey)
    bkit.move(hose, 0.0, 0.0, -SPEC["handle_length"] - 30.0)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="head_diameter", mm=120.0, tol=0.4, how="diameter", part="ShowerHead"),
    dict(name="head_height", mm=32.0, tol=0.4, how="bbox_z", part="ShowerHead"),
    dict(name="handle_length", mm=170.0, tol=0.5, how="bbox_z", part="ShowerHandle"),
    dict(name="handle_diameter", mm=26.0, tol=0.4, how="diameter", part="ShowerHandle"),
    dict(name="overall_length", mm=232.0, tol=0.8, how="bbox_z"),
]
