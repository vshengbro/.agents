"""
dslr_camera -- 152 x 160 x 117 mm DSLR with an 18-55 mm lens fitted: body,
pentaprism hump, grip, two top dials, a rear LCD and a bayonet lens.

Optics again, but the mirror-box furniture around it. The lens is the
`camera_lens` trick -- revolve about Z, rotate 90 degrees about X so the
optical axis runs along -Y, then `bkit.move()` it out through the mount ring.
Every housing part overlaps its neighbour by at least 1 mm: a body and a prism
hump that meet exactly at z=78 touch along a face, and a face-to-face touch is
one of the three ways a model quietly goes non-manifold.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=145.0,
    body_height=78.0,
    body_depth=76.0,
    prism_hump_height=36.0,
    lens_diameter=68.0,
    lens_length=72.0,
    mount_diameter=64.0,
)

BODY_D = SPEC["body_depth"]
FRONT_Y = -BODY_D / 2.0 + 10.0          # body front face, y = -28
BACK_Y = FRONT_Y + BODY_D                 # body back face, y = +48
BODY_H = SPEC["body_height"]


def build():
    shell = bkit.pbr("DslrShell", base=(0.075, 0.076, 0.080), rough=0.42)
    trim = bkit.pbr("DslrTrim", base=(0.60, 0.61, 0.62), metal=0.85,
                    rough=0.30)
    leather = bkit.pbr("DslrGrip", base=(0.035, 0.035, 0.038), rough=0.78)
    glass = bkit.pbr("DslrGlass", base=(0.14, 0.24, 0.40), metal=0.45,
                     rough=0.03)
    screen = bkit.pbr("DslrScreen", base=(0.06, 0.09, 0.11), rough=0.10,
                      emission=(0.30, 0.55, 0.68), emission_strength=0.8)

    # ---- body and grip. The grip overlaps the body by 40 mm --------------
    bkit.rounded_box("DslrBody", SPEC["body_width"], BODY_D, BODY_H, r=12.0,
                     segments=4, centre=(0.0, 10.0, BODY_H / 2.0), mat=shell)
    bkit.rounded_box("DslrGrip", 48.0, 92.0, 84.0, r=22.0, segments=4,
                     centre=(-56.0, 8.0, 42.0), mat=leather)

    # ---- pentaprism hump, sunk 2 mm into the body top --------------------
    bkit.rounded_box("PrismHump", 58.0, 62.0, SPEC["prism_hump_height"],
                     r=10.0, segments=3, centre=(18.0, 12.0, 94.0), mat=shell)
    bkit.rounded_box("HotShoe", 24.0, 20.0, 7.0, r=2.0, segments=2,
                     centre=(18.0, 10.0, 113.5), mat=trim)

    # ---- top dials: mode on the grip, exposure behind it -----------------
    bkit.cylinder("ModeDial", 16.0, 14.0, segments=40,
                  centre=(-56.0, 6.0, 89.0), mat=trim)
    bkit.cylinder("ExposureDial", 13.0, 9.0, segments=36,
                  centre=(-4.0, 30.0, 83.5), mat=trim)
    bkit.cylinder("ShutterButton", 7.0, 5.0, segments=24,
                  centre=(-56.0, -26.0, 85.5), mat=trim)

    # ---- lens mount ring and the lens itself -----------------------------
    bkit.tube("LensMountRing", 32.0, 27.0, 6.0, segments=56,
              centre=(18.0, FRONT_Y - 2.0, 42.0), axis="Y", mat=trim)

    lens = bkit.lathe("CameraLens", [(0.0, 0.0), (34.0, 0.0), (34.0, 50.0),
                                     (30.0, 50.0), (30.0, 72.0),
                                     (0.0, 72.0)], segments=64, mat=shell)
    lens.rotation_euler = (math.radians(90.0), 0.0, 0.0)   # +Z -> -Y
    bkit.move(lens, 18.0, FRONT_Y - 3.0, 42.0)

    front = bkit.lathe("LensFrontElement", [(0.0, 62.0), (27.0, 62.0),
                                            (27.0, 68.0), (0.0, 68.0)],
                       segments=64, mat=glass)
    front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(front, 18.0, FRONT_Y - 3.0, 42.0)

    # 40 ribs swept around the lens barrel. The rib is built at radius 34.4 from
    # the WORLD Z axis (not from the lens axis at x=18) because array_radial
    # orbits the world origin -- bake the axis offset in afterwards with move().
    rib = bkit.box("_lrib", 1.4, 34.0, 2.2, centre=(34.4, 0.0, 0.0),
                   mat=leather)
    bkit.array_radial(rib, count=48, axis="Y")
    bkit.move(rib, 18.0, -56.0, 42.0)

    # ---- rear screen, eyepiece and strap lugs -----------------------------
    bkit.rounded_box("RearScreen", 96.0, 6.0, 58.0, r=3.0, segments=2,
                     centre=(6.0, 49.0, 44.0), mat=screen)
    bkit.rounded_box("Viewfinder", 34.0, 14.0, 22.0, r=4.0, segments=2,
                     centre=(44.0, 50.0, 88.0), mat=leather)
    bkit.rounded_box("EyeCup", 36.0, 8.0, 24.0, r=6.0, segments=2,
                     centre=(44.0, 52.0, 88.0), mat=leather)
    for side in (-1.0, 1.0):
        bkit.torus("StrapLug" + ("L" if side < 0 else "R"), 6.0, 1.8,
                   seg_major=28, seg_minor=10, axis="X",
                   centre=(side * 74.0, 26.0, 58.0), mat=trim)

    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="body_width", mm=145.0, tol=0.5, how="bbox_x", part="DslrBody"),
    dict(name="body_height", mm=78.0, tol=0.5, how="bbox_z", part="DslrBody"),
    dict(name="body_depth", mm=76.0, tol=0.5, how="bbox_y", part="DslrBody"),
    dict(name="prism_hump_height", mm=36.0, tol=0.5, how="bbox_z",
         part="PrismHump"),
    # `diameter` is max(bbox_x, bbox_y), which on a 68 x 72 lens measures the
    # 72 mm AXIAL length. bbox_min is the honest radial extent here.
    dict(name="lens_diameter", mm=68.0, tol=0.5, how="bbox_min",
         part="CameraLens"),
    # Optical axis runs along -Y, so the 72 mm length is bbox_y; bbox_x is 68 mm.
    dict(name="lens_length", mm=72.0, tol=0.5, how="bbox_y", part="CameraLens"),
]