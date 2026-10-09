"""
mine_cart -- 600 mm gauge mine skip, 1,150 x 720 x 900 mm.

Deliberately SMALL. A full-gauge wagon cannot be under 1,200 mm in any
dimension -- the gauge alone forbids it -- but a mine car can and is, so this
model sits in the catalogue's `medium` size class honestly instead of being
shrunk to fit.

The body is one `extrude_profile` of the side silhouette extruded across the
width: `extrude_profile(..., axis="Y")` maps profile-x -> world X, profile-y
-> world Z and the extrusion -> world -Y, so writing the skip outline as
(x, z) gives a raked-sided hopper directly, with no boolean and no cavity.

Wheels are torus tyres on four spokes with a lathe flange proud of the tread,
on a 600 mm wheel centre -- and the flange tip, not the tread, is what rests
on z=0, exactly as on a full-gauge vehicle.
"""
import bpy
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=1180.0,
    body_length=1000.0,
    body_width=660.0,
    body_top_z=900.0,
    frame_top_z=470.0,
    tread_diameter=272.0,
    flange_diameter=300.0,
    wheel_centre_offset=300.0,
    gauge=600.0,
    capacity_t=0.5,
)

CHECKS = [
    dict(name="body_length", mm=1000.0, tol=3.0, how="bbox_x",
         part="MineBody"),
    dict(name="over_buffers", mm=590.0, tol=3.0, how="x_max",
         part="MineBufferF"),
    dict(name="body_width", mm=660.0, tol=3.0, how="bbox_y", part="MineBody"),
    dict(name="body_top_z", mm=900.0, tol=3.0, how="top_z", part="MineBody"),
    dict(name="frame_top_z", mm=470.0, tol=3.0, how="top_z", part="MineFrame"),
    dict(name="flange_diameter", mm=300.0, tol=3.0, how="bbox_z",
         part="MineWheels"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="MineWheels"),
    dict(name="axle_row_span", mm=960.0, tol=3.0, how="bbox_x",
         part="MineWheels"),
]

BODY_L = 1000.0
BODY_W = 660.0
FRAME_Z = 380.0
FRAME_H = 90.0
TOP_Z = 900.0
WHEEL_Y = 300.0
FLANGE_R = 150.0
AXLE_X = [-330.0, 330.0]


def build():
    steel = bkit.pbr("MineSteel", base=(0.22, 0.21, 0.20), metal=0.80,
                     rough=0.56)
    worn = bkit.pbr("MineWornSteel", base=(0.34, 0.31, 0.28), metal=0.78,
                    rough=0.66)
    rust = bkit.pbr("MineRust", base=(0.40, 0.22, 0.12), metal=0.60,
                    rough=0.74)

    # --- frame and buffer beams --------------------------------------------
    bkit.rounded_box("MineFrame", 1060.0, BODY_W, FRAME_H, r=20.0, segments=2,
                     centre=(0.0, 0.0, FRAME_Z + FRAME_H / 2.0), mat=steel)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        bkit.rounded_box("MineBeam" + tag, 60.0, BODY_W, 220.0, r=20.0,
                         segments=2,
                         centre=(s * 490.0, 0.0, FRAME_Z + 130.0), mat=steel)
        bkit.cylinder("MineBuffer" + tag, 60.0, 100.0, segments=20, axis="X",
                      centre=(s * 540.0, 0.0, FRAME_Z + 130.0), mat=worn)

    # --- the skip body: side silhouette extruded across the width ----------
    prof = [(-BODY_L / 2.0, TOP_Z), (BODY_L / 2.0, TOP_Z),
            (BODY_L / 2.0 - 150.0, FRAME_Z + FRAME_H),
            (-BODY_L / 2.0 + 150.0, FRAME_Z + FRAME_H)]
    body = bkit.extrude_profile("MineBody", prof, BODY_W, centre=(0.0, 0.0, 0.0),
                                axis="Y", mat=rust)
    bkit.recalc(body)
    # Only the bottom band is worn through to bare steel -- painting the
    # whole body leaves a grey skip instead of a rusted one.
    bkit.assign_faces_by(body, worn,
                         lambda c, n: c.z / bkit.MM < FRAME_Z + FRAME_H + 10.0)

    # --- raking ribs down the outside of the skip --------------------------
    ribs = []
    for i, x in enumerate(R.evenly(4, 640.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            ribs.append(R.raked_panel("MineRib%s%d" % (tag, i), 34.0, 170.0,
                                      300.0, 22.0, axis="X",
                                      centre=(x, s * (BODY_W / 2.0 + 10.0),
                                              640.0), r=10.0, mat=steel))
    rb_ob = bkit.join(ribs, "MineRibs")
    bkit.recalc(rb_ob)

    # --- flanged spoked wheels, one built at the origin and repeated -------
    tyre = bkit.torus("MineWheel_Tyre", 120.0, 16.0, seg_major=32, seg_minor=12,
                      centre=(0.0, 0.0, 0.0), axis="Y", mat=worn)
    flange = bkit.lathe("MineWheel_Flange",
                        [(136.0, 26.0), (150.0, 26.0), (150.0, -34.0),
                         (136.0, -34.0), (136.0, 26.0)],
                        segments=32, cap_ends=False, mat=steel)
    bkit.place(flange, (0.0, 0.0, 0.0), "Y")
    spokes = bkit.rounded_box("MineWheel_Spoke", 110.0, 34.0, 34.0, r=10.0,
                              segments=2, centre=(0.0, 0.0, 0.0), mat=steel)
    bkit.array_radial(spokes, 4, axis="Y")
    hub = bkit.cylinder("MineWheel_Hub", 40.0, 86.0, segments=16, axis="Y",
                        centre=(0.0, 0.0, 0.0), mat=steel)
    one = bkit.join([tyre, flange, spokes, hub], "MineWheel")
    bkit.recalc(one)
    R.freeze(one)
    one.location = (0.0, 0.0, 0.0)

    one.name = "MineWheelFL"
    bkit.move(one, AXLE_X[0], -WHEEL_Y, FLANGE_R)
    wparts = [one]
    for nm, (x, y) in (("MineWheelFR", (AXLE_X[0], WHEEL_Y)),
                       ("MineWheelRL", (AXLE_X[1], -WHEEL_Y)),
                       ("MineWheelRR", (AXLE_X[1], WHEEL_Y))):
        wparts.append(bkit.duplicate(one, nm, offset_mm=(x, y, FLANGE_R)))
    wheels = bkit.join(wparts, "MineWheels")
    bkit.recalc(wheels)
    R.freeze(wheels)
    wheels.location = (0.0, 0.0, 0.0)

    for i, x in enumerate(AXLE_X):
        R.strut("MineAxle%d" % i, (x, -WHEEL_Y - 40.0, FLANGE_R),
                (x, WHEEL_Y + 40.0, FLANGE_R), 22.0, steel, seg=12)

    # --- draw hook and shackle ---------------------------------------------
    R.strut("MineHook", (500.0, 0.0, FRAME_Z + 130.0),
            (570.0, 0.0, FRAME_Z + 60.0), 22.0, worn, seg=10)
    bkit.torus("MineShackle", 60.0, 14.0, seg_major=20, seg_minor=10,
               centre=(500.0, 0.0, FRAME_Z + 250.0), axis="X", mat=steel)

    return dict(spec=SPEC, parts=9)