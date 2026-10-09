"""
cement_mixer -- a 350 mm diesel site mixer: tilting drum, chassis, 2 wheels.

A site mixer reads as three things and they must all be right:

  1. the DRUM, which is a truncated cone (350 mm at the mouth, 480 mm at the
     base) tilted 45 deg on trunnions -- the tilt is the whole mechanism,
  2. the CHASSIS, a rectangular frame on two pneumatic wheels with the engine
     slung under the drum,
  3. the HANDLE, a tube rising at 30 deg from the drum's pivot, which is what
     makes it hand-tilting rather than a fixed drum.

Dimensions are a real 350/7 (350 L drum, 7 hp) mixer: 1300 mm to the drum
mouth, 1750 mm to the handle end, 1300 mm tall over the drum rim, wheels
550 mm in diameter on a 950 mm track. `sit_on_floor` then has nothing to do,
because the wheels are authored with their treads exactly on z=0.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import math
from mathutils import Matrix, Vector

import bpy
import bkit
import _sections as S

SPEC = dict(
    drum_mouth_dia=350.0,
    drum_base_dia=480.0,
    drum_depth=520.0,
    drum_tilt_deg=45.0,
    chassis_length=1300.0,
    chassis_width=560.0,
    handle_length=750.0,
    handle_angle_deg=32.0,
    wheel_dia=550.0,
    wheel_width=110.0,
    track=950.0,
)

MOUTH = SPEC["drum_mouth_dia"]
BASE = SPEC["drum_base_dia"]
DEPTH = SPEC["drum_depth"]
WD = SPEC["wheel_dia"]
WT = SPEC["wheel_width"]
TRACK = SPEC["track"]

# The drum's pivot sits at the chassis rear. The pivot height is NOT free: a
# 480 mm base disc swung through a 45 deg tilt reaches 240 mm below the trunnion,
# so the trunnion has to stand at least that high or the drum is under the
# floor. 560 mm clears it and keeps the machine a realistic site-mixer height.
PIVOT_X = -260.0
PIVOT_Z = 560.0

TILT = SPEC["drum_tilt_deg"]
CHASSIS_L = SPEC["chassis_length"]
CHASSIS_W = SPEC["chassis_width"]
HANDLE_L = SPEC["handle_length"]

CHECKS = [
    # The drum tilts about Y, so its Y extent is untouched by the tilt and is
    # still the drum's largest diameter. The MOUTH is the small end of a cone
    # seen at 45 deg, so its 350 mm cannot be read off any bounding box -- the
    # X extent (661 mm) is the drum's overall span down the slope instead.
    dict(name="drum_base_dia", mm=480.0, tol=3.0, how="bbox_y", part="MixerDrum"),
    dict(name="drum_span", mm=661.0, tol=4.0, how="bbox_x", part="MixerDrum"),
    dict(name="drum_rise", mm=661.0, tol=4.0, how="bbox_z", part="MixerDrum"),
    dict(name="wheel_dia", mm=550.0, tol=3.0, how="bbox_z", part="MixerWheel0"),
    # the two wheels on a 950 mm track, each 121 mm wide: the outer-to-outer
    # span is 950 + 121 = 1071 mm, which is what the assembly's Y extent is
    dict(name="wheel_track_outer", mm=1071.0, tol=4.0, how="bbox_y", part=None),
    dict(name="wheel_tread_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="MixerWheel0"),
]


def build():
    paint = bkit.pbr("MixerPaint", base=(0.72, 0.30, 0.05), metal=0.25,
                     rough=0.40, coat=0.3)
    steel = bkit.preset("dark_metal")
    frame = bkit.preset("steel")
    rubber = bkit.preset("rubber")

    # ---- drum: a truncated cone, open at the mouth -----------------
    # A mixer drum is a cone, so the taper is the read. It is a `lathe` of a
    # closed section: outer wall, mouth rim, inner wall back to the base, so the
    # mouth is genuinely open and you can see the helical blades inside.
    wall = 8.0
    r_out = BASE / 2.0
    r_in = MOUTH / 2.0
    prof = [
        (0.0, 0.0), (r_out - wall, 0.0), (r_out, 0.0),
        (r_in, DEPTH), (r_in - wall, DEPTH),
        (r_out - 2.0 * wall, wall), (0.0, wall),
    ]
    drum = bkit.lathe("MixerDrum", prof, segments=48, mat=paint,
                      cap_ends=False)
    bkit.recalc(drum)

    # the base disc, separately named so its diameter is measurable
    bkit.cylinder("MixerDrumBase", r_out, wall + 2.0, segments=48,
                  centre=(0.0, 0.0, (wall + 2.0) / 2.0), mat=paint)

    # two lifting bands around the drum
    for i, (rr, zz) in enumerate(((r_out - 30.0, 90.0),
                                  (r_out * 0.72, DEPTH * 0.62))):
        zr = DEPTH * (zz / DEPTH)
        rr_ = r_out + (r_in - r_out) * (zz / DEPTH)
        bkit.tube("MixerDrumBand%d" % i, rr_ + 10.0, rr_ - 4.0, 60.0,
                  segments=48, axis="Z", centre=(0.0, 0.0, zz),
                  mat=steel)

    # ---- tilt the drum onto its trunnions --------------------------
    # The rotation is about the drum's OWN base centre, and the trunnion offset
    # is a separate translation afterwards.
    #
    # Rotating about the trunnion instead is the obvious thing and it is wrong:
    # the base disc then sits 260 mm forward of the pivot, so the tilt swings it
    # 750 mm DOWN, the drum lands below z=0, and `sit_on_floor` raises the whole
    # machine by 210 mm -- lifting both wheels off the ground while the report
    # still shows a clean bounding box.
    tilt = math.radians(TILT)
    R = Matrix.Rotation(tilt, 4, "Y")

    for name in ("MixerDrum", "MixerDrumBase",
                 "MixerDrumBand0", "MixerDrumBand1"):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.data.transform(R)
            ob.location = (0.0, 0.0, 0.0)
    for name in ("MixerDrum", "MixerDrumBase",
                 "MixerDrumBand0", "MixerDrumBand1"):
        ob = bpy.data.objects.get(name)
        bkit.move(ob, PIVOT_X, 0.0, PIVOT_Z)
    bpy.context.view_layer.update()

    # ---- chassis frame ---------------------------------------------
    bkit.rounded_box("MixerChassis", CHASSIS_L, CHASSIS_W, 90.0, r=8.0,
                     segments=2, centre=(120.0, 0.0, PIVOT_Z - 60.0),
                     mat=frame)
    for sy in (-1, 1):
        S.bar_between("MixerChassisRail%s" % ("L" if sy < 0 else "R"),
                      (120.0 - CHASSIS_L / 2.0, sy * (CHASSIS_W / 2.0 - 40.0),
                       PIVOT_Z - 110.0),
                      (120.0 + CHASSIS_L / 2.0, sy * (CHASSIS_W / 2.0 - 40.0),
                       PIVOT_Z - 110.0),
                      70.0, 70.0, mat=frame, r=6.0)

    # ---- engine slung under the drum --------------------------------
    bkit.rounded_box("MixerEngine", 420.0, 380.0, 420.0, r=40.0, segments=2,
                     centre=(150.0, 0.0, PIVOT_Z - 300.0), mat=paint)
    bkit.cylinder("MixerExhaust", 45.0, 260.0, segments=18,
                  centre=(250.0, 150.0, PIVOT_Z + 60.0), mat=steel)

    # ---- handle rising from the pivot end --------------------------
    ang = math.radians(SPEC["handle_angle_deg"])
    hx = PIVOT_X - HANDLE_L * math.cos(ang)
    hz = PIVOT_Z + HANDLE_L * math.sin(ang)
    S.bar_between("MixerHandle", (PIVOT_X, 0.0, PIVOT_Z), (hx, 0.0, hz),
                  48.0, 48.0, mat=frame, r=8.0)
    S.bar_between("MixerHandleGrip", (hx, -60.0, hz), (hx, 60.0, hz),
                  50.0, 50.0, mat=steel, r=10.0)

    # ---- legs + 2 wheels, treads exactly on z=0 -------------------
    for sy in (-1, 1):
        S.bar_between("MixerLeg%s" % ("L" if sy < 0 else "R"),
                      (PIVOT_X + 60.0, sy * (CHASSIS_W / 2.0 - 30.0),
                       PIVOT_Z - 100.0),
                      (PIVOT_X + 20.0, sy * (CHASSIS_W / 2.0 - 30.0), 10.0),
                      60.0, 60.0, mat=frame, r=6.0)

    wheel = mixer_wheel("MixerWheel0", WD, WT, WD * 0.45)
    bkit.duplicate(wheel, "MixerWheel1",
                   offset_mm=(PIVOT_X + 40.0, TRACK / 2.0, WD / 2.0))
    bkit.move(wheel, PIVOT_X + 40.0, -TRACK / 2.0, WD / 2.0)

    return dict(spec=SPEC, parts=10)


def mixer_wheel(name, dia, width, rim_dia, seg=40):
    """A pneumatic site-mixer wheel: tyre carcass + rim, built at the origin."""
    rt = dia / 2.0
    ri = rim_dia / 2.0
    hw = width / 2.0
    prof = [(ri, -hw), (rt - 20.0, -hw), (rt, -hw + 22.0),
            (rt, hw - 22.0), (rt - 20.0, hw), (ri, hw), (ri, -hw)]
    tyre = bkit.lathe(name + "_Tyre", prof, segments=seg, cap_ends=False,
                      mat=bkit.preset("rubber"))
    tyre.rotation_euler = (1.5707963267948966, 0.0, 0.0)
    bpy.context.view_layer.update()
    rim = bkit.tube(name + "_Rim", ri + 2.0, ri - 40.0, width * 0.86,
                    segments=seg, axis="Y", mat=bkit.preset("steel"))
    hub = bkit.cylinder(name + "_Hub", 55.0, width * 1.1, segments=24,
                        axis="Y", mat=bkit.preset("dark_metal"))
    parts = [tyre, rim, hub]
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.name = name
    ob.location = (0.0, 0.0, 0.0)
    return ob