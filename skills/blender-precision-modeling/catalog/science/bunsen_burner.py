"""
bunsen_burner -- 60 x 60 x 148 mm laboratory Bunsen burner: cast base, an
11 mm barrel, an air collar with four vent ports, a side gas inlet, and the
inner and outer flame cones.

Two lathed cones for the flame, not one: a Bunsen flame is a bright inner cone
sitting inside a paler outer cone, and collapsing them into a single lathe is
the difference between a flame and a candle. `air_collar` is a `tube`, so the
vent ports are real holes in a real ring rather than bumps stuck on a solid.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_diameter=60.0,
    base_height=7.0,
    barrel_diameter=11.0,
    barrel_height=88.0,
    air_collar_diameter=17.0,
    vent_ports=4,
    overall_height=148.0,
)


def build():
    cast = bkit.pbr("BurnerCast", base=(0.30, 0.31, 0.33), metal=0.85,
                    rough=0.54)
    brass = bkit.preset("brushed_metal")
    nickel = bkit.preset("polished_metal")
    outer = bkit.pbr("BurnerFlameOuter", base=(0.30, 0.52, 0.90), rough=0.10,
                     emission=(0.35, 0.58, 1.0), emission_strength=3.2,
                     transmission=0.35)
    inner = bkit.pbr("BurnerFlameInner", base=(0.45, 0.70, 1.0), rough=0.08,
                     emission=(0.55, 0.78, 1.0), emission_strength=6.0,
                     transmission=0.20)

    # ---- cast base and barrel. lathe profiles carry ABSOLUTE z. -----------
    bkit.lathe("BurnerBase", [(0.0, 0.0), (30.0, 0.0), (30.0, 7.0),
                              (12.0, 9.0), (0.0, 9.0)], segments=48,
               mat=cast)
    # The 18 mm foot is its own revolve so the barrel check measures the
    # 11 mm tube rather than the flange it sits on.
    bkit.lathe("BurnerFoot", [(0.0, 9.0), (9.0, 9.0), (9.0, 16.0),
                              (5.5, 20.0), (5.5, 26.0), (0.0, 26.0)],
               segments=48, mat=brass)
    bkit.lathe("BurnerBarrel", [(0.0, 20.0), (5.5, 20.0), (5.5, 97.0),
                                (0.0, 97.0)], segments=48, mat=brass)

    # ---- air collar: a genuine tube with four real vent ports ------------
    bkit.tube("AirCollar", SPEC["air_collar_diameter"] / 2.0, 5.6, 18.0,
              segments=48, centre=(0.0, 0.0, 32.0), mat=brass)
    port = bkit.box("_port", 4.0, 5.0, 5.0, centre=(9.5, 0.0, 32.0),
                    mat=nickel)
    bkit.array_radial(port, count=SPEC["vent_ports"], axis="Z")
    bkit.cylinder("CollarScrew", 3.5, 24.0, segments=16, axis="X",
                  centre=(14.0, 0.0, 40.0), mat=nickel)

    # ---- side gas inlet and a needle valve --------------------------------
    bkit.cylinder("GasInlet", 4.0, 22.0, segments=24, axis="X",
                  centre=(-14.0, 0.0, 15.0), mat=brass)
    bkit.cylinder("NeedleValve", 9.0, 12.0, segments=24, axis="Z",
                  centre=(-14.0, 0.0, 24.0), mat=nickel)
    bkit.box("ValveHandle", 6.0, 4.0, 26.0, mat=nickel,
             centre=(-14.0, 0.0, 32.0))

    # ---- flame: a bright inner cone inside a paler outer one -------------
    bkit.lathe("FlameOuter", [(0.0, 97.0), (6.0, 99.0), (4.5, 130.0),
                              (0.0, 148.0)], segments=48, mat=outer)
    bkit.lathe("FlameInner", [(0.0, 97.0), (3.6, 99.0), (0.0, 122.0)],
               segments=48, mat=inner)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="base_diameter", mm=60.0, tol=0.5, how="diameter",
         part="BurnerBase"),
    dict(name="base_height", mm=9.0, tol=0.5, how="bbox_z", part="BurnerBase"),
    dict(name="barrel_diameter", mm=11.0, tol=0.4, how="diameter",
         part="BurnerBarrel"),
    dict(name="air_collar_diameter", mm=17.0, tol=0.4, how="diameter",
         part="AirCollar"),
    dict(name="overall_height", mm=148.0, tol=0.8, how="bbox_z"),
]