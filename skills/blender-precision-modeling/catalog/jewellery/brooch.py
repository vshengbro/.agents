"""
brooch -- 8.6 mm cloisonne flower brooch with eight petals and a pin hanger.

Built at the small end of the range on purpose. A real brooch exists at this
size -- the small enamel lapel pin / cocktail brooch -- and every dimension
below is that object's, not a full-size brooch shrunk to fit. The catalogue
class for this item is micro, and the whole point of a size class is that the
model is at the scale the class claims.

The petals come from array_radial about the brooch's own centre, with centre
passed explicitly: the brooch is built at the origin, but the hub still has to
be named or the copies orbit the world origin and spray outward. The hanger
loop is a small torus in the YZ plane, perpendicular to the face, which is what
a brooch pin bail actually is.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

BASE_R = 4.3            # 8.6 mm face
BASE_T = 1.2
PETAL_N = 8
PETAL_R = 1.05          # petal bead radius
PETAL_ORBIT = 2.55      # orbit radius of the petal centres
CENTRE_R = 1.45         # centre stone
BAIL_R = 1.0
BAIL_W = 0.30

SPEC = dict(face_diameter=2.0 * BASE_R,
            face_thickness=BASE_T,
            petal_count=PETAL_N,
            petal_diameter=2.0 * PETAL_R,
            centre_stone_diameter=2.0 * CENTRE_R,
            overall_height=9.6)


def build():
    gold = bkit.pbr("BroochGold", base=(0.98, 0.79, 0.40), metal=0.85, rough=0.16)
    enamel = bkit.pbr("BroochEnamel", base=(0.06, 0.22, 0.30), metal=0.0, rough=0.10,
                      coat=0.7)
    gem = bkit.pbr("BroochGem", base=(0.88, 0.92, 0.97), metal=0.0, rough=0.03,
                   transmission=0.55, ior=2.0)

    # ---- face: a turned disc with a chamfered rim --------------------------
    face = bkit.lathe(
        "Face",
        [(0.0, 0.0), (BASE_R - 0.25, 0.0), (BASE_R, 0.25),
         (BASE_R, BASE_T - 0.25), (BASE_R - 0.25, BASE_T), (0.0, BASE_T)],
        segments=64, mat=gold)

    # ---- eight petals, swept about the face centre -------------------------
    petal = bkit.cylinder("Petals", PETAL_R, 0.9, segments=24,
                          centre=(PETAL_ORBIT, 0.0, BASE_T + 0.35), mat=enamel)
    bkit.array_radial(petal, PETAL_N, centre=(0.0, 0.0, BASE_T + 0.35))

    # ---- centre stone -------------------------------------------------------
    centre = bkit.sphere("CentreStone", CENTRE_R, segments=28, rings=14,
                         centre=(0.0, 0.0, BASE_T + CENTRE_R * 0.55), mat=gem)

    # ---- pin hanger bail, perpendicular to the face ------------------------
    bail = bkit.torus("BailLoop", BAIL_R, BAIL_W, seg_major=36, seg_minor=10,
                      centre=(0.0, BASE_R - 0.3, BASE_T / 2.0), axis="X", mat=gold)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="face_diameter", mm=8.6, tol=0.05, how="diameter", part="Face"),
    dict(name="face_thickness", mm=1.2, tol=0.05, how="bbox_z", part="Face"),
    dict(name="petal_diameter", mm=2.1, tol=0.05, how="diameter", part="Petals"),
    dict(name="centre_stone", mm=2.9, tol=0.05, how="diameter", part="CentreStone"),
    # the bail extends the assembly in Y, not Z: it lies in the YZ plane so a
    # pin can pass through it while the enamel face stays flat
    dict(name="overall_span", mm=9.6, tol=0.2, how="bbox_y", part=None)
]