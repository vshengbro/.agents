"""turtle_land -- a 190 mm tortoise: the domed shell with real scute plates, a
columnar neck pulled forward, four elephantine column legs, and a small tail.

The column legs are the cue. A tortoise stands on four pillars, not on four
bent tubes like a lizard -- that is why it can withdraw its head and why it
walks the way it does. The shell's scutes are the other cue: a smooth dome
reads as a stone.

Construction: a lathed shell with a computed scute plate layout on top, a
swept neck and small wedge head, four column legs built once and mirrored
front/rear, and a short tail. Nothing is booleaned.

Orientation: the head points at -Y, X lateral, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    shell_length=140.0,
    shell_width=120.0,
    shell_height=80.0,
    neck_length=45.0,
    leg_span=132.0,
    scute_rows=4,
    scute_cols=4,
)

SHELL_H = 80.0
SHELL_RX = 60.0
SHELL_RY = 70.0
NECK = [(0.0, -62.0, 34.0), (0.0, -80.0, 40.0), (0.0, -98.0, 44.0),
        (0.0, -112.0, 44.0)]
NECK_RAD = [(20.0, 18.0), (16.0, 15.0), (13.0, 12.0), (11.0, 10.0)]
HEAD = [(0.0, -110.0, 44.0), (0.0, -124.0, 43.0), (0.0, -136.0, 41.0)]
HEAD_RAD = [(12.0, 10.0), (10.0, 8.5), (6.0, 5.0)]
# column legs: straight pillars with a slight foot pad, not bent tubes
FORE_LEG = [(0.0, -46.0, 30.0), (0.0, -48.0, 16.0), (0.0, -50.0, 4.0),
            (0.0, -51.0, 1.0)]
FORE_RAD = [(21.0, 20.0), (20.0, 19.0), (21.0, 19.0), (22.0, 17.0)]
HIND_LEG = [(0.0, 44.0, 30.0), (0.0, 46.0, 16.0), (0.0, 48.0, 4.0),
            (0.0, 49.0, 1.0)]
HIND_RAD = [(23.0, 22.0), (22.0, 21.0), (23.0, 21.0), (24.0, 18.0)]


def build():
    shellm = bkit.pbr("TortoiseShell", base=(0.30, 0.24, 0.15), rough=0.66)
    scute = bkit.pbr("TortoiseScute", base=(0.40, 0.33, 0.20), rough=0.58,
                     coat=0.15)
    skin = bkit.pbr("TortoiseSkin", base=(0.38, 0.33, 0.22), rough=0.68)
    eye = bkit.pbr("TortoiseEye", base=(0.02, 0.02, 0.025), rough=0.08)

    # ---- shell: a lathed dome squashed into an oval
    bkit.lathe("Carapace",
               [(0.0, 0.0), (34.0, 2.0), (54.0, 14.0), (62.0, 34.0),
                (56.0, 58.0), (36.0, 74.0), (0.0, 80.0)],
               segments=48, centre=(0.0, 0.0, 0.0), mat=shellm)
    me = bpy.data.objects["Carapace"].data
    for v in me.vertices:
        v.co.x = v.co.x * (SHELL_RX / 62.0)
        v.co.y = v.co.y * (SHELL_RY / 62.0)
    bpy.data.objects["Carapace"].data.update()

    # ---- scutes: five vertebral down the middle, three costal either side,
    # every pitch derived from the shell's own size
    n_row = 4
    n_col = 4
    pitch_y = (SHELL_RY * 1.5) / n_row
    pitch_x = (SHELL_RX * 1.55) / n_col
    for r in range(n_row):
        for c in range(n_col):
            y = -SHELL_RY * 0.72 + (r + 0.5) * pitch_y
            x = -SHELL_RX * 0.74 + (c + 0.5) * pitch_x
            t = max(0.0, 1.0 - (x / SHELL_RX) ** 2 - (y / SHELL_RY) ** 2)
            z = SHELL_H * math.sqrt(t) * 0.9
            if z < 30.0:
                continue
            bkit.rounded_box("Scute%d%d" % (r + 1, c + 1),
                             pitch_x * 0.8, pitch_y * 0.8, 10.0,
                             r=4.0, segments=3, centre=(x, y, z), mat=scute)

    F.tube("Neck", NECK, NECK_RAD, skin, n=2.4, steps=18)
    F.tube("Head", HEAD, HEAD_RAD, skin, n=2.4, steps=18)

    for tag, path, rad, sx in (("Fore", FORE_LEG, FORE_RAD, 1.0),
                               ("Hind", HIND_LEG, HIND_RAD, 1.0)):
        leg = F.tube("Leg%sL" % tag, [(sx * p[0] + 46.0, p[1], p[2])
                                      for p in path], rad, skin,
                     n=2.6, steps=18)
        F.mirror_copy(leg, "Leg%sR" % tag)

    F.tube("Tail", [(0.0, 66.0, 26.0), (0.0, 76.0, 20.0), (0.0, 82.0, 15.0)],
           [(9.0, 8.0), (6.0, 5.0), (2.5, 2.5)], skin, n=2.2, steps=12)

    for side, s in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 3.0, segments=14, rings=8,
                       centre=(s * 8.0, -122.0, 46.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=24)


CHECKS = [
    dict(name="shell_length", mm=140.0, tol=8.0, how="bbox_y",
         part="Carapace"),
    dict(name="shell_width", mm=120.0, tol=8.0, how="bbox_x",
         part="Carapace"),
    dict(name="shell_height", mm=80.0, tol=6.0, how="bbox_z",
         part="Carapace"),
    dict(name="leg_span", mm=134.0, tol=8.0, how="bbox_x"),
    dict(name="head_length", mm=26.0, tol=4.0, how="bbox_y", part="Head"),
]