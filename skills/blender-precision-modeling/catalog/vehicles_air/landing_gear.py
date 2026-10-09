"""
landing_gear -- an aircraft main-gear assembly: 1000 mm wheel on an oleo strut.

A gear leg has three things in order from the ground: the WHEEL, the AXLE
through it, and the OLEO STRUT that telescopes into the bay above. The oleo is
the whole detail -- the outer cylinder is a fat 120 mm tube and the inner piston
is a 78 mm rod sliding out of it, which is what makes the silhouette read as
suspension rather than as a post.

The brake stack is the second repeated feature: four discs on a real pitch
around the hub, arrayed about the axle, so they are never hand-placed.

Real airliner main gear: 1100 x 400 mm wheel, 120 mm strut barrel, 78 mm oleo
rod, four heat shields on a 95 mm pitch, 850 mm axle height.

NOTE on the size class: a main gear LEG is 2.5 m, which is outside the
`medium` band this item is catalogued in, so the model is the GEAR ASSEMBLY --
wheel, axle, brakes and strut -- on its own, not the leg that carries it.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _craft as C

SPEC = dict(
    wheel_dia=1000.0,
    wheel_width=400.0,
    rim_dia=560.0,
    strut_barrel=120.0,
    strut_height=260.0,
    oleo_dia=78.0,
    oleo_length=160.0,
    axle_height=560.0,
    brake_disks=4,
    brake_pitch=95.0,
    brake_dia=430.0,
    torque_link=520.0,
)

WR = SPEC["wheel_dia"] / 2.0

CHECKS = [
    dict(name="wheel_dia", mm=1000.0, tol=6.0, how="bbox_z", part="GearTyre"),
    dict(name="wheel_width", mm=400.0, tol=4.0, how="bbox_y", part="GearTyre"),
    dict(name="rim_dia", mm=560.0, tol=5.0, how="bbox_x", part="GearRim"),
    dict(name="strut_barrel", mm=120.0, tol=3.0, how="bbox_x",
         part="GearStrut"),
    dict(name="axle_top", mm=590.0, tol=6.0, how="z_max", part="GearAxle"),
    dict(name="strut_height", mm=260.0, tol=5.0, how="bbox_z",
         part="GearStrut"),
    dict(name="brake_dia", mm=430.0, tol=6.0, how="bbox_x",
         part="GearBrake0"),
    dict(name="wheel_on_floor", mm=0.0, tol=4.0, how="z_min", part="GearTyre"),
]


def build():
    rubber = bkit.preset("rubber")
    alloy = bkit.preset("brushed_metal")
    steel = bkit.preset("dark_metal")
    chrome = bkit.pbr("GearChrome", base=(0.82, 0.83, 0.85), metal=0.85,
                      rough=0.10)

    # ---- the tyre: a shouldered carcass, not a plain cylinder -------
    hw = SPEC["wheel_width"] / 2.0
    sh = SPEC["wheel_width"] * 0.28
    prof = [(280.0, -hw), (WR - sh * 0.8, -hw), (WR, -hw + sh),
            (WR, hw - sh), (WR - sh * 0.8, hw), (280.0, hw),
            (280.0, -hw)]
    tyre = bkit.lathe("GearTyre", prof, segments=48, cap_ends=False,
                      mat=rubber)
    tyre.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    # the wheel is built about its own centre at the origin, so the tyre,
    # rim and hub are LIFTED onto the axle height here. Left at the origin
    # the tyre's lower half is 500 mm below the floor, `sit_on_floor` shifts
    # the whole assembly 500 mm, and every absolute z check moves with it.
    bkit.move(tyre, 0.0, 0.0, SPEC["axle_height"])

    # ---- the rim, hub and half-shafts --------------------------------
    rim = bkit.tube("GearRim", SPEC["rim_dia"] / 2.0,
                    SPEC["rim_dia"] / 2.0 - 60.0,
                    SPEC["wheel_width"] * 0.86, segments=48, axis="Y",
                    mat=alloy)
    bkit.move(rim, 0.0, 0.0, SPEC["axle_height"])
    hub = bkit.cylinder("GearHub", 150.0, SPEC["wheel_width"] * 0.92,
                        segments=32, axis="Y", mat=alloy)
    bkit.move(hub, 0.0, 0.0, SPEC["axle_height"])
    bkit.cylinder("GearAxle", 90.0, 700.0, segments=28, axis="Y",
                  centre=(0.0, 200.0, SPEC["axle_height"]), mat=steel)

    # ---- four brake heat shields on a real pitch about the axle -----
    brake = bkit.tube("GearBrake0", SPEC["brake_dia"] / 2.0,
                      SPEC["brake_dia"] / 2.0 - 26.0, 22.0, segments=36,
                      axis="Y", mat=steel)
    # the rotation is baked into the MESH before the mesh is offset:
    # `place_in_mesh` adds in the object's own frame, so on a rotated
    # tube a (0, 190, 560) offset lands the shields 560 mm out in Y and
    # 25 mm below the floor.
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = brake
    brake.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    brake.select_set(False)
    C.place_in_mesh(brake, 0.0, 190.0, SPEC["axle_height"])
    bpy.context.view_layer.update()
    bkit.array_radial(brake, SPEC["brake_disks"], axis="Y",
                      centre=(0.0, 0.0, SPEC["axle_height"]))

    # ---- the oleo strut: barrel, rod, and the trunnion --------------
    bkit.cylinder("GearStrut", SPEC["strut_barrel"] / 2.0,
                  SPEC["strut_height"], segments=32,
                  centre=(0.0, 200.0, SPEC["axle_height"]
                          + SPEC["strut_height"] / 2.0), mat=alloy)
    bkit.cylinder("GearOleo", SPEC["oleo_dia"] / 2.0,
                  SPEC["oleo_length"], segments=28,
                  centre=(0.0, 200.0,
                          SPEC["axle_height"] + SPEC["strut_height"]
                          + SPEC["oleo_length"] / 2.0), mat=chrome)
    bkit.rounded_box("GearTrunnion", 160.0, 300.0, 160.0, r=40.0,
                     segments=3, centre=(0.0, 200.0, SPEC["axle_height"]),
                     mat=steel)
    # the torque link: two arms and a knee, which is how the leg stays upright
    C.strut("GearTorqueLink0", (90.0, 200.0, SPEC["axle_height"] + 60.0),
            (90.0, 200.0, SPEC["axle_height"] - 160.0), 26.0, mat=steel)
    C.strut("GearTorqueLink1", (90.0, 200.0, SPEC["axle_height"] - 160.0),
            (250.0, 200.0, SPEC["axle_height"] - 160.0), 26.0, mat=steel)

    # ---- the drag brace running up out of the bay -------------------
    C.strut("GearDragBrace", (0.0, 260.0,
                              SPEC["axle_height"] + SPEC["strut_height"]
                              + SPEC["oleo_length"] - 60.0),
            (-300.0, 260.0,
             SPEC["axle_height"] + SPEC["strut_height"]
             + SPEC["oleo_length"] + 140.0), 42.0, mat=alloy)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8,
                note="Four brake shields arrayed about the axle axis with "
                     "the pitch in mesh space.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
