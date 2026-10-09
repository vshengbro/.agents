"""
greenhouse -- a 5.6 x 2.8 m barrel-vaulted glasshouse, 1.9 m eaves.

The structure is an ARC, not a rectangle, and the geometry that matters is the
segmental arch: a 1400 mm half-span rising 1000 mm to the ridge is a 1480 mm
radius whose centre sits 480 mm BELOW the eave line, not a 1400 mm quarter
circle. Every portal frame is one `arc_torus` on that radius, and the glazing
follows it from exactly the eave angle where the two meet.

The glass is a SHELL, not a sheet: each pane is a closed ring (outer arc, inner
arc back again) lofted along its length, so the glass has real 14 mm thickness
and a real edge instead of a zero-thickness surface that renders as a black
card.

Real domestic glasshouse: 5600 mm long, 2800 mm wide, 1900 mm eaves, 2886 mm
ridge, portal frames at 700 mm centres over a 300 mm dwarf wall.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy

SPEC = dict(
    length=5600.0,
    width=2800.0,
    dwarf_wall_height=300.0,
    eaves_height=1900.0,
    ridge_height=2886.0,
    frame_span=2990.0,
    arch_radius=1480.0,
    arch_rise=1000.0,
    bays=8,
    bay_pitch=700.0,
    glass_thickness=14.0,
)

L = SPEC["length"]
W = SPEC["width"]
DW = SPEC["dwarf_wall_height"]
EAVE = SPEC["eaves_height"]
R = SPEC["arch_radius"]
ZC = EAVE + SPEC["arch_rise"] - R      # 480 mm below the eave line
BAYS = SPEC["bays"]
PITCH = SPEC["bay_pitch"]
HALF = W / 2.0
T = SPEC["glass_thickness"]
BAY_X = [-L / 2.0 + i * PITCH for i in range(BAYS + 1)]

A_EAVE = math.degrees(math.asin((EAVE - ZC) / R))          # 18.90 deg
A_GLASS = math.degrees(math.asin((EAVE - ZC) / (R - T)))    # glazing radius

CHECKS = [
    dict(name="length", mm=5600.0, tol=8.0, how="bbox_x",
         part="GreenhouseSideGlass0"),
    dict(name="eaves_height", mm=1900.0, tol=6.0, how="top_z",
         part="GreenhouseSideGlass0"),
    dict(name="ridge_height", mm=2886.0, tol=10.0, how="top_z",
         part="GreenhouseRoofGlass"),
    dict(name="frame_span", mm=2990.0, tol=8.0, how="bbox_y",
         part="GreenhouseFrame4"),
    dict(name="gable_width", mm=2800.0, tol=6.0, how="bbox_y",
         part="GreenhouseGable0"),
    dict(name="dwarf_wall_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="GreenhouseBrickWall0"),
]


def _arc(radius, z_centre, a0, a1, x, steps=28):
    """Points on the arch, in the YZ plane at `x` (mm)."""
    return [(x, radius * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             z_centre + radius * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


def build():
    alu = bkit.pbr("GHAlu", base=(0.72, 0.74, 0.76), metal=0.85, rough=0.30)
    glass = bkit.pbr("GHGlass", base=(0.86, 0.91, 0.90), rough=0.04,
                     transmission=0.92, ior=1.45)
    brick = bkit.pbr("GHBase", base=(0.42, 0.40, 0.37), rough=0.80)

    # ---- the dwarf wall the whole house stands on ------------------------
    for s in (1, -1):
        bkit.rounded_box("GreenhouseBrickWall%d" % (0 if s < 0 else 1),
                         L + 120.0, 220.0, DW, r=8.0, segments=2,
                         centre=(0.0, s * (HALF + 70.0), DW / 2.0), mat=brick)

    # ---- portal frames: one arch and two legs each, on the 700 mm pitch --
    for i, x in enumerate(BAY_X):
        bkit.arc_torus("GreenhouseFrame%d" % i, R, 15.0, 0.0, 180.0,
                       centre=(x, 0.0, ZC), plane="YZ", seg_minor=12,
                       mat=alu)
        for s in (1, -1):
            bkit.cylinder("GreenhousePost%d%s" % (i, "L" if s < 0 else "R"),
                          15.0, EAVE - DW - 20.0, segments=14,
                          centre=(x, s * (R - 15.0),
                                  DW + (EAVE - DW - 20.0) / 2.0), mat=alu)

    # ---- the ridge beam and the eave purlins run the full length ---------
    bkit.cylinder("GreenhouseRidge", 18.0, L, segments=16, axis="X",
                  centre=(0.0, 0.0, ZC + R - T - 8.0), mat=alu)
    for s in (1, -1):
        tag = 0 if s < 0 else 1
        bkit.cylinder("GreenhouseEaveRail%d" % tag, 14.0, L, segments=14,
                      axis="X", centre=(0.0, s * (R - 18.0), EAVE - 34.0),
                      mat=alu)
        # purlins up the arch: fixed arc angles, so they are real geometry and
        # not hand-placed offsets that drift off the curve
        for j, deg in enumerate((38.0, 71.0, 109.0, 142.0)):
            a = math.radians(deg)
            bkit.cylinder("GreenhousePurlin%d_%d" % (tag, j), 10.0, L,
                          segments=10, axis="X",
                          centre=(0.0, (R - T - 10.0) * math.cos(a),
                                  ZC + (R - T - 10.0) * math.sin(a)), mat=alu)

    # ---- side glass: one pane per side, standing on the dwarf wall -------
    gh = EAVE - DW
    for s in (1, -1):
        bkit.rounded_box("GreenhouseSideGlass%d" % (0 if s < 0 else 1),
                         L, T, gh, r=3.0, segments=1,
                         centre=(0.0, s * (HALF - T / 2.0), DW + gh / 2.0),
                         mat=glass)

    # ---- roof glass: a closed shell, outer arc then inner arc back -------
    ring = _arc(R - T, ZC, A_GLASS, 180.0 - A_GLASS, 0.0) + \
        _arc(R - 2.0 * T, ZC, 180.0 - A_GLASS, A_GLASS, 0.0)[::-1]
    roof = bkit.loft("GreenhouseRoofGlass",
                     [[(x, y, z) for (_x, y, z) in ring]
                      for x in (-L / 2.0, L / 2.0)], mat=glass)
    bkit.recalc(roof)

    # ---- gable ends: side wall, eave, arch head, one prism per end -------
    ge = (R - T) * math.cos(math.radians(A_GLASS))
    gable = [(-HALF, 0.0), (HALF, 0.0), (HALF, EAVE)] + \
        [(y, z) for (_x, y, z) in _arc(R - T, ZC, A_GLASS,
                                       180.0 - A_GLASS, 0.0)[1:-1]] + \
        [(-ge, EAVE)]
    for s in (1, -1):
        tag = 0 if s < 0 else 1
        x = s * (L / 2.0 + T / 2.0)
        g = bkit.loft("GreenhouseGable%d" % tag,
                      [[(x, y, z) for (y, z) in gable],
                       [(x + s * T, y, z) for (y, z) in gable]], mat=glass)
        bkit.recalc(g)

    # ---- the door: a frame and a leaf in one gable -----------------------
    bkit.rounded_box("GreenhouseDoorFrame", 70.0, 1000.0, 1980.0, r=10.0,
                     segments=2, centre=(L / 2.0 + 44.0, 0.0, DW + 990.0),
                     mat=alu)
    bkit.rounded_box("GreenhouseDoor", 24.0, 900.0, 1880.0, r=6.0,
                     segments=1, centre=(L / 2.0 + 20.0, -70.0, DW + 950.0),
                     mat=glass)
    bkit.cylinder("GreenhouseDoorHandle", 12.0, 260.0, segments=12,
                  centre=(L / 2.0 + 52.0, 330.0, DW + 1050.0), mat=alu)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 3 + 2 + 2 + BAYS * 3 + 1,
                note="The arch is a %.0f mm radius centred %.0f mm below the "
                     "eave line; the glazing is a closed shell with %.0f mm "
                     "thickness, not a sheet."
                     % (R, R - SPEC["arch_rise"], 2.0 * T))


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
