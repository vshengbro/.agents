"""padlock_shackle -- a 40 mm padlock shackle: the hardened bow, the heel, and
the two shackle holes that meet the lock body.

The shackle holes are the model. A shackle is a bow whose two ends are bored so
they can drop into the lock body -- so the bores are real, cut with
`bkit.bore` so the cutters use host segments + 7 and never share a facet with
the shackle's own surface.

Construction: a swept bow with a real bend radius, the two bored ends, a screw
collar on one leg, and the lock body. The bow is one closed solid; nothing is
booleaned except the two shackle holes.

Orientation: the bow standing in the X-Z plane, the lock body below, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    shackle_outer_width=37.0,
    shackle_inner_width=15.0,
    shackle_height=34.5,
    leg_diameter=11.0,
    hole_diameter=8.0,
    body_width=38.0,
    body_height=24.0,
)

LEG_R = 5.5
OUT = 13.0          # shackle centreline radius
Y0 = 0.0


def shackle_path():
    """The shackle centreline: two straight legs and a semicircular top."""
    leg_bottom = 2.0
    pts = [(-OUT, Y0, leg_bottom)]
    pts.append((-OUT, Y0, 18.0))
    for k in range(1, 17):
        a = math.pi - math.pi * k / 16.0
        pts.append((OUT * math.cos(a), Y0, 18.0 + OUT * math.sin(a)))
    pts.append((OUT, Y0, leg_bottom))
    return pts


def build():
    steel = bkit.pbr("ShackleSteel", base=(0.72, 0.74, 0.78), metal=0.85,
                     rough=0.22)
    dark = bkit.pbr("ShackleDark", base=(0.20, 0.21, 0.23), metal=0.85,
                    rough=0.36)
    brass = bkit.pbr("ShackleBrass", base=(0.80, 0.64, 0.28), metal=0.85,
                     rough=0.28)

    path = shackle_path()
    rad = [(LEG_R, LEG_R)] * len(path)

    # ---- the bow, swept along the path as one closed solid
    rings = []
    m = len(path)
    for i, (px, py, pz) in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, m - 1)]
        t = [b[k] - a[k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        t = [c / tl for c in t]
        # the path lies in X-Z, so the ring's axes are Y and (t x Y)
        s = (0.0, 1.0, 0.0)
        v = [t[1] * s[2] - t[2] * s[1], t[2] * s[0] - t[0] * s[2],
             t[0] * s[1] - t[1] * s[0]]
        w, h = rad[i]
        ring = []
        for j in range(24):
            ang = 2.0 * math.pi * j / 24.0
            ring.append((px + s[0] * w * math.cos(ang) + v[0] * h * math.sin(ang),
                         py + s[1] * w * math.cos(ang) + v[1] * h * math.sin(ang),
                         pz + s[2] * w * math.cos(ang) + v[2] * h * math.sin(ang)))
        rings.append(ring)
    bow = bkit.loft("Shackle", rings, mat=steel, smooth=True)
    bkit.recalc(bow)

    # ---- the two shackle holes. `bkit.bore` picks host_segments + 7 on
    # purpose: a cutter sharing the host's segment count puts coincident
    # facets on both surfaces.
    bkit.bore(bow, radius=4.0, depth=30.0, centre=(-OUT, Y0, 2.0), axis="Z",
              host_segments=24)
    bkit.bore(bow, radius=4.0, depth=30.0, centre=(OUT, Y0, 2.0), axis="Z",
              host_segments=24)

    # ---- the screw collar on one leg
    bkit.lathe("Collar",
               [(0.0, 0.0), (6.4, 0.0), (6.4, 3.0), (5.6, 3.6), (0.0, 3.6)],
               segments=40, centre=(0.0, Y0, 0.0), mat=brass)
    collar = bpy.data.objects["Collar"]
    for v in collar.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        # mesh vertices are METRES: a bare + OUT puts the collar 13 m away
        v.co = (x + bkit.u(OUT), y, z)
    collar.data.update()
    bkit.recalc(collar)

    # ---- the lock body: a rounded laminated block with the keyway
    body = bkit.rounded_box("LockBody", 38.0, 16.0, 24.0, r=2.5, segments=4,
                            centre=(0.0, Y0, -10.0), mat=dark)
    bkit.boolean(body, bkit.rounded_box("_keyway", 3.4, 4.0, 14.0, r=0.6,
                                        segments=2,
                                        centre=(0.0, Y0 - 7.0, -4.0)),
                 "DIFFERENCE")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="shackle_outer_width", mm=37.0, tol=1.0, how="bbox_x",
         part="Shackle"),
    dict(name="shackle_height", mm=34.5, tol=2.0, how="bbox_z", part="Shackle"),
    dict(name="leg_diameter", mm=11.0, tol=0.6, how="bbox_y", part="Shackle"),
    dict(name="body_width", mm=38.0, tol=1.5, how="bbox_x", part="LockBody"),
    dict(name="body_height", mm=24.0, tol=1.0, how="bbox_z", part="LockBody"),
    dict(name="overall_height", mm=58.0, tol=3.0, how="bbox_z"),
]