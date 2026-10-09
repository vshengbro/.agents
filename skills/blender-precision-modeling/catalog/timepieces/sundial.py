"""
sundial -- 180 mm cast sundial with a triangular gnomon and seven hour lines.

A sundial is a dial face, so it is held to the same standard as a clock dial:
the hour lines are placed at REAL hour angles, not spread evenly. The sun's
hour angle moves 15 degrees per hour, so the lines are at 8:00, 9:00 ... 16:00,
each a thin bar swept by array_radial about the dial's own centre. Even
spacing would be wrong and is the mistake that makes a sundial read as a
prop.

The gnomon is the classic triangular plate -- its hypotenuse is the polar
style, and it is a 3 mm plate set at the latitude angle, so it is an extruded
triangle rather than a wedge of blocks. The base is a turned stone disc with a
moulded rim.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BASE_R = 90.0
BASE_T = 18.0
RIM_H = 6.0
LATITUDE = 52.0            # degrees north, which sets the style's rake
STYLE_L = 78.0             # the polar style's length
STYLE_T = 3.0
PLATE_H = 46.0
HOUR_LINES = 7             # 8:00 through 16:00 in summer time
LINE_W = 1.6
LINE_T = 1.2
LINE_R0 = 26.0
LINE_R1 = 76.0

SPEC = dict(base_diameter=2.0 * BASE_R, base_thickness=BASE_T,
            latitude=LATITUDE, style_length=STYLE_L, style_thickness=STYLE_T,
            hour_line_count=HOUR_LINES, hour_line_pitch=15.0,
            hour_line_length=LINE_R1 - LINE_R0)


def build():
    stone = bkit.pbr("DialStone", base=(0.74, 0.72, 0.66), metal=0.0, rough=0.72)
    bronze = bkit.pbr("DialBronze", base=(0.62, 0.50, 0.28), metal=0.85, rough=0.38)

    # ---- the base: a turned disc with a moulded rim ------------------------
    base = bkit.lathe(
        "Base",
        [(0.0, 0.0), (BASE_R - 4.0, 0.0), (BASE_R, 4.0), (BASE_R, BASE_T - 4.0),
         (BASE_R - 4.0, BASE_T), (0.0, BASE_T)],
        segments=96, mat=stone)
    rim = bkit.lathe(
        "Rim",
        [(BASE_R - 12.0, BASE_T - 1.0), (BASE_R + 5.0, BASE_T - 1.0),
         (BASE_R + 5.0, BASE_T + RIM_H), (BASE_R - 12.0, BASE_T + RIM_H),
         (BASE_R - 12.0, BASE_T - 1.0)],
        segments=96, cap_ends=False, mat=stone)

    # ---- the gnomon: a triangular plate set at the latitude ---------------
    # Profile in (x = radius outward, z = height): a right triangle whose
    # hypotenuse is the polar style. Extruded across the dial by the thickness.
    gnomon = bkit.extrude_profile(
        "Gnomon",
        [(0.0, 0.0), (STYLE_L, 0.0), (0.0, STYLE_L * math.tan(math.radians(LATITUDE)))],
        STYLE_T, axis="Y", centre=(0.0, 0.0, BASE_T), mat=bronze)
    bkit.recalc(gnomon)
    bkit.move(gnomon, 0.0, -STYLE_T / 2.0, 0.0)
    # the style is the raised edge along the hypotenuse, so it catches the light
    bkit.extrude_profile(
        "_style",
        [(STYLE_L - 9.0, 0.0), (STYLE_L, 0.0),
         (STYLE_L, 9.0 * math.tan(math.radians(LATITUDE)))],
        STYLE_T + 1.2, axis="Y", centre=(0.0, 0.0, BASE_T), mat=bronze)

    # ---- seven hour lines on real 15 degree hour angles --------------------
    # One line, placed at the first hour, then swept by array_radial: the
    # pitch is the sun's 15 degrees per hour, so the array count IS the
    # geometry.
    line = bkit.rounded_box("HourLines", LINE_R1 - LINE_R0, LINE_W, LINE_T,
                            r=0.5, segments=2,
                            centre=((LINE_R0 + LINE_R1) / 2.0, 0.0,
                                    BASE_T + LINE_T / 2.0 - 0.4), mat=bronze)
    line.rotation_euler = (0.0, 0.0, math.radians(105.0))   # 7:00 position
    bkit.array_radial(line, HOUR_LINES, centre=(0.0, 0.0, 0.0))

    # ---- the compass rose points, 8 of them at 45 degrees -------------------
    rose = bkit.rounded_box("CompassPoints", 12.0, 2.4, 1.0, r=0.4, segments=2,
                            centre=(BASE_R - 14.0, 0.0, BASE_T + RIM_H - 0.4),
                            mat=bronze)
    bkit.array_radial(rose, 8, centre=(0.0, 0.0, 0.0))

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_diameter", mm=180.0, tol=0.3, how="diameter", part="Base"),
    dict(name="base_thickness", mm=18.0, tol=0.2, how="bbox_z", part="Base"),
    dict(name="rim_height", mm=7, tol=0.1, how="bbox_z",
         part="Rim"),
    dict(name="style_length", mm=78.0, tol=0.2, how="bbox_x", part="Gnomon"),
    dict(name="style_thickness", mm=3.0, tol=0.1, how="bbox_y", part="Gnomon"),
    # 6 x 15 deg across the swept set = 90 degrees of arc
    dict(name="hour_line_run", mm=145.7, tol=0.4, how="bbox_x",
         part="HourLines"),
    dict(name="overall_height", mm=117.8, tol=0.3, how="bbox_z",
         part=None)
]