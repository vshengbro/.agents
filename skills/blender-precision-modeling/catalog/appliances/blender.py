"""
blender -- countertop high-speed blender: a moulded motor base with a vent grille
and four speed keys, a drive coupler, a lathed tapered jar with a real wall and
a removable lid, and a swept jar handle.

The tapered jar is the reason this is a blender and not a stand mixer, so it is
a lathe profile whose radius shrinks with height.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=186.0,
    base_depth=196.0,
    base_height=186.0,
    overall_height=416.0,
    corner_radius=18.0,
    jar_diameter=140.0,       # at the jar foot, where it meets the coupler
    jar_top_diameter=124.0,
    jar_height=196.0,
    jar_wall=3.0,
    lid_diameter=132.0,
    handle_reach=34.0,
    handle_tube=12.0,
    key_count=4,
    key_diameter=20.0,
    key_pitch=34.0,
)

BW = SPEC["base_width"]
BD = SPEC["base_depth"]
BH = SPEC["base_height"]
JR = SPEC["jar_diameter"] / 2.0
JT = SPEC["jar_top_diameter"] / 2.0
JH = SPEC["jar_height"]
WALL = SPEC["jar_wall"]
JAR_Z = BH + 10.0                      # 196, jar foot height, into the collar
FRONT = -(BD / 2.0)


def build():
    plastic = bkit.preset("white_plastic")
    dark = bkit.preset("black_plastic")
    jar_mat = bkit.pbr("BlenderJar", base=(0.82, 0.86, 0.88), rough=0.10,
                       coat=0.5)
    steel = bkit.preset("brushed_metal")
    lamp = bkit.pbr("BlenderKey", base=(0.10, 0.11, 0.12), rough=0.25,
                    emission=(0.30, 0.55, 0.85), emission_strength=0.9)

    # ---- motor base -------------------------------------------------------
    body = bkit.rounded_box("BlenderBase", BW, BD, BH, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, BH / 2.0), mat=plastic)
    # A slightly proud collar reads as the jar seat, and gives the lid and jar
    # something to stand on other than the bare top face.
    bkit.lathe("BaseCollar",
               [(0.0, 0.0), (58.0, 0.0), (60.0, 2.0), (60.0, 16.0),
                (54.0, 20.0), (0.0, 20.0)],
               segments=64, centre=(0.0, 0.0, BH - 6.0), mat=dark)
    bkit.cylinder("DriveCoupler", 26.0, 34.0, segments=40,
                  centre=(0.0, 0.0, BH + 13.0), mat=dark)

    # ---- speed keys -------------------------------------------------------
    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["key_count"], gap=SPEC["key_pitch"] - kd)):
        bkit.cylinder("SpeedKey%d" % i, kd / 2.0, 12.0, segments=32, axis="Y",
                      centre=(x, FRONT - 6.0 + 4.0, 96.0), mat=lamp)

    # ---- jar --------------------------------------------------------------
    # ONE closed profile: out along the foot, up the outside, over the rim,
    # back down the inside, across the inner floor. The radius shrinks with
    # height, which is what makes it a blender jar.
    prof = [
        (0.0, 0.0),
        (JR - 6.0, 0.0),
        (JR, 8.0),
        (JR - 4.0, 30.0),
        (JT + 2.0, JH - 26.0),
        (JT, JH - 6.0),
        (JT + 1.0, JH),                 # rolled rim
        (JT - WALL, JH),
        (JT - WALL - 1.0, JH - 8.0),
        (JR - 8.0 - WALL, 26.0),
        (JR - 12.0 - WALL, 12.0),
        (0.0, 10.0),
    ]
    bkit.lathe("BlenderJar", prof, segments=96, centre=(0.0, 0.0, JAR_Z),
               mat=jar_mat)

    # ---- blade stack inside the jar ---------------------------------------
    for i, z in enumerate((JAR_Z + 14.0, JAR_Z + 40.0)):
        bkit.box("Blade%d" % i, 2.0, 74.0, 9.0,
                 centre=(0.0, 0.0, z), mat=steel)
    bkit.cylinder("JarSpindle", 8.0, 96.0, segments=24,
                  centre=(0.0, 0.0, JAR_Z + 52.0), mat=dark)

    # ---- lid --------------------------------------------------------------
    bkit.lathe("BlenderLid",
               [(0.0, 0.0), (SPEC["lid_diameter"] / 2.0 - 6.0, 0.0),
                (SPEC["lid_diameter"] / 2.0, 5.0),
                (SPEC["lid_diameter"] / 2.0 - 4.0, 16.0),
                (34.0, 22.0), (30.0, 28.0), (0.0, 30.0)],
               segments=96, centre=(0.0, 0.0, JAR_Z + JH - 6.0), mat=dark)

    # ---- jar handle -------------------------------------------------------
    # plane="YZ" puts the arc in the depth plane, which is where a blender's
    # handle actually lives; both tips end up inside the jar wall.
    reach = SPEC["handle_reach"] - SPEC["handle_tube"]
    bkit.arc_torus("JarHandle", reach, SPEC["handle_tube"], -82.0, 82.0,
                   centre=(0.0, JR - 10.0, JAR_Z + JH * 0.55), plane="YZ",
                   seg_major=44, mat=dark, caps=True)

    # ---- motor vents on the back ------------------------------------------
    n = 9
    pitch = 20.0
    span = (n - 1) * pitch
    vent = bkit.rounded_box("BaseVent", 14.0, 6.0, 7.0, r=2.0, segments=2,
                            centre=(-span / 2.0, BD / 2.0 - 1.0, 150.0),
                            mat=dark)
    bkit.array_linear(vent, n, (pitch, 0.0, 0.0))

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="base_width", mm=186.0, tol=0.4, how="bbox_x", part="BlenderBase"),
    dict(name="base_depth", mm=196.0, tol=0.4, how="bbox_y", part="BlenderBase"),
    dict(name="overall_height", mm=416.0, tol=0.5, how="bbox_z"),
    dict(name="jar_diameter", mm=140.0, tol=0.5, how="diameter", part="BlenderJar"),
    dict(name="jar_height", mm=196.0, tol=0.5, how="bbox_z", part="BlenderJar"),
]