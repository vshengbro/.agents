"""
fishing_trawler -- 38 m stern trawler, 38000 x 8000 x 7200 mm.

A trawler is a working deck and the working deck is the model: a clear
4200 x 6600 mm area aft with a gantry at the transom, two otter boards
stowed on the bulwark, a net drum on the foredeck and a gallows frame. The
hull is the seaworthiness argument -- 2400 mm of freeboard aft rising to
3600 mm at the bow, a raked stem, and a pronounced sheer, because a trawler
works in a seaway and a yacht does not. The wheelhouse is forward of the
working deck, not on top of it.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=38000.0,
    beam=8000.0,
    hull_depth=3600.0,
    freeboard_aft=2400.0,
    wheelhouse_height=2600.0,
    gantry_top_z=8650.0,
    mast_top_z=9200.0,
)

CHECKS = [
    dict(name="length", mm=38000.0, tol=12.0, how="bbox_x", part="TrawlerHull"),
    dict(name="beam", mm=8000.0, tol=12.0, how="bbox_y", part="TrawlerHull"),
    dict(name="hull_depth", mm=3600.0, tol=12.0, how="bbox_z",
         part="TrawlerHull"),
    dict(name="bow_sheer_z", mm=3600.0, tol=12.0, how="top_z",
         part="TrawlerHull"),
    dict(name="wheelhouse_height", mm=2600.0, tol=10.0, how="bbox_z",
         part="TrawlerWheelhouse"),
    dict(name="gantry_top_z", mm=8650.0, tol=20.0, how="top_z",
         part="TrawlerGantry"),
    dict(name="mast_top_z", mm=9200.0, tol=20.0, how="top_z",
         part="TrawlerMast"),
]

# (x, half beam, keel, sheer, bottom ratio) -- pronounced sheer, raked stem
STATIONS = [
    (-19000.0, 3000.0, 300.0, 2600.0, 0.78),
    (-15000.0, 3700.0, 100.0, 2800.0, 0.84),
    (-6000.0, 4000.0, 0.0, 2600.0, 0.90),
    (6000.0, 3950.0, 0.0, 2800.0, 0.88),
    (13000.0, 3600.0, 60.0, 3200.0, 0.80),
    (17000.0, 2500.0, 400.0, 3500.0, 0.66),
    (19000.0, 1100.0, 1100.0, 3600.0, 0.56),
]


def build():
    topside = bkit.pbr("TrawlerTopside", base=(0.14, 0.32, 0.46), rough=0.34)
    boot = bkit.pbr("TrawlerBoot", base=(0.30, 0.12, 0.08), rough=0.55)
    deck_mat = bkit.pbr("TrawlerDeck", base=(0.32, 0.30, 0.26), rough=0.70)
    house = bkit.pbr("TrawlerHouse", base=(0.90, 0.89, 0.85), rough=0.26)
    glass = bkit.pbr("TrawlerGlass", base=(0.05, 0.06, 0.08), rough=0.05)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")
    net_mat = bkit.pbr("TrawlerNet", base=(0.24, 0.26, 0.22), rough=0.90)

    hull = V.hull("TrawlerHull", STATIONS, mat=topside, smooth=28.0)
    bkit.assign_faces_by(hull, boot, lambda c, n: c.z / bkit.MM < 1100.0)
    bkit.assign_faces_by(hull, deck_mat, lambda c, n: n.z > 0.75)

    # bulwark round the working deck: three boxes and a mirror
    bw = bkit.rounded_box("TrawlerBulwarkP", 15000.0, 300.0, 1200.0, r=80.0,
                          segments=2, centre=(-11000.0, 3900.0, 3100.0),
                          mat=topside)
    bkit.mirror(bw, "Y")
    bkit.rounded_box("TrawlerTransomBulwark", 400.0, 7600.0, 1200.0, r=80.0,
                     segments=2, centre=(-18600.0, 0.0, 3000.0), mat=topside)

    # gantry: two legs and a cross beam over the transom
    for i, y in enumerate((2600.0, -2600.0)):
        V.strut("TrawlerGantryLeg%d" % i, (-17600.0, y, 2600.0),
                (-16200.0, y, 8500.0), 180.0, steel, 12)
    gantry = bkit.rounded_box("TrawlerGantry", 1800.0, 6200.0, 300.0, r=100.0,
                              segments=2, centre=(-16200.0, 0.0, 8500.0),
                              mat=steel)
    gantry.name = "TrawlerGantry"
    for i, y in enumerate((2400.0, -2400.0)):
        bkit.torus("TrawlerBlock%d" % i, 420.0, 110.0, seg_major=36,
                   seg_minor=14, centre=(-16200.0, y, 7700.0), axis="Y",
                   mat=dark)
    bkit.rounded_box("TrawlerNet", 2400.0, 5200.0, 1600.0, r=400.0,
                     segments=3, centre=(-15600.0, 0.0, 4600.0), mat=net_mat)
    for i, s in enumerate((1, -1)):
        otter = bkit.rounded_box("TrawlerOtterBoard%d" % i, 3600.0, 200.0,
                                 2000.0, r=100.0, segments=2,
                                 centre=(-11000.0, s * 3600.0, 4000.0),
                                 mat=steel)
        otter.name = "TrawlerOtterBoard%d" % i

    bkit.cylinder("TrawlerNetDrum", 900.0, 4200.0, segments=28, axis="Y",
                  centre=(7000.0, 0.0, 3600.0), mat=dark)
    bkit.rounded_box("TrawlerNetDrumFrame", 2600.0, 5200.0, 500.0, r=100.0,
                     segments=2, centre=(7000.0, 0.0, 3100.0), mat=steel)

    wh = bkit.rounded_box("TrawlerWheelhouse", 5000.0, 6600.0, 2600.0, r=200.0,
                          segments=3, centre=(12000.0, 0.0, 5300.0), mat=house)
    V.window_band(wh, 5000.0, 6300.0, glass, max_nz=0.6)
    bkit.rounded_box("TrawlerWheelhouseRoof", 5400.0, 7000.0, 160.0, r=80.0,
                     segments=2, centre=(12000.0, 0.0, 6520.0), mat=house)
    bkit.rounded_box("TrawlerBridgeWing", 1200.0, 8200.0, 300.0, r=100.0,
                     segments=2, centre=(12000.0, 0.0, 6000.0), mat=house)
    bkit.rounded_box("TrawlerForecastle", 6000.0, 5600.0, 1800.0, r=300.0,
                     segments=3, centre=(12000.0, 0.0, 4000.0), mat=house)
    bkit.cylinder("TrawlerMast", 170.0, 5000.0, segments=14, axis="Z",
                  centre=(11000.0, 0.0, 6700.0), mat=steel)
    bkit.rounded_box("TrawlerRadar", 300.0, 2200.0, 200.0, r=80.0,
                     segments=2, centre=(11000.0, 0.0, 9100.0), mat=steel)
    bkit.rounded_box("TrawlerStack", 1400.0, 1600.0, 2600.0, r=150.0,
                     segments=2, centre=(8600.0, 0.0, 4400.0),
                     mat=bkit.pbr("TrawlerStackMat", base=(0.60, 0.14, 0.10),
                                  rough=0.38))
    bkit.cylinder("TrawlerExhaust", 200.0, 1400.0, segments=12, axis="Z",
                  centre=(8600.0, 0.0, 6400.0), mat=dark)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=19)
