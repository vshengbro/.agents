"""
iv_drip -- 1800 mm five-leg IV drip stand: 300 mm castored base, a 25 mm lower
pole inside a 19 mm sliding upper pole, a knurled collar and four top hooks.

The five legs and the four hooks come from `bkit.array_radial`, not from typed
in coordinates: five hand-placed legs at 72 degrees either collide with each
other or leave a gap you cannot see until the render.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit


def radial_array(obj, name, count, join=True):
    """Place `count` copies of `obj` evenly about the Z axis.

    `bkit.array_radial` does not orbit correctly in this Blender build -- its
    pivot empty's matrix_world is still identity when the modifier is applied,
    so each copy is offset by the object's own location instead of a rotation,
    and the parts march off in a diagonal line. The copies are therefore placed
    here: the part's local origin is rotated about Z and its location rotated
    with it. `obj` must be unrotated about X/Y (box, cylinder, arc_torus all
    qualify).
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
    if join:
        bpy.context.view_layer.update()
        return bkit.join(copies, name=name)
    return copies

SPEC = dict(
    overall_height=1760.0,
    base_span=566.0,          # leg tip to leg tip, over the castors
    lower_pole_diameter=25.0,
    upper_pole_diameter=19.0,
    collar_diameter=42.0,
    hooks=4,
    legs=5,
    caster_diameter=50.0,
)

LEGS = SPEC["legs"]
LEG_REACH = 285.0            # pole axis to the leg end, where the castors sit
LOWER_TOP = 1080.0
TOP_Z = SPEC["overall_height"] - 60.0        # 1700.0, where the cross sits
CAST_R = SPEC["caster_diameter"] / 2.0


def build():
    steel = bkit.pbr("IVSteel", base=(0.76, 0.78, 0.80), metal=0.80, rough=0.26)
    chrome = bkit.pbr("IVChrome", base=(0.82, 0.84, 0.86), metal=0.86,
                      rough=0.12)
    rubber = bkit.preset("rubber")
    plastic = bkit.preset("white_plastic")

    # ---- base: hub, five legs, five castors -------------------------------
    bkit.cylinder("BaseHub", 52.0, 46.0, segments=48, centre=(0, 0, 30.0),
                  mat=steel)

    leg = bkit.rounded_box("BaseLeg", LEG_REACH, 34.0, 24.0, r=8.0, segments=3,
                           centre=(LEG_REACH / 2.0, 0.0, 26.0), mat=steel)
    radial_array(leg, "BaseLegs", LEGS)

    caster = []
    for i in range(LEGS):
        a = 2.0 * math.pi * i / LEGS
        # centre the castor ON the floor line: at z = CAST_R it rests on z=0
        # instead of sinking 13 mm, which would make sit_on_floor lift the whole
        # stand and add that lift to every height in the report
        caster.append(bkit.cylinder("_caster", CAST_R, 20.0, segments=32,
                                    centre=(LEG_REACH * math.cos(a),
                                            LEG_REACH * math.sin(a), CAST_R),
                                    axis="Y", mat=rubber))
    casters = bkit.join(caster, name="BaseCasters")

    # ---- the two telescoping poles ----------------------------------------
    bkit.cylinder("LowerPole", SPEC["lower_pole_diameter"] / 2.0, LOWER_TOP - 10.0,
                  segments=48, centre=(0, 0, (LOWER_TOP - 10.0) / 2.0 + 30.0),
                  mat=chrome)
    upper_len = TOP_Z + 60.0 - (LOWER_TOP - 240.0)
    bkit.cylinder("UpperPole", SPEC["upper_pole_diameter"] / 2.0, upper_len,
                  segments=48,
                  centre=(0, 0, (LOWER_TOP - 240.0 + TOP_Z + 60.0) / 2.0),
                  mat=chrome)
    bkit.cylinder("PoleCollar", SPEC["collar_diameter"] / 2.0, 34.0, segments=48,
                  centre=(0, 0, LOWER_TOP - 180.0), mat=plastic)
    bkit.cylinder("PoleKnob", 15.0, 16.0, segments=32,
                  centre=(SPEC["collar_diameter"] / 2.0 + 10.0, 0.0,
                          LOWER_TOP - 180.0),
                  axis="X", mat=plastic)

    # ---- the top cross and its four hooks ---------------------------------
    bkit.cylinder("TopCross", 13.0, 78.0, segments=32,
                  centre=(0, 0, TOP_Z + 8.0), mat=steel)
    hook = bkit.arc_torus("TopHook", 22.0, 4.5, -95.0, 175.0,
                          centre=(40.0, 0.0, TOP_Z - 40.0), plane="XZ",
                          seg_major=28, mat=steel, caps=True)
    radial_array(hook, "TopHooks", SPEC["hooks"])

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="lower_pole_diameter", mm=25.0, tol=0.3, how="diameter",
         part="LowerPole"),
    dict(name="base_hub_diameter", mm=104.0, tol=0.5, how="diameter",
         part="BaseHub"),
    dict(name="base_span", mm=565.6, tol=8.0, how="bbox_x"),
    dict(name="overall_height", mm=1760.0, tol=8.0, how="bbox_z"),
]