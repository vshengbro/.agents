"""
drone -- a 240 mm folding camera quad with ducted rotor guards and a ball gimbal.

Different from `quadcopter` on purpose: that one is an open X-frame with bare
motors, this one is a compact folding camera drone whose four rotors sit inside
GUARDS. The guards are the whole identity -- four rings arrayed about the hub,
so the drone reads as protected, and the array hub is passed explicitly because
the airframe centre is not the world origin once the battery is fitted forward.

The camera is on a two-axis BALL gimbal, which is what distinguishes a camera
drone from a racer: the ball is one sphere, and the roll arm wraps it.

Real Mavic Mini class drone: 245 x 245 x 70 mm folded airframe, 160 mm guards,
32 mm camera ball, 2100 mAh pack.
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
    span=245.0,
    guard_dia=160.0,
    guard_thickness=7.0,
    rotors=4,
    motor_dia=34.0,
    prop_dia=118.0,
    body_length=245.0,
    body_width=180.0,
    body_height=180.0,
    camera_ball=64.0,
    camera_lens=24.0,
    arm_length=78.0,
)

HUB = (0.0, 0.0, 46.0)
ARM_R = SPEC["span"] / 2.0 - SPEC["arm_length"] / 2.0
GUARD_R = ARM_R + SPEC["arm_length"] / 2.0 - SPEC["prop_dia"] / 2.0 + 6.0

CHECKS = [
    dict(name="span", mm=245.0, tol=5.0, how="bbox_y", part="DroneArms"),
    dict(name="guard_row_span", mm=299.0, tol=6.0, how="bbox_x",
         part="DroneGuards"),
    dict(name="prop_dia", mm=118.0, tol=6.0, how="bbox_max", part="DroneProp0"),
    dict(name="body_length", mm=245.0, tol=3.0, how="bbox_x",
         part="DroneBody"),
    dict(name="body_height", mm=180.0, tol=4.0, how="bbox_z", part="DroneBody"),
    dict(name="camera_ball", mm=64.0, tol=2.0, how="bbox_y",
         part="DroneCameraBall"),
    dict(name="lens_dia", mm=24.0, tol=1.5, how="bbox_y", part="DroneLens"),
    dict(name="body_on_floor", mm=5.0, tol=2.0, how="z_min",
         part="DroneBody"),
]


def build():
    shell = bkit.pbr("DroneShell", base=(0.88, 0.88, 0.86), rough=0.30)
    dark = bkit.preset("black_plastic")
    glass = bkit.pbr("DroneGlass", base=(0.08, 0.10, 0.14), rough=0.04,
                     metal=0.35)
    accent = bkit.pbr("DroneAccent", base=(0.10, 0.28, 0.52), rough=0.30)

    # ---- the fuselage: a flat slab with a tapered nose ---------------
    secs = []
    for (x, sx, sy, n) in ((-122.0, 70.0, 60.0, 3.6),
                           (-80.0, 180.0, 130.0, 3.4),
                           (20.0, 245.0, 180.0, 4.5),
                           (100.0, 190.0, 150.0, 3.6),
                           (122.0, 110.0, 90.0, 3.2)):
        ring = bkit.superellipse_section(sx, sy, n=n, steps=36,
                                         centre=(0.0, 95.0))
        secs.append([(x, px, py) for (px, py) in ring])
    body = bkit.loft("DroneBody", secs, mat=shell)
    bkit.recalc(body)
    bkit.shade_smooth(body, 40.0)

    # ---- four arms, four guards, four motors, four props -------------
    arm = bkit.rounded_box("DroneArms", SPEC["arm_length"], 22.0, 14.0,
                           r=6.0, segments=3, centre=(ARM_R, 0.0, HUB[2]),
                           mat=shell)
    bpy.context.view_layer.update()
    bkit.array_radial(arm, SPEC["rotors"], axis="Z", centre=HUB)

    guard = bkit.tube("DroneGuards", SPEC["guard_dia"] / 2.0,
                      SPEC["guard_dia"] / 2.0 - SPEC["guard_thickness"],
                      26.0, segments=36, mat=dark)
    C.place_in_mesh(guard, GUARD_R, 0.0, HUB[2])
    bpy.context.view_layer.update()
    bkit.array_radial(guard, SPEC["rotors"], axis="Z", centre=HUB)

    motor = bkit.lathe("DroneMotors",
                       [(0.0, 0.0), (16.0, 0.0), (17.0, 6.0), (12.0, 20.0),
                        (0.0, 20.0)], segments=20, mat=accent)
    C.place_in_mesh(motor, GUARD_R, 0.0, HUB[2] - 4.0)
    bpy.context.view_layer.update()
    bkit.array_radial(motor, SPEC["rotors"], axis="Z", centre=HUB)

    p = C.rotor("DroneProp0", SPEC["prop_dia"] + 30.0, 2, 30.0, dark,
                chord=26.0, thick=2.6, twist=20.0)
    C.place_in_mesh(p, GUARD_R, 0.0, HUB[2] + 18.0)
    for i in range(1, SPEC["rotors"]):
        cp = bkit.duplicate(p, "DroneProp%d" % i, offset_mm=(0, 0, 0))
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = cp
        cp.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                        scale=True)
        cp.select_set(False)
        a = 2.0 * math.pi * i / SPEC["rotors"]
        ca, sa = math.cos(a), math.sin(a)
        for v in cp.data.vertices:
            v.co = bkit.v(GUARD_R + v.co.x * ca - v.co.y * sa,
                          v.co.x * sa + v.co.y * ca, v.co.z)
        cp.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ---- the landing skids, the battery and the gimballed camera ----
    for i, s in enumerate((-1, 1)):
        bkit.rounded_box("DroneSkid%d" % i, 150.0, 14.0, 14.0, r=6.0,
                         segments=2, centre=(0.0, s * 92.0, 7.0), mat=dark)
        for j, t in enumerate((-1, 1)):
            C.strut("DroneSkidLeg%d_%d" % (i, j), (t * 40.0, s * 45.0, 46.0),
                    (t * 62.0, s * 92.0, 7.0), 7.0, mat=dark)
    bkit.rounded_box("DroneBattery", 96.0, 74.0, 26.0, r=6.0, segments=2,
                     centre=(-52.0, 0.0, 62.0), mat=dark)

    bkit.uv_sphere("DroneCameraBall", SPEC["camera_ball"] / 2.0, segments=28,
                   rings=16, centre=(92.0, 0.0, 45.0), mat=dark)
    bkit.cylinder("DroneLens", SPEC["camera_lens"] / 2.0, 16.0, segments=24,
                  axis="X", centre=(118.0, 0.0, 45.0), mat=glass)
    bkit.arc_torus("DroneGimbalArm", 40.0, 6.0, -70.0, 70.0,
                   centre=(92.0, 0.0, 68.0), plane="YZ", seg_minor=12,
                   mat=accent)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 4 * 3 + 2 + 2 + 1 + 3,
                note="Guards, motors and props are arrayed about the hub with "
                     "the orbit radius baked into the mesh.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
