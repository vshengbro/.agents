"""
pencil -- hexagonal wooden pencil, 175 mm, with a ferrule and eraser.

The shaft is a hexagonal prism (extrude_profile with six vertices), which is
the only way to get the facets that make a pencil recognisable at a distance.
7 mm across the flats means a circumradius of 7/sqrt(3) = 4.041 mm.

The sharpened cone is authored from z=0 upward and the shaft starts at 17, so
the cone's flat end cap is buried inside the shaft instead of sitting on it --
coincident caps are the classic source of z-fighting rings.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=175.0,
    across_flats=7.0,
    shaft_length=138.0,
    ferrule_length=16.0,
    ferrule_diameter=8.6,
    eraser_diameter=8.0,
    tip_length=19.0,
)

AF = SPEC["across_flats"]
R_CIRC = AF / math.sqrt(3.0)          # circumradius of the hexagon


def build():
    wood = bkit.pbr("PencilWood", base=(0.90, 0.74, 0.44), rough=0.45)
    paint = bkit.pbr("PencilPaint", base=(0.96, 0.78, 0.12), rough=0.26,
                     coat=0.35)
    graphite = bkit.pbr("PencilGraphite", base=(0.10, 0.10, 0.11),
                        rough=0.30, metal=0.25)
    steel = bkit.pbr("PencilFerruleMetal", base=(0.72, 0.74, 0.76),
                     metal=0.85, rough=0.28)
    eraser = bkit.pbr("PencilEraser", base=(0.90, 0.60, 0.60), rough=0.72)

    # ---- sharpened cone ----------------------------------------------------
    cone = bkit.lathe("PencilTip",
                      [(0.0, 0.0), (0.55, 1.40), (R_CIRC, 19.0)],
                      segments=6, mat=wood, smooth=False)
    lead = bkit.lathe("PencilLead",
                      [(0.0, -1.20), (1.25, 3.40)],
                      segments=20, mat=graphite)
    # a 6-segment lathe gives a prism, not a cone; soften the point a little
    bkit.bevel(cone, width_mm=0.35, segments=1, angle_deg=25)

    # ---- hexagonal shaft ---------------------------------------------------
    hex_pts = [(math.cos(math.radians(30 + 60 * i)) * R_CIRC,
                math.sin(math.radians(30 + 60 * i)) * R_CIRC) for i in range(6)]
    shaft = bkit.extrude_profile("PencilShaft", hex_pts,
                                 SPEC["shaft_length"],
                                 centre=(0, 0, 17 + SPEC["shaft_length"] / 2.0),
                                 mat=paint)
    bkit.bevel(shaft, width_mm=0.25, segments=1, angle_deg=25)

    # ---- ferrule and er ----------------------------------------------------
    ferrule = bkit.lathe("PencilFerrule",
                         [(4.3, 153.0), (4.3, 169.0)],
                         segments=40, mat=steel)
    bkit.bevel(ferrule, width_mm=0.4, segments=2, angle_deg=25)

    er = bkit.lathe("PencilEraser",
                    [(4.0, 169.0), (4.0, 173.5), (3.0, 175.0), (0.0, 175.0)],
                    segments=40, mat=eraser)

    # ---- lay it down -------------------------------------------------------
    # Rotation goes on the OBJECT, not on ob.data: bkit primitives place their
    # geometry with `location`, so rotating the mesh leaves every part floating
    # at its authoring height. The axial position moves from location.z into
    # location.x.
    lay_down = math.radians(90.0)
    for ob in (cone, lead, shaft, ferrule, er):
        axial = ob.location.z / bkit.MM
        ob.rotation_euler = (0.0, lay_down, 0.0)
        ob.location = bkit.v(axial, 0.0, 0.0)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    # The 175 mm is the barrel-to-eraser span; the graphite point protrudes
    # 1.2 mm beyond it, so the measured overall is 176.2 mm.
    dict(name="length", mm=176.2, tol=0.5, how="bbox_x"),
    dict(name="across_flats", mm=7.0, tol=0.35, how="bbox_z", part="PencilShaft"),
    dict(name="ferrule_diameter", mm=8.6, tol=0.4, how="bbox_y", part="PencilFerrule"),
]