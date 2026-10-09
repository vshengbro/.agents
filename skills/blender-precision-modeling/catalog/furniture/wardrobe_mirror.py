"""
wardrobe_mirror -- cheval standing mirror, 600 mm wide, 1700 mm high.

A full-length mirror is proportioned against a person: 1700 mm of glass height
is about 94 % of standing eye-to-chin height, and the 600 mm width is the
shoulder-to-shoulder measure that lets you see both shoulders. The 500 mm
foot bars sit front-to-back so the frame cannot tip -- the reason a cheval
mirror is 500 mm deep while the frame itself is only 60 mm.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=600.0,
    depth=500.0,             # over the foot bars, which set the tipping depth
    height=1700.0,
    frame_width=60.0,        # stile and rail section, square in the front view
    frame_depth=60.0,
    glass_width=470.0,
    glass_height=1570.0,
    glass_thickness=10.0,
    foot_length=500.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
FW = SPEC["frame_width"]
FD = SPEC["frame_depth"]
GLASS_W = SPEC["glass_width"]
GLASS_H = SPEC["glass_height"]
STILE_X = W / 2.0 - FW / 2.0                 # 270
RAIL_W = W - 2 * FW                          # 480: clear width between stiles

CHECKS = [
    dict(name="overall_width", mm=600.0, tol=0.3, how="bbox_x"),
    dict(name="overall_depth", mm=500.0, tol=0.3, how="bbox_y"),
    dict(name="overall_height", mm=1700.0, tol=0.4, how="bbox_z"),
    dict(name="glass_height", mm=1570.0, tol=0.3, how="bbox_z", part="Glass"),
    dict(name="frame_width", mm=60.0, tol=0.3, how="bbox_x", part="StileLeft"),
    dict(name="foot_length", mm=500.0, tol=0.3, how="bbox_y", part="FootLeft"),
]


def build():
    frame = bkit.pbr("MirrorFrame", base=(0.56, 0.40, 0.22), metal=0.0, rough=0.34)
    frame_dk = bkit.pbr("MirrorFrameEdge", base=(0.42, 0.29, 0.15), metal=0.0,
                        rough=0.40)
    # A true mirror: metallic 1.0 with almost no roughness. The "glass" preset
    # is transmissive, and against a dark studio a transmissive panel renders
    # as a black hole -- a metal reflects the bright half of the world
    # gradient instead, which is what makes it read as a mirror.
    glass = bkit.pbr("MirrorGlass", base=(0.95, 0.96, 0.97), metal=1.0, rough=0.02)

    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Stile%s" % tag, FW, FD, H, r=5.0, segments=3,
                         centre=(sx * STILE_X, 0, H / 2.0), mat=frame)
        bkit.rounded_box("Foot%s" % tag, FW, SPEC["foot_length"], FD, r=5.0,
                         segments=3, centre=(sx * STILE_X, 0, FD / 2.0),
                         mat=frame_dk)

    for (nm, cz) in (("Top", H - FW / 2.0), ("Bottom", FW / 2.0)):
        bkit.rounded_box("Rail%s" % nm, RAIL_W, FD, FW, r=5.0, segments=3,
                         centre=(0, 0, cz), mat=frame)

    # Glass sits between the rails: 1700 - 2*60 = 1580 clear, 5 mm of shadow
    # gap top and bottom, so 1570 of glass shows.
    bkit.rounded_box("Glass", GLASS_W, SPEC["glass_thickness"], GLASS_H, r=2.0,
                     segments=2, centre=(0, 6.0, H / 2.0), mat=glass)

    return dict(spec=SPEC, parts=7)
