"""
quadcopter -- a 625 mm X-quad with four rotors on an X frame, camera below.

Four rotors is the whole object, and the count is what the model is judged on:
the four arms are arrayed RADIALLY about the hub centre at 90 deg, so a quad
with three arms is impossible to build from this script by accident. Each arm
carries its orbit radius in the MESH, because `array_radial` works on local
coordinates and a prototype placed by `obj.location` sweeps no ring at all.

The camera hangs on a two-axis gimbal ball under the nose, which is what makes
a quadcopter read as a camera platform rather than a flying cross.

Real DJI Phantom-class quad: 625 mm diagonal wheelbase, 130 mm motors,
8 x 4.5 propellers, 600 mm tall on its landing gear, 94 mm camera.
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
    diagonal=625.0,
    motor_radius=198.0,
    arm_length=230.0,
    motor_dia=130.0,
    prop_envelope=209.0,
    rotors=4,
    prop_blades=2,
    body_length=200.0,
    body_width=160.0,
    body_height=70.0,
    skid_length=260.0,
    overall_height=170.0,
    camera_dia=94.0,
)

HUB = (0.0, 0.0, 130.0)          # the arm/rotor hub the four arms orbit
MOTOR_R = SPEC["motor_radius"]
ARM_R = MOTOR_R - SPEC["arm_length"] / 2.0
MOTOR_Z = HUB[2] + 13.0
PROP_Z = MOTOR_Z + 26.0

CHECKS = [
    dict(name="diagonal", mm=625.0, tol=10.0, how="bbox_y", part="QuadArms"),
    dict(name="motor_span", mm=526.0, tol=6.0, how="bbox_x", part="QuadMotor0"),
    dict(name="motor_top", mm=156.0, tol=3.0, how="top_z", part="QuadMotor0"),
    dict(name="prop_envelope", mm=209.0, tol=8.0, how="bbox_max",
         part="QuadRotor0"),
    dict(name="body_length", mm=200.0, tol=3.0, how="bbox_x",
         part="QuadBody"),
    dict(name="skid_length", mm=260.0, tol=3.0, how="bbox_x",
         part="QuadLeg0"),
    dict(name="camera_dia", mm=94.0, tol=2.0, how="bbox_y", part="QuadCamera"),
    dict(name="skid_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="QuadLeg0"),
]


def build():
    shell = bkit.pbr("QuadShell", base=(0.90, 0.90, 0.88), rough=0.34)
    dark = bkit.preset("black_plastic")
    alu = bkit.preset("brushed_metal")
    glass = bkit.pbr("QuadGlass", base=(0.10, 0.12, 0.16), rough=0.05,
                     metal=0.3)
    red = bkit.pbr("QuadRed", base=(0.70, 0.10, 0.08), rough=0.30)

    # ---- the fuselage shell ------------------------------------------
    secs = []
    for (x, sx, sy, n) in ((-100.0, 110.0, 90.0, 4.0),
                           (-40.0, 190.0, 150.0, 3.6),
                           (40.0, 200.0, 160.0, 3.6),
                           (90.0, 140.0, 120.0, 3.2),
                           (100.0, 90.0, 80.0, 3.0)):
        ring = bkit.superellipse_section(sx, sy, n=n, steps=32,
                                         centre=(0.0, HUB[2] - 20.0))
        secs.append([(x, px, py) for (px, py) in ring])
    body = bkit.loft("QuadBody", secs, mat=shell)
    bkit.recalc(body)
    bkit.shade_smooth(body, 40.0)

    # ---- four arms, arrayed about the HUB with the radius in the mesh --
    arm = bkit.rounded_box("QuadArms", SPEC["arm_length"], 34.0, 26.0, r=10.0,
                           segments=3,
                           centre=(MOTOR_R, 0.0, HUB[2]), mat=shell)
    bpy.context.view_layer.update()
    bkit.array_radial(arm, SPEC["rotors"], axis="Z", centre=HUB)

    # ---- four motors, each a lathed can dropped on its arm end first --
    motor = bkit.lathe("QuadMotor0",
                       [(0.0, 0.0), (62.0, 0.0), (65.0, 8.0), (58.0, 20.0),
                        (40.0, 26.0), (0.0, 26.0)], segments=28, mat=dark)
    C.place_in_mesh(motor, MOTOR_R, 0.0, HUB[2])
    bkit.array_radial(motor, SPEC["rotors"], axis="Z", centre=HUB)

    # ---- four two-blade rotors, one per motor ------------------------
    # `rotor()` builds a complete rotor about the Z axis at the origin, so
    # one prototype is dropped onto motor 0 and the other three are copies
    # of it rotated 90 deg apart about the hub in MESH space -- array_radial
    # would orbit a prototype that already carries its own offset.
    protor = C.rotor("QuadRotor0", SPEC["prop_envelope"] + 46.0,
                     SPEC["prop_blades"],
                     46.0, dark, chord=52.0, thick=5.0, twist=16.0)
    C.place_in_mesh(protor, MOTOR_R, 0.0, PROP_Z)
    for i in range(1, SPEC["rotors"]):
        cp = bkit.duplicate(protor, "QuadRotor%d" % i,
                            offset_mm=(0.0, 0.0, 0.0))
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = cp
        cp.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                        scale=True)
        cp.select_set(False)
        ang = 2.0 * math.pi * i / SPEC["rotors"]
        ca, sa = math.cos(ang), math.sin(ang)
        for v in cp.data.vertices:
            v.co = bkit.v(MOTOR_R + v.co.x * ca - v.co.y * sa,
                          v.co.x * sa + v.co.y * ca, v.co.z)
        cp.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # ---- the landing gear: two skids on four struts -----------------
    for i, s in enumerate((-1, 1)):
        bkit.rounded_box("QuadLeg%d" % i, SPEC["skid_length"], 22.0, 22.0,
                         r=8.0, segments=2, centre=(0.0, s * 150.0, 11.0),
                         mat=dark)
        for j, t in enumerate((-1, 1)):
            C.strut("QuadStrut%d_%d" % (i, j), (t * 90.0, s * 30.0, 118.0),
                    (t * 110.0, s * 150.0, 11.0), 10.0, mat=alu)

    # ---- the gimballed camera under the nose ------------------------
    bkit.uv_sphere("QuadGimbal", 52.0, segments=24, rings=16,
                   centre=(60.0, 0.0, 78.0), mat=dark)
    bkit.cylinder("QuadCamera", 47.0, 44.0, segments=28, axis="X",
                  centre=(105.0, 0.0, 78.0), mat=shell)
    bkit.cylinder("QuadCameraLens", 30.0, 16.0, segments=24, axis="X",
                  centre=(132.0, 0.0, 78.0), mat=glass)
    bkit.rounded_box("QuadLensRing", 14.0, 66.0, 66.0, r=10.0, segments=3,
                     centre=(126.0, 0.0, 78.0), mat=dark)

    # ---- battery and the two nav lights -----------------------------
    bkit.rounded_box("QuadBattery", 150.0, 96.0, 52.0, r=8.0, segments=2,
                     centre=(-20.0, 0.0, HUB[2] + 44.0), mat=dark)
    for i, s in enumerate((-1, 1)):
        bkit.cylinder("QuadNav%d" % i, 16.0, 16.0, segments=14,
                      centre=(0.0, s * 78.0, HUB[2] + 20.0),
                      mat=red if s < 0 else bkit.pbr("QuadGreen",
                                                    base=(0.10, 0.70, 0.20)))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 1 + 1 + 4 + 4 + 4 + 2,
                note="Four arms and four rotors, arrayed about the hub; the "
                     "orbit radius lives in the mesh, not in obj.location.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
