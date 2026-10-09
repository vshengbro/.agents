"""
flatbed_wagon -- 14 m bogie flat wagon with side stakes, deck at 1,250 mm.

A flat wagon is 95 % empty, so the read is entirely in the deck and the
stake pockets. The deck is a run of transverse planks laid out by
`array_linear(..., world=True)` rather than typed as coordinates, and the
bunnings are a computed row from `evenly()` -- sixteen sockets a side at
900 mm centres is the difference between a wagon and a bare solebar pair.

A flat wagon is still a railway vehicle: four axles on two two-axle bogies,
buffers at 1,065 mm over the railhead, a brake wheel and a step at each end.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=14000.0,
    deck_length=13200.0,
    deck_width=2900.0,
    deck_z=1250.0,
    stake_pitch=900.0,
    stake_height=1300.0,
    stake_count_per_side=16,
    wheel_diameter=840.0,
    payload_t=27.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="length_over_buffers", mm=14000.0, tol=3.0, how="bbox_x",
         part="FlatFrame"),
    dict(name="deck_z", mm=1250.0, tol=3.0, how="top_z", part="FlatFrame"),
    dict(name="deck_width", mm=2900.0, tol=3.0, how="bbox_y", part="FlatFrame"),
    dict(name="deck_length", mm=13200.0, tol=4.0, how="bbox_x",
         part="FlatDeck"),
    dict(name="stake_top_z", mm=2550.0, tol=4.0, how="top_z",
         part="FlatStakes"),
    dict(name="stake_envelope_length", mm=13790.0, tol=4.0, how="bbox_x",
         part="FlatStakes"),
    dict(name="wheel_flange_diameter", mm=896.0, tol=3.0, how="bbox_z",
         part="FlatAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min", part="FlatAxles"),
]

LENGTH = 14000.0
HALF_W = 1450.0
DECK_Z = 1250.0
DECK_L = 13700.0
STAKE_H = 1300.0
STAKE_N = 16
WHEEL_D = 840.0
BOGIE_X = 3500.0
BOGIE_WB = 2000.0


def build():
    frame_m = bkit.pbr("FlatFramePaint", base=(0.30, 0.19, 0.12), rough=0.60)
    plank_m = bkit.pbr("FlatPlank", base=(0.44, 0.33, 0.21), rough=0.72)
    steel = bkit.preset("dark_metal")
    rust_steel = bkit.pbr("FlatRust", base=(0.34, 0.26, 0.19), metal=0.72,
                          rough=0.64)

    R.underframe("FlatFrame", LENGTH, half_w=HALF_W, z_bot=950.0, depth=300.0,
                 mat=frame_m)

    # transverse deck planks, laid out by pitch in WORLD space
    plank = bkit.rounded_box("FlatPlank", 240.0, 2.0 * HALF_W - 60.0, 50.0,
                             r=8.0, segments=2,
                             centre=(0.0, 0.0, DECK_Z - 25.0), mat=plank_m)
    bkit.array_linear(plank, 28, (480.0, 0.0, 0.0), world=True)
    bkit.move(plank, -(27 * 480.0) / 2.0, 0.0, 0.0)
    plank.name = "FlatDeck"

    # stake pockets and stakes, evenly spread both sides
    stakes = []
    for i, x in enumerate(R.evenly(STAKE_N, 13500.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            stakes.append(bkit.rounded_box("FlatStake%s%d" % (tag, i), 130.0,
                                           150.0, STAKE_H, r=18.0, segments=2,
                                           centre=(x, s * (HALF_W + 10.0),
                                                   DECK_Z + STAKE_H / 2.0),
                                           mat=plank_m))
            stakes.append(bkit.rounded_box("FlatSocket%s%d" % (tag, i), 190.0,
                                           190.0, 260.0, r=20.0, segments=2,
                                           centre=(x, s * (HALF_W + 10.0),
                                                   DECK_Z - 110.0),
                                           mat=rust_steel))
    # end stakes
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        for j, y in enumerate(R.evenly(7, 2400.0)):
            stakes.append(bkit.rounded_box("FlatEndStake%s%d" % (tag, j), 150.0,
                                           130.0, STAKE_H, r=18.0,
                                           segments=2,
                                           centre=(s * (LENGTH / 2.0 - 180.0),
                                                   y, DECK_Z + STAKE_H / 2.0),
                                           mat=plank_m))
    st_ob = bkit.join(stakes, "FlatStakes")
    bkit.recalc(st_ob)

    # chain anchors and a lashing turnbuckle on the deck
    anchors = []
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        anchors.append(bkit.rounded_box("FlatAnchor" + tag, 320.0, 900.0, 90.0,
                                        r=18.0, segments=2,
                                        centre=(s * (DECK_L / 2.0 - 900.0), 0.0,
                                                DECK_Z + 45.0), mat=steel))
    an_ob = bkit.join(anchors, "FlatAnchors")
    bkit.recalc(an_ob)
    for i, x in enumerate(R.evenly(5, 9000.0)):
        R.strut("FlatTurnbuckle%d" % i, (x - 320.0, 0.0, DECK_Z + 90.0),
                (x + 320.0, 0.0, DECK_Z + 90.0), 34.0, steel, seg=10)

    R.running_gear("Flat", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=steel)
    R.air_reservoir("FlatAirRes", -1800.0, 0.0, 840.0, steel, r=215.0,
                    length=1100.0)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("FlatBuffers" + tag, s * (LENGTH / 2.0), z=1065.0,
                  pitch=1750.0, mat_body=frame_m, mat_head=rust_steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("FlatStep%s%s" % (tag, ytag), s * 6650.0, sy * 1330.0,
                    480.0, DECK_Z - 20.0, steel, width=420.0, n=3)
    hb = R.spoked_ring("FlatBrakeWheel", 265.0, 5, axis="Y", rim_r=26.0,
                       hub_r=62.0, spoke_w=52.0, spoke_t=52.0,
                       mat=rust_steel, seg=32)
    bkit.move(hb, -6250.0, 1340.0, 2150.0)

    return dict(spec=SPEC, parts=12)