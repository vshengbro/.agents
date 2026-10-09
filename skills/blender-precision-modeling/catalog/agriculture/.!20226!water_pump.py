"""
water_pump -- a centrifugal irrigation pump on a steel skid: 520 x 300 x 380.

The three things that make a pump read as a pump are the VOLUTE (the spiral
snail casing), the two FLANGES that are coaxial with the shaft but NOT with each
other, and the MOTOR. The flanges are the reason this model uses two separate
lathes rather than one: a suction flange on the shaft axis and a discharge
flange turned 90 deg and pointing up, because that is the only way the pumped
water can get out of a skid-mounted unit.

Real 3-inch self-priming irrigation pump: 1450 x 380 mm inlet flange, 520 mm
long skid, 180 mm motor frame, 380 mm to the top of the motor.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _agri as A

SPEC = dict(
    skid_length=520.0,
    skid_width=300.0,
    skid_height=40.0,
    motor_dia=180.0,
    motor_length=300.0,
    pump_casing_dia=210.0,
    inlet_flange_dia=145.0,
    outlet_flange_dia=100.0,
    overall_height=380.0,
    suction_flange_top=262.5,
)

CHECKS = [
    dict(name="skid_length", mm=520.0, tol=3.0, how="bbox_x",
         part="PumpSkid"),
    dict(name="skid_width", mm=300.0, tol=3.0, how="bbox_y",
         part="PumpSkid"),
    dict(name="motor_dia", mm=180.0, tol=2.0, how="bbox_y", part="PumpMotor"),
    dict(name="pump_casing_dia", mm=210.0, tol=2.0, how="bbox_y",
         part="PumpVolute"),
    dict(name="inlet_flange_dia", mm=145.0, tol=2.0, how="bbox_y",
         part="PumpInlet"),
    dict(name="outlet_flange_dia", mm=100.0, tol=2.0, how="bbox_y",
         part="PumpOutlet"),
    dict(name="overall_height", mm=397.0, tol=5.0, how="bbox_z"),
    dict(name="inlet_flange_top", mm=262.5, tol=4.0, how="top_z",
         part="PumpInlet"),
]


def build():
    paint = bkit.pbr("PumpPaint", base=(0.10, 0.32, 0.52), metal=0.25,
                     rough=0.34)
    iron = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")
    copper = bkit.preset("copper")

    # ---- the skid it is bolted to: this is what touches the floor --------
    bkit.rounded_box("PumpSkid", SPEC["skid_length"], SPEC["skid_width"],
                     SPEC["skid_height"], r=6.0, segments=2,
                     centre=(0.0, 0.0, SPEC["skid_height"] / 2.0), mat=iron)
    for s in (1, -1):
        bkit.rounded_box("PumpFoot%d" % (0 if s > 0 else 1),
                         90.0, SPEC["skid_width"], 60.0, r=8.0, segments=2,
                         centre=(s * 190.0, 0.0, 70.0), mat=iron)

    # ---- motor: a lathed frame with cooling fins, axis along X ----------
    mx = 110.0
    prof = [(0.0, -150.0), (62.0, -150.0), (78.0, -132.0), (78.0, 60.0),
            (90.0, 60.0), (90.0, 96.0), (60.0, 112.0), (0.0, 112.0)]
    mo = bkit.lathe("PumpMotor", prof, segments=40, mat=paint)
    bkit.place(mo, (mx, 0.0, 190.0), "X")
    # cooling fins: a radial array about the motor axis, which is what makes
    # the silhouette ribbed instead of a plain can
    # built at the origin so `location` is the ONLY placement: rounded_box
    # bakes its `centre` into the mesh, so setting location on top of a
    # centred box applies the offset twice and the orbit lands at 2x radius
    fin = bkit.rounded_box("PumpMotorFins", 120.0, 14.0, 150.0, r=5.0,
                           segments=2, mat=paint)
    fin.location = bkit.v(mx - 10.0, 86.0, 190.0)
    bpy.context.view_layer.update()
    bkit.array_radial(fin, 12, axis="X", centre=(mx, 0.0, 190.0))
    bkit.rounded_box("PumpTerminalBox", 70.0, 90.0, 60.0, r=6.0, segments=2,
                     centre=(mx - 60.0, 0.0, 300.0), mat=iron)

    # ---- the volute: a lathed snail casing whose axis is the SHAFT ------
    # (X), so the suction flange is coaxial with the motor and the discharge
    # points straight up -- the only arrangement that works on a skid.
    vprof = [(0.0, -95.0), (105.0, -95.0), (105.0, 95.0),
             (78.0, 95.0), (78.0, -58.0), (0.0, -58.0)]
    vol = bkit.lathe("PumpVolute", vprof, segments=48, mat=paint)
    bkit.place(vol, (-90.0, 0.0, 190.0), "X")
    # the tongue / discharge throat, a genuine raised spiral lip
    bkit.tube("PumpVoluteTongue", 105.0, 86.0, 40.0, segments=48, axis="X",
              centre=(-90.0, 0.0, 190.0), mat=paint)

    # ---- flanges: coaxial with the SHAFT (X), not with each other -------
    bkit.tube("PumpInlet", 72.5, 48.0, 34.0, segments=40, axis="X",
              centre=(-208.0, 0.0, 190.0), mat=steel)
    bkit.tube("PumpInletNeck", 56.0, 46.0, 60.0, segments=40, axis="X",
              centre=(-170.0, 0.0, 190.0), mat=paint)
    # bolt holes around the suction flange, on a real bolt circle
    for i in range(4):
        a = math.pi / 4.0 + math.pi / 2.0 * i
        bkit.cylinder("PumpInletBolt%d" % i, 9.0, 44.0, segments=12,
                      centre=(-208.0, 60.0 * math.cos(a), 190.0 + 60.0 * math.sin(a)),
                      axis="X", mat=steel)

    # ---- discharge: flange faces UP, out of the top of the volute -------
    bkit.tube("PumpDischargeNeck", 50.0, 42.0, 120.0, segments=40,
              centre=(-90.0, 0.0, 316.0), mat=paint)
    bkit.tube("PumpOutlet", 50.0, 39.0, 22.0, segments=40,
              centre=(-90.0, 0.0, 386.0), mat=steel)

    # ---- prime tank and fuel line: the small honesty details -------------
    bkit.cylinder("PumpPrimer", 46.0, 130.0, segments=24,
                  centre=(-90.0, 96.0, 210.0), mat=copper)
    A.tube_between("PumpPrimerLine", (-90.0, 60.0, 210.0),
                   (-90.0, 58.0, 296.0), 11.0, mat=copper)

    return dict(spec=SPEC, parts=13)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
