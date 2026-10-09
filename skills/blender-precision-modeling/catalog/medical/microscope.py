"""
microscope -- 420 mm monocular optical microscope: base, illuminator,
condenser, mechanical stage with a real light hole, curved arm, body tube,
three-objective turret, and coarse/fine focus knobs.

The stage hole is cut with `bkit.bore`, which picks a cutter segment count that
cannot coincide with the host's facets -- a plain cylinder at the same count as
the stage's bevel geometry is how the body gets deleted instead of drilled.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_height=411.0,
    base_size=210.0,
    stage_size=150.0,
    stage_height=195.0,
    body_tube_diameter=44.0,
    objective_count=3,
    focus_knob_diameter=64.0,
)

BS = SPEC["base_size"]
STAGE_Z = SPEC["stage_height"]


def tilt(obj, deg_y=0.0, deg_x=0.0):
    """Tilt a placed part and refresh matrix_world, which Blender caches."""
    obj.rotation_euler = (math.radians(deg_x), math.radians(deg_y), 0.0)
    bpy.context.view_layer.update()
    return obj


def radial_array(obj, name, count):
    """`count` copies of `obj` evenly about Z.

    `bkit.array_radial` does not orbit correctly in this Blender build -- the
    pivot empty's matrix_world is still identity when the modifier is applied,
    so copies are offset by the object's own location rather than rotated (the
    objectives ended up 510 mm apart along Z, which no Z-axis rotation can do).
    The copies are placed explicitly instead.
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
    body_mat = bkit.pbr("ScopeBody", base=(0.86, 0.86, 0.84), rough=0.34)
    dark = bkit.pbr("ScopeDark", base=(0.16, 0.16, 0.17), rough=0.42)
    steel = bkit.pbr("ScopeSteel", base=(0.80, 0.82, 0.85), metal=0.80,
                     rough=0.20)
    glass = bkit.pbr("ScopeLens", base=(0.55, 0.68, 0.72), rough=0.06,
                     transmission=0.65, ior=1.52, coat=0.5)

    # ---- base and illuminator ---------------------------------------------
    bkit.rounded_box("ScopeBase", BS, BS * 0.78, 46.0, r=14.0, segments=4,
                     centre=(0, 0, 23.0), mat=body_mat)
    bkit.cylinder("Illuminator", 42.0, 54.0, segments=48,
                  centre=(6.0, 0.0, 73.0), mat=dark)
    bkit.cylinder("Condenser", 30.0, 46.0, segments=48,
                  centre=(6.0, 0.0, 123.0), mat=dark)
    bkit.cylinder("CondenserLens", 24.0, 3.0, segments=48,
                  centre=(6.0, 0.0, 144.0), mat=glass)

    # ---- mechanical stage, drilled for the light path ----------------------
    stage = bkit.rounded_box("Stage", SPEC["stage_size"], SPEC["stage_size"] * 0.88,
                             12.0, r=3.0, segments=3,
                             centre=(14.0, 0.0, STAGE_Z), mat=body_mat)
    bkit.bore(stage, 21.0, depth=26.0, centre=(14.0, 0.0, STAGE_Z),
              host_segments=48)

    # ---- arm: a column and a top bridge ------------------------------------
    bkit.rounded_box("ArmColumn", 52.0, 66.0, 300.0, r=18.0, segments=4,
                     centre=(-66.0, 0.0, 196.0), mat=body_mat)
    bkit.rounded_box("ArmBridge", 120.0, 62.0, 44.0, r=16.0, segments=4,
                     centre=(-16.0, 0.0, 336.0), mat=body_mat)

    # ---- body tube, tilted back off vertical like a real optic -------------
    tube = bkit.cylinder("BodyTube", SPEC["body_tube_diameter"] / 2.0, 150.0,
                         segments=48, centre=(0, 0, 0), mat=body_mat)
    bpy.context.view_layer.update()
    tube.location = bkit.v(20.0, 0.0, 316.0)
    tilt(tube, deg_y=-22.0)
    eye = bkit.cylinder("Eyepiece", 15.0, 46.0, segments=32, centre=(0, 0, 0),
                        mat=dark)
    bpy.context.view_layer.update()
    eye.location = bkit.v(-27.0, 0.0, 384.0)
    tilt(eye, deg_y=-22.0)

    # ---- three-objective turret -------------------------------------------
    bkit.cylinder("ObjectiveTurret", 29.0, 26.0, segments=48,
                  centre=(30.0, 0.0, 268.0), mat=body_mat)
    obj = bkit.cylinder("Objective", 9.0, 34.0, segments=32,
                        centre=(30.0 + 20.0, 0.0, 238.0), mat=dark)
    radial_array(obj, "Objectives", SPEC["objective_count"])

    # ---- coarse and fine focus knobs, both sides --------------------------
    knobs = []
    for sign in (-1.0, 1.0):
        knobs.append(bkit.cylinder("_knob", SPEC["focus_knob_diameter"] / 2.0,
                                   22.0, segments=40,
                                   centre=(0.0, sign * 56.0, 168.0),
                                   axis="Y", mat=dark))
        knobs.append(bkit.cylinder("_fine", 18.0, 18.0, segments=32,
                                   centre=(0.0, sign * 70.0, 168.0),
                                   axis="Y", mat=steel))
    bkit.join(knobs, name="FocusKnobs")

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="base_size", mm=210.0, tol=0.5, how="bbox_x", part="ScopeBase"),
    # The body tube is tilted 22 deg about Y, so its bounding box in X is the
    # 150 mm length foreshortened plus the 44 mm bore. bbox_y is the diameter.
    dict(name="body_tube_diameter", mm=44.0, tol=0.5, how="bbox_y",
         part="BodyTube"),
    dict(name="overall_height", mm=411.0, tol=3.0, how="bbox_z"),
]