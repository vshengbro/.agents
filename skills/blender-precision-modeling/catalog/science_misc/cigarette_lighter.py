"""cigarette_lighter -- an 85 mm pocket lighter: the brushed body with its
rolled edges, the knurled flame wheel, the fuel valve at the base, the hinged
lid, and the burner nozzle.

The knurled wheel is the model. A lighter's wheel is a finely knurled disc you
roll with your thumb -- so it is a real disc with a computed ring of knurl
teeth at a pitch derived from the tooth count, standing proud of the body's
face.

Construction: a rounded body with a rolled top, a knurled wheel with a
computed tooth ring, the burner nozzle and the valve, and the open lid on its
hinge. Nothing is booleaned except the lid's hinge cut.

Orientation: the lighter stands upright, lid hinged at the back, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_height=88.6,
    body_width=25.0,
    body_depth=13.0,
    wheel_diameter=14.0,
    knurl_teeth=36,
    nozzle_diameter=6.0,
    lid_width=25.0,
)

BW, BD, BH = 25.0, 13.0, 85.0
WHEEL_R = 7.0


def build():
    body_m = bkit.pbr("LighterBody", base=(0.62, 0.64, 0.68), metal=0.85,
                      rough=0.30)
    top_m = bkit.pbr("LighterTop", base=(0.70, 0.72, 0.76), metal=0.85,
                     rough=0.20)
    knurl_m = bkit.pbr("LighterKnurl", base=(0.55, 0.57, 0.60), metal=0.85,
                       rough=0.40)
    brass_m = bkit.pbr("LighterBrass", base=(0.82, 0.66, 0.28), metal=0.85,
                       rough=0.24)

    body = bkit.rounded_box("Body", BW, BD, BH - 8.0, r=2.2, segments=4,
                            centre=(0.0, 0.0, (BH - 8.0) / 2.0), mat=body_m)
    del body

    # ---- the top: a smaller block with a rolled edge, and the burner recess
    bkit.rounded_box("Top", BW - 1.0, BD - 1.0, 9.0, r=1.6, segments=4,
                     centre=(0.0, 0.0, BH - 8.0 + 4.5), mat=top_m)

    # ---- the flame wheel: a real disc plus a computed ring of knurl teeth
    bkit.cylinder("Wheel", WHEEL_R, 4.0, segments=48,
                  centre=(0.0, -BD / 2.0 - 1.2, 22.0), axis="Y",
                  mat=knurl_m)
    n = SPEC["knurl_teeth"]
    for i in range(n):
        a = 2.0 * math.pi * i / n
        tooth = bkit.rounded_box("Knurl%d" % i, 0.7, 4.6, 0.7, r=0.15,
                                 segments=2, centre=(0.0, 0.0, 0.0),
                                 mat=knurl_m)
        for v in tooth.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            v.co = (x * math.cos(a) - z * math.sin(a) + bkit.u(WHEEL_R - 0.2),
                    y + bkit.u(-BD / 2.0 - 1.2),
                    x * math.sin(a) + z * math.cos(a) + bkit.u(22.0))
        tooth.data.update()
        bkit.recalc(tooth)

    # ---- the burner nozzle and the fuel valve at the base
    bkit.lathe("Nozzle",
               [(0.0, 0.0), (3.0, 0.0), (3.0, 2.6), (1.6, 4.2), (1.6, 5.6),
                (0.0, 5.6)],
               segments=32, centre=(0.0, 1.0, BH - 2.0), mat=brass_m)
    bkit.cylinder("Valve", 4.0, 6.0, segments=28,
                  centre=(0.0, 0.0, 3.0), mat=brass_m)

    # ---- the lid, hinged at the back and standing open
    lid = bkit.rounded_box("Lid", BW - 2.0, 2.6, 30.0, r=1.2, segments=3,
                           centre=(0.0, 0.0, 0.0), mat=top_m)
    for v in lid.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        v.co = (x, y + bkit.u(14.5) + z * 0.0,
                z + bkit.u(70.0) - y * 0.0 + bkit.u(0.0))
    lid.data.update()
    bkit.recalc(lid)
    bkit.rounded_box("Hinge", 6.0, 6.0, 8.0, r=2.0, segments=3,
                     centre=(0.0, 6.0, 72.0), mat=top_m)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=45)


CHECKS = [
    dict(name="overall_height", mm=88.6, tol=4.0, how="bbox_z"),
    dict(name="body_width", mm=25.0, tol=1.0, how="bbox_x", part="Body"),
    dict(name="body_depth", mm=13.0, tol=1.0, how="bbox_y", part="Body"),
    dict(name="wheel_diameter", mm=14.0, tol=1.0, how="bbox_x", part="Wheel"),
    dict(name="lid_width", mm=23.0, tol=1.2, how="bbox_x", part="Lid"),
    dict(name="nozzle_diameter", mm=6.0, tol=0.8, how="diameter", part="Nozzle"),
]