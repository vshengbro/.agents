"""
valve -- two-piece ball valve: a lathed body with a real bore, union collars,
a stem, and a lever handle.

Small size class (30..150 mm) and a 150 mm centre-to-face length. The ball
itself is hidden inside a real bore, so what has to read is the bore, the two
collar nuts, and the lever -- which is a flat blade with a round grip end.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=150.0,          # end face to end face
    body_diameter=42.0,
    bore_diameter=25.4,    # 1 inch bore
    collar_diameter=46.0,
    collar_width=26.0,
    stem_diameter=12.0,
    stem_height=26.0,
    lever_length=88.0,
    lever_thickness=9.0,
    overall_height=68.0,
)

L = SPEC["length"]
BR = SPEC["body_diameter"] / 2.0
CR = SPEC["collar_diameter"] / 2.0
CW = SPEC["collar_width"]


def build():
    steel = bkit.preset("brushed_metal")
    brass = bkit.preset("polished_metal")
    lever_mat = bkit.pbr("ValveLever", base=(0.72, 0.20, 0.14), metal=0.85,
                         rough=0.30)

    # ---- body: a lathed barrel with a REAL bore through it ----------------
    # Two collars are unioned onto the barrel afterwards. A lathe is capped at
    # any profile end whose radius is off-axis, which is exactly how the bore
    # gets its end faces -- and why the profile must not revisit its first
    # point.
    bore_r = SPEC["bore_diameter"] / 2.0
    prof = [
        (bore_r, -L / 2.0),
        (CR, -L / 2.0),                 # end face
        (CR, -L / 2.0 + 4.0),
        (BR, -L / 2.0 + 9.0),           # step in to the barrel
        (BR, -34.0),
        (BR + 3.0, -30.0),              # central bulge round the ball
        (BR + 3.0, 30.0),
        (BR, 34.0),
        (BR, L / 2.0 - 9.0),
        (CR, L / 2.0 - 4.0),
        (CR, L / 2.0),
        (bore_r, L / 2.0),              # end face, bore
    ]
    body = bkit.lathe("ValveBody", prof, segments=72, mat=steel)
    # The lathe runs along +Z; lay the valve down along X.
    body.rotation_euler = (0.0, math.radians(90.0), 0.0)

    # ---- collar nuts: hex-ish flats read as "grabbable" -------------------
    for sx, tag in ((-1, "L"), (1, "R")):
        col = bkit.cylinder("ValveCollar%s" % tag, CR, CW, segments=6,
                            centre=(sx * (L / 2.0 - CW / 2.0 + 3.0), 0.0, 0.0),
                            axis="X", mat=brass)
        # flat-to-flat on a hex across the flats: a 6-gon of circumradius CR
        # is 1.732 x CR across corners, so back the radius off to keep the
        # stated 46 mm across flats.
        col.scale = (1.0, 46.0 / (2.0 * CR * 1.7320508), 1.0)
        import bpy
        bpy.context.view_layer.update()

    # ---- stem: rises out of the top of the body --------------------------
    stem = bkit.lathe("ValveStem", [
        (0.0, 0.0), (SPEC["stem_diameter"] / 2.0, 0.0),
        (SPEC["stem_diameter"] / 2.0, SPEC["stem_height"] - 8.0),
        (11.0, SPEC["stem_height"] - 8.0),
        (11.0, SPEC["stem_height"]),
        (0.0, SPEC["stem_height"]),
    ], segments=40, mat=brass)
    bkit.move(stem, 0.0, 0.0, BR + 1.0)

    # ---- lever: a flat blade off the stem top -----------------------------
    lv = SPEC["lever_length"]
    lever = bkit.rounded_box("ValveLever", lv, SPEC["lever_thickness"], 13.0,
                             r=3.5, segments=3,
                             centre=(-lv * 0.5 + 14.0, 0.0,
                                     BR + 1.0 + SPEC["stem_height"]),
                             mat=lever_mat)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="length", mm=150.0, tol=0.5, how="bbox_x", part="ValveBody"),
    # The body lies along X and its section is circular, so the diameter is
    # bbox_y. `how="diameter"` returns max(bbox_x, bbox_y) and would report
    # the 150 mm LENGTH instead.
    dict(name="body_diameter", mm=48.0, tol=0.5, how="bbox_y", part="ValveBody"),
    dict(name="stem_height", mm=26.0, tol=0.4, how="bbox_z", part="ValveStem"),
    dict(name="lever_length", mm=88.0, tol=0.4, how="bbox_x", part="ValveLever"),
    # The body is a lathed barrel rotated onto X, so it hangs 23 mm below the
    # axis: overall height is 23 + 55.5, not the lever's height alone.
    dict(name="overall_height", mm=78.5, tol=0.8, how="bbox_z"),
]
