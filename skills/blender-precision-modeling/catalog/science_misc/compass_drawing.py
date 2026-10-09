"""compass_drawing -- a 160 mm drawing compass: two tapered legs joined at a
hinge boss, a knurled adjustment wheel, a pencil lead on one leg and a needle
point on the other, and a carrying handle on the head.

The hinge is the model. A compass is two legs that pivot about a screw -- so
the hinge is a real boss with a bore through it, the legs taper toward their
points, and the wheel sits in the boss where the screw passes. Both points
touch z=0, which is what a compass does when it is set to a radius.

Construction: two swept tapered legs meeting at the hinge, a lathed hinge
boss with a bore cut through it, a knurled wheel, and the two points. Nothing
is booleaned except the hinge bore.

Orientation: the hinge at the top (+Z), both points on z=0, legs splayed in
the Y-Z plane so the compass stands as it would when in use.
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
    overall_height=187.0,
    leg_span=106.0,
    leg_diameter=8.0,
    hinge_diameter=14.0,
    wheel_diameter=12.0,
    point_length=16.0,
)

H = 160.0
LEG_R = 4.0


def build():
    steel = bkit.pbr("CompassSteel", base=(0.70, 0.72, 0.76), metal=0.85,
                     rough=0.26)
    dark = bkit.pbr("CompassDark", base=(0.18, 0.19, 0.21), metal=0.85,
                    rough=0.36)
    brass = bkit.pbr("CompassBrass", base=(0.82, 0.66, 0.28), metal=0.85,
                     rough=0.26)
    wood = bkit.pbr("CompassWood", base=(0.38, 0.22, 0.10), rough=0.50)
    lead = bkit.pbr("CompassLead", base=(0.30, 0.30, 0.32), metal=0.6,
                    rough=0.36)

    # ---- the hinge boss, bored through for the screw
    boss = bkit.lathe("Hinge",
                      [(0.0, -6.0), (7.0, -6.0), (7.0, -4.4), (4.4, -3.4),
                       (4.4, 3.4), (7.0, 4.4), (7.0, 6.0), (0.0, 6.0)],
                      segments=48, centre=(0.0, 0.0, H - 8.0), mat=dark)
    boss = bpy.data.objects["Hinge"]
    bkit.bore(boss, radius=1.6, depth=30.0, centre=(0.0, 0.0, H - 8.0),
              axis="Y", host_segments=48)

    # ---- the two legs, tapered from the hinge to their points
    spread = math.radians(19.0)
    for side, sy in (("A", 1.0), ("B", -1.0)):
        path = []
        rad = []
        for i in range(6):
            t = i / 5.0
            y = sy * (math.sin(spread) * (H - 8.0) * t)
            z = (H - 8.0) - math.cos(spread) * (H - 8.0) * t
            path.append((0.0, y, z))
            r = LEG_R * (1.0 - 0.78 * t)
            rad.append((r, r))
        rings = []
        for i, p in enumerate(path):
            ring = []
            w, h = rad[i]
            for j in range(20):
                a = 2.0 * math.pi * j / 20.0
                ring.append((p[0] + w * math.cos(a), p[1] + 1.6 * math.sin(a),
                             p[2] + h * math.sin(a)))
            rings.append(ring)
        leg = bkit.loft("Leg%s" % side, rings, mat=steel, smooth=True)
        bkit.recalc(leg)

    # ---- the adjustment wheel in the hinge
    bkit.cylinder("Wheel", 6.0, 7.0, segments=40, centre=(0.0, 0.0, H - 8.0),
                  axis="Y", mat=brass)
    bkit.cylinder("Screw", 1.5, 16.0, segments=20, centre=(0.0, 0.0, H - 8.0),
                  axis="Y", mat=steel)
    n = 16
    for i in range(n):
        a = 2.0 * math.pi * i / n
        tooth = bkit.rounded_box("Knurl%d" % i, 0.6, 7.6, 0.6, r=0.12,
                                 segments=2, centre=(0.0, 0.0, 0.0),
                                 mat=brass)
        for v in tooth.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            # the wheel's axis is Y, so the teeth stand on the rim in X-Z and
            # stay centred on y = 0
            v.co = (x * math.cos(a) - z * math.sin(a) + bkit.u(5.9),
                    y,
                    x * math.sin(a) + z * math.cos(a) + bkit.u(H - 8.0))
        tooth.data.update()
        bkit.recalc(tooth)

    # ---- the two points: a steel needle and a pencil lead, both on z=0
    F.cone_between("Needle", (0.0, math.sin(spread) * (H - 8.0), 0.0),
                      (0.0, math.sin(spread) * (H - 8.0) + 1.4,
                       -SPEC["point_length"]),
                      2.0, 0.2, seg=12, mat=steel)
    bkit.lathe("Pencil",
               [(0.0, 0.0), (4.6, 0.0), (4.6, 6.0), (2.0, 20.0), (0.0, 24.0)],
               segments=32, centre=(0.0, 0.0, 0.0), mat=wood)
    # the pencil hangs along the other leg's axis, so its lathe profile is
    # tipped over by the leg's spread before it is re-seated
    pen = bpy.data.objects["Pencil"]
    ty = -math.sin(spread) * (H - 8.0)
    for v in pen.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        v.co = (x, y + bkit.u(ty - z * math.tan(spread)), z)
    pen.data.update()
    bkit.recalc(pen)
    F.cone_between("Lead",
                      (0.0, -math.sin(spread) * (H - 8.0) - 1.2, 8.0),
                      (0.0, -math.sin(spread) * (H - 8.0) - 2.4, 0.0),
                      1.8, 0.2, seg=10, mat=lead)

    # ---- the carrying handle above the hinge
    bkit.rounded_box("Handle", 10.0, 5.0, 14.0, r=2.0, segments=4,
                     centre=(0.0, 0.0, H + 4.0), mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=30)


CHECKS = [
    dict(name="overall_height", mm=187.0, tol=6.0, how="bbox_z"),
    dict(name="leg_span", mm=106.0, tol=8.0, how="bbox_y"),
    dict(name="hinge_diameter", mm=14.0, tol=1.2, how="bbox_x", part="Hinge"),
    dict(name="wheel_diameter", mm=12.0, tol=1.2, how="bbox_x", part="Wheel"),
    dict(name="leg_diameter", mm=8.0, tol=1.0, how="bbox_x", part="LegA"),
]