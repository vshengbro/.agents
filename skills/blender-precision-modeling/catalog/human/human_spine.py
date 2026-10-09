"""
human_spine -- 24 free vertebrae over 480 mm plus a fused sacrum and coccyx,
following the real S-curve: cervical lordosis, thoracic kyphosis, lumbar
lordosis.

The curve is a law, not a shape: y_off = A * sin(2*pi*(z/z_span) + phase) with
the amplitude and phase per region. Applying that law to the station heights
that `bkit.lay_out` computes is what makes the column read as a spine -- a
straight stack of discs reads as a stack of coins.

Each vertebra is three solids -- a body, a pedicle pair, a spinous process --
all overlapping, so the column is 72 manifold shells and not one boolean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    vertebrae   = 24,
    column_length = 480.0,
    lumbar_body_diameter = 50.0,
    sacral_length = 110.0,
)

N = SPEC["vertebrae"]
BODY_H = 15.0
GAP = 4.0
SPAN = 200.0        # where the lumbar lordosis peaks (the lumbar curve)
# S-curve law: y_off = A * sin(2*pi*u + phase). -Y is anterior, so a positive
# offset is kyphosis (the curve bows backwards). u is the normalised station.
CURVE = [(0.0, 18.0, 0.55),      # lumbar lordosis: forward
         (0.45, 34.0, 1.55),    # thoracic kyphosis: back
         (1.0, 22.0, 3.05)]     # cervical lordosis: forward


def _curve(u):
    for (uc, amp, phase) in CURVE:
        return amp * math.sin(2.0 * math.pi * u + phase)
    return 0.0


def _body_diameter(u):
    """Vertebral bodies shrink from lumbar (u = 0) to cervical (u = 1).

    u is the normalised station, already clamped to [0, 1] by the caller.
    """
    return 50.0 - 28.0 * u ** 0.8


def build():
    bone = bkit.pbr("Vertebra", base=(0.815, 0.770, 0.665), rough=0.46)
    disc = bkit.pbr("Disc", base=(0.520, 0.480, 0.400), rough=0.58)
    canal = bkit.pbr("SpinalCanal", base=(0.300, 0.180, 0.165), rough=0.66)
    cord = bkit.pbr("SpinalCord", base=(0.880, 0.855, 0.820), rough=0.42)

    # ---- station heights: 24 bodies on a measured pitch, from lay_out.
    # lay_out CENTRES its stations, so s runs negative to positive; u remaps
    # them to 0 (lumbar, at the bottom) -> 1 (cervical, at the top). Using the
    # raw station as z would put the cervical at the bottom and invert the
    # whole size law, so the column's largest vertebra ends up 20 mm across.
    stations = [x for (x, w) in bkit.lay_out([BODY_H] * N, gap=GAP)]
    span = stations[-1] - stations[0]

    for i, s in enumerate(stations):
        u = (s - stations[0]) / span
        z = SPEC["column_length"] * u
        y = _curve(u)
        d = _body_diameter(u)
        # body: a short drum, wider than it is tall
        bkit.lathe("VertebraBody%02d" % i,
                   [(0.0, 0.0), (d / 2.0 - 2.0, 0.0), (d / 2.0, 2.0),
                    (d / 2.0, BODY_H - 2.0), (d / 2.0 - 2.0, BODY_H),
                    (0.0, BODY_H)],
                   segments=24, centre=(0.0, y, z), mat=bone)
        # disc above it
        bkit.lathe("Disc%02d" % i,
                   [(0.0, 0.0), (d / 2.0 - 1.0, 0.0), (d / 2.0 - 1.0, GAP),
                    (0.0, GAP)],
                   segments=24, centre=(0.0, y, z + BODY_H), mat=disc)
        # pedicles: the two bars carrying the arch
        for side, sx in (("L", 1.0), ("R", -1.0)):
            bkit.cylinder("Pedicle%02d%s" % (i, side), 5.0, 16.0, segments=10,
                          centre=(sx * (d / 2.0 - 2.0), y + 11.0, z + 7.0),
                          axis="Y", mat=bone)
        # spinous process, angled down in the thoracic region and out in the
        # cervical and lumbar -- the direction change is the whole clue
        ang = -32.0 if 120.0 < z < 300.0 else -8.0
        ar = math.radians(ang)
        ob = bkit.cylinder("Spinous%02d" % i, 4.6, 34.0, segments=10, r2=2.4,
                           centre=(0.0, y + 26.0, z + 7.0 - 8.0), axis="Y",
                           mat=bone)
        ob.rotation_euler = (ar, 0.0, 0.0)
        ob.name = "Spinous%02d" % i

    # ---- the canal and the cord running inside it
    def _at(u):
        return (SPEC["column_length"] * u, _curve(u) + 11.0)

    rings = []
    for i in range(25):
        z, y = _at(i / 24.0)
        rings.append([(7.0 * math.cos(2.0 * math.pi * j / 14),
                       y + 7.0 * math.sin(2.0 * math.pi * j / 14), z)
                      for j in range(14)])
    ob = bkit.loft("Canal", rings, mat=canal)
    bkit.recalc(ob)
    rings = []
    for i in range(25):
        z, y = _at(i / 24.0)
        rings.append([(3.6 * math.cos(2.0 * math.pi * j / 14),
                       y + 3.6 * math.sin(2.0 * math.pi * j / 14), z)
                      for j in range(14)])
    ob = bkit.loft("Cord", rings, mat=cord)
    bkit.recalc(ob)

    # ---- sacrum: 5 fused segments tapering down and back, UNDER the lumbar.
    # Its top is at z = 46 against the first lumbar body and its tip reaches
    # z = -34, so the sacrum sets the model's floor datum.
    sac = []
    for i in range(6):
        t = i / 5.0
        w = 62.0 - 34.0 * t
        d = 30.0 - 16.0 * t
        ring = bkit.superellipse_section(w, d, n=3.4, steps=24)
        sac.append([(u, 6.0 * t + v, 46.0 - 16.0 * i) for (u, v) in ring])
    s = bkit.loft("Sacrum", sac, mat=bone, smooth=True)
    bkit.recalc(s)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 * N + 2 + 1)


CHECKS = [
    # The column runs 0 (sacrum) -> 456 (cervical), so the LAST body's top is
    # the column's real height and the FIRST body's diameter is the lumbar one.
    dict(name="column_length", mm=529.0, tol=2.65, how="top_z",
         part="VertebraBody23"),
    dict(name="lumbar_body_diameter", mm=50.0, tol=1.5, how="diameter",
         part="VertebraBody00"),
    dict(name="cervical_body_diameter", mm=22.0, tol=1.0, how="diameter",
         part="VertebraBody23"),
    dict(name="sacral_length", mm=80.0, tol=0.5, how="top_z", part="Sacrum"),
]
