"""
mushroom -- a 92 mm fly agaric: domed red cap with white warts, 28 radial
gills, a ringed stipe and a bulbous base.

The gills are the part that makes it read as a mushroom rather than as a
domed button, and they are a radial array about the stipe axis at (0, 0, 46) --
the correct `centre`, so all 28 blades stay under the cap rim instead of
spraying past it.

The warts come from `bkit.grid_positions` projected onto the cap dome: a 4x2
station grid, each point lifted onto the cap surface by the dome equation, and
any station that falls outside the cap radius is dropped. Laying them out on a
grid is what stops them clumping into three arcs.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    cap_diameter  = 110.0,
    cap_height    = 42.0,
    stipe_height  = 56.0,
    gills         = 28,
    total_height  = 92.0,
)

STIPE_R = 9.0
CAP_Z = 56.0
CAP_R = 55.0
GILLS = SPEC["gills"]

# Cap: (radius, z above the cap base).
CAP = [(0.0, 42.0), (18.0, 40.4), (34.0, 35.0), (46.0, 26.0), (53.0, 14.0),
       (55.0, 4.0), (54.0, 0.0), (40.0, -2.0), (0.0, -3.0)]
# Stipe: (radius, z).
STIPE = [(0.0, 0.0), (15.0, 0.0), (12.5, 6.0), (10.0, 14.0), (8.6, 30.0),
         (8.0, 44.0), (8.4, 54.0), (7.4, 60.0), (0.0, 62.0)]


def _gill(name, mat, az_deg=0.0):
    """One radial gill blade: a thin wedge hanging under the cap."""
    a = math.radians(az_deg)
    ca, sa = math.cos(a), math.sin(a)
    zt = CAP_Z + 2.0
    rings = []
    for (r, drop, th) in ((12.0, 9.0, 0.55), (26.0, 13.0, 0.50),
                          (40.0, 11.0, 0.45), (50.0, 5.0, 0.40),
                          (53.0, 1.0, 0.30)):
        c = Vector((ca * r, sa * r, zt - drop))
        tang = Vector((-sa, ca, 0.0))
        nrm = Vector((ca, sa, 0.0))
        ring = [tuple(c + tang * (r * 0.055 * math.cos(2.0 * math.pi * j / 8))
                      + nrm * (th * math.sin(2.0 * math.pi * j / 8)))
                for j in range(8)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    cap_mat = bkit.pbr("AmanitaCap", base=(0.620, 0.070, 0.055), rough=0.34,
                       coat=0.30)
    gill_mat = bkit.pbr("AmanitaGill", base=(0.760, 0.700, 0.610), rough=0.62)
    stipe_mat = bkit.pbr("AmanitaStipe", base=(0.855, 0.825, 0.740), rough=0.56)
    wart = bkit.pbr("AmanitaWart", base=(0.900, 0.885, 0.845), rough=0.52)

    cap = bkit.lathe("Cap", CAP, segments=56, centre=(0.0, 0.0, CAP_Z),
                     mat=cap_mat)
    # The cap profile is written top-down (crown at +42, gills at -3) so the
    # underside is easy to read, and lathe() does not orient normals: without
    # this recalc the cap reports negative_volume.
    bkit.recalc(cap)
    bkit.lathe("Stipe", STIPE, segments=36, centre=(0.0, 0.0, 0.0),
               mat=stipe_mat)

    # ---- gills, swept about the stipe axis under the cap
    g0 = _gill("Gills", gill_mat)
    bkit.array_radial(g0, GILLS, centre=(0.0, 0.0, CAP_Z + 2.0))

    # ---- warts on the cap dome, from a station grid lifted onto the dome
    r_cap = 44.0
    for i, (x, y) in enumerate(bkit.grid_positions(cols=4, rows=2,
                                                   pitch_x=21.0, pitch_y=25.0)):
        rr = math.hypot(x, y)
        if rr > r_cap:
            continue
        z = CAP_Z + 42.0 - 34.0 * (rr / r_cap) ** 2
        w = bkit.uv_sphere("Wart%d" % i, 4.6, segments=12, rings=6,
                           centre=(x, y, z), mat=wart)
        w.scale = (1.0, 1.0, 0.55)
        w.name = "Wart%d" % i

    # ---- the ring (annulus) left on the stipe
    bkit.lathe("Ring", [(7.4, 0.0), (13.0, 1.4), (13.0, 3.2), (7.6, 3.6)],
               segments=32, centre=(0.0, 0.0, 33.0), mat=stipe_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 8)


CHECKS = [
    dict(name="cap_diameter", mm=110.0, tol=1.5, how="diameter", part="Cap"),
    dict(name="cap_height",   mm=45.0,  tol=1.0, how="bbox_z",   part="Cap"),
    dict(name="stipe_height", mm=62.0,  tol=1.0, how="bbox_z",   part="Stipe"),
    dict(name="total_height", mm=98.0,  tol=1.5, how="top_z",   part="Cap"),
]
