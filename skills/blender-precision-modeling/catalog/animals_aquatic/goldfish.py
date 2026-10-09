"""goldfish -- a 58 mm fancy goldfish: deep laterally-compressed body, twin-lobed
flowing caudal, tall dorsal and anal fins, paired pectorals and pelvics.

The species cue is proportion, not decoration: a goldfish is roughly as deep as
it is long in the body proper, where a trout is a cylinder. So the body table
below reaches a half-height of 13 mm on a 46 mm body, and the caudal plus the
flowing dorsal are what push the overall length past the body length.

Orientation: nose at -Y, world X lateral, Z up -- the catalog's fixed side view
puts the camera on +X, so the fish is built along Y and side.png shows a
silhouette. Every part is its own closed solid, so nothing is booleaned.

A fancy goldfish is around 58 mm long; the catalog class is `tiny`, whose band
tops out at 60 mm on the long axis, so this is a young fish at real scale.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

# --- real-world dimensions, millimetres -------------------------------------
SPEC = dict(
    overall_length=58.0,
    body_length=46.0,
    body_depth=26.0,
    body_width=14.0,
    caudal_span=30.0,
    dorsal_height=15.0,
    eye_diameter=3.2,
)

# (y, half_height, half_width, z_centre) -- nose at y=-29, peduncle at y=+17
BODY = [
    (-29.0, 2.0, 1.2, 20.0),
    (-26.5, 5.2, 2.6, 20.0),
    (-22.0, 9.4, 5.0, 20.0),
    (-15.0, 12.6, 7.0, 20.0),
    (-6.0, 13.0, 7.0, 20.0),
    (3.0, 11.0, 5.6, 19.8),
    (10.0, 7.4, 3.6, 19.4),
    (14.5, 4.2, 2.2, 19.0),
    (17.0, 2.4, 1.5, 19.0),
]
# twin-lobed caudal: two streamers trailing from a short peduncle
CAUDAL = [
    (16.0, 19.0), (20.0, 30.0), (29.0, 33.5), (26.5, 19.0),
    (29.0, 4.5), (20.0, 8.0),
]
# dorsal runs from mid-back up and back over the peduncle
DORSAL = [
    (-14.0, 31.0), (-9.0, 44.0), (2.0, 43.0), (10.0, 33.0), (14.0, 28.5),
]
# the anal fin's ROOT must sit INSIDE the body, or the fin renders as a
# rectangle floating below the fish: the belly line at these stations is
# around z = 12-16, so the root is authored at z = 17
ANAL = [
    (1.0, 17.0), (5.0, 1.0), (12.0, 2.0), (14.0, 15.0),
]
PECTORAL = [
    (0.0, 0.0), (11.0, -7.0), (13.0, -1.0), (4.0, 4.0),
]


def build():
    scale = bkit.pbr("GoldfishBody", base=(0.86, 0.36, 0.045), rough=0.34,
                     coat=0.35)
    deep = bkit.pbr("GoldfishDeep", base=(0.72, 0.20, 0.02), rough=0.36)
    fin = bkit.pbr("GoldfishFin", base=(0.94, 0.50, 0.08), rough=0.26,
                   alpha=0.92)
    eye = bkit.pbr("GoldfishEye", base=(0.02, 0.02, 0.025), rough=0.10)

    torso = F.body("Body", BODY, scale, n=2.6, steps=36)
    # a second material on the ONE body solid: a separate inner shell would
    # z-fight with the real surface
    bkit.assign_faces_by(torso, deep,
                         lambda c, n: c.z / bkit.MM > 20.0 + 4.0)

    F.plate_yz("FinCaudal", CAUDAL, 1.6, x=0.0, mat=fin)
    F.plate_yz("FinDorsal", DORSAL, 1.6, x=0.0, mat=fin)
    F.plate_yz("FinAnal", ANAL, 1.4, x=0.0, mat=fin)

    # paired pectorals: one blade authored on +X, then its exact world mirror
    pect = F.plate_xy("FinPectoralL", PECTORAL, 1.3, z=0.0, mat=fin)
    bkit.move(pect, 5.0, -17.0, 14.0)
    F.mirror_copy(pect, "FinPectoralR")

    # paired pelvics, smaller and lower
    pelv = F.plate_xy("FinPelvicL", [(0.0, 0.0), (8.0, -4.0), (9.0, 1.0),
                                    (2.0, 4.0)], 1.1, z=0.0, mat=fin)
    bkit.move(pelv, 3.2, 0.0, 13.0)
    F.mirror_copy(pelv, "FinPelvicR")

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 1.6, segments=20, rings=10,
                       centre=(sx * 4.2, -25.0, 23.5), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="overall_length", mm=58.0, tol=1.2, how="bbox_y"),
    dict(name="body_length", mm=46.0, tol=0.6, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=26.0, tol=0.6, how="bbox_z", part="Body"),
    dict(name="body_width", mm=14.0, tol=0.4, how="bbox_x", part="Body"),
    dict(name="eye_diameter", mm=3.2, tol=0.2, how="bbox_x", part="EyeL"),
]