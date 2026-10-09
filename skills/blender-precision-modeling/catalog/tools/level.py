"""
level -- 600 mm box spirit level, 60 x 26 mm section.

The horizontal vial sits on the top face, the two vertical vials on the long
side faces near the ends, which is where a real 600 mm level carries them and
what stops the model reading as a plain yellow bar.

The vial glass is deliberately only lightly transmissive. bkit's `glass`
preset is 0.82 transmission and renders near-black against this dark studio,
because there is nothing bright behind it; at 0.35 the tube still reads as a
vial and the bubble inside stays visible.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

L = 600.0
W = 60.0
H = 26.0

SPEC = dict(
    overall_length=600.0,
    level_length=L,
    level_width=W,
    level_height=H,
    vial_outer_diameter=14.0,
)


def build():
    shell = bkit.preset("yellow_paint")
    rubber = bkit.preset("rubber")
    vial = bkit.pbr("LevelVial", base=(0.86, 0.90, 0.90), rough=0.08,
                    transmission=0.35, ior=1.45)
    bubble = bkit.pbr("LevelBubble", base=(0.92, 0.95, 0.97), rough=0.05,
                      transmission=0.10)

    body = bkit.rounded_box("LevelBody", L, W, H, r=4.0, segments=4,
                            centre=(0, 0, H / 2.0), mat=shell)
    for name, x in (("LevelEndCapL", -295.0), ("LevelEndCapR", 295.0)):
        bkit.rounded_box(name, 10.0, 62.0, 28.0, r=4.0, segments=4,
                         centre=(x, 0, 14.0), mat=rubber)

    # horizontal vial on the top face
    bkit.tube("LevelVialHoriz", 7.0, 5.4, 64.0, segments=40, axis="X",
              centre=(0, 0, H), mat=vial)
    bkit.uv_sphere("LevelBubbleHoriz", 4.6, segments=24, rings=12,
                   centre=(0, 0, H), mat=bubble)

    # two vertical vials, one on each long side face
    for side, y in (("Left", W / 2.0), ("Right", -W / 2.0)):
        bkit.tube("LevelVial%s" % side, 6.0, 4.6, 70.0, segments=40,
                  axis="X", centre=(190.0 if side == "Left" else -190.0,
                                    y, H / 2.0), mat=vial)
        bkit.uv_sphere("LevelBubble%s" % side, 4.0, segments=24, rings=12,
                       centre=(190.0 if side == "Left" else -190.0,
                               y, H / 2.0), mat=bubble)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="level_length", mm=600.0, tol=0.5, how="bbox_x",
         part="LevelBody"),
    dict(name="level_width", mm=60.0, tol=0.5, how="bbox_y", part="LevelBody"),
    dict(name="level_height", mm=26.0, tol=0.4, how="bbox_z", part="LevelBody"),
    dict(name="overall_length", mm=600.0, tol=1.0, how="bbox_x"),
]