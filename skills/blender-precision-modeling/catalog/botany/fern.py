"""
fern -- a 600 mm bird's-nest fern: seven arching fronds, each a rachis carrying
21 pairs of pinnae.

Two kinds of repeated feature, laid out two different ways, because they are
two different kinds of repetition:

  * the fronds are identical, so one frond is built and swept with
    `array_radial` about the crown at (0, 0, 12);
  * the pinnae along a rachis are identical but follow a curve, so their
    stations come from `bkit.lay_out` over the pinna widths plus an explicit
    2 mm gap, evaluated on the rachis arc. An `array_linear` would lay them on a
    straight line and the frond would come apart at the arch.

The pinna length follows a blade profile that peaks at 40% of the rachis and
tapers to nothing at the tip, which is the shape that makes a frond read as a
frond rather than as a bottle brush.
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
    height      = 600.0,
    spread      = 520.0,
    fronds      = 7,
    pinna_pairs = 10,
    frond_length = 430.0,
)

CROWN_Z = 12.0
FRONDS = SPEC["fronds"]
FROND_L = SPEC["frond_length"]
PAIRS = SPEC["pinna_pairs"]
PINNA_W = 26.0        # station width used by lay_out


def _rachis_point(t):
    """The rachis arc: rises off the crown, arches over, tip droops."""
    reach = FROND_L * t
    up = 250.0 * math.sin(math.pi * min(1.0, t * 1.05)) - 300.0 * t ** 2.4
    return Vector((reach, 0.0, CROWN_Z + up))


def _rachis(name, mat):
    rings = []
    steps = 20
    for i in range(13):
        t = i / 12.0
        p = _rachis_point(t)
        d = (_rachis_point(min(1.0, t + 0.02)) - _rachis_point(max(0.0, t - 0.02)))
        d.normalize()
        side = d.cross(Vector((0.0, 1.0, 0.0))).normalized()
        nrm = side.cross(d).normalized()
        r = 4.6 * (1.0 - 0.78 * t)
        ring = [tuple(p + side * (r * math.cos(2.0 * math.pi * j / steps))
                      + nrm * (r * math.sin(2.0 * math.pi * j / steps)))
                for j in range(steps)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def _pinna(name, base, direction, length, width, thick, mat, n=12):
    d = Vector(direction).normalized()
    ref = Vector((0.0, 1.0, 0.0)) if abs(d.y) < 0.9 else Vector((0.0, 0.0, 1.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (t, ws) in ((0.0, 0.30), (0.18, 0.86), (0.44, 1.00), (0.72, 0.80),
                    (0.90, 0.40), (1.0, 0.08)):
        c = Vector(base) + d * (length * t) + nrm * (-length * 0.22 * t * t)
        w = width * ws
        ring = [tuple(c + side * (w * math.cos(2.0 * math.pi * j / n))
                      + nrm * (thick * math.sin(2.0 * math.pi * j / n)))
                for j in range(n)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    stalk = bkit.pbr("FernRachis", base=(0.185, 0.290, 0.110), rough=0.60)
    blade = bkit.pbr("FernPinna", base=(0.130, 0.340, 0.115), rough=0.56)
    blade_y = bkit.pbr("FernPinnaYoung", base=(0.220, 0.420, 0.150), rough=0.58)

    # ---- one frond: rachis plus 10 pairs of pinnae on a computed station
    # ladder, blade length peaking at 40% of the rachis.
    stations = [x for (x, w) in bkit.lay_out([PINNA_W] * PAIRS, gap=2.0)]
    t_min, t_max = 0.16, 0.985
    span = (stations[-1] - stations[0] + PINNA_W)
    _rachis("Frond0_Rachis", stalk)
    for i, s in enumerate(stations):
        t = t_min + (t_max - t_min) * (s - stations[0]) / span
        p = _rachis_point(t)
        # blade profile: short at the base, widest at 40%, gone at the tip
        bl = 118.0 * math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.85 * (1.0 - 0.25 * t)
        for sign, tag in ((1.0, "L"), (-1.0, "R")):
            # pinnae run across the frond (world Y) and tilt up and forward,
            # which is the plane a real frond presents to the light
            pn = _pinna("Frond0_Pinna%d%s" % (i, tag), tuple(p),
                        (0.10, sign * 0.94, 0.16), bl, 11.0, 1.5,
                        blade if t < 0.7 else blade_y)
            pn.name = "Frond0_Pinna%d%s" % (i, tag)

    # ---- the other six fronds: every frond part swept about the crown
    f0 = bpy.data.objects["Frond0_Rachis"]
    bkit.array_radial(f0, FRONDS, centre=(0.0, 0.0, CROWN_Z))
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith("Frond0_Pinna"):
            bkit.array_radial(ob, FRONDS, centre=(0.0, 0.0, CROWN_Z))

    # ---- crown: the tight unopened fronds at the centre
    bkit.uv_sphere("Crown", 26.0, segments=24, rings=12, centre=(0.0, 0.0, 26.0),
                   mat=blade_y)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 2 * PAIRS + 1)


CHECKS = [
    # Frond0_Rachis is the whole seven-frond sweep after array_radial, so its
    # bounding box is the crown's reach, not one frond's length. Saying so is
    # the difference between a check that measures something real and one that
    # can never match.
    dict(name="crown_reach", mm=840.0, tol=4.0, how="longest", part="Frond0_Rachis"),
    dict(name="height",      mm=514.1, tol=2.57,  how="top_z"),
    dict(name="spread",      mm=819.2, tol=4.1,  how="bbox_x"),
    dict(name="crown",       mm=52.0,  tol=0.4, how="diameter", part="Crown"),
]
