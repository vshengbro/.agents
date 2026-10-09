"""
bunk_bed -- 1050 x 2050 mm bunk bed, upper mattress 1500 mm, posts to 1700 mm.

Bunk proportion is a clearance problem, not a style problem. The lower mattress
top is at 570 mm and the upper deck starts at 1250 mm, so a seated child on the
lower bunk has 680 mm of headroom -- the number that decides whether the thing
is usable. The ladder is then a fifth system sized to that gap: two 1150 mm
stiles with five 25 mm rungs at a computed 212.5 mm pitch.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=1050.0,
    length=2050.0,
    overall_height=1700.0,
    post_section=80.0,
    mattress_width=890.0,
    mattress_length=1850.0,
    mattress_thickness=220.0,
    lower_mattress_top=570.0,
    upper_deck_bottom=1250.0,
    rail_height=150.0,
    rail_thickness=70.0,
    deck_thickness=30.0,
    headroom=680.0,          # upper deck bottom minus lower mattress top
    ladder_stile_height=1150.0,
    ladder_rung_count=5,
    ladder_rung_thickness=25.0,
    ladder_rung_gap=212.5,
    ladder_rung_length=500.0,
)

W, L, H = SPEC["width"], SPEC["length"], SPEC["overall_height"]
POST = SPEC["post_section"]
POST_X = W / 2.0 - POST / 2.0                 # 485
POST_Y = L / 2.0 - POST / 2.0                 # 985
MW, ML = SPEC["mattress_width"], SPEC["mattress_length"]
MT = SPEC["mattress_thickness"]
RAIL_H = SPEC["rail_height"]
RAIL_T = SPEC["rail_thickness"]
DECK_T = SPEC["deck_thickness"]
LOW_TOP = SPEC["lower_mattress_top"]          # 570
UPPER_DECK = SPEC["upper_deck_bottom"]        # 1250: underside of the rails
# A deck's usable surface is its rails plus its slat board, NOT the rail
# bottom: offsetting the mattress from UPPER_DECK alone drops it 180 mm into
# the rails, which still measures 220 mm thick and passes every check while
# rendering as a mattress buried in the frame.
DECK_SURFACE = RAIL_H + DECK_T                # 180
LOW_DECK_Z1 = LOW_TOP - MT                    # 350: top of the lower deck
RAIL_Z0 = LOW_DECK_Z1 - DECK_SURFACE          # 170
UPPER_SURFACE = UPPER_DECK + DECK_SURFACE     # 1430
UPPER_TOP = UPPER_SURFACE + MT                # 1650
LADDER_MID = 825.0

CHECKS = [
    dict(name="overall_width", mm=1050.0, tol=0.4, how="bbox_x"),
    dict(name="overall_length", mm=2050.0, tol=0.4, how="bbox_y"),
    dict(name="overall_height", mm=1700.0, tol=0.4, how="bbox_z"),
    dict(name="mattress_width", mm=890.0, tol=0.3, how="bbox_x",
         part="MattressLower"),
    dict(name="mattress_thickness", mm=220.0, tol=0.3, how="bbox_z",
         part="MattressLower"),
    dict(name="upper_mattress_thickness", mm=220.0, tol=0.3, how="bbox_z",
         part="MattressUpper"),
    dict(name="ladder_rung_length", mm=500.0, tol=0.3, how="bbox_x",
         part="LadderRung1"),
]


def _deck(tag, rail_z0, mat_deck, mat_rail):
    """Side, head and foot rails plus the slat deck for one bunk level."""
    for (sx, s_tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Rail%s%s" % (tag, s_tag), RAIL_T,
                         L - 2 * POST, RAIL_H, r=5.0, segments=2,
                         centre=(sx * (W / 2.0 - RAIL_T / 2.0), 0,
                                 rail_z0 + RAIL_H / 2.0),
                         mat=mat_rail)
    for (sy, s_tag) in ((-1, "Foot"), (1, "Head")):
        bkit.rounded_box("Rail%s%s" % (tag, s_tag), W - 2 * POST, RAIL_T, RAIL_H,
                         r=5.0, segments=2,
                         centre=(0, sy * (L / 2.0 - RAIL_T / 2.0),
                                 rail_z0 + RAIL_H / 2.0),
                         mat=mat_rail)
    bkit.rounded_box("Deck%s" % tag, W - 2 * POST, L - 2 * POST, DECK_T, r=3.0,
                     segments=2,
                     centre=(0, 0, rail_z0 + RAIL_H + DECK_T / 2.0),
                     mat=mat_deck)


def build():
    wood = bkit.pbr("BunkPine", base=(0.58, 0.42, 0.24), metal=0.0, rough=0.44)
    wood_dk = bkit.pbr("BunkRail", base=(0.46, 0.32, 0.17), metal=0.0, rough=0.50)
    linen = bkit.pbr("BunkLinen", base=(0.78, 0.78, 0.75), metal=0.0, rough=0.86)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            bkit.rounded_box("Post%s%s" % (yn, xn), POST, POST, H, r=6.0,
                             segments=3,
                             centre=(sx * POST_X, sy * POST_Y, H / 2.0),
                             mat=wood)

    # lower deck: rails 170..320, board 320..350, mattress 350..570
    _deck("Lower", RAIL_Z0, wood_dk, wood)
    bkit.rounded_box("MattressLower", MW, ML, MT, r=24.0, segments=3,
                     centre=(0, 0, LOW_DECK_Z1 + MT / 2.0), mat=linen)

    # upper deck: rails 1250..1400, board 1400..1430, mattress 1430..1650
    _deck("Upper", UPPER_DECK, wood_dk, wood)
    bkit.rounded_box("MattressUpper", MW, ML, MT, r=24.0, segments=3,
                     centre=(0, 0, UPPER_SURFACE + MT / 2.0), mat=linen)

    # ---- ladder: stiles on the front face, rungs at a computed pitch ------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("LadderStile%s" % tag, 50.0, 40.0,
                         SPEC["ladder_stile_height"], r=6.0, segments=3,
                         centre=(sx * 250.0, -1000.0, LADDER_MID), mat=wood)
    for i, (dz, _t) in enumerate(
            bkit.lay_out([SPEC["ladder_rung_thickness"]]
                         * SPEC["ladder_rung_count"],
                         gap=SPEC["ladder_rung_gap"])):
        bkit.rounded_box("LadderRung%d" % (i + 1),
                         SPEC["ladder_rung_length"],
                         SPEC["ladder_rung_thickness"],
                         SPEC["ladder_rung_thickness"], r=6.0, segments=3,
                         centre=(0, -1000.0, LADDER_MID + dz), mat=wood)

    return dict(spec=SPEC, parts=19)
