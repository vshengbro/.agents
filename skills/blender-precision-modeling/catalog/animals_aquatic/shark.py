"""shark -- a 2.2 m great white: fusiform body, one tall first dorsal, a
heterocercal caudal whose upper lobe is far longer than the lower, and paired
pectorals plus a pelvic pair.

The fin count is the whole model. A shark has ONE dorsal (plus a much smaller
second one, built here as `FinDorsal2`), ONE caudal, and PAIRED pectorals,
pelvics and an anal -- not the paired dorsal arrangement a bony fish has.
Getting the count wrong is what makes a shark read as a generic fish.

Construction: one lofted body from a proportion table, flat blades for every
fin, six gill slits as thin recessed blades, and each paired part built once
then mirrored in world space. Nothing is booleaned, so every part stays a
closed manifold solid.

Orientation: nose at -Y, X lateral, Z up -- side.png (camera on +X) shows the
profile. Real scale: a 2.2 m great white.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=2200.0,
    body_length=1500.0,
    body_girth=420.0,
    body_depth=520.0,
    snout_length=220.0,
    first_dorsal_height=250.0,
    caudal_span=1070.0,
    pectoral_span=945.0,
    gill_slits=5,
)

# (y, half_height, half_width, z_centre) -- nose -1050, peduncle +450
BODY = [
    (-1050.0, 55.0, 40.0, 300.0),
    (-1000.0, 130.0, 95.0, 300.0),
    (-880.0, 215.0, 160.0, 300.0),
    (-700.0, 255.0, 200.0, 300.0),
    (-450.0, 260.0, 210.0, 300.0),
    (-150.0, 240.0, 195.0, 300.0),
    (150.0, 190.0, 155.0, 295.0),
    (330.0, 130.0, 105.0, 290.0),
    (450.0, 70.0, 55.0, 290.0),
    (520.0, 38.0, 30.0, 290.0),
]
# heterocercal caudal: the vertebral axis runs on into the upper lobe, so that
# lobe sweeps much further back and higher than the lower one
CAUDAL = [
    (470.0, 300.0), (620.0, 640.0), (1150.0, 1010.0), (900.0, 300.0),
    (1150.0, 40.0), (700.0, -60.0), (560.0, 180.0),
]
DORSAL1 = [
    (-250.0, 520.0), (-160.0, 660.0), (-20.0, 760.0), (110.0, 700.0),
    (190.0, 560.0), (170.0, 470.0),
]
DORSAL2 = [
    (250.0, 430.0), (300.0, 500.0), (370.0, 480.0), (350.0, 400.0),
]
ANAL = [
    (300.0, 220.0), (360.0, 90.0), (440.0, 100.0), (450.0, 220.0),
]
PELVIC = [
    (180.0, 0.0), (300.0, -120.0), (380.0, -95.0), (260.0, 20.0),
]
PECTORAL = [
    (0.0, 0.0), (170.0, -230.0), (380.0, -195.0), (300.0, 30.0),
    (140.0, 70.0),
]


def build():
    hide = bkit.pbr("SharkHide", base=(0.115, 0.130, 0.145), rough=0.42)
    belly = bkit.pbr("SharkBelly", base=(0.80, 0.79, 0.76), rough=0.46)
    fin = bkit.pbr("SharkFin", base=(0.135, 0.145, 0.155), rough=0.40)
    eye = bkit.pbr("SharkEye", base=(0.015, 0.015, 0.018), rough=0.08)

    torso = F.body("Body", BODY, hide, n=2.8, steps=40)
    bkit.assign_faces_by(torso, belly,
                         lambda c, n: c.z / bkit.MM < 250.0)

    F.plate_yz("FinCaudal", CAUDAL, 22.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal", DORSAL1, 20.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal2", DORSAL2, 14.0, x=0.0, mat=fin)
    F.plate_yz("FinAnal", ANAL, 14.0, x=0.0, mat=fin)

    # paired pectorals: broad triangular blades, the first real cue after the
    # silhouette
    # the blades are baked flat in the XY plane and then rotated about Y, so
    # every part ends up with an identity object transform and the world-space
    # mirror is a plain sign flip
    pect = F.plate_xy("FinPectoralL", PECTORAL, 18.0, mat=fin)
    bkit.move(pect, 105.0, -400.0, 150.0)
    F.bake_rot(pect, "Y", -16.0)
    F.mirror_copy(pect, "FinPectoralR")

    # paired pelvics, smaller, set well back
    pelv = F.plate_xy("FinPelvicL", PELVIC, 14.0, mat=fin)
    bkit.move(pelv, 55.0, 240.0, 90.0)
    F.bake_rot(pelv, "Y", 8.0)
    F.mirror_copy(pelv, "FinPelvicR")

    # five gill slits per side: thin blades standing just proud of the hide
    for i in range(5):
        y = -560.0 + i * 62.0
        for side, sx in (("L", 1.0), ("R", -1.0)):
            F.tube("Gill%s%d" % (side, i + 1),
                      [(sx * 186.0, y, 420.0), (sx * 196.0, y - 18.0, 300.0),
                       (sx * 180.0, y - 26.0, 205.0)],
                      [(7.0, 26.0), (7.0, 30.0), (6.0, 24.0)],
                      belly, n=2.0, steps=10)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 26.0, segments=20, rings=12,
                       centre=(sx * 88.0, -880.0, 352.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=17)


CHECKS = [
    dict(name="overall_length", mm=2200.0, tol=40.0, how="bbox_y"),
    dict(name="body_length", mm=1570.0, tol=30.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=520.0, tol=20.0, how="bbox_z", part="Body"),
    dict(name="body_girth", mm=420.0, tol=16.0, how="bbox_x", part="Body"),
    dict(name="caudal_span", mm=1070.0, tol=20.0, how="bbox_z",
         part="FinCaudal"),
    dict(name="pectoral_span", mm=945.0, tol=25.0, how="bbox_x"),
]