"""
light_bulb -- A60 LED lamp with an Edison screw (E27) base.

An E27 base is 42.7 mm across major diameter on a 2.54 mm pitch, and the thread
is modelled as real geometry with bkit.thread rather than a painted groove --
at this scale a flat cylinder with a stripe on it reads as a plastic bottle cap.
The A60 envelope is 60 mm across the globe and 110 mm overall.

The envelope is a solid of revolution rather than a hollow shell, which is
correct for a modern LED lamp: the globe is an opal diffuser that you genuinely
cannot see through, and a hollow shell would only add an invisible internal
surface.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    globe_diameter=60.0,     # A60
    overall_height=110.0,
    base_major_diameter=42.7,    # E27 / B22
    base_thread_pitch=2.54,      # E-series pitch
    base_length=22.0,
    neck_diameter=40.0,
)

BASE_R = SPEC["base_major_diameter"] / 2.0
H = SPEC["overall_height"]


def build():
    nickel = bkit.preset("brushed_metal")
    opal = bkit.pbr("OpalGlobe", base=(0.95, 0.95, 0.94), rough=0.40,
                    emission=(1.0, 0.97, 0.90), emission_strength=0.7)
    pcb = bkit.pbr("DriverBoard", base=(0.09, 0.30, 0.13), rough=0.55)
    dark = bkit.preset("black_plastic")

    # ---- E27 base shell: the threaded barrel plus the locating flange ---
    base = bkit.lathe("BulbBase", [
        (0.0, 0.0),
        (17.0, 0.0),              # centre contact disc
        (17.0, 3.0),
        (BASE_R - 1.4, 4.0),      # up to the thread core
        (BASE_R - 1.4, 19.0),
        (20.0, 20.0),
        (20.0, 22.0),             # shoulder onto the neck
        (0.0, 22.0),
    ], segments=64, mat=nickel)

    # real E27 helix: major 42.7, pitch 2.54, ~5 turns up the barrel
    thread = bkit.thread("BulbThread", BASE_R, SPEC["base_thread_pitch"],
                         15.0, turns=5, thread_h=1.4, mat=nickel,
                         segments_per_turn=20)
    bkit.move(thread, 0.0, 0.0, 4.0 + 15.0 / 2.0)

    # ---- LED driver board bridging the neck -----------------------------
    board = bkit.cylinder("BulbBoard", 19.5, 3.0, segments=48,
                          centre=(0.0, 0.0, 24.0), mat=pcb)

    # ---- A60 opal globe --------------------------------------------------
    globe = bkit.lathe("BulbGlobe", [
        (0.0, 25.5),
        (20.0, 25.5),        # sits over the neck
        (24.5, 30.0),
        (28.5, 40.0),
        (30.0, 56.0),        # widest: 60 mm
        (29.0, 70.0),
        (25.5, 84.0),
        (19.0, 96.0),
        (11.0, 104.0),
        (4.0, 108.0),
        (0.0, H),
    ], segments=96, mat=opal)

    # ---- the lamp base skirt below the globe, in dark plastic -----------
    skirt = bkit.lathe("BulbSkirt", [
        (0.0, 21.0),
        (20.5, 21.0),
        (20.5, 25.5),
        (0.0, 25.5),
    ], segments=64, mat=dark)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="globe_diameter", mm=60.0, tol=0.3, how="diameter", part="BulbGlobe"),
    dict(name="globe_height", mm=84.5, tol=0.4, how="bbox_z", part="BulbGlobe"),
    dict(name="thread_diameter", mm=42.7, tol=0.3, how="diameter", part="BulbThread"),
    dict(name="base_height", mm=22.0, tol=0.3, how="bbox_z", part="BulbBase"),
    dict(name="board_diameter", mm=39.0, tol=0.3, how="diameter", part="BulbBoard"),
]