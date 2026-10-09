"""
yacht -- 21 m motor yacht, 21000 x 6200 x 7600 mm.

A motor yacht is a hull plus three stacked slabs, and the read is the ratio
between them: 6200 mm of beam over 21 m of length is 3.4:1, which is the
difference between a yacht and a ferry, and the superstructure is set well
inboard at 5400 mm so the walkways round it are visible from above. The
bow is at +x. The hull's forward third carries a raked stem, the deck is
crowned, and the flybridge radar arch is the highest point at 7600.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=21000.0,
    beam=6200.0,
    hull_depth=2800.0,
    main_deck_z=2800.0,
    superstructure_width=5400.0,
    superstructure_height=3600.0,
    radar_arch_top_z=7600.0,
    flybridge_top_z=5900.0,
)

CHECKS = [
    dict(name="length", mm=21000.0, tol=8.0, how="bbox_x", part="YachtHull"),
    dict(name="beam", mm=6200.0, tol=8.0, how="bbox_y", part="YachtHull"),
    dict(name="hull_depth", mm=2800.0, tol=8.0, how="bbox_z", part="YachtHull"),
    # `top_z` is a COORDINATE above the floor. sit_on_floor lifts this hull
    # 420.6 mm to seat it, so every deck height measures 420.6 mm higher here
    # than in the model's own build frame.
    dict(name="main_deck_z", mm=3220.6, tol=8.0, how="top_z",
         part="YachtHull"),
    dict(name="superstructure_width", mm=5400.0, tol=8.0, how="bbox_y",
         part="YachtHouse"),
    dict(name="flybridge_top_z", mm=6320.6, tol=8.0, how="top_z",
         part="YachtFlybridge"),
    dict(name="radar_arch_top_z", mm=8020.6, tol=10.0, how="top_z",
         part="YachtRadarArch"),
]

# (x, half beam, keel, sheer, bottom ratio) -- raked stem, wide transom
STATIONS = [
    (-10500.0, 2500.0, 900.0, 2500.0, 0.94),
    (-9500.0, 2900.0, 500.0, 2620.0, 0.92),
    (-7000.0, 3080.0, 150.0, 2740.0, 0.88),
    (-3000.0, 3100.0, 0.0, 2800.0, 0.86),
    (2000.0, 3050.0, 0.0, 2760.0, 0.82),
    (6500.0, 2700.0, 60.0, 2600.0, 0.72),
    (9500.0, 1800.0, 320.0, 2400.0, 0.58),
    (10400.0, 700.0, 1100.0, 2250.0, 0.46),
    (10500.0, 260.0, 1600.0, 2180.0, 0.44),
]

HOUSE_X0, HOUSE_X1 = -8200.0, 3200.0


def build():
    topside = bkit.pbr("YachtTopside", base=(0.88, 0.88, 0.86), rough=0.14,
                       coat=0.7)
    boot = bkit.pbr("YachtBoot", base=(0.10, 0.12, 0.16), rough=0.30)
    glass = bkit.pbr("YachtGlass", base=(0.04, 0.05, 0.06), rough=0.05)
    teak = bkit.pbr("YachtTeak", base=(0.52, 0.34, 0.18), rough=0.55)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    hull = V.hull("YachtHull", STATIONS, mat=topside, smooth=32.0)
    bkit.assign_faces_by(hull, boot, lambda c, n: c.z / bkit.MM < 500.0)

    house = V.deckhouse("YachtHouse", HOUSE_X0, HOUSE_X1, 2785.0, 2700.0,
                        4800.0, topside, mat_glass=glass,
                        glass_z=(3900.0, 4600.0), steps=56, n=5.2)
    bkit.rounded_box("YachtHouseRoof", 11600.0, 5500.0, 200.0, r=100.0,
                     segments=3, centre=(-2500.0, 0.0, 4850.0), mat=topside)
    bkit.rounded_box("YachtUpperDeck", 8400.0, 4600.0, 180.0, r=90.0,
                     segments=3, centre=(-3600.0, 0.0, 5250.0), mat=topside)
    bkit.rounded_box("YachtFlybridge", 4600.0, 3400.0, 520.0, r=120.0,
                     segments=3, centre=(-1200.0, 0.0, 5640.0), mat=topside)
    bkit.rounded_box("YachtFlybridgeScreen", 300.0, 3000.0, 380.0, r=60.0,
                     segments=2, centre=(1100.0, 0.0, 5500.0), mat=glass)

    # radar arch: two legs and a cross beam, the highest point on the boat
    for i, y in enumerate((1500.0, -1500.0)):
        V.strut("YachtArchLeg%d" % i, (-5200.0, y, 5300.0),
                (-4900.0, y * 0.7, 7500.0), 90.0, steel, 14)
    bkit.rounded_box("YachtRadarArch", 500.0, 2400.0, 200.0, r=80.0,
                     segments=3, centre=(-4850.0, 0.0, 7500.0), mat=steel)
    bkit.lathe("YachtRadar", [(0.0, 7600.0), (700.0, 7600.0), (700.0, 7700.0),
                              (0.0, 7700.0)], segments=32,
               mat=bkit.preset("white_plastic"))

    # aft deck: cockpit sole, two dining chairs, a sunpad and the swim platform
    bkit.rounded_box("YachtCockpitSole", 5200.0, 4200.0, 120.0, r=60.0,
                     segments=2, centre=(-7000.0, 0.0, 2760.0), mat=teak)
    bkit.rounded_box("YachtSunpad", 2600.0, 3600.0, 320.0, r=150.0,
                     segments=3, centre=(-9500.0, 0.0, 2900.0), mat=topside)
    bkit.rounded_box("YachtSwimPlatform", 1400.0, 4200.0, 160.0, r=80.0,
                     segments=2, centre=(-11300.0, 0.0, 2300.0), mat=teak)
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=2,
                                                   pitch_x=900.0,
                                                   pitch_y=1400.0)):
        bkit.rounded_box("YachtDiningChair%d" % i, 600.0, 600.0, 900.0, r=80.0,
                         segments=2, centre=(-6600.0 + x, y, 3260.0),
                         mat=topside)
    bkit.rounded_box("YachtDiningTable", 1200.0, 2000.0, 80.0, r=40.0,
                     segments=2, centre=(-6600.0, 0.0, 3320.0), mat=teak)

    # foredeck: a sunpad, a pulpit rail and a mast
    bkit.rounded_box("YachtForedeckSunpad", 3000.0, 3000.0, 260.0, r=120.0,
                     segments=3, centre=(6000.0, 0.0, 2760.0), mat=topside)
    bkit.cylinder("YachtForemast", 110.0, 3000.0, segments=16, axis="Z",
                  centre=(7000.0, 0.0, 4150.0), mat=steel)
    for i, (x, w) in enumerate(((8000.0, 900.0), (9000.0, 500.0),
                                (9800.0, 240.0))):
        for s in (1, -1):
            V.strut("YachtPulpitStanchion%d%s" % (i, "P" if s > 0 else "S"),
                    (x, s * w, 2700.0), (x, s * (w - 60.0), 3300.0), 22.0,
                    steel, 10)
    for i in range(2):
        a, b = ((8000.0, 840.0), (9000.0, 440.0)) if i == 0 else \
               ((9000.0, 440.0), (9800.0, 180.0))
        for s in (1, -1):
            V.strut("YachtPulpitRail%d%s" % (i, "P" if s > 0 else "S"),
                    (a[0], s * a[1], 3300.0), (b[0], s * b[1], 3300.0), 26.0,
                    steel, 10)

    # portholes are painted on the one watertight hull rather than modelled as
    # separate rings -- a ring of holes as real geometry would need 20 booleans
    # for a feature the render can only see as a dark dot
    bkit.assign_faces_by(hull, glass,
                         lambda c, n: (1750.0 <= c.z / bkit.MM <= 2000.0
                                       and abs(n.z) < 0.5))
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=22)
