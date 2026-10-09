"""
nerf_dart -- 130 mm foam dart: 24 mm ogive, 78 mm body, three swept fins.

A foam dart is a single turned body -- the profile runs from a point on the axis
at the nose, out to the 13 mm barrel, and back to a point on the axis at the
tail, so lathe() welds both poles and the solid closes without caps. The whole
dart is therefore one lathe, and the only separate part is the fin set.

The three fins are one extruded triangle swept three times by array_radial
about the dart's own axis. Two fins would look like a mistake and six would
make it a badminton shuttlecock; three at 120 degrees is what the real thing
has, and the fin outline tapers to the tail so the silhouette is pointed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

L = 130.0
R = 6.5                # barrel radius (13 mm, a real 13 mm dart)
NOSE_L = 24.0
BARREL_L = 78.0
TAIL_L = 28.0
FIN_N = 3
FIN_ROOT = 5.6
FIN_TIP = 18.0
FIN_T = 1.6
FIN_Z0 = 100.0
FIN_Z1 = 128.0

SPEC = dict(length=L, barrel_diameter=2.0 * R, nose_length=NOSE_L,
            barrel_length=BARREL_L, tail_length=TAIL_L,
            fin_count=FIN_N, fin_tip_radius=FIN_TIP, fin_thickness=FIN_T)


def build():
    foam = bkit.pbr("DartFoam", base=(0.88, 0.32, 0.10), metal=0.0, rough=0.72)
    tip = bkit.pbr("DartTip", base=(0.10, 0.11, 0.14), metal=0.0, rough=0.26,
                   coat=0.6)

    # ---- one turned body: axis -> barrel -> axis ---------------------------
    body = bkit.lathe(
        "DartBody",
        [(0.0, 0.0),
         (R * 0.30, NOSE_L * 0.22), (R * 0.72, NOSE_L * 0.62), (R, NOSE_L),
         (R, NOSE_L + BARREL_L),
         (R * 0.80, NOSE_L + BARREL_L + TAIL_L * 0.55),
         (R * 0.36, L - 2.0), (0.0, L)],
        segments=56, mat=foam)

    # ---- the rubber tip, a real part on a real dart ------------------------
    nose = bkit.lathe(
        "DartTip",
        [(0.0, 0.0), (R * 0.34, 0.0), (R * 0.34, NOSE_L * 0.26),
         (R * 0.30, NOSE_L * 0.27), (0.0, NOSE_L * 0.27)],
        segments=48, mat=tip)

    # ---- three fins, one triangle swept about the dart's axis --------------
    # Built as a two-section loft directly in the XZ plane, NOT as an
    # extrude_profile with axis="Y". array_radial composes its rotation with
    # the object's OWN matrix_world, so a fin that already carries a 90 deg X
    # rotation from place() has its radial step turned into a step about Y --
    # the three fins come out as a flat fan instead of a tail. An unrotated
    # loft is what makes the sweep come out radial.
    tri = [(FIN_ROOT, FIN_Z0), (FIN_TIP, FIN_Z1 - 4.0), (FIN_ROOT, FIN_Z1)]
    sections = [[(x, -FIN_T / 2.0, z) for (x, z) in tri],
                [(x, FIN_T / 2.0, z) for (x, z) in tri]]
    fin = bkit.loft("Fins", sections, closed_loop=True, cap_start=True,
                    cap_end=True, mat=foam)
    bkit.recalc(fin)
    bkit.array_radial(fin, FIN_N, centre=(0.0, 0.0, 0.0))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="length", mm=130.0, tol=0.2, how="bbox_z", part="DartBody"),
    dict(name="barrel_diameter", mm=13.0, tol=0.1, how="diameter", part="DartBody"),
    dict(name="tip_diameter", mm=4.4, tol=0.1, how="diameter", part="DartTip"),
    # 2 x fin tip radius across the swept set
    # three fins on a 120 deg pitch: the swept set's X and Y spans are its
    # fin_span_x and fin_span_y. A fin's own 1.6 mm thickness is not measurable
    # on the swept set, so it is declared in SPEC rather than as a check.
    dict(name="fin_span_x", mm=27.69, tol=0.2, how="bbox_x",
         part="Fins"),
    dict(name="fin_span_y", mm=31.98, tol=0.2, how="bbox_y", part="Fins")
]