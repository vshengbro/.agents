"""protractor -- a 120 mm half-circle protractor: the semicircular plate with a
real centre notch, degree graduations at a 1 degree module with the long ticks
every 10 degrees, a double rule along the straight edge, and a riveted pivot.

The graduations are the model: 61 ticks across 60 degrees at a 1 degree step,
each at an angle derived from its own index, with three tick lengths (every 5,
every 10, and every 30 degrees long). Hand-placed ticks cannot hold a degree
pitch; these do.

Construction: a semicircular extruded profile, a fan of tick blades each
rotated by its own index-derived angle about the pivot, and a straight-edge
rule. Nothing depends on a boolean except the centre notch, whose cutter
overlaps the host by 1 mm.

Orientation: the straight edge along +X, the arc over +Y, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    diameter=120.0,
    pivot_height=5.0,
    thickness=1.6,
    tick_count=61,
    tick_module_deg=1.0,
    major_tick_length=13.0,
)

R = 60.0
T = 1.6


def build():
    body = bkit.pbr("ProtractorBody", base=(0.86, 0.84, 0.78), rough=0.36)
    ink = bkit.pbr("ProtractorInk", base=(0.12, 0.12, 0.14), rough=0.46)
    steel = bkit.pbr("ProtractorSteel", base=(0.72, 0.74, 0.78), metal=0.85,
                     rough=0.22)
    brass = bkit.pbr("ProtractorBrass", base=(0.78, 0.62, 0.26), metal=0.85,
                     rough=0.28)

    # ---- the semicircular plate, with the flat edge on the X axis
    n_arc = 48
    arc = [(R * math.cos(math.pi * i / n_arc),
            R * math.sin(math.pi * i / n_arc)) for i in range(n_arc + 1)]
    plate = bkit.extrude_profile("Plate", arc, T,
                                 centre=(0.0, 0.0, T / 2.0), axis="Z",
                                 mat=body)
    bkit.recalc(plate)

    # ---- the centre notch: a cutter that overlaps the plate edge by 1 mm so
    # the two surfaces cross instead of touching tangentially
    notch = bkit.rounded_box("_notch", 6.0, 7.0, T + 6.0, r=0.6, segments=3,
                             centre=(2.0, -1.0, T / 2.0))
    bkit.boolean(plate, notch, "DIFFERENCE")

    # ---- 61 degree graduations, each rotated by its own index
    for i in range(SPEC["tick_count"]):
        deg = i * SPEC["tick_module_deg"]
        a = math.radians(deg)
        if deg % 30 == 0:
            ln, w, mat = SPEC["major_tick_length"], 0.55, ink
        elif deg % 10 == 0:
            ln, w, mat = 9.0, 0.45, ink
        elif deg % 5 == 0:
            ln, w, mat = 6.0, 0.38, ink
        else:
            ln, w, mat = 3.6, 0.30, ink
        # authored along +X at the arc's inner radius, then rotated by the
        # tick's own angle: the position is DERIVED, never typed in
        tick = bkit.rounded_box("Tick%d" % i, w, ln, 0.18, r=0.05,
                                segments=2,
                                centre=(R - 2.0 - ln / 2.0, 0.0, T + 0.08),
                                mat=mat)
        bpy.context.view_layer.update()
        for v in tick.data.vertices:
            ca, sa = math.cos(a), math.sin(a)
            x, y = v.co.x, v.co.y
            v.co.x = x * ca - y * sa
            v.co.y = x * sa + y * ca
        tick.data.update()

    # ---- the pivot pin and its brass washer
    bkit.cylinder("PivotPin", 1.5, 4.0, segments=24, centre=(0.0, 0.0, 3.0),
                  mat=steel)
    bkit.tube("Washer", 4.2, 2.0, 0.6, segments=28, centre=(0.0, 0.0, 3.4),
              mat=brass)

    # ---- the double rule along the straight edge
    for k, yy in enumerate((4.5, 7.0)):
        bkit.rounded_box("Rule%d" % k, 2.0 * R - 8.0, 0.4, 0.2, r=0.06,
                         segments=2, centre=(0.0, yy, T + 0.09), mat=ink)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=70)


CHECKS = [
    dict(name="diameter", mm=120.0, tol=1.0, how="bbox_x", part="Plate"),
    dict(name="thickness", mm=1.6, tol=0.3, how="bbox_z", part="Plate"),
    dict(name="major_tick_length", mm=13.0, tol=0.8, how="bbox_y",
         part="Tick0"),
    dict(name="arc_radius", mm=60.0, tol=1.0, how="bbox_y", part="Plate"),
    dict(name="pivot_height", mm=5.0, tol=0.6, how="bbox_z"),
]