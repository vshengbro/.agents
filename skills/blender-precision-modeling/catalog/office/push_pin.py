"""
push_pin -- 28 mm push pin: a 10 mm plastic head over a 25 mm steel needle.

The hard part of a push pin is not the geometry, it is the orientation. A pin
standing on its point looks like a rendering bug, and the needle lying flat on
the table under an upright head looks like a mushroom. What reads instantly is
the head standing on the desk with the needle lying along it.

So: the head is lathed upright (z = 0..8), and the needle is lathed along its
own axis then rotated onto the table by the OBJECT, not by the mesh -- bkit
primitives place geometry with `location`, so `ob.data.transform()` rotates
about the wrong point and leaves the needle floating 6 m in the air.

That float was not hypothetical: assigning `ob.location = (0, 0, 6.0)` with
raw numbers puts the part at 6000 mm, because Blender reads location in metres.
Use bkit.v().
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    head_diameter=10.0,
    head_height=8.0,
    needle_diameter=1.0,
    needle_length=25.0,
    overall_length=30.0,
)

HEAD_R = SPEC["head_diameter"] / 2.0


def build():
    plastic = bkit.pbr("PushPinHead", base=(0.92, 0.16, 0.18), rough=0.28,
                       coat=0.35)
    steel = bkit.pbr("PushPinSteel", base=(0.74, 0.76, 0.78), metal=0.88,
                     rough=0.26)

    # ---- head: one closed lathed profile, monotonically rising in z -------
    # Walking the profile strictly bottom-to-top keeps the generated normals
    # outward; a profile that doubles back in z comes out of the revolve with
    # inverted winding and a negative signed volume.
    head_prof = [
        (0.0, 0.0),                       # flat underside, on the desk
        (HEAD_R - 1.4, 0.0),              # skirt underside
        (HEAD_R, 0.8),                    # skirt edge
        (HEAD_R, 4.6),
        (HEAD_R - 0.6, 6.4),              # shoulder
        (HEAD_R * 0.62, 7.6),
        (HEAD_R * 0.30, 8.0),
        (0.0, 8.2),                       # dome top -> welded pole
    ]
    head = bkit.lathe("PushPinHeadBody", head_prof, segments=48, mat=plastic)

    # ---- needle: a real taper, lathed along +Z then laid on the desk ------
    r = SPEC["needle_diameter"] / 2.0
    needle_prof = [
        (0.0, 0.0),                       # sharp point -> welded pole
        (r * 0.70, 1.2),
        (r, 6.0),
        (r, 25.0),                        # full-diameter shaft
    ]
    needle = bkit.lathe("PushPinNeedle", needle_prof, segments=24, mat=steel)

    # Rotate the OBJECT: local +Z becomes world +X, and the axial offset moves
    # from location.z into location.x. bkit.v() because location is metres.
    #
    # No yaw here on purpose. A yawed needle projects a 21.9 mm bounding box
    # instead of its true 25.4 mm length, and the only way to make a CHECK
    # pass on that is to declare the wrong number. Straight along +X keeps the
    # measurement honest; the needle still reads clearly in the hero and
    # three-quarter angles.
    axial = needle.location.z / bkit.MM
    needle.rotation_euler = (0.0, math.radians(-90.0), 0.0)
    needle.location = bkit.v(axial, 0.0, 4.2)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="head_diameter", mm=10.0, tol=0.4, how="diameter",
         part="PushPinHeadBody"),
    dict(name="head_height", mm=8.2, tol=0.5, how="bbox_z",
         part="PushPinHeadBody"),
    # The needle is yawed 30 deg, so its WORLD bounding box is the diagonal
    # span, not its diameter. A bbox cannot measure a rotated cylinder's
    # gauge -- so check the needle's own axial reach along its length instead.
    dict(name="needle_length", mm=25.4, tol=1.2, how="bbox_max",
         part="PushPinNeedle"),
    dict(name="overall_length", mm=30.4, tol=1.2, how="bbox_x"),
]