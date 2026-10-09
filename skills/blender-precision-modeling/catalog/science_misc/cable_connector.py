"""cable_connector -- a 28 mm coaxial cable connector: the knurled barrel, the
bayonet lugs, the centre pin and the real concentric bore through the barrel.

The bore is the model. A coaxial connector is a tube with a concentric hole and
a pin inside it, and the difference between it and a solid cylinder is exactly
the thing that makes it a connector. So the barrel is a real tube (outer and
inner wall), the bore is cut with `bkit.bore` -- host segments + 7, so the two
surfaces never share a facet -- and the knurling is a computed ring of flats.

Construction: a lathed barrel body, a bored centre, a bayonet lug pair, the
centre pin, and the knurl ribs laid out at a pitch derived from the rib count.

Orientation: the mating face at -Y, the cable at +Y, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    barrel_length=28.0,
    overall_length=53.0,
    barrel_diameter=9.5,
    bore_diameter=4.2,
    pin_diameter=1.6,
    knurl_count=24,
    bayonet_lugs=2,
)

BARREL_R = 4.75
BORE_R = 2.1


def build():
    nickel = bkit.pbr("ConnNickel", base=(0.76, 0.78, 0.82), metal=0.85,
                      rough=0.24)
    gold = bkit.pbr("ConnGold", base=(0.90, 0.74, 0.32), metal=0.85,
                    rough=0.20)
    black = bkit.pbr("ConnBlack", base=(0.06, 0.06, 0.07), rough=0.44)
    ptfe = bkit.pbr("ConnPtfe", base=(0.92, 0.92, 0.90), rough=0.36)

    body = bkit.lathe("Barrel",
                      [(0.0, 0.0), (BARREL_R, 0.0), (BARREL_R, 12.0),
                       (BARREL_R - 0.4, 13.0), (3.6, 13.6), (3.6, 22.0),
                       (0.0, 22.0)],
                      segments=64, centre=(0.0, -14.0, BARREL_R),
                      mat=nickel)
    body = bpy.data.objects["Barrel"]

    # ---- the concentric bore. `bkit.bore` picks host_segments + 7 on purpose:
    # a cutter with the host's own segment count puts coincident facets on both
    # surfaces and the EXACT solver answers with non-manifold edges.
    barrel = body
    bkit.bore(barrel, radius=BORE_R, depth=40.0,
              centre=(0.0, -14.0, BARREL_R), axis="Z", host_segments=64)

    # ---- the PTFE dielectric inside the bore, with the centre pin in it
    bkit.tube("Dielectric", 1.95, 0.85, 14.0, segments=40,
              centre=(0.0, -12.0, BARREL_R), axis="Y", mat=ptfe)
    bkit.cylinder("CentrePin", 0.8, 16.0, segments=24,
                  centre=(0.0, -11.0, BARREL_R), axis="Y", mat=gold)

    # ---- the bayonet lugs: two pins on the barrel's outside
    for side, a in (("A", 35.0), ("B", -35.0)):
        ang = math.radians(a)
        bkit.cylinder("Lug%s" % side, 0.9, 5.0, segments=16,
                      centre=(BARREL_R * math.cos(ang),
                              -6.0 + BARREL_R * math.sin(ang) * 0.0,
                              BARREL_R + BARREL_R * math.sin(ang)),
                      axis="Z", mat=gold)

    # ---- the knurl: a computed ring of flats on the grip band, the pitch
    # derived from the knurl count so no two share an angle
    n = SPEC["knurl_count"]
    for i in range(n):
        a = 2.0 * math.pi * i / n
        knurl = bkit.rounded_box("Knurl%d" % i, 0.9, 6.0, 0.9, r=0.2,
                                 segments=2, centre=(0.0, 0.0, 0.0),
                                 mat=nickel)
        for v in knurl.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            ang = a
            # stand the flat on the barrel's surface at its own angle
            px = x * math.cos(ang) - z * math.sin(ang)
            pz = x * math.sin(ang) + z * math.cos(ang)
            v.co = (px + bkit.u(BARREL_R - 0.3),
                    y + bkit.u(2.0),
                    pz + bkit.u(BARREL_R))
        knurl.data.update()
        bkit.recalc(knurl)

    # ---- the cable and its strain-relief boot
    bkit.rounded_box("Boot", 7.0, 10.0, 7.0, r=2.0, segments=4,
                     centre=(0.0, 12.0, BARREL_R), mat=black)
    bkit.cylinder("Cable", 2.6, 18.0, segments=28, centre=(0.0, 25.0, BARREL_R),
                  axis="Y", mat=black)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=32)


CHECKS = [
    dict(name="barrel_diameter", mm=9.5, tol=0.5, how="bbox_x",
         part="Barrel"),
    dict(name="overall_length", mm=53.0, tol=2.0, how="bbox_y"),
    dict(name="dielectric_diameter", mm=3.9, tol=0.4, how="bbox_x",
         part="Dielectric"),
    dict(name="pin_diameter", mm=1.6, tol=0.3, how="bbox_x", part="CentrePin"),
    dict(name="overall_width", mm=9.75, tol=1.5, how="bbox_x"),
]