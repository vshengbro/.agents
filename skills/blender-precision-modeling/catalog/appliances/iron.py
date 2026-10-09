"""
iron -- 250 x 124 mm soleplate, 155 mm tall steam iron: an extruded soleplate
outline with a real point, 21 steam holes cut through it on a computed grid, a
lofted body that narrows toward the nose, an arched handle, a temperature dial
and a steam button.

The soleplate outline is the identity. A rounded rectangle reads as a
wooden block; the asymmetric point is what makes it an iron.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    soleplate_length=250.0,
    soleplate_width=124.0,
    soleplate_thickness=8.0,
    overall_height=149.0,
    handle_tube=11.0,
    handle_reach=87.0,      # centreline radius + tube radius of the bail
    handle_centre_z=62.0,
    handle_centre_x=10.0,
    steam_hole_diameter=6.0,
    steam_hole_cols=7,
    steam_hole_rows=3,
    steam_hole_pitch_x=28.0,
    steam_hole_pitch_y=26.0,
    dial_diameter=34.0,
)

PL = SPEC["soleplate_length"]
PW = SPEC["soleplate_width"]
PT = SPEC["soleplate_thickness"]

# Counter-clockwise outline of a real iron soleplate: a point at +X, a full
# width at the heel. Walked nose -> top edge -> heel -> bottom edge -> nose.
OUTLINE = [
    (125.0, 0.0), (113.0, 22.0), (93.0, 40.0), (61.0, 54.0), (21.0, 62.0),
    (-30.0, 62.0), (-80.0, 60.0), (-112.0, 50.0), (-125.0, 26.0),
    (-125.0, -26.0), (-112.0, -50.0), (-80.0, -60.0), (-30.0, -62.0),
    (21.0, -62.0), (61.0, -54.0), (93.0, -40.0), (113.0, -22.0),
]

# The body loft: each section is (height, size_x, size_y, corner_r, x_shift).
# It narrows and drifts toward the nose, which is what a moulded iron shell
# does and what stops the upper body reading as a loaf.
SECTIONS = [
    (6.0, 236.0, 116.0, 28.0, 2.0),      # starts 2 mm inside the plate
    (44.0, 226.0, 112.0, 30.0, 6.0),
    (72.0, 192.0, 102.0, 34.0, 12.0),
    (94.0, 144.0, 90.0, 36.0, 18.0),
    (110.0, 106.0, 76.0, 32.0, 20.0),    # shell top, below the handle bail
]


def build():
    chrome = bkit.pbr("IronPlate", base=(0.84, 0.85, 0.87), metal=0.60,
                      rough=0.22)
    shell = bkit.pbr("IronShell", base=(0.86, 0.87, 0.88), metal=0.0, rough=0.24,
                     coat=0.35)
    dark = bkit.preset("black_plastic")

    # ---- soleplate ---------------------------------------------------------
    plate = bkit.extrude_profile("IronSoleplate", OUTLINE, PT,
                                 centre=(0.0, 0.0, PT / 2.0), mat=chrome)
    bkit.bevel(plate, 1.2, segments=2)

    # ---- steam holes -------------------------------------------------------
    # All 21 cutters are joined into ONE mesh and subtracted in a single
    # boolean. 21 separate booleans would be slow and each one a chance for
    # the solver to produce a non-manifold result.
    hr = SPEC["steam_hole_diameter"] / 2.0
    cols, rows = SPEC["steam_hole_cols"], SPEC["steam_hole_rows"]
    span_x = (cols - 1) * SPEC["steam_hole_pitch_x"] + 4 * hr
    span_y = (rows - 1) * SPEC["steam_hole_pitch_y"] + 4 * hr
    assert span_x < PL - 40.0, "steam hole row must fit inside the soleplate length"
    assert span_y < PW - 40.0, "steam hole row must fit inside the soleplate width"
    cutters = []
    for i, (x, y) in enumerate(bkit.grid_positions(
            cols=cols, rows=rows, pitch_x=SPEC["steam_hole_pitch_x"],
            pitch_y=SPEC["steam_hole_pitch_y"])):
        # The blade is 40 mm deep in a plate 8 mm thick: it exits both faces,
        # so the hole has real walls instead of ending tangent to a skin.
        cutters.append(bkit.cylinder("_steam_cut%d" % i, hr, 40.0,
                                     segments=24, centre=(x, y, PT / 2.0)))
    blade = bkit.join(cutters, name="_steam_blade")
    bkit.boolean(plate, blade, "DIFFERENCE")
    bkit.recalc(plate)
    bkit.health(plate)

    # ---- lofted body -------------------------------------------------------
    rings = []
    for (z, sx, sy, r, cx) in SECTIONS:
        ring = bkit.rounded_rect_section(sx, sy, r, per_corner=8,
                                         centre=(cx, 0.0))
        rings.append([(x, y, z) for (x, y) in ring])
    # Five lofted sections leave a visible facet band at every row boundary --
    # the render showed the shell as a faceted pebble rather than a moulded
    # one. The loft is resampled to 6x the stations with a smoothstep blend,
    # the same cure the snowboard and the climbing hold use.
    dense = []
    for i in range(len(rings) - 1):
        for k in range(6):
            t = k / 6.0
            ts = t * t * (3.0 - 2.0 * t)
            r0, r1 = rings[i], rings[i + 1]
            dense.append([(a[0] + (b[0] - a[0]) * ts,
                           a[1] + (b[1] - a[1]) * ts,
                           a[2] + (b[2] - a[2]) * ts)
                          for (a, b) in zip(r0, r1)])
    dense.append(rings[-1])
    body = bkit.loft("IronBody", dense, mat=shell, smooth=True)
    bkit.recalc(body)
    bkit.health(body)

    # ---- arched handle -----------------------------------------------------
    # The bail is a wide flat arch from 8 deg to 172 deg: a steep arch (say
    # 20..160) lands its rear tip outside the shell, because the loft narrows
    # fastest at the heel. Sweeping nearly to 180 deg drops BOTH tips down to
    # z = 73 where the shell is still 191 mm wide, and leaves a 118 x 39 mm
    # finger opening above the shell top at z = 110.
    hz = SPEC["handle_centre_z"]
    hx = SPEC["handle_centre_x"]
    r_major = SPEC["handle_reach"] - SPEC["handle_tube"]
    bkit.arc_torus("IronHandle", r_major, SPEC["handle_tube"], 8.0, 172.0,
                   centre=(hx, 0.0, hz), plane="XZ", seg_major=56,
                   mat=dark, caps=True)

    # ---- temperature dial and steam slider --------------------------------
    top_z = SECTIONS[-1][0]
    bkit.cylinder("TempDial", SPEC["dial_diameter"] / 2.0, 26.0,
                  segments=48, centre=(46.0, 0.0, top_z - 10.0), mat=dark)
    # A slider straddling the sloped nose reads as a switch; a cylinder parked
    # on the crown of a tapering shell just reads as a blob.
    bkit.rounded_box("SteamSlider", 30.0, 12.0, 9.0, r=3.0, segments=2,
                     centre=(72.0, 0.0, top_z - 14.0), mat=dark)

    # ---- cord exit at the HEEL ---------------------------------------------
    # The cord used to leave at x = -128, which is the heel end, but at
    # z = 28 -- mid-height on the side of the shell, where the loft's flank
    # has already narrowed to 226 x 112 mm, so the stub came out of the side
    # wall like a pipe. A steam iron's cord exits at the very back of the
    # heel, close to the sole, where the shell is full width.
    bkit.cylinder("CordStub", 9.0, 44.0, segments=24, axis="X",
                  centre=(-132.0, 0.0, 16.0), mat=dark)
    # the strain-relief boot it emerges through, so the exit is not a bare
    # cylinder intersecting the shell
    bkit.lathe("CordBoot",
               [(0.0, 0.0), (13.0, 0.0), (13.0, 16.0), (9.0, 22.0), (0.0, 22.0)],
               segments=32, centre=(-124.0, 0.0, 16.0), mat=dark)
    bkit.move(bpy.data.objects["CordBoot"], 0.0, 0.0, 0.0)
    boot = bpy.data.objects["CordBoot"]
    boot.rotation_euler = (0.0, math.radians(-90.0), 0.0)
    bkit.apply_mods(boot)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="soleplate_length", mm=250.0, tol=0.5, how="bbox_x",
         part="IronSoleplate"),
    dict(name="soleplate_width", mm=124.0, tol=0.5, how="bbox_y",
         part="IronSoleplate"),
    dict(name="soleplate_thickness", mm=8.0, tol=0.5, how="bbox_z",
         part="IronSoleplate"),
    dict(name="dial_diameter", mm=34.0, tol=0.4, how="diameter", part="TempDial"),
]