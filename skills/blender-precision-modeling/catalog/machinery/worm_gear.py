"""
worm_gear -- worm and wheel pair, 1-start worm driving a 16-tooth wheel.

The pair is the point: a worm on its own is a threaded rod, and a wheel on its
own is a spur gear. What makes it a worm drive is the axis relationship (the
worm axis is perpendicular to the wheel axis) and the centre distance, which is
the sum of the two pitch radii. The worm's crest circle therefore cuts into the
wheel's tip circle by exactly the two addenda, which is the real mesh.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    worm_major_diameter=28.0,
    worm_core_diameter=20.0,
    worm_pitch=8.0,
    worm_length=70.0,
    wheel_teeth=16,
    wheel_module_mm=4.0,
    wheel_tip_diameter=72.0,
    wheel_pitch_diameter=64.0,
    wheel_face_width=14.0,
    wheel_bore_diameter=18.0,
    hub_diameter=40.0,
    hub_length=22.0,
    centre_distance=44.0,        # 32 (wheel pitch r) + 12 (worm pitch r)
)


def build():
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- worm: a real helical thread swept on a solid core ---------------
    # thread() sweeps a triangle whose inner edge sits at radius - thread_h, so
    # the core must be slightly LARGER than that or the union has two exactly
    # coincident cylindrical surfaces (non-manifold edges, not a fillet).
    core_r = SPEC["worm_major_diameter"] / 2.0 - 4.0 + 0.4
    worm_thread = bkit.thread("WormThread", radius=SPEC["worm_major_diameter"] / 2.0,
                              pitch=SPEC["worm_pitch"], length=64.0,
                              thread_h=4.0, segments_per_turn=32, mat=steel)
    bkit.place(worm_thread, (0.0, 0.0, SPEC["centre_distance"]), "X")
    core = bkit.cylinder("WormCore", core_r, 64.0, segments=64, axis="X",
                         centre=(0.0, 0.0, SPEC["centre_distance"]), mat=steel)
    bkit.boolean(worm_thread, core, "UNION")
    bkit.recalc(worm_thread)
    worm = worm_thread
    worm.name = "Worm"

    # ---- wheel: spur blank + hub ----------------------------------------
    wheel = bkit.gear("WheelBlank", teeth=SPEC["wheel_teeth"],
                      module_mm=SPEC["wheel_module_mm"],
                      thickness=SPEC["wheel_face_width"],
                      bore_r=SPEC["wheel_bore_diameter"] / 2.0, mat=steel)
    hub = bkit.tube("WheelHub", SPEC["hub_diameter"] / 2.0,
                    SPEC["wheel_bore_diameter"] / 2.0, SPEC["hub_length"],
                    segments=72, mat=dark)
    bkit.boolean(wheel, hub, "UNION")
    # web lightening: one shallow recess each side, keeps the rim full width
    relief = bkit.cylinder("Relief", 24.0, 4.0, segments=64)
    bkit.boolean(wheel, relief, "DIFFERENCE")
    bkit.recalc(wheel)
    bkit.place(wheel, (0.0, 0.0, 0.0), "Y")
    wheel.name = "Wheel"

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="wheel_tip_diameter", mm=72.0, tol=0.6, how="diameter", part="Wheel"),
    dict(name="worm_major_diameter", mm=28.0, tol=0.5, how="bbox_y", part="Worm"),
    dict(name="worm_length", mm=70.0, tol=0.8, how="bbox_x", part="Worm"),
]
