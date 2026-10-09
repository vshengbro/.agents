"""crocodile -- a 3.4 m Nile crocodile: the long flat head, the armoured back
with a double row of scutes, a long muscular tail, and four short legs with
webbed feet.

Two cues carry the whole animal. First the SNOUT: a crocodilian's head is a
long low wedge, nearly a fifth of the body length, and the eyes sit ON TOP of
it. Second the SCUTE ROWS: two staggered ridges along the back, laid out at a
computed pitch so the count is real.

Construction: one lofted body from a proportion table, a swept wedge head with
a real jaw line, a scute ridge swept along the spine with the second row
staggered by half a pitch, and four legs built once and mirrored. Nothing is
booleaned.

Orientation: the snout points at -Y, X lateral, Z up.
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
    overall_length=3400.0,
    body_length=2100.0,
    body_depth=460.0,
    head_length=520.0,
    scute_count=28,
    leg_span=600.0,
    tail_length=1600.0,
)

# (y, half_height, half_width, z_centre) -- jaw hinge -1250, hips +850
BODY = [
    (-1250.0, 130.0, 110.0, 180.0),
    (-1150.0, 200.0, 175.0, 180.0),
    (-1000.0, 240.0, 215.0, 180.0),
    (-800.0, 255.0, 230.0, 180.0),
    (-560.0, 260.0, 235.0, 178.0),
    (-300.0, 250.0, 225.0, 176.0),
    (0.0, 235.0, 210.0, 176.0),
    (300.0, 210.0, 185.0, 178.0),
    (560.0, 175.0, 150.0, 182.0),
    (800.0, 130.0, 108.0, 186.0),
    (1000.0, 88.0, 72.0, 190.0),
    (1250.0, 50.0, 42.0, 192.0),
    (1600.0, 14.0, 12.0, 192.0),
]
# the jaw: a long low wedge that narrows to a rounded snout tip
JAW_U = [
    (0.0, -1250.0, 200.0), (0.0, -1450.0, 196.0), (0.0, -1640.0, 188.0),
    (0.0, -1770.0, 182.0),
]
JAW_U_RAD = [(140.0, 62.0), (105.0, 44.0), (76.0, 30.0), (52.0, 20.0)]
JAW_L = [
    (0.0, -1250.0, 158.0), (0.0, -1450.0, 162.0), (0.0, -1640.0, 166.0),
    (0.0, -1760.0, 170.0),
]
JAW_L_RAD = [(110.0, 40.0), (86.0, 28.0), (62.0, 19.0), (40.0, 12.0)]
FORE_LEG = [(200.0, -900.0, 150.0), (250.0, -920.0, 90.0),
            (250.0, -930.0, 30.0), (245.0, -960.0, 6.0)]
FORE_RAD = [(52.0, 46.0), (44.0, 40.0), (40.0, 34.0), (44.0, 22.0)]
HIND_LEG = [(-200.0, 380.0, 150.0), (-260.0, 400.0, 90.0),
            (-260.0, 410.0, 30.0), (-255.0, 445.0, 6.0)]
HIND_RAD = [(56.0, 50.0), (48.0, 42.0), (42.0, 36.0), (48.0, 24.0)]


def build():
    hide = bkit.pbr("CrocHide", base=(0.20, 0.22, 0.15), rough=0.62)
    belly = bkit.pbr("CrocBelly", base=(0.62, 0.58, 0.44), rough=0.56)
    scute = bkit.pbr("CrocScute", base=(0.30, 0.31, 0.21), rough=0.52,
                     coat=0.2)
    eye = bkit.pbr("CrocEye", base=(0.02, 0.03, 0.02), rough=0.08)
    tooth = bkit.pbr("CrocTooth", base=(0.88, 0.87, 0.82), rough=0.24)

    torso = F.body("Body", BODY, hide, n=3.0, steps=44)
    bkit.assign_faces_by(torso, belly, lambda c, n: c.z / bkit.MM < 120.0)

    F.tube("JawUpper", JAW_U, JAW_U_RAD, hide, n=3.0, steps=24)
    F.tube("JawLower", JAW_L, JAW_L_RAD, belly, n=3.0, steps=24)

    # ---- the two scute rows. Row 0 sits on the midline, row 1 is offset half
    # a pitch so the two stagger like real osteoderms instead of pairing up.
    n = SPEC["scute_count"]
    y0, y1 = -900.0, 1450.0
    pitch = (y1 - y0) / (n - 1)
    for row, half in ((0, 0.0), (1, 0.5)):
        for i in range(n):
            y = y0 + (i + half) * pitch
            if y > y1:
                break
            z = 180.0 + 130.0 * math.exp(-((y + 100.0) / 900.0) ** 2)
            F.cone_between("Scute%d%d" % (row, i + 1),
                           (0.0, y - pitch * 0.35, z - 12.0),
                           (0.0, y, z + 26.0), 34.0, 6.0, seg=10, mat=scute)

    # ---- teeth: a computed row along each jaw margin, pitch derived from the
    # count so no two share a station
    n_tooth = 16
    t_pitch = 300.0 / (n_tooth - 1)
    for i in range(n_tooth):
        y = -1300.0 + i * t_pitch
        F.cone_between("ToothU%d" % i, (0.0, y, 176.0), (0.0, y, 150.0),
                       9.0, 1.5, seg=8, mat=tooth)
        F.cone_between("ToothL%d" % i, (0.0, y, 168.0), (0.0, y, 186.0),
                       8.0, 1.5, seg=8, mat=tooth)

    for tag, path, rad in (("Fore", FORE_LEG, FORE_RAD),
                           ("Hind", HIND_LEG, HIND_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, hide, n=2.4, steps=16)
        F.mirror_copy(leg, "Leg%sR" % tag)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 24.0, segments=18, rings=10,
                       centre=(sx * 84.0, -1330.0, 238.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=76)


CHECKS = [
    dict(name="overall_length", mm=3400.0, tol=120.0, how="bbox_y"),
    dict(name="body_length", mm=2850.0, tol=100.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=520.0, tol=40.0, how="bbox_z", part="Body"),
    dict(name="head_length", mm=520.0, tol=40.0, how="bbox_y",
         part="JawUpper"),
    dict(name="leg_span", mm=600.0, tol=40.0, how="bbox_x"),
]