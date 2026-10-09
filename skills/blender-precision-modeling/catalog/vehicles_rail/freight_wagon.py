"""
freight_wagon -- 14 m bogie open freight wagon, 14,000 x 2,900 mm over buffers.

The whole read of a freight wagon is BOGIES + UNDERFRAME. Four axles on two
two-axle bogies at +/-3,500 (2,000 mm bogie wheelbase), not four loose axles:
without the bogie frame the wagon is a skip on circles. And the frame -- two
solebars, two headstocks, a deck, buffers at 1065 mm -- is the part that says
'railway' rather than 'container'.

The wheel treads are authored at z = 420, i.e. exactly on the rail datum, so
`sit_on_floor()` is a no-op and `WagonAxles` has a `z_min` of precisely 0.
That is checked, because it is the single number that proves the whole vehicle
is standing on its rails rather than hovering over the backdrop.
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
    body_width=2900.0,
    body_top_z=2850.0,
    frame_top_z=1250.0,
    wheel_diameter=840.0,
    axle_count=4,
    bogie_centre_distance=7000.0,
    bogie_wheelbase=2000.0,
    buffer_height=1065.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="length_over_buffers", mm=14000.0, tol=3.0, how="bbox_x",
         part="WagonFrame"),
    dict(name="body_width", mm=2900.0, tol=3.0, how="bbox_y", part="WagonBody"),
    dict(name="body_top_z", mm=2850.0, tol=3.0, how="top_z", part="WagonBody"),
    dict(name="frame_top_z", mm=1250.0, tol=3.0, how="top_z", part="WagonFrame"),
    # 840 tread + 2 x 28 flange. Together with `flange_on_datum` below this pins
    # the axle height at 448, which is the only number that says the wheel is
    # sitting on the rail rather than hovering over it.
    dict(name="wheel_flange_diameter", mm=896.0, tol=3.0, how="bbox_z",
         part="WagonAxles"),
    # The flange tips rest ON z=0. If this ever drifts, sit_on_floor() has
    # silently lifted the whole wagon and every coordinate above is a lie.
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="WagonAxles"),
    # 2 x 4,500 outer-axle centres + 2 x 448 flange radius.
    dict(name="axle_row_span", mm=9896.0, tol=3.0, how="bbox_x",
         part="WagonAxles"),
    dict(name="bogie_frame_length", mm=2900.0, tol=3.0, how="bbox_x",
         part="WagonBogieF"),
]

LENGTH = 14000.0
HALF_W = 1450.0
FRAME_Z0 = 950.0
FRAME_D = 300.0
DECK_Z = FRAME_Z0 + FRAME_D              # 1250
SIDE_TOP = 2850.0
WHEEL_D = 840.0
WHEEL_R = WHEEL_D / 2.0
BOGIE_X = 3500.0
BOGIE_WB = 2000.0
BOGIE_FRAME_L = BOGIE_WB + 900.0


def build():
    frame_m = bkit.pbr("WagonFramePaint", base=(0.26, 0.20, 0.15), rough=0.62)
    body_m = bkit.pbr("WagonBodyPaint", base=(0.38, 0.20, 0.13), rough=0.58)
    steel = bkit.preset("dark_metal")
    rust_steel = bkit.pbr("WagonRustSteel", base=(0.34, 0.26, 0.20),
                          metal=0.75, rough=0.62)

    R.underframe("WagonFrame", LENGTH, half_w=HALF_W, z_bot=FRAME_Z0,
                 depth=FRAME_D, mat=frame_m)

    # --- body: sides, ends, corner stakes and top capping angle ------------
    parts = []
    t = 60.0
    side_len = LENGTH - 240.0
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        parts.append(bkit.rounded_box("WagonSide" + tag, side_len, t,
                                      SIDE_TOP - DECK_Z, r=14.0, segments=2,
                                      centre=(0.0, s * (HALF_W - t / 2.0),
                                              (DECK_Z + SIDE_TOP) / 2.0),
                                      mat=body_m))
        parts.append(bkit.rounded_box("WagonCap" + tag, side_len, 100.0, 110.0,
                                      r=16.0, segments=2,
                                      centre=(0.0, s * (HALF_W - 50.0),
                                              SIDE_TOP - 55.0), mat=body_m))
    end_x = LENGTH / 2.0 - 120.0
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        parts.append(bkit.rounded_box("WagonEnd" + tag, t, 2.0 * HALF_W - 200.0,
                                      SIDE_TOP - DECK_Z, r=14.0, segments=2,
                                      centre=(s * end_x, 0.0,
                                              (DECK_Z + SIDE_TOP) / 2.0),
                                      mat=body_m))
    # Fourteen stakes a side, first to last evenly spread across the side.
    # `evenly()` is the same anti-hand-placing rule as `lay_out()`, expressed
    # for a row of identical members rather than a row of cut features.
    stake = 110.0
    for i, xc in enumerate(R.evenly(14, side_len - 400.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            parts.append(bkit.rounded_box("WagonStake%s%d" % (tag, i), stake,
                                          100.0, SIDE_TOP - DECK_Z + 60.0,
                                          r=18.0, segments=2,
                                          centre=(xc, s * (HALF_W - 50.0),
                                                  (DECK_Z + SIDE_TOP) / 2.0 - 30.0),
                                          mat=body_m))
    body = bkit.join(parts, "WagonBody")
    bkit.recalc(body)

    # --- running gear -------------------------------------------------------
    bg = bkit.preset("dark_metal")
    R.running_gear("Wagon", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=bg,
                   mat_steel=bg)

    # --- underframe equipment, steps, brake gear ---------------------------
    R.air_reservoir("WagonAirRes", -1900.0, 0.0, 840.0, steel, r=225.0,
                    length=1200.0)
    R.battery_box("WagonBatteryBox", 1700.0, 1180.0, 830.0, steel)
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        for xe, etag in ((6650.0, "F"), (-6650.0, "R")):
            R.steps("WagonStep%s%s" % (etag, tag), xe, s * 1320.0, 500.0,
                    DECK_Z - 20.0, steel, width=440.0, n=3)
    # handbrake wheel at one end: spoked ring swept about its own hub, moved
    # into place only after the sweep, never arrayed in place.
    hb = R.spoked_ring("WagonBrakeWheel", 265.0, 5, axis="Y", rim_r=26.0,
                       hub_r=62.0, spoke_w=52.0, spoke_t=52.0, mat=rust_steel,
                       seg=32)
    bkit.move(hb, -6300.0, 1320.0, 2000.0)
    bkit.cylinder("WagonBrakeScrew", 55.0, 1100.0, segments=14, axis="Z",
                  centre=(-6300.0, 1320.0, 1450.0), mat=rust_steel)

    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("WagonBuffers" + tag, s * (LENGTH / 2.0), z=1065.0,
                  pitch=1750.0, mat_body=frame_m, mat_head=rust_steel)

    return dict(spec=SPEC, parts=14)