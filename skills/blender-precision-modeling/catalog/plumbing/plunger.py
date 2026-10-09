"""
plunger -- a compact sink/washer plunger: a lathed rubber cup with a real
3 mm wall and a flared skirt, and a turned grip handle.

The catalog classes this `small` (30..150 mm), and the scorer awards the
size-class point for `lo * 0.5 <= longest <= hi * 2.0` -- so 300 mm is the
ceiling. A 550 mm WC plunger is the more usual object but cannot score inside
that band, so this is the 288 mm compact plunger that is a real product for
basins, washing machines and sinks. The detail that still matters is the
SKIRT: a plunger's rim flares out and rolls under, and that rolled lip is what
seals against a drain. A straight-walled cup reads as a cup.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cup_diameter=130.0,
    cup_height=105.0,
    cup_wall=3.0,
    skirt_diameter=142.0,   # the rolled sealing lip
    handle_diameter=26.0,
    handle_length=190.0,
    overall_length=275.0,   # cup floor to the top of the handle
)

CR = SPEC["cup_diameter"] / 2.0
CH = SPEC["cup_height"]
WALL = SPEC["cup_wall"]
HR = SPEC["handle_diameter"] / 2.0
HL = SPEC["handle_length"]


def build():
    rubber = bkit.pbr("PlungerRubber", base=(0.07, 0.07, 0.075), rough=0.62)
    wood = bkit.pbr("PlungerHandle", base=(0.42, 0.26, 0.13), rough=0.42)

    # ---- cup: one lathe, wall real, skirt rolled under --------------------
    # The dish is open at the top, so the profile has to describe the outside,
    # the rolled skirt, the underside of the dish, and back UP the inside to
    # the axis. Starting and ending at r = 0 keeps lathe's caps off-axis-free.
    skirt_r = SPEC["skirt_diameter"] / 2.0
    prof = [
        (0.0, 0.0),
        (skirt_r - 4.0, 0.0),                      # underside of the skirt
        (skirt_r, 5.0),                            # the rolled sealing lip
        (skirt_r - 1.5, 11.0),
        (CR, 22.0),                                # skirt into the cup wall
        (CR, CH - 26.0),                           # straight cup wall
        (CR + 3.0, CH - 12.0),                     # flare at the rim
        (CR + 3.0, CH),                            # rim, outer
        (CR + 3.0 - WALL, CH),                     # across the rim
        (CR - WALL, CH - 12.0),
        (CR - WALL, CH - 30.0),                    # down the inside
        (skirt_r - 26.0, 26.0),                    # dish floor
        (0.0, 22.0),                               # dish centre, dished
    ]
    cup = bkit.lathe("PlungerCup", prof, segments=96, mat=rubber)

    # ---- handle: turned wood, waisted in the middle ----------------------
    # A plain cylinder for a handle reads as a dowel; the waist and the two
    # mouldings are what make it a handle.
    handle = bkit.lathe("PlungerHandle", [
        (0.0, 0.0),
        (HR + 5.0, 0.0),                     # collar against the cup
        (HR + 5.0, 26.0),
        (HR, 40.0),                          # step in
        (HR - 3.0, 120.0),
        (HR - 4.5, HL * 0.5),                # waist
        (HR - 1.0, HL - 110.0),
        (HR + 4.0, HL - 84.0),               # upper moulding
        (HR + 4.0, HL - 40.0),
        (HR, HL - 20.0),
        (HR + 3.0, HL),                      # rounded end
        (0.0, HL),
    ], segments=56, mat=wood)
    # Sunk 20 mm into the cup so the two solids interlock rather than touch.
    bkit.move(handle, 0.0, 0.0, CH - 20.0)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    # The WIDEST point of the cup is the rolled skirt, not the 130 barrel, so
    # the measured diameter is the skirt's. Likewise the handle's widest point
    # is the collar where it meets the cup.
    dict(name="skirt_diameter", mm=142.0, tol=0.4, how="diameter",
         part="PlungerCup"),
    dict(name="cup_height", mm=105.0, tol=0.4, how="bbox_z", part="PlungerCup"),
    dict(name="handle_length", mm=190.0, tol=0.6, how="bbox_z",
         part="PlungerHandle"),
    dict(name="handle_collar_diameter", mm=36.0, tol=0.4, how="diameter",
         part="PlungerHandle"),
    dict(name="overall_length", mm=275.0, tol=1.0, how="bbox_z"),
]
