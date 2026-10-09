"""
flywheel -- 300 mm cast flywheel: heavy rim, six equally spaced spokes, bored hub.

The six spokes are what make it a flywheel instead of a washer, and they are
laid out by angle (k * 360/6) rather than by hand-placed coordinates: a
seven-spoke or lopsided wheel is the classic failure here. The rim is a real
tube with a wall thickness, and each spoke reaches 3 mm past both the hub OD and
the rim ID so no union ever sees two faces meeting exactly.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    outside_diameter=300.0,
    rim_inner_diameter=264.0,
    rim_width=60.0,
    hub_diameter=90.0,
    hub_length=70.0,
    bore_diameter=44.0,
    spoke_count=6,
    spoke_width=28.0,
    spoke_thickness=18.0,
    spoke_angle_deg=60.0,
)


def build():
    r_out = SPEC["outside_diameter"] / 2.0
    r_rim_in = SPEC["rim_inner_diameter"] / 2.0
    r_hub = SPEC["hub_diameter"] / 2.0
    r_bore = SPEC["bore_diameter"] / 2.0

    iron = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55,
                     rough=0.30)

    # ---- rim: a real ring, not a disc ----------------------------------
    rim = bkit.tube("FlywheelRim", r_out, r_rim_in, SPEC["rim_width"],
                    segments=128, mat=iron)

    # ---- hub + spokes ---------------------------------------------------
    web = bkit.tube("FlywheelWeb", r_hub, r_bore, SPEC["hub_length"],
                    segments=96, mat=iron)

    # spoke runs from inside the hub wall to inside the rim wall
    r_a = r_hub - 5.0
    r_b = r_rim_in + 5.0
    spoke_len = r_b - r_a
    spoke = bkit.rounded_box("Spoke", spoke_len, SPEC["spoke_width"],
                             SPEC["spoke_thickness"], r=5.0, segments=3,
                             centre=((r_a + r_b) / 2.0, 0.0, 0.0), mat=iron)
    for k in range(1, SPEC["spoke_count"]):
        copy = bkit.duplicate(spoke, "Spoke%02d" % k,
                              rot_deg=(0.0, 0.0, k * SPEC["spoke_angle_deg"]))
        bkit.boolean(web, copy, "UNION")
    bkit.boolean(web, spoke, "UNION")
    web.name = "FlywheelWeb"

    # keyway in the hub bore
    key = bkit.box("Keyway", 14.0, 8.0, SPEC["hub_length"] * 2.0,
                   centre=(r_bore - 4.0, 0.0, 0.0))
    bkit.boolean(web, key, "DIFFERENCE")
    bkit.recalc(web)

    # ---- lighten the rim faces, the way a cast rim is machined ----------
    for zc in (SPEC["rim_width"] / 2.0 - 1.5, -SPEC["rim_width"] / 2.0 + 1.5):
        cut = bkit.tube("RimRelief", r_out - 4.0, r_rim_in + 2.0, 3.0, segments=128,
                        centre=(0.0, 0.0, zc))
        bkit.boolean(rim, cut, "DIFFERENCE")
    bkit.assign(rim, steel)
    bkit.recalc(rim)

    return dict(spec=SPEC, parts=2, spokes=SPEC["spoke_count"])


CHECKS = [
    dict(name="outside_diameter", mm=300.0, tol=0.6, how="diameter", part="FlywheelRim"),
    dict(name="rim_width", mm=60.0, tol=0.4, how="bbox_z", part="FlywheelRim"),
    dict(name="rim_outer_diameter_y", mm=300.0, tol=0.6, how="bbox_y", part="FlywheelRim"),
    dict(name="overall_height", mm=70.0, tol=0.4, how="bbox_z", part="FlywheelWeb"),
]
