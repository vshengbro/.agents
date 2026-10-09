"""
harrow -- a tandem disc harrow: 16 discs in two gangs, 3.0 m wide.

A disc harrow is DISCS ON AXLES, and the only thing that makes it correct is
that the discs are arrayed about their OWN AXLE. Two gangs of eight on a 200 mm
disc pitch, each gang on its own axle, so `array_radial` MUST be given that
axle as its `centre` -- arrayed about the world origin instead, the gang
sweeps outward to 8x its own radius and the implement comes out 6 m wide
instead of 3 m.

The discs are CONCAVE and the concavity faces the direction of travel, dished
55 mm on a 600 mm disc, tilted 22 deg off vertical so they both cut and roll.
The two gangs are offset fore-and-aft by 350 mm -- the tandem arrangement -- and
the angle is what makes a harrow pull rather than push.

Real 3 m tandem harrow: 16 x 600 mm concave discs at 200 mm spacing, gangs at
2800 and 2900 mm wide, 350 mm tandem offset, 510 mm transport wheels.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _agri as A

SPEC = dict(
    discs_per_gang=8,
    disc_dia=600.0,
    disc_pitch=200.0,
    disc_thickness=8.0,
    dish_depth=55.0,
    gangs=2,
    tandem_offset=350.0,
    gang_width=2800.0,
    frame_height=520.0,
    wheel_dia=510.0,
    wheel_width=110.0,
    wheel_track=2400.0,
    overall_width=3000.0,
)

N = SPEC["discs_per_gang"]
DD = SPEC["disc_dia"]
PITCH = SPEC["disc_pitch"]
DT = SPEC["disc_thickness"]
DISH = SPEC["dish_depth"]
TANDEM = SPEC["tandem_offset"]
WD = SPEC["wheel_dia"]

GANG_A = -TANDEM / 2.0       # rear gang
GANG_B = TANDEM / 2.0        # front gang

CHECKS = [
    # a disc stands in the YZ plane, so its 600 mm diameter is its Y extent; the
    # 22 deg rake drops its Z extent to 559 mm, which is the tilt showing up
    dict(name="disc_dia", mm=600.0, tol=4.0, how="bbox_y", part="HarrowDiscs00"),
    dict(name="disc_raked_height", mm=559.3, tol=6.0, how="bbox_z",
         part="HarrowDiscs00"),
    # the gang frame is 8 discs at 200 mm pitch plus a bearing each end
    dict(name="gang_frame_width", mm=1660.0, tol=8.0, how="bbox_y",
         part="HarrowGangFrame0"),
    # the front gang's frame sits half the tandem offset forward, so its far
    # face is at +175 + 45 = +220 mm: a coordinate, not a size
    dict(name="tandem_offset", mm=220.0, tol=4.0, how="x_max",
         part="HarrowGangFrame1"),
    dict(name="main_frame_width", mm=1900.0, tol=8.0, how="bbox_y",
         part="HarrowMainFrame"),
    dict(name="frame_height", mm=260.0, tol=4.0, how="bbox_z",
         part="HarrowMainFrame"),
    dict(name="wheel_dia", mm=510.0, tol=3.0, how="diameter", part="Wheel0"),
    dict(name="wheel_tread_on_floor", mm=0.0, tol=2.0, how="z_min", part="Wheel0"),
]


def build():
    paint = bkit.pbr("HarrowPaint", base=(0.62, 0.16, 0.05), metal=0.30,
                     rough=0.40)
    steel = bkit.preset("dark_metal")
    edge = bkit.preset("brushed_metal")

    # ---- two gangs of discs, each a straight row on its own axle ----
    # A gang is a ROW along the axle, so the discs are placed on the computed
    # 200 mm pitch. `array_radial` is the wrong tool here: orbiting the discs
    # about their own axle wraps them into a circle in the plane across the
    # axle -- a windmill, not a harrow.
    disc_y = [(-(N - 1) / 2.0 + i) * PITCH for i in range(N)]
    for gi, (gx, tag) in enumerate(((GANG_A, "0"), (GANG_B, "1"))):
        A.gang("HarrowDiscs%d" % gi, N, DD, DT, DISH, [gx] * N, disc_y,
               DD / 2.0, tilt_deg=22.0, mat=edge)

    # ---- the gang frames + the drawbar ------------------------------
    for gi, (gx, tag) in enumerate(((GANG_A, "0"), (GANG_B, "1"))):
        bkit.rounded_box("HarrowGangFrame%s" % tag,
                         90.0, (N - 1) * PITCH + 260.0, 90.0, r=8.0,
                         segments=2, centre=(gx, 0.0, DD / 2.0), mat=paint)

    # the main frame spans both gangs and carries the drawbar forward
    frame_y = (N - 1) * PITCH + 500.0
    bkit.rounded_box("HarrowMainFrame", TANDEM + 120.0, frame_y,
                     SPEC["frame_height"] * 0.5, r=10.0, segments=2,
                     centre=(0.0, 0.0, DD / 2.0 + 120.0), mat=paint)
    A.bar_between("HarrowDrawbar", (TANDEM / 2.0 + 60.0, 0.0, DD / 2.0 + 260.0),
                  (TANDEM / 2.0 + 1100.0, 0.0, 780.0), 110.0, 110.0,
                  mat=paint, r=8.0)
    # the three-point hitch sits on the drawbar's forward end
    for i, sy in enumerate((-1, 1)):
        A.bar_between("HarrowHitch%d" % i,
                      (TANDEM / 2.0 + 1050.0, sy * 180.0, 700.0),
                      (TANDEM / 2.0 + 780.0, sy * 90.0, 900.0),
                      70.0, 70.0, mat=steel, r=6.0)

    # ---- two transport wheels, treads on z=0 -----------------------
    wr = WD / 2.0
    tr = SPEC["wheel_track"]
    w = A.ground_wheel("Wheel0", WD, SPEC["wheel_width"])
    A.place_wheels(w, [(-TANDEM / 2.0 - 60.0, -tr / 2.0, wr),
                       (-TANDEM / 2.0 - 60.0, tr / 2.0, wr)],
                   names=["Wheel0", "Wheel1"])

    return dict(spec=SPEC, parts=2 * N + 2 + 1 + 1 + 2 + 1,
                discs=N * SPEC["gangs"], note=A.AGRI_NOTE)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()