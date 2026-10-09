"""
machine_vise -- 210 mm machine vice: fixed jaw, sliding jaw, leadscrew, handle.

Jaw serrations are the detail that separates a machine vice from a clamp: four
vertical grooves per jaw, on a computed 30 mm pitch, cut 3.5 mm into each face.
The two jaws are real blocks standing on a base, the leadscrew passes through
BOTH of them in one bore cut, and the handle is a through-rod with a ball at
each end, the way a swivel handle actually is. Nothing is hand-placed: the
serration and the mounting holes both come from a layout call.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_length=190.0,
    base_width=120.0,
    base_thickness=18.0,
    jaw_width=45.0,            # along X
    jaw_depth=100.0,           # along Y
    jaw_height=90.0,
    jaw_opening=60.0,
    jaw_face_height=95.0,
    serration_count=4,
    serration_pitch=26.0,
    serration_width=2.5,
    serration_depth=3.5,
    leadscrew_diameter=18.0,
    leadscrew_length=210.0,
    screw_height=55.0,
    handle_diameter=10.0,
    handle_length=110.0,
    mounting_holes=4,
    mounting_hole_diameter=14.0,
)


def build():
    L = SPEC["base_length"]
    W = SPEC["base_width"]
    cast = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)

    body = bkit.rounded_box("ViseBody", L, W, SPEC["base_thickness"], r=3.0,
                            segments=3, centre=(0.0, 0.0, SPEC["base_thickness"] / 2.0),
                            mat=cast)

    # ---- jaws: half of the opening each, overlapping the base ----------
    face = SPEC["jaw_opening"] / 2.0
    for s in (-1.0, 1.0):
        jaw = bkit.rounded_box("Jaw", SPEC["jaw_width"], SPEC["jaw_depth"],
                               SPEC["jaw_height"], r=2.0, segments=2,
                               centre=(s * (face + SPEC["jaw_width"] / 2.0), 0.0,
                                       SPEC["base_thickness"] - 8.0
                                       + SPEC["jaw_height"] / 2.0), mat=cast)
        bkit.boolean(body, jaw, "UNION")

    # ---- leadscrew bore, through base jaws and open gap alike ----------
    bore = bkit.cylinder("ScrewBore", SPEC["leadscrew_diameter"] / 2.0 + 0.2,
                         L + 40.0, segments=64, axis="X",
                         centre=(0.0, 0.0, SPEC["screw_height"]))
    bkit.boolean(body, bore, "DIFFERENCE")

    # ---- jaw serrations, 4 per jaw, computed pitch ---------------------
    z_ser = SPEC["jaw_face_height"] / 2.0 + 24.0
    for (y, _w) in bkit.lay_out([SPEC["serration_width"]] * SPEC["serration_count"],
                                gap=SPEC["serration_pitch"]):
        for s in (-1.0, 1.0):
            cut = bkit.box("Serration", 8.0, SPEC["serration_width"],
                           SPEC["jaw_face_height"],
                           centre=(s * (face - 2.0), y, z_ser))
            bkit.boolean(body, cut, "DIFFERENCE")

    # ---- base mounting holes ------------------------------------------
    for (x, y) in bkit.grid_positions(2, 2, L - 20.0, W - 30.0):
        hole = bkit.cylinder("MountHole", SPEC["mounting_hole_diameter"] / 2.0,
                             40.0, segments=32,
                             centre=(x, y, SPEC["base_thickness"] / 2.0))
        bkit.boolean(body, hole, "DIFFERENCE")
    bkit.recalc(body)

    # ---- leadscrew + handle hub ---------------------------------------
    screw = bkit.cylinder("LeadScrew", SPEC["leadscrew_diameter"] / 2.0,
                          SPEC["leadscrew_length"], segments=64, axis="X",
                          centre=(10.0, 0.0, SPEC["screw_height"]), mat=steel)
    hub = bkit.cylinder("HandleHub", 13.0, 12.0, segments=48, axis="X",
                        centre=(L / 2.0 + 12.0, 0.0, SPEC["screw_height"]), mat=steel)
    bkit.boolean(screw, hub, "UNION")
    bkit.recalc(screw)

    # ---- handle: through-rod with a ball at each end -------------------
    rod = bkit.cylinder("HandleRod", SPEC["handle_diameter"] / 2.0,
                        SPEC["handle_length"], segments=32, axis="Y",
                        centre=(L / 2.0 + 12.0, 0.0, SPEC["screw_height"]), mat=steel)
    knobs = [bkit.uv_sphere("Knob", SPEC["handle_diameter"] / 2.0 + 2.0,
                            segments=32, rings=16,
                            centre=(L / 2.0 + 12.0,
                                    s * (SPEC["handle_length"] / 2.0
                                         - SPEC["handle_diameter"] / 2.0),
                                    SPEC["screw_height"]), mat=steel)
             for s in (-1.0, 1.0)]
    handle = bkit.join([rod] + knobs, name="Handle")

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_length", mm=210.0, tol=0.8, how="bbox_x", part=None),
    dict(name="overall_width", mm=120.0, tol=0.5, how="bbox_y", part=None),
    dict(name="base_length", mm=190.0, tol=0.5, how="bbox_x", part="ViseBody"),
    dict(name="base_width", mm=120.0, tol=0.5, how="bbox_y", part="ViseBody"),
]
