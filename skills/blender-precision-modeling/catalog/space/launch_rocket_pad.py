"""
launch_rocket_pad -- a two-launch mount with a 118 m umbilical tower, a
flame trench and a 49 m water tower.

Size class `huge` (3000..40000 mm). Stated at 1:1000 scale: the tower is
11 800 mm, the deck 2 400 mm across, the pad 18 000 mm. The real ratios are
preserved -- an umbilical tower taller than the vehicle it serves, a flame
trench running UNDER the mount, and the strong diagonal of the hammerhead
crane.

What makes it a launch complex and not a tower with a box on it:
1. the flame trench is a real cut through the deck, so the mount sits over a
   slot and the exhaust has somewhere to go,
2. the umbilical tower carries nine swing arms on a computed floor pitch --
   that pitch is the classic repeated feature and it is laid out, not typed,
3. the strongback diagonal brace runs the full height, which is the thing
   that visually stiffens a launch tower,
4. the water tower and the deluge headers sit apart, as they do on a real pad.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tower_height=11800.0,
    tower_width=2400.0,
    swing_arms=9,
    swing_arm_floor=1180.0,     # one storey of the tower
    deck_width=14400.0,
    deck_thickness=900.0,
    flame_trench_width=1800.0,
    flame_trench_depth=1400.0,
    strongback_base=3600.0,
    water_tower_height=6100.0,
)

TH = SPEC["tower_height"]
TW = SPEC["tower_width"]
FLOOR = SPEC["swing_arm_floor"]
DW = SPEC["deck_width"]
DT = SPEC["deck_thickness"]
TR = SPEC["flame_trench_width"]
TD = SPEC["flame_trench_depth"]


def build():
    concrete = bkit.pbr("PadConcrete", base=(0.42, 0.42, 0.41), rough=0.88)
    deck_mat = bkit.pbr("PadDeck", base=(0.30, 0.30, 0.30), rough=0.82)
    steel = bkit.pbr("TowerSteel", base=(0.58, 0.58, 0.57), metal=0.85, rough=0.36)
    paint = bkit.pbr("TowerPaint", base=(0.72, 0.30, 0.16), rough=0.52)
    dark = bkit.pbr("PadDark", base=(0.14, 0.14, 0.15), rough=0.66)
    water = bkit.pbr("WaterTank", base=(0.78, 0.80, 0.82), metal=0.85, rough=0.30)

    # ---- launch deck: a slab with a real trench slot --------------------
    # The trench is cut with a cutter whose segment count deliberately differs
    # from nothing in particular (the deck is a box, so any count works) --
    # the point is that the slot is a THROUGH cut with 40 mm of overlap on
    # every side, so the deck is not left as two exactly-touching halves.
    deck = bkit.rounded_box("LaunchDeck", DW, DW, DT, r=40.0,
                            centre=(0.0, 0.0, -DT / 2.0), mat=deck_mat)
    trench = bkit.box("_trench_cut", TR, DW * 1.4, DT + 400.0,
                      centre=(0.0, 0.0, -DT / 2.0))
    bkit.boolean(deck, trench, "DIFFERENCE")
    bkit.recalc(deck)
    # the trench walls and floor below it
    bkit.rounded_box("FlameTrenchFloor", TR + 80.0, DW * 1.2, 300.0, r=20.0,
                     centre=(0.0, 0.0, -DT - TD), mat=concrete)
    for (s, sign) in (("L", 1.0), ("R", -1.0)):
        bkit.rounded_box("TrenchWall" + s, 40.0, DW * 1.2, TD, r=10.0,
                         centre=(sign * (TR / 2.0 + 20.0), 0.0, -DT / 2.0),
                         mat=concrete)

    # ---- launch mount: the four hold-down legs over the trench ----------
    for (name, lx, ly) in (("MountFL", -1.0, -1.0), ("MountFR", 1.0, -1.0),
                          ("MountRL", -1.0, 1.0), ("MountRR", 1.0, 1.0)):
        bkit.rounded_box(name, 420.0, 420.0, 1500.0, r=30.0,
                         centre=(lx * (TR / 2.0 + 320.0), ly * 900.0, 750.0),
                         mat=steel)
    bkit.rounded_box("MountDeck", TR + 1400.0, 2200.0, 300.0, r=30.0,
                     centre=(0.0, 0.0, 1350.0), mat=steel)

    # ---- umbilical tower: four legs, floors, and swing arms -------------
    # Floor pitch is the declared storey height, so the nine swing arms land on
    # storeys by construction rather than by nine hand-typed z values.
    floors = int(TH / FLOOR)
    for (name, lx, ly) in (("LegFL", -1.0, -1.0), ("LegFR", 1.0, -1.0),
                          ("LegRL", -1.0, 1.0), ("LegRR", 1.0, 1.0)):
        bkit.rounded_box(name, 300.0, 300.0, TH, r=24.0,
                         centre=(lx * TW / 2.0, ly * TW / 2.0, TH / 2.0),
                         mat=paint)
    for i in range(floors):
        z = FLOOR * (i + 0.5)
        bkit.rounded_box("Floor%02d" % (i + 1), TW, TW, 120.0, r=12.0,
                         centre=(0.0, 0.0, z), mat=steel)
    # ---- swing arms: the repeated feature, on the computed storey pitch --
    for i in range(SPEC["swing_arms"]):
        z = FLOOR * (i + 0.5) + FLOOR * 0.5
        reach = 900.0 + 90.0 * (i % 3)
        bkit.rounded_box("SwingArm%02d" % (i + 1), TW / 2.0 + reach, 220.0,
                         260.0, r=30.0,
                         centre=(-(TW / 2.0 + (TW / 2.0 + reach) / 2.0 - TW / 4.0),
                                 0.0, z), mat=paint)
        bkit.rounded_box("ArmTruss%02d" % (i + 1), reach, 60.0, 60.0, r=16.0,
                         centre=(-(TW / 2.0 + reach / 2.0), 0.0, z - 220.0),
                         mat=steel)
    # ---- strongback: the full-height diagonal brace --------------------
    sb_len = math.hypot(TH, SPEC["strongback_base"])
    sb = bkit.rounded_box("Strongback", sb_len, 220.0, 300.0, r=40.0,
                          centre=(0.0, TW / 2.0 + 400.0, TH / 2.0), mat=steel)
    sb.rotation_euler = (0.0, math.atan2(SPEC["strongback_base"], TH), 0.0)

    # ---- hammerhead crane at the top ------------------------------------
    bkit.rounded_box("HammerheadBoom", 3200.0, 400.0, 400.0, r=40.0,
                     centre=(-900.0, 0.0, TH + 300.0), mat=paint)
    bkit.rounded_box("HammerheadCounterweight", 900.0, 700.0, 700.0, r=40.0,
                     centre=(900.0, 0.0, TH + 300.0), mat=dark)

    # ---- lightning masts -------------------------------------------------
    for (name, mx, my) in (("MastA", -3900.0, -3900.0), ("MastB", 3900.0, 3900.0)):
        bkit.cylinder(name, 60.0, 4200.0, segments=14,
                      centre=(mx, my, 2100.0), smooth=True, mat=steel)
        bkit.rounded_box(name + "Tip", 30.0, 30.0, 1200.0, r=8.0,
                         centre=(mx, my, 4500.0), mat=steel)

    # ---- water tower and deluge headers ---------------------------------
    bkit.cylinder("WaterTank", 1400.0, 2600.0, segments=32,
                  centre=(-DW * 0.40, DW * 0.42, SPEC["water_tower_height"] - 1300.0),
                  smooth=True, mat=water)
    for i, (mx, my) in enumerate(((-900.0, 900.0), (900.0, -900.0))):
        bkit.cylinder("WaterLeg%d" % (i + 1), 90.0,
                      SPEC["water_tower_height"] - 2600.0, segments=12,
                      centre=(-DW * 0.40 + mx, DW * 0.42 + my,
                              (SPEC["water_tower_height"] - 2600.0) / 2.0),
                      smooth=True, mat=steel)
    for i, y in enumerate((-2600.0, 2600.0)):
        bkit.cylinder("DelugeHeader%d" % (i + 1), 130.0, DW * 0.80, segments=14,
                      centre=(0.0, y, -DT - TD - 200.0), axis="X",
                      smooth=True, mat=paint)

    return dict(spec=SPEC,
                parts=3 + 2 + 4 + 1 + 4 + floors + SPEC["swing_arms"] * 2
                + 1 + 2 + 2 * 2 + 1 + 2 + 2)


CHECKS = [
    dict(name="tower_height", mm=11800.0, tol=20.0, how="bbox_z", part="LegFL"),
    # LegFL is one 300 mm column: bbox_x measures the column, not the tower.
    # The tower width is the distance between leg centres, which is not a
    # bounding box of anything, so the leg pitch is declared on the floor.
    dict(name="tower_floor_width", mm=2400.0, tol=4.0,
         how="bbox_x", part="Floor09"),
    dict(name="deck_width", mm=14400.0, tol=20.0, how="bbox_x", part="LaunchDeck"),
    dict(name="deck_thickness", mm=900.0, tol=10.0,
         how="bbox_z", part="LaunchDeck"),
    dict(name="water_tank_diameter", mm=2800.0, tol=30.0,
         how="diameter", part="WaterTank"),
    dict(name="deluge_header_length", mm=11520.0, tol=60.0,
         how="bbox_x", part="DelugeHeader1"),
    dict(name="overall_width", mm=14855.0, tol=20.0, how="bbox_x"),
    dict(name="overall_height", mm=15080.0, tol=200.0, how="bbox_z"),
]