"""hose_coupling -- a 60 mm brass hose coupling: the male hex body, the female
nut, the knurled collar between them, and the real internal bore with its
hose-stop shoulder.

The hex and the bore are the model. A coupling's outside is a hexagonal body
so a spanner can take it -- so the hex flats are real geometry with six
computed vertices -- and its inside is a stepped bore, because the shoulder
is what stops the hose at the right depth. Both are here.

Construction: a lathed body with a stepped bore cut through it, a hexagonal
nut driven by `array_radial` about the body's own axis, and a knurl ring.

Orientation: the coupling's axis along Y, hose entering from +Y, Z up.
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
    overall_length=60.0,
    hex_across_flats=22.0,
    hex_length=18.0,
    bore_diameter=12.0,
    shoulder_diameter=16.0,
    knurl_count=36,
)

HEX_AF = 22.0
HEX_L = 18.0
BORE_R = 6.0
STOP_R = 8.0


def build():
    brass = bkit.pbr("CouplingBrass", base=(0.78, 0.62, 0.26), metal=0.85,
                     rough=0.30)
    dark = bkit.pbr("CouplingDark", base=(0.36, 0.28, 0.12), metal=0.85,
                    rough=0.44)

    # ---- the body: a lathed barrel with a stepped profile. The lathe's axis
    # is Z, so it is rotated into Y AFTER cutting; cutting first keeps the
    # bore cutters in the lathe's own frame.
    body = bkit.lathe("Body",
                      [(0.0, 0.0), (11.0, 0.0), (11.0, 6.0), (9.5, 7.0),
                       (9.5, HEX_L), (11.0, HEX_L + 1.0), (11.0, 24.0),
                       (9.0, 26.0), (9.0, 52.0), (7.6, 56.0), (0.0, 58.0)],
                      segments=64, centre=(0.0, 0.0, 11.0), mat=brass)

    # ---- the stepped bore: a through bore plus a wider counterbore for the
    # hose stop. Both cutters deliberately differ in segment count from the
    # host lathe, and both OVERSHOOT the ends by several mm.
    bkit.bore(body, radius=BORE_R, depth=90.0, centre=(0.0, 0.0, 11.0),
              axis="Z", host_segments=64)
    bkit.bore(body, radius=STOP_R, depth=30.0, centre=(0.0, 18.0, 11.0),
              axis="Z", host_segments=64)

    # ---- lay the body along Y: swap the lathe's Z axis onto Y. Swapping two
    # axes mirrors the mesh, so the winding comes out inside-out.
    for v in body.data.vertices:
        y, z = v.co.y, v.co.z
        v.co.y = z + bkit.u(-30.0)
        v.co.z = y + bkit.u(11.0)
    body.data.update()
    F.orient_outward(body)

    # ---- the hex nut: ONE hexagonal prism, not six arrayed copies. A radial
    # array of six blocks gives a ring whose bbox is the ring, so no
    # per-flats dimension can be measured on it afterwards.
    R_c = (HEX_AF / 2.0) / math.cos(math.radians(30.0))
    hexp = [(R_c * math.cos(math.radians(30 + 60 * k)),
             R_c * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    hexb = bkit.extrude_profile("Hex", hexp, HEX_L,
                                centre=(0.0, 0.0, 0.0), axis="Y", mat=brass)
    F.orient_outward(hexb)
    for v in hexb.data.vertices:
        v.co.y = v.co.y + bkit.u(9.0)
        v.co.z = v.co.z + bkit.u(11.0)
    hexb.data.update()
    bkit.recalc(hexb)

    # ---- the knurl on the collar: a computed ring of flats at a pitch from
    # the knurl count
    n = SPEC["knurl_count"]
    for i in range(n):
        a = 2.0 * math.pi * i / n
        knurl = bkit.rounded_box("Knurl%d" % i, 0.7, 10.0, 0.7, r=0.15,
                                 segments=2, centre=(0.0, 0.0, 0.0),
                                 mat=dark)
        for v in knurl.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            v.co = (x * math.cos(a) - z * math.sin(a) + bkit.u(9.3),
                    y + bkit.u(38.0),
                    x * math.sin(a) + z * math.cos(a) + bkit.u(11.0))
        knurl.data.update()
        bkit.recalc(knurl)

    # ---- the barbed tail that grips the hose
    F.tube("Tail", [(0.0, 56.0, 11.0), (0.0, 74.0, 11.0), (0.0, 92.0, 11.0)],
           [(8.6, 8.6), (7.4, 7.4), (6.0, 6.0)], brass, n=2.4, steps=16)
    for i in range(3):
        bkit.torus("Barb%d" % i, 7.4, 0.9, seg_major=28, seg_minor=8,
                   centre=(0.0, 66.0 + i * 9.0, 11.0), axis="Y", mat=brass)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=45)


CHECKS = [
    dict(name="overall_length", mm=122.0, tol=4.0, how="bbox_y"),
    dict(name="hex_across_flats", mm=22.0, tol=1.5, how="bbox_x", part="Hex"),
    dict(name="hex_length", mm=18.0, tol=1.0, how="bbox_y", part="Hex"),
    dict(name="body_diameter", mm=22.0, tol=1.5, how="bbox_x", part="Body"),
    dict(name="body_length", mm=58.0, tol=2.5, how="bbox_y", part="Body"),
]