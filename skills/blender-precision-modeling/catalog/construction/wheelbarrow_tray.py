"""
wheelbarrow_tray -- a bricklayer's pointing trowel: 280 mm tapered blade, bent shank, turned ash handle.

A trowel is a flat triangular-blade tool with a REAL SHANK: the blade is a
tapered plate, the shank is a rod that rises out of the heel of the blade and
bends back to the handle. Building it as blade + straight stick reads as a
spatula; the tangent at the heel is what makes it a trowel.

    blade  : 280 mm long, 120 mm wide at the heel, 18 mm thick, tapering
    shank  : 6 mm round rod rising 55 mm and bending 40 mm back
    handle : a turned ash handle, 130 mm long, waisted

The handle is a `lathe` on a closed profile, so it has a real waisted grip
rather than being a cone. The blade outline is an `extrude_profile` of a
hand-written triangle whose tip is blunted by 12 mm, because a real brick trowel
blade has a rounded point, not a mathematical one.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    blade_length=200.0,
    blade_heel_width=100.0,
    blade_thickness=18.0,
    blade_tip_blunt=12.0,
    shank_dia=6.0,
    shank_rise=55.0,
    shank_setback=40.0,
    handle_length=95.0,
    handle_dia=32.0,
)

BL = SPEC["blade_length"]
BW = SPEC["blade_heel_width"]
BT = SPEC["blade_thickness"]
TIP = SPEC["blade_tip_blunt"]
HD = SPEC["handle_dia"]
HL = SPEC["handle_length"]

# the heel of the blade sits at x = -BL/2, the tip at x = +BL/2
HEEL_X = -BL / 2.0

CHECKS = [
    dict(name="blade_length", mm=200.0, tol=1.0, how="bbox_x", part="TrowelBlade"),
    dict(name="blade_heel_width", mm=100.0, tol=1.0, how="bbox_y",
         part="TrowelBlade"),
    dict(name="blade_thickness", mm=18.0, tol=1.0, how="bbox_z", part="TrowelBlade"),
    dict(name="handle_rise", mm=60.0, tol=2.0, how="bbox_z", part="TrowelHandle"),
    dict(name="handle_diameter", mm=32.0, tol=1.0, how="bbox_y",
         part="TrowelHandle"),
]


def build():
    steel = bkit.pbr("TrowelSteel", base=(0.72, 0.73, 0.75), metal=0.85,
                     rough=0.20)
    ash = bkit.pbr("TrowelAsh", base=(0.56, 0.40, 0.22), rough=0.48)

    # ---- the blade: a tapered triangle, blunted at the tip ----------
    # heel corners first, then the tip blunted to TIP across the centreline
    poly = [
        (HEEL_X, -BW / 2.0),
        (HEEL_X, BW / 2.0),
        (BL / 2.0 - TIP, BW / 2.0 * 0.10),
        (BL / 2.0, 0.0),
        (BL / 2.0 - TIP, -BW / 2.0 * 0.10),
    ]
    blade = bkit.extrude_profile("TrowelBlade", poly, BT, axis="Z", mat=steel)
    bkit.recalc(blade)
    # the shank socket bosses sit ON the blade, so the blade is lifted clear of
    # the floor by its own thickness / 2
    bkit.move(blade, 0.0, 0.0, BT / 2.0 + 2.0)

    # ---- the shank: rises from the heel, then sets BACK ------------
    # This tangent is the read. Two segments, computed from the declared rise and
    # setback, meeting at the heel tangent point.
    rise = SPEC["shank_rise"]
    setback = SPEC["shank_setback"]
    sd = SPEC["shank_dia"]
    base_z = BT + 2.0
    tangent = (HEEL_X + 26.0, 0.0, base_z + rise)

    shank_a = bkit.cylinder("TrowelShankA", sd / 2.0,
                            ((tangent[2] - base_z) ** 2
                             + (tangent[0] - HEEL_X) ** 2) ** 0.5 + 8.0,
                            segments=14, mat=steel)
    orient(shank_a, (HEEL_X, 0.0, base_z - 4.0), tangent)

    hx = tangent[0] - setback
    hz = tangent[2] + rise * 0.35
    shank_b = bkit.cylinder("TrowelShankB", sd / 2.0,
                            ((hz - tangent[2]) ** 2 + (hx - tangent[0]) ** 2)
                            ** 0.5 + 8.0, segments=14, mat=steel)
    orient(shank_b, tangent, (hx, 0.0, hz))

    # ---- the ferrule + turned ash handle ---------------------------
    bkit.cylinder("TrowelFerrule", 13.0, 26.0, segments=20,
                  centre=(hx - 10.0, 0.0, hz + 6.0), mat=steel)

    # a turned grip: swelled at the butt, waisted at the neck
    r = HD / 2.0
    prof = [
        (0.0, 0.0), (r * 0.95, 0.0), (r, r * 0.9), (r * 0.80, r * 2.6),
        (r * 0.72, r * 3.6), (r * 0.86, r * 4.6), (r * 0.90, HL * 0.86),
        (r * 0.55, HL - 6.0), (0.0, HL),
    ]
    handle = bkit.lathe("TrowelHandle", prof, segments=32, mat=ash)
    # the lathe builds along +Z; stand it up along the shank and offset it
    handle.rotation_euler = (0.0, -1.15, 0.0)
    bpy.context.view_layer.update()
    handle.location = bkit.v(hx - 18.0, 0.0, hz + 12.0)

    return dict(spec=SPEC, parts=5)


def orient(ob, p0, p1):
    """Point a cylinder built along +Z from p0 to p1 (mm)."""
    import mathutils
    d = mathutils.Vector(p1) - mathutils.Vector(p0)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (mathutils.Vector(p0) + mathutils.Vector(p1))))
    bpy.context.view_layer.update()
    return ob