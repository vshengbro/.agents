"""
kettlebell -- 8 kg cast bell, 130 mm across the flank and 158 mm overall, with
a 76 mm handle opening.

Two solids, deliberately. The handle is an arc_torus whose centreline radius
(50 mm) is smaller than the bell's flank radius (65 mm), so both ends finish
3 mm INSIDE the wall and their caps are invisible. Joining the meshes (rather
than booleaning them) gives a clean two-shell assembly: no coincident faces,
no z-fight on the visible surface, zero non-manifold edges.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    height=158.0,             # overall, crown of the handle included
    body_height=116.0,
    body_diameter=130.0,
    base_diameter=110.0,
    handle_opening=76.0,
    handle_wall=24.0,
    handle_arc_radius=50.0,
)

R = SPEC["body_diameter"] / 2.0        # 65
RA = SPEC["handle_arc_radius"]         # 50
RT = SPEC["handle_wall"] / 2.0         # 12
ARC_Z = 96.0                           # arc centre height
TOP = ARC_Z + RA + RT                  # 158

CHECKS = [
    dict(name="body_diameter", mm=130.0, tol=0.5, how="diameter",
         part="KettlebellBody"),
    dict(name="body_height", mm=116.0, tol=0.5, how="bbox_z",
         part="KettlebellBody"),
    dict(name="overall_height", mm=158.0, tol=0.5, how="bbox_z"),
]


def build():
    cast = bkit.pbr("KettlebellCast", base=(0.34, 0.35, 0.37), rough=0.48)
    paint = bkit.pbr("BellPaint", base=(0.10, 0.12, 0.15), rough=0.34)

    # ---- bell: flat base, straight flank, domed shoulder ------------------
    prof = [
        (0.0, 0.0), (55.0, 0.0), (62.0, 2.0), (65.0, 10.0), (65.0, 92.0),
        (64.0, 100.0), (58.0, 108.0), (42.0, 113.0), (0.0, 116.0),
    ]
    body = bkit.lathe("KettlebellBody", prof, segments=96, mat=paint)
    # the cast base is left bare, exactly as a real bell is finished
    bkit.assign_faces_by(body, cast, lambda c, n: c.z / bkit.MM < 11.0)

    # ---- handle: a 180 degree arch, both ends buried in the flank ---------
    handle = bkit.arc_torus("KettlebellHandle", RA, RT, 0.0, 180.0,
                            centre=(0.0, 0.0, ARC_Z), plane="XZ",
                            seg_major=72, seg_minor=28, mat=cast)
    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
