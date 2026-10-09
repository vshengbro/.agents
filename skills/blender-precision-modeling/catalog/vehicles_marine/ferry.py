"""
ferry -- 42 m double-ended passenger ferry, 42000 x 11000 x 6400 mm.

A ferry is a box on a hull and the box has to be right: the car deck is a
slab, the passenger deck above it is set inboard so the two side decks read as
open promenade, and the wheelhouse is a separate block on the roof with a
window band all the way round. Double-ended is the type decision -- the same
raked stem at both ends, so the bow and stern stations mirror -- and it is why
there is no bow thruster and why the bow rail is drawn twice.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=42000.0,
    beam=11000.0,
    hull_depth=4200.0,
    car_deck_z=4200.0,
    passenger_deck_width=8400.0,
    saloon_top_z=6200.0,
    wheelhouse_top_z=10000.0,
)

CHECKS = [
    dict(name="length", mm=42000.0, tol=12.0, how="bbox_x", part="FerryHull"),
    dict(name="beam", mm=11000.0, tol=12.0, how="bbox_y", part="FerryHull"),
    dict(name="hull_depth", mm=4200.0, tol=12.0, how="bbox_z", part="FerryHull"),
    dict(name="car_deck_z", mm=4200.0, tol=12.0, how="top_z", part="FerryHull"),
    dict(name="passenger_deck_width", mm=8400.0, tol=12.0, how="bbox_y",
         part="FerrySaloon"),
    dict(name="saloon_top_z", mm=6200.0, tol=12.0, how="top_z",
         part="FerrySaloon"),
    dict(name="wheelhouse_top_z", mm=10000.0, tol=20.0, how="top_z",
         part="FerryWheelhouse"),
]

# (x, half beam, keel, sheer, bottom ratio) -- symmetric fore and aft
STATIONS = [
    (-21000.0, 2400.0, 2100.0, 3600.0, 0.62),
    (-19000.0, 4100.0, 900.0, 3950.0, 0.74),
    (-14000.0, 5300.0, 200.0, 4150.0, 0.86),
    (0.0, 5500.0, 0.0, 4200.0, 0.90),
    (14000.0, 5300.0, 200.0, 4150.0, 0.86),
    (19000.0, 4100.0, 900.0, 3950.0, 0.74),
    (21000.0, 2400.0, 2100.0, 3600.0, 0.62),
]


def build():
    topside = bkit.pbr("FerryTopside", base=(0.82, 0.16, 0.12), rough=0.26,
                       coat=0.4)
    boot = bkit.pbr("FerryBoot", base=(0.08, 0.09, 0.11), rough=0.40)
    deck_mat = bkit.pbr("FerryDeck", base=(0.34, 0.36, 0.34), rough=0.66)
    house = bkit.pbr("FerryHouse", base=(0.90, 0.90, 0.88), rough=0.22)
    glass = bkit.pbr("FerryGlass", base=(0.05, 0.06, 0.08), rough=0.05)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    hull = V.hull("FerryHull", STATIONS, mat=topside, smooth=30.0)
    bkit.assign_faces_by(hull, boot, lambda c, n: c.z / bkit.MM < 900.0)
    bkit.assign_faces_by(hull, deck_mat, lambda c, n: n.z > 0.75)

    # car deck: a slab with a ramp well cut through it at the bow
    car = bkit.rounded_box("FerryCarDeck", 34000.0, 9400.0, 260.0, r=60.0,
                           segments=2, centre=(0.0, 0.0, 4100.0), mat=deck_mat)
    V.window_band(hull, 2900.0, 3400.0, glass, max_nz=0.55, y_half=4600.0)

    saloon = bkit.rounded_box("FerrySaloon", 24000.0, 8400.0, 2400.0, r=200.0,
                              segments=3, centre=(-1000.0, 0.0, 5000.0),
                              mat=house)
    V.window_band(saloon, 5300.0, 6400.0, glass, max_nz=0.6)
    bkit.rounded_box("FerrySaloonRoof", 24600.0, 8600.0, 200.0, r=100.0,
                     segments=2, centre=(-1000.0, 0.0, 6100.0), mat=house)
    lounge = bkit.rounded_box("FerryUpperLounge", 12000.0, 7200.0, 2100.0,
                              r=200.0, segments=3,
                              centre=(-3000.0, 0.0, 7300.0), mat=house)
    V.window_band(lounge, 7600.0, 8600.0, glass, max_nz=0.6)
    bkit.rounded_box("FerryUpperRoof", 12600.0, 7400.0, 180.0, r=90.0,
                     segments=2, centre=(-3000.0, 0.0, 8250.0), mat=house)

    wh = bkit.rounded_box("FerryWheelhouse", 6000.0, 6400.0, 1700.0, r=200.0,
                          segments=3, centre=(-1000.0, 0.0, 9150.0), mat=house)
    V.window_band(wh, 9000.0, 9800.0, glass, max_nz=0.6)
    bkit.rounded_box("FerryWheelhouseRoof", 6400.0, 6800.0, 160.0, r=80.0,
                     segments=2, centre=(-1000.0, 0.0, 9900.0), mat=house)
    bkit.cylinder("FerryFunnel", 900.0, 2200.0, segments=20, axis="Z",
                  centre=(-7000.0, 0.0, 9450.0), mat=dark)
    bkit.cylinder("FerryMast", 140.0, 3000.0, segments=12, axis="Z",
                  centre=(-1000.0, 0.0, 11500.0), mat=steel)

    # side decks: bulwarks both sides, drawn with the Mirror modifier so the
    # two sides cannot drift apart
    rail = bkit.rounded_box("FerryBulwark", 38000.0, 300.0, 1000.0, r=60.0,
                            segments=2, centre=(0.0, 4900.0, 4500.0),
                            mat=topside)
    bkit.mirror(rail, "Y")
    bow_rail = bkit.rounded_box("FerryBowRail", 5000.0, 300.0, 1000.0, r=60.0,
                                segments=2, centre=(19500.0, 0.0, 3900.0),
                                mat=topside)
    bkit.mirror(bow_rail, "Y")

    # vehicle deck markings: two lanes and a centre line, painted on the slab
    for i, y in enumerate((-1600.0, 1600.0)):
        bkit.rounded_box("FerryLane%d" % i, 30000.0, 60.0, 8.0, r=2.0,
                         segments=1, centre=(0.0, y, 4232.0),
                         mat=bkit.preset("yellow_paint"))
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=17)
