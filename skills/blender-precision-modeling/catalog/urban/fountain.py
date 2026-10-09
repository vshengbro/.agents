"""
fountain -- 2500 x 2500 x 1010 mm public fountain: a 2400 mm basin with a real
50 mm wall and coping, a 340 mm water body, a lathed pedestal, an upper bowl, a
finial and four radial jets.

`large`. Everything circular is a `lathe` over a profile that includes the wall
thickness, so the basin is a bowl with a floor you can see into rather than a
solid drum -- the single thing that decides whether a fountain reads as a
fountain. The four jets are one `cylinder` swept by `array_radial`, built at its
radius from the world origin.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    basin_diameter=2400.0,
    basin_wall=50.0,
    basin_height=420.0,
    coping_diameter=2500.0,
    pedestal_diameter=360.0,
    bowl_diameter=1200.0,
    water_depth=340.0,
    jets=4,
    overall_height=1010.0,
)

R = SPEC["basin_diameter"] / 2.0
WALL = SPEC["basin_wall"]


def build():
    stone = bkit.pbr("FountainStone", base=(0.70, 0.68, 0.63), rough=0.60)
    stone2 = bkit.pbr("FountainStoneWorn", base=(0.60, 0.58, 0.54),
                      rough=0.70)
    water = bkit.pbr("FountainWater", base=(0.22, 0.45, 0.52), rough=0.06,
                     transmission=0.45, ior=1.33)
    jet = bkit.pbr("FountainJet", base=(0.55, 0.72, 0.80), rough=0.08,
                   transmission=0.35,
                   emission=(0.45, 0.65, 0.75), emission_strength=0.8)
    bronze = bkit.preset("brushed_metal")

    # ---- two steps up to the basin -------------------------------------
    bkit.lathe("FountainStep1", [(0.0, 0.0), (1380.0, 0.0), (1380.0, 80.0),
                                 (1300.0, 80.0), (0.0, 80.0)], segments=64,
               mat=stone2)
    bkit.lathe("FountainStep2", [(0.0, 80.0), (1300.0, 80.0), (1300.0, 150.0),
                                 (R + 2.0, 150.0), (R + 2.0, 80.0),
                                 (0.0, 80.0)], segments=64, mat=stone2)

    # ---- basin with a real wall and a coping torus ---------------------
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("FountainBasin", [
        (0.0, 150.0), (R, 150.0), (R, SPEC["basin_height"]), (R - WALL,
        SPEC["basin_height"]), (R - WALL, 210.0), (0.0, 210.0),
    ], segments=72, mat=stone)
    bkit.torus("FountainCoping", R - WALL / 2.0, WALL + 20.0, seg_major=72,
               seg_minor=16, centre=(0.0, 0.0, SPEC["basin_height"]),
               mat=stone2)

    # ---- water body -----------------------------------------------------
    bkit.lathe("FountainWater", [
        (0.0, 215.0), (R - WALL - 4.0, 215.0), (R - WALL - 4.0, 215.0
                                                        + SPEC["water_depth"]),
        (0.0, 215.0 + SPEC["water_depth"]),
    ], segments=64, mat=water)

    # ---- central pedestal, upper bowl and finial -----------------------
    bkit.lathe("FountainPedestal", [
        (0.0, 215.0), (180.0, 215.0), (150.0, 620.0), (110.0, 700.0),
        (200.0, 760.0), (210.0, 800.0), (0.0, 800.0),
    ], segments=56, mat=stone)
    bkit.lathe("FountainBowl", [
        (0.0, 780.0), (600.0, 780.0), (580.0, 850.0), (300.0, 900.0),
        (0.0, 900.0),
    ], segments=56, mat=stone2)
    bkit.tube("BowlRim", 605.0, 575.0, 40.0, segments=56,
              centre=(0.0, 0.0, 800.0), mat=stone)
    bkit.lathe("FountainFinial", [
        (0.0, 890.0), (70.0, 900.0), (95.0, 950.0), (70.0, 1000.0),
        (0.0, 1010.0),
    ], segments=40, mat=bronze)

    # ---- four radial jets, swept about the world origin -----------------
    jet_part = bkit.cylinder("_jet", 16.0, 260.0, segments=20, r2=7.0,
                             centre=(420.0, 0.0, 560.0), mat=jet)
    bkit.array_radial(jet_part, count=SPEC["jets"], axis="Z")
    jet_part.name = "WaterJets"
    bkit.recalc(jet_part)

    # ---- spout blocks at each jet base, swept with the jets -------------
    # Built at radius 300 from the world origin, like the jets themselves.
    spout = bkit.rounded_box("_spout", 90.0, 90.0, 70.0, r=10.0, segments=2,
                             mat=bronze, centre=(300.0, 0.0, 620.0))
    bkit.array_radial(spout, count=SPEC["jets"], axis="Z")
    spout.name = "JetSpouts"

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="basin_diameter", mm=2400.0, tol=2.0, how="diameter",
         part="FountainBasin"),
    dict(name="basin_height", mm=270.0, tol=1.5, how="bbox_z",
         part="FountainBasin"),
    dict(name="coping_diameter", mm=2490.0, tol=2.0, how="diameter",
         part="FountainCoping"),
    dict(name="bowl_diameter", mm=1200.0, tol=2.0, how="diameter",
         part="FountainBowl"),
    dict(name="overall_height", mm=1010.0, tol=3.0, how="bbox_z"),
]