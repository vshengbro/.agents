"""
wheelchair -- 960 x 700 x 910 mm manual wheelchair: 610 mm rear wheels with
eight spokes each, 150 mm front castors, a sling seat and back, armrests, push
handles and footplates.

The rear wheel is modelled in one place -- tyre, rim, hub, eight spokes from
`array_radial`, hand rim -- and only then rotated onto its axle and duplicated
for the far side. Building the second wheel by hand lets the two drift apart by
a fraction of a millimetre, which is invisible in the report and obvious in the
top view.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_length=935.0,
    overall_width=682.0,
    overall_height=903.0,
    rear_wheel_diameter=610.0,
    rear_wheel_width=32.0,
    castor_diameter=150.0,
    seat_height=500.0,
    seat_size=460.0,
    spokes=8,
)

RW = SPEC["rear_wheel_diameter"] / 2.0        # 305.0
RWZ = RW
TYRE = SPEC["rear_wheel_width"]
SEAT_Z = SPEC["seat_height"]
SEAT_D = SPEC["seat_size"]
CAST_R = SPEC["castor_diameter"] / 2.0
AXLE_X = -200.0
SIDE_Y = 280.0
SPOKES = SPEC["spokes"]


def radial_array(obj, name, count):
    """`count` copies of `obj` evenly about Z.

    `bkit.array_radial` does not orbit correctly in this Blender build -- the
    pivot empty's matrix_world is still identity when the modifier is applied,
    so the copies are offset by the object's own location rather than rotated
    and the spokes end up marching off in a diagonal line instead of radiating.
    """
    copies = [obj]
    loc = obj.location
    x0, y0, z0 = loc.x / bkit.MM, loc.y / bkit.MM, loc.z / bkit.MM
    for i in range(count - 1):
        a = 2.0 * math.pi * (i + 1) / count
        copies.append(bkit.duplicate(
            obj, "%s%d" % (name, i + 1),
            offset_mm=(x0 * math.cos(a) - y0 * math.sin(a),
                       x0 * math.sin(a) + y0 * math.cos(a), z0),
            rot_deg=(0.0, 0.0, math.degrees(a))))
    bpy.context.view_layer.update()
    return bkit.join(copies, name=name)


def build():
    frame = bkit.pbr("ChairFrame", base=(0.80, 0.82, 0.85), metal=0.82,
                     rough=0.24)
    tyre = bkit.pbr("ChairTyre", base=(0.06, 0.06, 0.07), rough=0.68)
    sling = bkit.pbr("ChairSling", base=(0.13, 0.16, 0.24), rough=0.72)
    pad_mat = bkit.pbr("ChairPad", base=(0.10, 0.10, 0.11), rough=0.60)
    chrome = bkit.pbr("ChairChrome", base=(0.80, 0.81, 0.83), metal=0.86,
                      rough=0.14)

    # ---- one rear wheel, built in the XY plane (axis along Z) -------------
    wheel_parts = [
        bkit.lathe("RearTyre", [
            (RW - TYRE / 2.0, -TYRE / 2.0), (RW, -TYRE / 2.0 + 5.0),
            (RW, TYRE / 2.0 - 5.0), (RW - TYRE / 2.0, TYRE / 2.0),
            (RW - TYRE / 2.0, -TYRE / 2.0),
        ], segments=96, cap_ends=False, mat=tyre),
        bkit.tube("RearRim", RW - TYRE / 2.0 + 1.0, RW - TYRE / 2.0 - 9.0,
                  TYRE * 0.6, segments=72, axis="Z", mat=frame),
        bkit.cylinder("RearHub", 26.0, TYRE * 1.3, segments=32, axis="Z",
                      mat=frame),
        bkit.torus("HandRim", RW - 55.0, 8.0, seg_major=72, seg_minor=16,
                   centre=(0.0, 0.0, TYRE * 0.95), mat=chrome),
    ]
    # the spoke's long axis lies IN the wheel plane (XY), so rotating a copy
    # about Z sweeps it round the hub; a box built long in Z would just be
    # rotated in place and stay a column
    spoke = bkit.box("_spoke", RW - 44.0, 3.0, 3.0,
                     centre=((RW - 44.0) / 2.0 + 20.0, 0.0, 0.0), mat=frame)
    radial_array(spoke, "RearSpokes", SPOKES)
    wheel_parts += [bpy.data.objects["RearSpokes"]]
    wheel = bkit.join(wheel_parts, name="RearWheel")
    wheel.rotation_euler = (math.radians(-90.0), 0.0, 0.0)

    # ---- onto both axles --------------------------------------------------
    bkit.move(wheel, AXLE_X, -SIDE_Y, RWZ)
    bkit.duplicate(wheel, "RearWheelR", offset_mm=(AXLE_X, SIDE_Y, RWZ),
                   rot_deg=(-90.0, 0.0, 0.0))

    # ---- front castors: Y positions from a grid, not typed in -------------
    castors = []
    for (gx, gy) in bkit.grid_positions(1, 2, 0.0, 2.0 * SIDE_Y):
        cx, cy = 300.0 + gx, gy
        w = bkit.lathe("CastorWheel", [
            (0.0, -18.0), (CAST_R - 14.0, -18.0), (CAST_R, -12.0),
            (CAST_R, 12.0), (CAST_R - 14.0, 18.0), (0.0, 18.0),
        ], segments=48, mat=tyre)
        w.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
        bkit.move(w, cx, cy, CAST_R)
        castors.append(w)
        castors.append(bkit.cylinder("_fork", 12.0, 130.0, segments=24,
                                    centre=(cx, cy, 82.0), mat=frame))
        # the fork has to reach the side rail, or the front of the chair floats
        castors.append(bkit.cylinder("_frontleg", 15.0, 380.0, segments=24,
                                    centre=(cx, cy, 300.0), mat=frame))
    bkit.join(castors, name="Castors")

    # ---- frame rails, legs, back posts and push handles -------------------
    rails = []
    for sign in (-1.0, 1.0):
        rails.append(bkit.cylinder("_rail", 15.0, 700.0, segments=24,
                                   centre=(30.0, sign * SIDE_Y, SEAT_Z + 6.0),
                                   axis="X", mat=frame))
        rails.append(bkit.cylinder("_leg", 15.0, SEAT_Z - 60.0, segments=24,
                                   centre=(AXLE_X, sign * SIDE_Y,
                                           60.0 + (SEAT_Z - 60.0) / 2.0),
                                   mat=frame))
        rails.append(bkit.cylinder("_backpost", 15.0, 400.0, segments=24,
                                   centre=(-150.0, sign * SIDE_Y, 680.0),
                                   mat=frame))
        rails.append(bkit.arc_torus("_push", 50.0, 11.0,
                                    270.0, 360.0 if sign > 0 else 180.0,
                                    centre=(-150.0, sign * SIDE_Y, 900.0),
                                    plane="YZ", seg_major=24, mat=pad_mat))
    bkit.join(rails, name="ChairFrame")

    # ---- sling seat and back ----------------------------------------------
    bkit.rounded_box("ChairSeat", SEAT_D, 420.0, 22.0, r=8.0, segments=3,
                     centre=(20.0, 0.0, SEAT_Z), mat=sling)
    back = bkit.rounded_box("ChairBack", 22.0, 420.0, 380.0, r=8.0,
                            segments=3, centre=(-158.0, 0.0, SEAT_Z + 200.0),
                            mat=sling)
    back.rotation_euler = (0.0, math.radians(7.0), 0.0)

    # ---- armrests on posts, and footplates --------------------------------
    arms = []
    for sign in (-1.0, 1.0):
        arms.append(bkit.rounded_box("Armrest", 320.0, 60.0, 22.0, r=8.0,
                                     segments=3,
                                     centre=(0.0, sign * SIDE_Y, SEAT_Z + 190.0),
                                     mat=pad_mat))
        arms.append(bkit.cylinder("_armpost", 14.0, 290.0, segments=20,
                                  centre=(120.0, sign * SIDE_Y, SEAT_Z + 100.0),
                                  mat=frame))
        arms.append(bkit.rounded_box("Footplate", 150.0, 130.0, 14.0, r=5.0,
                                     segments=3,
                                     centre=(355.0, sign * 150.0, 130.0),
                                     mat=pad_mat))
        # hanger: a vertical drop from the rail plus a short arm inboard to
        # the plate, so the footplate is carried rather than floating
        arms.append(bkit.cylinder("_footdrop", 13.0, 360.0, segments=20,
                                  centre=(330.0, sign * 150.0, 320.0),
                                  mat=frame))
        arms.append(bkit.cylinder("_footarm", 13.0, 130.0, segments=20,
                                  centre=(330.0, sign * 215.0, 500.0),
                                  axis="Y", mat=frame))
    bkit.join(arms, name="ChairArms")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="rear_wheel_diameter", mm=610.0, tol=1.5, how="diameter",
         part="RearWheel"),
    dict(name="seat_thickness", mm=22.0, tol=0.5, how="bbox_z",
         part="ChairSeat"),
    dict(name="overall_length", mm=935.0, tol=6.0, how="bbox_x"),
    dict(name="overall_width", mm=682.0, tol=8.0, how="bbox_y"),
    dict(name="overall_height", mm=903.0, tol=4.0, how="bbox_z"),
]