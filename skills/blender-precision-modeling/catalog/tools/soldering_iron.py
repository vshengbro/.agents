"""
soldering_iron -- 210 mm mains soldering iron, 6.6 mm barrel.

Tip down at z=0 so the model stands on its own point the way a hot iron would
rest in a stand, and the copper tip is the first thing the camera sees.

The tip is a lathe cone with a blunt 0.7 mm end, not a needle: a real
soldering tip is a truncated cone because the flat is what transfers heat.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=211.0,
    tip_length=40.0,
    barrel_diameter=13.2,
    handle_diameter=22.0,
    handle_length=101.0,
)


def build():
    copper = bkit.pbr("IronCopper", base=(0.88, 0.54, 0.36), metal=0.55,
                      rough=0.28)
    steel = bkit.pbr("BarrelMetal", base=(0.38, 0.39, 0.42), metal=0.28,
                     rough=0.40)
    shell = bkit.pbr("IronHandle", base=(0.055, 0.16, 0.46), rough=0.30)
    cord = bkit.pbr("IronCord", base=(0.11, 0.11, 0.12), rough=0.45)

    tip = bkit.lathe("SolderingIronTip",
                     [(0, 0), (0.7, 0), (1.6, 8), (3.2, 18),
                      (5.0, 30), (5.6, 40), (0, 40)], segments=56,
                     mat=copper)
    bkit.recalc(tip)

    barrel = bkit.cylinder("SolderingIronBarrel", 6.6, 50.0, segments=48,
                           centre=(0, 0, 64.0), mat=steel)

    handle = bkit.lathe("SolderingIronHandle",
                        [(0, 89), (9.5, 89), (11, 100), (10.4, 140),
                         (10.8, 176), (9, 190), (0, 190)], segments=56,
                        mat=shell)
    bkit.recalc(handle)

    strain = bkit.cylinder("SolderingIronStrain", 5.0, 22.0, segments=40,
                           r2=4.0, centre=(0, 0, 200.0), mat=cord)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="tip_length", mm=40.0, tol=0.5, how="bbox_z",
         part="SolderingIronTip"),
    dict(name="barrel_diameter", mm=13.2, tol=0.4, how="diameter",
         part="SolderingIronBarrel"),
    dict(name="handle_diameter", mm=22.0, tol=0.4, how="diameter",
         part="SolderingIronHandle"),
    dict(name="overall_length", mm=211.0, tol=1.2, how="bbox_z"),
]