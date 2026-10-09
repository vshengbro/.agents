"""salmon -- a 620 mm Atlantic salmon: fusiform body, adipose fin (the small
"second dorsal" behind the dorsal), forked caudal, and a kype -- the hooked
lower jaw of the male -- which is the species cue most people miss.

Construction: one lofted body from a proportion table, flat blades for the
dorsal / adipose / anal / pelvic / caudal fins, a paired pectoral mirrored in
world space, and gill cover / lateral line / flank spots as a second material
on the ONE body solid rather than as extra shells that would z-fight.

Orientation: nose at -Y, X lateral, Z up, so side.png shows the profile.
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
    overall_length=620.0,
    body_length=460.0,
    body_depth=145.0,
    body_width=84.0,
    caudal_span=190.0,
    adipose_height=28.0,
    kype_height=34.0,
)

# (y, half_height, half_width, z_centre) -- nose -290, peduncle +170
BODY = [
    (-290.0, 9.0, 6.0, 150.0),
    (-275.0, 32.0, 22.0, 150.0),
    (-245.0, 56.0, 34.0, 150.0),
    (-195.0, 70.0, 42.0, 150.0),
    (-130.0, 72.5, 40.0, 150.0),
    (-60.0, 65.0, 35.0, 148.0),
    (0.0, 52.0, 28.0, 146.0),
    (60.0, 36.0, 20.0, 144.0),
    (120.0, 24.0, 14.0, 142.0),
    (170.0, 14.0, 9.0, 142.0),
]
# forked caudal: two equal lobes with a real notch between them
CAUDAL = [
    (155.0, 142.0), (215.0, 235.0), (330.0, 242.0), (255.0, 142.0),
    (330.0, 42.0), (215.0, 49.0),
]
DORSAL = [
    (-95.0, 210.0), (-75.0, 268.0), (-15.0, 268.0), (5.0, 200.0),
    (-35.0, 200.0),
]
# the adipose fin: small, fleshy, and always BETWEEN the dorsal and the tail
ADIPOSE = [
    (110.0, 168.0), (120.0, 196.0), (145.0, 186.0), (140.0, 166.0),
]
ANAL = [
    (40.0, 118.0), (60.0, 66.0), (120.0, 74.0), (110.0, 116.0),
]
PELVIC = [
    (0.0, 0.0), (46.0, -34.0), (70.0, -24.0), (48.0, 10.0),
]
PECTORAL = [
    (0.0, 0.0), (66.0, -48.0), (104.0, -34.0), (72.0, 16.0),
]


def build():
    silver = bkit.pbr("SalmonSilver", base=(0.42, 0.45, 0.48), rough=0.30,
                      metal=0.15, coat=0.3)
    back = bkit.pbr("SalmonBack", base=(0.12, 0.17, 0.20), rough=0.36)
    belly = bkit.pbr("SalmonBelly", base=(0.80, 0.79, 0.76), rough=0.42)
    fin = bkit.pbr("SalmonFin", base=(0.20, 0.24, 0.26), rough=0.34)
    spot = bkit.pbr("SalmonSpot", base=(0.06, 0.07, 0.08), rough=0.42)
    eye = bkit.pbr("SalmonEye", base=(0.02, 0.02, 0.025), rough=0.08)

    torso = F.body("Body", BODY, silver, n=2.8, steps=40)
    bkit.assign_faces_by(torso, back,
                         lambda c, n: c.z / bkit.MM > 178.0)
    bkit.assign_faces_by(torso, belly,
                         lambda c, n: c.z / bkit.MM < 124.0)

    F.plate_yz("FinCaudal", CAUDAL, 9.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal", DORSAL, 8.0, x=0.0, mat=fin)
    F.plate_yz("FinAdipose", ADIPOSE, 7.0, x=0.0, mat=fin)
    F.plate_yz("FinAnal", ANAL, 7.0, x=0.0, mat=fin)

    pect = F.plate_xy("FinPectoralL", PECTORAL, 7.0, mat=fin)
    bkit.move(pect, 30.0, -175.0, 138.0)
    F.bake_rot(pect, "Y", -14.0)
    F.mirror_copy(pect, "FinPectoralR")

    pelv = F.plate_xy("FinPelvicL", PELVIC, 6.0, mat=fin)
    bkit.move(pelv, 20.0, -35.0, 118.0)
    F.bake_rot(pelv, "Y", 4.0)
    F.mirror_copy(pelv, "FinPelvicR")

    # ---- the kype: the male salmon's hooked lower jaw, a swept spur that
    # turns up under the snout. Missing it is why most "salmon" models read as
    # a trout.
    F.tube("Kype", [(-296.0, 4.0, 142.0), (-292.0, -2.0, 130.0),
                    (-282.0, -4.0, 122.0), (-272.0, -2.0, 128.0)],
           [(9.0, 8.0), (8.0, 9.0), (6.0, 8.0), (4.0, 5.0)],
           fin, n=2.4, steps=16)

    # ---- flank spots: a computed patch of small marks on the silver side.
    # grid_positions with an explicit pitch means no two spots share a
    # coordinate, and a spot per position keeps every one a closed solid.
    for (i, (x, y)) in enumerate(
            bkit.grid_positions(cols=4, rows=5, pitch_x=22.0, pitch_y=52.0)):
        if abs(y) > 190.0:
            continue
        for sx in (1.0, -1.0):
            z = 150.0 + ((i * 7) % 5) * 5.0 - 10.0
            bkit.uv_sphere("Spot%d%s" % (i, "LR"[sx > 0]), 5.0, segments=12,
                           rings=6, centre=(sx * 34.0, y - 160.0, z), mat=spot)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 12.0, segments=20, rings=10,
                       centre=(sx * 24.0, -258.0, 168.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=48)


CHECKS = [
    dict(name="overall_length", mm=620.0, tol=15.0, how="bbox_y"),
    dict(name="body_length", mm=460.0, tol=8.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=145.0, tol=6.0, how="bbox_z", part="Body"),
    dict(name="body_width", mm=84.0, tol=4.0, how="bbox_x", part="Body"),
    dict(name="caudal_span", mm=200.0, tol=8.0, how="bbox_z", part="FinCaudal"),
    dict(name="kype_height", mm=32.0, tol=3.0, how="bbox_z", part="Kype"),
]