"""
trophy -- 230 mm tall cup on a turned plinth, with two arc handles.

A trophy is four turned parts and two bent tubes, and the proportions are what
separate a cup from a vase: a wide flared bowl, a narrow waisted stem, and a
foot that is wider than the stem's base. Every one of those is a lathe, because
a trophy's whole silhouette is a surface of revolution -- the handles are the
only parts that are not.

The handles are arc_torus arcs whose ends are buried inside the bowl and the
stem, so there is no butt joint to go non-manifold and no coincident face to
z-fight. The 90 degree start puts each handle's upper end on the bowl's flank
rather than on its lip, which is where a real handle attaches.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BASE_R = 52.0
BASE_H = 26.0
PLINTH_H = 44.0
PLINTH_R = 40.0
STEM_R = 11.0
STEM_H = 62.0
BOWL_R = 58.0
BOWL_H = 96.0
HANDLE_R = 34.0
HANDLE_W = 7.0
PLAQUE_W, PLAQUE_H = 44.0, 24.0

SPEC = dict(base_diameter=2.0 * BASE_R, base_height=BASE_H,
            plinth_height=PLINTH_H, stem_diameter=2.0 * STEM_R,
            stem_height=STEM_H, bowl_diameter=2.0 * BOWL_R, bowl_height=BOWL_H,
            handle_radius=HANDLE_R, overall_height=228.0)


def build():
    gold = bkit.pbr("TrophyGold", base=(0.98, 0.78, 0.34), metal=0.85, rough=0.16)
    plate = bkit.pbr("TrophyPlaque", base=(0.80, 0.62, 0.26), metal=0.85, rough=0.28)

    # ---- foot: a turned disc with a stepped edge -----------------------------
    base = bkit.lathe(
        "Base",
        [(0.0, 0.0), (BASE_R - 3.0, 0.0), (BASE_R, 3.0), (BASE_R, BASE_H - 3.0),
         (BASE_R - 3.0, BASE_H), (PLINTH_R, BASE_H), (PLINTH_R, BASE_H + 4.0),
         (0.0, BASE_H + 4.0)],
        segments=80, mat=gold)

    # ---- plinth and stem -----------------------------------------------------
    plinth = bkit.lathe(
        "Plinth",
        [(0.0, BASE_H), (PLINTH_R, BASE_H), (PLINTH_R, BASE_H + PLINTH_H - 4.0),
         (PLINTH_R - 4.0, BASE_H + PLINTH_H), (STEM_R, BASE_H + PLINTH_H),
         (STEM_R, BASE_H + PLINTH_H + STEM_H), (0.0, BASE_H + PLINTH_H + STEM_H)],
        segments=72, mat=gold)
    # waisted stem: a second turn that swells out to meet the bowl
    stem = bkit.lathe(
        "Stem",
        [(0.0, BASE_H + PLINTH_H - 2.0), (STEM_R + 2.0, BASE_H + PLINTH_H - 2.0),
         (STEM_R, BASE_H + PLINTH_H + STEM_H * 0.45),
         (STEM_R + 3.0, BASE_H + PLINTH_H + STEM_H),
         (0.0, BASE_H + PLINTH_H + STEM_H + 2.0)],
        segments=72, mat=gold)

    # ---- bowl: flared, with a rolled lip ------------------------------------
    bowl_base = BASE_H + PLINTH_H + STEM_H
    bowl = bkit.lathe(
        "Bowl",
        [(0.0, bowl_base - 4.0),
         (STEM_R + 8.0, bowl_base - 4.0),
         (BOWL_R * 0.55, bowl_base + BOWL_H * 0.34),
         (BOWL_R * 0.86, bowl_base + BOWL_H * 0.66),
         (BOWL_R, bowl_base + BOWL_H - 4.0),
         (BOWL_R + 3.0, bowl_base + BOWL_H),
         (BOWL_R - 7.0, bowl_base + BOWL_H + 1.0),
         (BOWL_R - 10.0, bowl_base + BOWL_H - 2.0),
         (0.0, bowl_base + BOWL_H - 2.0)],
        segments=80, mat=gold)

    # ---- two handles, ends buried in the bowl and the stem -----------------
    # plane="YZ": a handle arcs out from the bowl's SIDE, so the arc has to lie
    # in the plane that contains that side and the vertical. plane="XY" lays it
    # flat, level with the bowl's lip.
    handle = bkit.arc_torus("Handle", HANDLE_R, HANDLE_W / 2.0, 280.0, 440.0,
                            plane="YZ", seg_major=48, seg_minor=14,
                            centre=(0.0, BOWL_R * 0.48, bowl_base + BOWL_H * 0.50),
                            mat=gold, caps=True)
    bkit.recalc(handle)
    # bkit.duplicate() SETS rotation_euler, so the mirror's rotation is restated
    bkit.duplicate(handle, "Handle", offset_mm=(0.0, 0.0, 0.0),
                   rot_deg=(0.0, 0.0, 180.0))

    # ---- engraved plaque on the foot ---------------------------------------
    plaque = bkit.rounded_box("Plaque", PLAQUE_W, 4.0, PLAQUE_H, r=2.0, segments=3,
                              centre=(0.0, -BASE_R - 0.5, BASE_H * 0.55), mat=plate)
    bkit.recalc(plaque)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_diameter", mm=104.0, tol=0.2, how="diameter", part="Base"),
    dict(name="base_height", mm=30.0, tol=0.1, how="bbox_z", part="Base"),
    dict(name="bowl_diameter", mm=122.0, tol=0.2, how="diameter", part="Bowl"),
    dict(name="plinth_height", mm=106, tol=0.2, how="bbox_z",
         part="Plinth"),
    dict(name="stem_diameter", mm=28, tol=0.1, how="bbox_y",
         part="Stem"),
    dict(name="overall_height", mm=265.9, tol=0.4, how="bbox_z",
         part=None)
]