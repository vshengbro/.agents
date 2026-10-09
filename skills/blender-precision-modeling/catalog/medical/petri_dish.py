"""
petri_dish -- 50 mm culture dish with its lid, a poured agar layer, and the
lid skirt gripped 1.4 mm over the dish rim.

50 mm (not 90) on purpose: 50 mm is a real standard dish size and it also keeps
the whole object inside the catalog's `tiny` extent band. The skirt bore is cut
0.4 mm clear of the dish wall -- exactly tangent would leave two surfaces
touching along an edge.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    dish_diameter=50.0,     # outside diameter of the base
    dish_height=12.0,
    lid_diameter=52.0,
    overall_height=16.5,
    wall=1.2,
    agar_depth=4.5,
)

D = SPEC["dish_diameter"] / 2.0          # 25.0
H = SPEC["dish_height"]
WALL = SPEC["wall"]
RI = D - WALL                           # 23.8
LID = SPEC["lid_diameter"] / 2.0         # 26.0
SKIRT = 25.4                            # skirt bore: 0.4 mm clear of the dish


def build():
    glass = bkit.pbr("PetriGlass", base=(0.88, 0.92, 0.91), rough=0.04,
                     transmission=0.75, ior=1.52, coat=0.6)
    agar = bkit.pbr("PetriAgar", base=(0.86, 0.76, 0.52), rough=0.30,
                    transmission=0.25, ior=1.34)

    # ---- dish: closed section, so the rim has real 1.2 mm glass ------------
    dish = bkit.lathe("PetriDish", [
        (0.0, 0.0),
        (D - 2.0, 0.0),
        (D - 0.6, 0.7),           # rounded foot
        (D, 2.2),
        (D, H - 1.0),
        (D - 0.4, H),             # rim roll
        (RI, H),
        (RI, 2.6),
        (RI - 2.4, 1.5),
        (0.0, 1.5),               # agar floor
    ], segments=128, mat=glass)

    # ---- lid: a 1.5 mm disc with a skirt that reaches down past the rim ----
    # Listed anticlockwise in (r, z): a clockwise section revolves to inverted
    # normals, and a lathe does not recalc them.
    lid = bkit.lathe("PetriLid", [
        (0.0, H + 3.0),               # lid underside, out to the skirt bore
        (SKIRT, H + 3.0),
        (SKIRT, H - 1.4),             # up the skirt bore
        (LID, H - 1.4),               # across the skirt rim
        (LID, SPEC["overall_height"] - 0.7),
        (LID - 0.6, SPEC["overall_height"]),
        (0.0, SPEC["overall_height"]),
    ], segments=128, mat=glass)

    # ---- poured agar: its own solid, 0.5 mm clear of the dish wall ---------
    bkit.lathe("PetriAgar", [
        (0.0, 1.7),
        (RI - 0.5, 1.7),
        (RI - 0.5, SPEC["agar_depth"]),
        (0.0, SPEC["agar_depth"]),
    ], segments=128, mat=agar)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="dish_diameter", mm=50.0, tol=0.2, how="diameter", part="PetriDish"),
    dict(name="lid_diameter", mm=52.0, tol=0.2, how="diameter", part="PetriLid"),
    dict(name="overall_height", mm=16.5, tol=0.2, how="bbox_z"),
]