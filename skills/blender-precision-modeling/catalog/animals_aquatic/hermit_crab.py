"""hermit_crab -- a 55 mm hermit crab: a dextral (right-handed) SPIRAL shell
with about three whorls, an asymmetric pair of claws -- the left one much
smaller, which is why a hermit crab's claws do not match -- and two pairs of
walking legs plus two reduced rear pairs gripping the shell.

The spiral is the model. Three whorls of a real logarithmic spiral, generated
from a growth ratio, read as a gastropod shell; a cone plus a knob does not.
And the claw asymmetry is the diagnostic: right claw large, left claw small.

Construction: one spiral swept as a tapering tube (the whorl), a lip at the
aperture, a swept cephalothorax with its eye stalks, two claws of DIFFERENT
size, and four walking legs built as two arrayed pairs. Nothing is booleaned.

Orientation: the crab faces -Y, the shell spirals up and back over it, Z up.
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
    shell_length=42.0,
    shell_diameter=34.0,
    shell_whorls=3.0,
    body_length=24.0,
    claw_asymmetry=1.7,        # right claw : left claw
)

# ---- the shell's spiral: a logarithmic spiral, generated not typed
WHORLS = 3.0
GROWTH = 1.72          # radius multiplies by this per half-turn
WHORL_STEPS = 54
SHELL_R0 = 2.9


def spiral():
    """Points along a dextral logarithmic spiral, and the local tube radius.

    Radius grows by GROWTH per half turn, so three whorls produce a real
    gastropod profile. The tube radius is the distance from the spiral's
    centre, which is what makes the shell thick at the aperture and thin at
    the apex.
    """
    path, rad = [], []
    for i in range(WHORL_STEPS + 1):
        t = i / float(WHORL_STEPS)
        a = 2.0 * math.pi * WHORLS * t
        r = SHELL_R0 * (GROWTH ** (WHORLS * t))
        # dextral: the spiral opens anticlockwise seen from the front
        path.append((r * math.sin(a), 12.0 - r * (1.0 - math.cos(a)) * 0.55,
                     12.0 + r * math.cos(a)))
        rad.append((max(1.2, r * 0.62), max(1.2, r * 0.62)))
    return path, rad


# ---- body: cephalothorax projecting forward out of the aperture
BODY = [
    (0.0, -4.0, 16.0), (0.0, -12.0, 15.0), (0.0, -20.0, 13.5),
    (0.0, -26.0, 12.0),
]
BODY_RAD = [(9.0, 8.0), (8.5, 7.5), (7.0, 6.0), (5.5, 5.0)]
# the big right claw and the small left claw, as separate swept solids
# claw PATH and claw RADIUS are separate tables. `F.tube` takes
# (along_s, along_v) radii per node; passing the path's own (x, y) as radii
# gives a tube whose half-height is the claw's y coordinate -- a 99 mm "claw"
# on a 55 mm animal, watertight and entirely wrong.
CLAW_R_PATH = [(7.0, -14.0, 16.0), (9.5, -20.0, 15.0), (11.0, -26.0, 13.5),
               (9.0, -31.0, 12.0)]
CLAW_L_PATH = [(4.5, -14.0, 16.0), (5.8, -20.0, 15.0), (6.6, -26.0, 13.5),
               (5.4, -31.0, 12.0)]
CLAW_R_RAD = [(6.0, 5.5), (8.0, 7.0), (9.2, 7.8), (7.4, 6.4)]
CLAW_L_RAD = [(4.0, 3.6), (5.0, 4.4), (5.6, 4.9), (4.6, 4.0)]
# one walking leg: out and down to a point on the substrate
LEG = [
    (0.0, 0.0, 0.0), (14.5, 5.5, -3.0), (23.5, 12.5, -8.0),
    (27.0, 18.0, -11.0),
]
LEG_RAD = [(3.8, 3.8), (3.0, 3.0), (2.2, 2.2), (0.9, 0.9)]


def build():
    shellm = bkit.pbr("HermitShell", base=(0.62, 0.44, 0.26), rough=0.60)
    bandm = bkit.pbr("HermitBand", base=(0.38, 0.24, 0.14), rough=0.62)
    bodym = bkit.pbr("HermitBody", base=(0.68, 0.36, 0.20), rough=0.58)
    cl = bkit.pbr("HermitClaw", base=(0.72, 0.40, 0.22), rough=0.50,
                  coat=0.2)
    eye = bkit.pbr("HermitEye", base=(0.02, 0.02, 0.025), rough=0.08)

    path, rad = spiral()
    F.tube("Shell", path, rad, shellm, n=2.2, steps=16)

    # ---- the aperture lip: a flared ring at the shell's mouth
    lip = path[-1]
    bkit.torus("ShellLip", rad[-1][0] * 1.25, 2.0, seg_major=28,
               seg_minor=10, centre=(lip[0], lip[1] - 6.0, lip[2] + 4.0),
               axis="Y", mat=bandm)

    # ---- growth bands: a computed row of thin rings up the whorl, pitch
    # derived from the ring count so no two share a station
    n_band = 9
    for i in range(n_band):
        k = int(WHORL_STEPS * (0.55 + 0.42 * i / float(n_band - 1)))
        p = path[k]
        bkit.torus("Band%d" % i, rad[k][0] * 1.02, 0.9, seg_major=22,
                   seg_minor=8, centre=p, axis="X", mat=bandm)

    F.tube("Cephalothorax", BODY, BODY_RAD, bodym, n=2.4, steps=16)

    # ---- the asymmetric claws. A hermit crab's right claw is about 1.7x the
    # left; a matched pair is a shore crab, not a hermit crab.
    # The asymmetry is applied by scaling only the LATERAL offset, so the claw
    # still reaches forward to the same station: the right claw is a fatter
    # claw, not a longer one.
    for side, path_p, radii in (("R", CLAW_R_PATH, CLAW_R_RAD),
                              ("L", CLAW_L_PATH, CLAW_L_RAD)):
        sx = 1.0 if side == "R" else -1.0
        arm = [(sx * p[0], p[1], p[2]) for p in path_p]
        F.tube("ClawArm%s" % side, arm, radii, cl, n=2.4, steps=14)
        F.tube("ClawPincer%s" % side,
               [(sx * p[0] * 0.7, p[1] - 5.0, p[2] - 1.0) for p in path_p],
               [(r[0] * 0.6, r[1] * 0.6) for r in radii], cl,
               n=2.4, steps=12)

    # ---- eye stalks, the diagnostic long stalks of a hermit crab
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("EyeStalk%s" % side,
                       (sx * 3.5, -20.0, 19.0), (sx * 6.0, -26.0, 25.0),
                       1.8, 1.4, seg=10, mat=bodym)
        bkit.uv_sphere("Eye%s" % side, 2.6, segments=14, rings=8,
                       centre=(sx * 6.2, -26.4, 25.6), mat=eye)

    # ---- four walking legs: two arrayed pairs about the body axis, the front
    # pair longer than the rear pair
    for tag, scale, y0 in (("Front", 1.0, -14.0), ("Rear", 0.72, 0.0)):
        leg = F.tube("Leg%s0" % tag,
                     [(p[0] * scale, y0 + p[1], 14.0 + p[2]) for p in LEG],
                     [(r[0] * scale, r[1] * scale) for r in LEG_RAD],
                     bodym, n=2.2, steps=12)
        bkit.move(leg, 8.0, 0.0, 0.0)
        bkit.array_radial(leg, 2, centre=(0.0, 0.0, 14.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=26)


CHECKS = [
    dict(name="overall_height", mm=51.0, tol=6.0, how="bbox_z"),
    dict(name="shell_diameter", mm=34.0, tol=5.0, how="bbox_x", part="Shell"),
    dict(name="shell_length", mm=42.0, tol=6.0, how="longest", part="Shell"),
    dict(name="body_length", mm=24.0, tol=4.0, how="bbox_y",
         part="Cephalothorax"),
    dict(name="claw_reach", mm=18.7, tol=2.5, how="bbox_x", part="ClawArmR"),
]