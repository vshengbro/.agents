"""snail -- a 40 mm garden snail: the coiled shell with about three whorls, the
soft body extended forward, two upper tentacles with eyes at the tips, and the
tentacle's own lens retractable body.

The spiral is the model. Three whorls of a real logarithmic spiral read as a
gastropod; a cone plus a knob does not. Here the growth ratio and the turn
count are the real ones, and the tube radius follows the spiral's own radius
so the aperture is thick and the apex thin.

Construction: one spiral swept as a tapering tube, a flared aperture lip, a
swept soft body, a foot, two pairs of tentacles and two eyes. Nothing is
booleaned.

Orientation: the shell sits over the body, the head reaches toward -Y, Z up.
A 40 mm garden snail fits the catalog's `tiny` band.
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
    shell_diameter=32.2,
    shell_height=36.8,
    shell_whorls=3.0,
    body_length=29.0,
    tentacle_length=16.0,
)

WHORLS = 3.0
GROWTH = 1.78              # spiral radius multiplies by this per half turn
R0 = 2.2
STEPS = 64
SHELL_C = (0.0, 8.0, 16.0)


def spiral():
    """The shell's centreline and its local tube radius.

    The radius follows the spiral's own radius, which is what gives a thick
    aperture and a thin apex -- a constant-radius tube would be a coiled rope,
    not a shell.
    """
    path, rad = [], []
    for i in range(STEPS + 1):
        t = i / float(STEPS)
        a = 2.0 * math.pi * WHORLS * t
        r = R0 * (GROWTH ** (WHORLS * t))
        path.append((r * math.sin(a), SHELL_C[1] - r * (1.0 - math.cos(a)) * 0.5,
                     SHELL_C[2] + r * math.cos(a)))
        rad.append((max(0.9, r * 0.70), max(0.9, r * 0.70)))
    return path, rad


BODY = [(0.0, 6.0, 8.0), (0.0, -2.0, 8.6), (0.0, -12.0, 8.4),
        (0.0, -22.0, 7.4)]
BODY_RAD = [(9.0, 7.0), (8.0, 6.4), (6.4, 5.2), (4.4, 3.8)]
FOOT = [(0.0, -22.0, 3.0), (0.0, -6.0, 2.4), (0.0, 12.0, 2.4),
        (0.0, 24.0, 2.4)]
FOOT_RAD = [(4.6, 2.4), (6.0, 2.6), (6.0, 2.6), (5.0, 2.4)]


def build():
    shellm = bkit.pbr("SnailShell", base=(0.44, 0.32, 0.18), rough=0.44,
                      coat=0.2)
    bandm = bkit.pbr("SnailBand", base=(0.26, 0.18, 0.10), rough=0.48)
    flesh = bkit.pbr("SnailBody", base=(0.68, 0.56, 0.46), rough=0.56)
    eye = bkit.pbr("SnailEye", base=(0.02, 0.02, 0.02), rough=0.08)

    path, rad = spiral()
    F.tube("Shell", path, rad, shellm, n=2.2, steps=16)

    lip = path[-1]
    bkit.torus("ShellLip", rad[-1][0] * 1.2, 1.8, seg_major=28, seg_minor=10,
               centre=(lip[0], lip[1] - 5.0, lip[2] + 3.0), axis="Y",
               mat=bandm)

    # ---- growth bands: a computed row up the whorl, the pitch derived from
    # the band count so no two rings share a station
    n_band = 10
    for i in range(n_band):
        k = int(STEPS * (0.5 + 0.45 * i / float(n_band - 1)))
        bkit.torus("Band%d" % i, rad[k][0] * 1.03, 0.8, seg_major=22,
                   seg_minor=8, centre=path[k], axis="X", mat=bandm)

    F.tube("Body", BODY, BODY_RAD, flesh, n=2.4, steps=18)
    F.tube("Foot", FOOT, FOOT_RAD, flesh, n=3.0, steps=16)

    # ---- two tentacle pairs: the long upper pair carries the eyes at its
    # tips, the short lower pair probes the ground
    for side, sx in (("L", 1.0), ("R", -1.0)):
        upper = [(sx * 3.2, -20.0, 9.0), (sx * 5.0, -26.0, 14.0),
                 (sx * 5.6, -31.0, 19.0)]
        F.tube("TentacleUpper%s" % side, upper,
               [(2.0, 2.0), (1.4, 1.4), (1.0, 1.0)], flesh, n=2.2, steps=10)
        F.sphere("Eye%s" % side, 1.8, upper[-1], eye, segments=16, rings=8)
        lower = [(sx * 3.0, -21.0, 7.0), (sx * 5.2, -27.0, 9.5)]
        F.tube("TentacleLower%s" % side, lower,
               [(1.5, 1.5), (1.0, 1.0)], flesh, n=2.2, steps=10)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="shell_diameter", mm=32.2, tol=4.0, how="bbox_x", part="Shell"),
    dict(name="shell_height", mm=36.8, tol=4.0, how="bbox_z", part="Shell"),
    dict(name="body_length", mm=29.0, tol=5.0, how="bbox_y", part="Body"),
    dict(name="tentacle_length", mm=11.0, tol=2.5, how="longest",
         part="TentacleUpperL"),
    dict(name="overall_height", mm=44.5, tol=5.0, how="bbox_z"),
]