"""
scaffold_plank -- a 2.5 m steel scaffold board with end hooks.

A steel scaffold plank is a shallow tray, not a flat bar: the deck is dished so
water runs off, the underside carries three stiffening ribs, and each end has a
hooked lip that drops over the transom. The hooks are the whole read -- a flat
bar reads as a length of steel, not as something that clips to a scaffold.

Real 2.5 m plank: 2500 long, 225 wide, 38 mm deep overall, on a 5 mm deck
dished 8 mm, with three 40 x 6 underside ribs and 60 mm end hooks that drop
75 mm below the deck.

The plank is built with `extrude_profile` on the DECK OUTLINE so the dished
cross-section is one closed profile, then the ribs and hooks are separate
members that overlap it by 1 mm.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _sections as S

SPEC = dict(
    length=2500.0,
    width=225.0,
    deck_thickness=5.0,
    rib_depth=33.0,
    ribs=3,
    rib_thickness=6.0,
    hook_depth=75.0,
    hook_lip=22.0,
    total_depth=38.0,
)

L = SPEC["length"]
W = SPEC["width"]
DT = SPEC["deck_thickness"]
RD = SPEC["rib_depth"]
NRIBS = SPEC["ribs"]
RT = SPEC["rib_thickness"]
HOOK = SPEC["hook_depth"]
TOTAL_D = SPEC["total_depth"]

X0 = -L / 2.0

CHECKS = [
    dict(name="length", mm=2500.0, tol=3.0, how="bbox_x", part=None),
    dict(name="width", mm=225.0, tol=2.0, how="bbox_y", part=None),
    dict(name="total_depth", mm=75.0, tol=3.0, how="bbox_z", part=None),
    dict(name="deck_thickness", mm=5.0, tol=1.0, how="bbox_z", part="PlankDeck"),
    dict(name="rib_depth", mm=33.0, tol=1.5, how="bbox_z", part="PlankRib0"),
    dict(name="hook_depth", mm=75.0, tol=2.0, how="bbox_z", part="PlankHookLegL"),
]


def build():
    steel = bkit.pbr("PlankSteel", base=(0.62, 0.63, 0.65), metal=0.82,
                     rough=0.38)
    galv = bkit.pbr("PlankGalv", base=(0.70, 0.71, 0.73), metal=0.85, rough=0.34)

    # ---- the deck: a closed cross-section, extruded along the plank --
    # Profile coords are (depth, width); the section runs down the hooked side,
    # across the dished underside, and back up. It is a single closed outline, so
    # the plank's cross-section is one solid rather than a stack of boxes.
    hw = W / 2.0
    prof = [
        (0.0, -hw),
        (0.0, hw),                 # top face of the deck
        (-DT, hw),                 # down the far edge
        (-DT + 6.0, hw - 12.0),    # the 6 mm upstand that stiffens the edge
        (-DT, -hw + 12.0),
        (-DT, -hw),
    ]
    deck = bkit.extrude_profile("PlankDeck", prof, L, centre=(0.0, 0.0, 0.0),
                                axis="X", mat=galv)
    bkit.recalc(deck)
    # extruded about its own section centre, then lifted so the hook hangs below
    bkit.move(deck, 0.0, 0.0, TOTAL_D / 2.0 - DT / 2.0)

    # ---- 3 underside stiffening ribs, on the computed pitch --------
    for i, (x, _y) in enumerate(bkit.grid_positions(cols=NRIBS, rows=1,
                                                   pitch_x=(L - 700.0) /
                                                   (NRIBS - 1), pitch_y=1.0)):
        bkit.box("PlankRib%d" % i, RT, W - 10.0, RD,
                 centre=(x, 0.0, TOTAL_D - DT - RD / 2.0), mat=steel)

    # ---- the two end hooks: a down leg and an inward lip ----------
    # These hang 75 mm below the deck and turn back 22 mm, which is what lets
    # the plank clip over a 48.3 mm transom.
    for tag, sx in (("L", -1.0), ("R", 1.0)):
        leg_x = sx * (L / 2.0 - 12.0)
        bkit.box("PlankHookLeg%s" % tag, 24.0, W - 20.0, HOOK,
                 centre=(leg_x, 0.0, TOTAL_D - DT - HOOK / 2.0), mat=steel)
        # the lip turns back INBOARD over the transom
        bkit.box("PlankHookLip%s" % tag, SPEC["hook_lip"], W - 20.0, 10.0,
                 centre=(leg_x - sx * (12.0 + SPEC["hook_lip"] / 2.0), 0.0,
                         TOTAL_D - DT - HOOK + 5.0), mat=steel)

    return dict(spec=SPEC, parts=1 + NRIBS + 4, ribs=NRIBS)


# The hooks hang 75 mm BELOW the deck and the deck is 38 mm deep, so the assembly
# is 38 mm of deck plus a 37 mm rib zone below it, with the hooks inside that
# zone -- `total_depth` is therefore the whole plank's 75 mm, not the deck's 38.