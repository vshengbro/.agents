"""
cargo_ship -- 78 m coastal container feeder, 78000 x 13000 x 3200 mm.

A feeder is a barge with a box on it, and the box is the model: eight rows of
containers on a 78 m deck, laid out from real 40 ft and 20 ft box lengths with
an explicit 60 mm gap, so no two boxes touch and the row widths come out
honest. The hull is a parallel-midbody barge form (bottom ratio 0.95) with a
blunt raked bow, the accommodation block is aft with a single funnel, and the
whole thing sits on two keels and a skeg so the deck is not a lid at z=0.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=78000.0,
    beam=13000.0,
    hull_depth=3200.0,
    deck_z=3200.0,
    container_rows=4,
    container_height=2590.0,
    bridge_top_z=9000.0,
)

CHECKS = [
    dict(name="length", mm=78000.0, tol=15.0, how="bbox_x",
         part="CargoShipHull"),
    dict(name="beam", mm=13000.0, tol=15.0, how="bbox_y",
         part="CargoShipHull"),
    dict(name="hull_depth", mm=3200.0, tol=15.0, how="bbox_z",
         part="CargoShipHull"),
    dict(name="deck_z", mm=3200.0, tol=15.0, how="top_z",
         part="CargoShipHull"),
    dict(name="container_height", mm=2590.0, tol=20.0, how="bbox_z",
         part="Container1"),
    dict(name="bridge_top_z", mm=9000.0, tol=30.0, how="top_z",
         part="CargoShipBridge"),
]

# (x, half beam, keel, sheer, bottom ratio) -- barge midbody, raked bow
STATIONS = [
    (-39000.0, 5200.0, 1500.0, 2700.0, 0.96),
    (-34000.0, 6100.0, 700.0, 2950.0, 0.95),
    (-20000.0, 6500.0, 100.0, 3150.0, 0.95),
    (10000.0, 6500.0, 0.0, 3200.0, 0.95),
    (26000.0, 6300.0, 0.0, 3150.0, 0.92),
    (33000.0, 5200.0, 200.0, 2950.0, 0.84),
    (38000.0, 3000.0, 900.0, 2700.0, 0.70),
    (39000.0, 1100.0, 1700.0, 2550.0, 0.62),
]

BRIDGE_X0, BRIDGE_X1 = -33000.0, -24000.0
CONTAINER_L, CONTAINER_W, CONTAINER_H = 12190.0, 2440.0, 2590.0


def build():
    topside = bkit.pbr("CargoShipTopside", base=(0.16, 0.20, 0.30), rough=0.40)
    boot = bkit.pbr("CargoShipBoot", base=(0.34, 0.10, 0.06), rough=0.55)
    deck_mat = bkit.pbr("CargoShipDeck", base=(0.30, 0.32, 0.30), rough=0.70)
    house_mat = bkit.pbr("CargoShipHouse", base=(0.86, 0.87, 0.86), rough=0.24)
    glass = bkit.pbr("CargoShipGlass", base=(0.05, 0.06, 0.07), rough=0.06)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    hull = V.hull("CargoShipHull", STATIONS, mat=topside, smooth=30.0)
    bkit.assign_faces_by(hull, boot, lambda c, n: c.z / bkit.MM < 700.0)
    bkit.assign_faces_by(hull, deck_mat, lambda c, n: n.z > 0.75)

    # deckhouse: accommodation block aft, wheelhouse on top, one funnel
    bkit.rounded_box("CargoShipHouse", 8200.0, 11000.0, 3600.0, r=300.0,
                     segments=3, centre=(-29000.0, 0.0, 4900.0), mat=house_mat)
    bridge = bkit.rounded_box("CargoShipBridge", 3400.0, 10000.0, 2400.0,
                              r=200.0, segments=3,
                              centre=(-29000.0, 0.0, 7800.0), mat=house_mat)
    V.window_band(bridge, 7100.0, 8500.0, glass, max_nz=0.9)
    bkit.rounded_box("CargoShipFunnel", 2600.0, 3400.0, 2900.0, r=200.0,
                     segments=3, centre=(-33500.0, 0.0, 7400.0),
                     mat=bkit.pbr("CargoShipFunnelMat", base=(0.72, 0.16, 0.10),
                                  rough=0.34))
    bkit.cylinder("CargoShipMast", 200.0, 4000.0, segments=14, axis="Z",
                  centre=(-25000.0, 0.0, 9000.0), mat=steel)
    bkit.rounded_box("CargoShipAccommodationLadder", 200.0, 400.0, 4000.0,
                     r=60.0, segments=2, centre=(-32000.0, 5600.0, 5000.0),
                     mat=steel)

    # container stacks: five rows of boxes, each row a real 40 ft bay, with an
    # explicit gap so no two boxes share a face
    n_rows = SPEC["container_rows"]
    row_y = [(i - (n_rows - 1) / 2.0) * (CONTAINER_W + 120.0)
             for i in range(n_rows)]
    for i, y in enumerate(row_y):
        for j, x in enumerate((-15000.0, -1500.0, 12000.0)):
            bkit.rounded_box("Container%d" % (i * 3 + j + 1), CONTAINER_L,
                             CONTAINER_W, CONTAINER_H, r=40.0, segments=1,
                             centre=(x, y, 3200.0 + CONTAINER_H / 2.0 + 20.0),
                             mat=container_mat(i, j))
    # lashing bridges between the bays
    for i, y in enumerate(row_y):
        bkit.rounded_box("LashingBridge%d" % i, 400.0, CONTAINER_W + 200.0,
                         300.0, r=40.0, segments=1,
                         centre=(-6750.0, y, 6000.0), mat=steel)

    # bow: a hatch cover, two anchor windlasses and the forecastle rail
    bkit.rounded_box("CargoShipHatchCover", 14000.0, 10500.0, 400.0, r=120.0,
                     segments=2, centre=(20000.0, 0.0, 3400.0), mat=deck_mat)
    bkit.cylinder("CargoShipWindlass", 700.0, 2200.0, segments=24, axis="Y",
                  centre=(33000.0, 0.0, 3700.0), mat=steel)
    bulwark = bkit.rounded_box("CargoShipBulwark", 20000.0, 400.0, 1200.0,
                               r=80.0, segments=2, centre=(24000.0, 6300.0,
                                                            3800.0),
                               mat=deck_mat)
    bkit.mirror(bulwark, "Y")
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=27)


def container_mat(i, j):
    """A deterministic colour per bay: real feeder stacks are never one colour."""
    pal = ((0.62, 0.16, 0.12), (0.10, 0.28, 0.48), (0.55, 0.42, 0.10),
           (0.24, 0.38, 0.24), (0.50, 0.50, 0.52), (0.40, 0.16, 0.34))
    return bkit.pbr("ContainerPaint%d" % ((i * 3 + j) % len(pal)),
                    base=pal[(i * 3 + j) % len(pal)], rough=0.55)
