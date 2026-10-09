"""saucepan -- 180 mm straight-sided pan with a welded stay-cool handle.

95 mm deep on a 180 mm body. Straight sides make the wall thickness legible
in a side view, which a curved pan does not.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    body_diameter=180.0,    # outside diameter at the rim
    body_height=95.0,       # rim height above the table
    handle_length=105.0,    # outside reach from the wall
    handle_diameter=16.0,
    wall=2.5,
    base_thickness=4.0,
    capacity_ml=2000.0,
)

R = SPEC["body_diameter"] / 2.0 - 0.5    # the rim flare adds the last 0.5 mm
H = SPEC["body_height"]
WALL = SPEC["wall"]


def build():
    # A full metal reflects a dark studio and reads black; a brighter base and a
    # tighter roughness keep the specular highlights that make it read as steel.
    steel = bkit.pbr("PanSteelBright", base=(0.86, 0.87, 0.89), metal=1.0,
                     rough=0.24)

    prof = [
        (0.0, 0.0),
        (66.0, 0.0),            # flat base
        (78.0, 1.0),
        (86.0, 4.0),
        (89.0, 12.0),
        (R, 26.0),              # straight side
        (R, 90.0),
        (R + 0.5, 93.5),        # rim flare
        (R - 2.0, H),
        (R - 2.0 - WALL, H),    # across the rim
        (R - 2.0, 90.0),
        (R - WALL, 26.0),       # down the inside
        (86.0, 14.0),
        (81.0, 7.0),
        (66.0, SPEC["base_thickness"]),
        (0.0, SPEC["base_thickness"]),
    ]
    body = bkit.lathe("SaucepanBody", prof, segments=96, mat=steel)

    # Root sits inside the 2.5 mm wall (inner face at R-WALL), not in the
    # cavity, so the handle's end cap is buried in metal.
    handle = bkit.cylinder("SaucepanHandle", 8.0, SPEC["handle_length"],
                           segments=40, centre=(0.0, 0.0, 0.0), axis="Y",
                           r2=6.0, mat=steel)
    bkit.move(handle, 0.0, R - 1.5 + SPEC["handle_length"] / 2.0, 74.0)

    # welded bracket plate: overlaps both the wall and the handle root, so
    # there is no coincident face at either joint.
    bracket = bkit.rounded_box("SaucepanBracket", 26.0, 34.0, 8.0, r=3.0,
                               centre=(0.0, 96.0, 73.0), mat=steel)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_diameter", mm=180.0, tol=0.3, how="diameter",
         part="SaucepanBody"),
    dict(name="body_height", mm=95.0, tol=0.3, how="bbox_z", part="SaucepanBody"),
    dict(name="handle_length", mm=105.0, tol=0.3, how="bbox_y",
         part="SaucepanHandle"),
]
