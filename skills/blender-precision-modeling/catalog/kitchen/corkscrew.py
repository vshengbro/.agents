"""corkscrew -- 106 mm T-bar worm corkscrew with a side crank.

The worm is a real helix: `bkit.thread()` sweeps a triangular section along a
helix, which is exactly the shape of a corkscrew wire and gives a genuine
watertight spiral for free. It hangs in front of the turned frame, joined at
the top by the guide block, which is where a real one has its bearing.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height=106.0,           # crank face to the top of the T-bar
    tbar_length=54.0,       # across the top grip
    tbar_diameter=12.0,
    crank_diameter=26.0,
    worm_length=54.0,
    worm_turns=6.0,
    frame_diameter=22.0,
)

FRAME = [
    (0.0, 0.0),
    (9.0, 0.0),
    (11.0, 3.0),
    (11.0, 20.0),
    (9.5, 26.0),
    (9.0, 70.0),
    (10.0, 84.0),
    (10.5, 92.0),
    (9.0, 96.0),
    (0.0, 96.0),
]

TBAR = [
    (0.0, -27.0),
    (5.2, -27.0),
    (6.0, -25.0),
    (6.0, 25.0),
    (5.2, 27.0),
    (0.0, 27.0),
]


def _to_y(obj, pos):
    obj.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.move(obj, *pos)
    return obj


def build():
    wood = bkit.pbr("CorkWood", base=(0.52, 0.34, 0.17), metal=0.0, rough=0.38)
    # Same reasoning as the other cutlery: a mirror metal reflects this dark
    # studio and the worm disappears into the background.
    steel = bkit.pbr("CutlerySteel", base=(0.82, 0.83, 0.85), metal=0.65,
                     rough=0.22)
    dark = bkit.preset("dark_metal")

    frame = bkit.lathe("CorkFrame", FRAME, segments=64, mat=wood)
    # T-bar sits low enough that its capsule swallows the top of the frame,
    # so the two solids interpenetrate instead of leaving a floating gap.
    tbar = _to_y(bkit.lathe("CorkTBar", TBAR, segments=48, mat=wood),
                 (0.0, 0.0, 100.0))

    # The crank wheel is a 26 mm disc standing on its edge, so its centre has
    # to sit at half its diameter -- at z=7 it hung 6 mm below the floor and
    # sit_on_floor() silently lifted the whole model by that much.
    crank = bkit.cylinder("CorkCrank", 13.0, 7.0, segments=48,
                          centre=(0.0, 0.0, 13.0), axis="Y", mat=wood)
    arm = bkit.cylinder("CorkCrankArm", 3.5, 18.0, segments=24,
                        centre=(7.0, 0.0, 13.0), axis="X", mat=steel)
    knob = bkit.uv_sphere("CorkCrankKnob", 7.0, segments=40, rings=20,
                          centre=(17.0, 0.0, 13.0), mat=wood)

    guide = bkit.rounded_box("CorkGuide", 9.0, 11.0, 11.0, r=2.5,
                             centre=(-14.0, 0.0, 91.0), mat=steel)

    # 54 mm of helix at a 9 mm pitch = 6 turns of a 3.4 mm crest wire, hung
    # clear of the frame so the spiral is not hidden behind it
    worm = bkit.thread("CorkWorm", radius=3.4, pitch=9.0,
                       length=SPEC["worm_length"], turns=SPEC["worm_turns"],
                       thread_h=1.8, segments_per_turn=24, mat=steel)
    bkit.move(worm, -16.0, 0.0, 66.0)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="corkscrew_height", mm=106.0, tol=0.3, how="bbox_z"),
    dict(name="tbar_length", mm=54.0, tol=0.3, how="bbox_y", part="CorkTBar"),
    dict(name="crank_diameter", mm=26.0, tol=0.3, how="bbox_x", part="CorkCrank"),
]
