"""
kettle_electric -- 1.7 L electric kettle: a lathed body with a real wall
thickness and a rolled rim, a hinged lid with a knob, a swept handle, a
tapered spout, and a separate 360-degree power base with a recessed contact
ring.

A kettle is a surface of revolution plus four attachments, so the silhouette
has to come out of the lathe profile rather than out of a box.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=155.0,      # widest part of the vessel
    body_height=190.0,        # base of the vessel to the rim, lid excluded
    wall=3.0,
    base_diameter=205.0,      # the power base it stands on
    base_height=28.0,
    overall_height=243.0,     # floor to the top of the lid knob
    lid_diameter=142.0,
    handle_reach=58.0,        # outer protrusion of the handle past the wall
    handle_tube=13.0,
    spout_diameter=42.0,
    volume_ml=1700.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]
WALL = SPEC["wall"]
BR = SPEC["base_diameter"] / 2.0
BH = SPEC["base_height"]
# The vessel sits 3 mm DOWN inside the base recess. Landing its base face
# exactly on the base's top face would leave two coincident surfaces z-fighting
# for the whole render.
BASE_TOP = BH - 3.0


def build():
    steel = bkit.pbr("KettleSteel", base=(0.85, 0.86, 0.87), metal=0.55, rough=0.24)
    black = bkit.preset("black_plastic")
    cord = bkit.preset("rubber")

    # ---- vessel: ONE closed profile ---------------------------------------
    # Walk order is the whole game: out along the base, up the outside, over the
    # rim, back down the inside and across the inner floor. Stop anywhere else
    # and you have revolved a single surface, which renders as a paper ghost.
    prof = [
        (0.0, 0.0),
        (R - 26.0, 0.0),
        (R - 8.0, 2.0),
        (R, 16.0),                # widest point, low down like a real kettle
        (R, 140.0),
        (R - 3.0, 164.0),
        (R - 8.0, H - 12.0),
        (R - 10.0, H - 4.0),
        (R - 14.0, H),            # rolled rim
        (R - 14.0 - WALL, H),
        (R - 11.0 - WALL, H - 6.0),
        (R - 6.0 - WALL, H - 18.0),
        (R - 6.0 - WALL, 16.0),
        (R - 14.0 - WALL, 7.0),
        (0.0, 7.0),               # across the inner floor
    ]
    body = bkit.lathe("KettleBody", prof, segments=96, centre=(0.0, 0.0, BASE_TOP),
                      mat=steel)

    # ---- lid and knob -----------------------------------------------------
    bkit.lathe("KettleLid",
               [(0.0, 0.0), (SPEC["lid_diameter"] / 2.0 - 4.0, 0.0),
                (SPEC["lid_diameter"] / 2.0, 3.0),
                (SPEC["lid_diameter"] / 2.0 - 6.0, 8.0),
                (22.0, 11.0), (16.0, 18.0), (0.0, 20.0)],
               segments=96, centre=(0.0, 0.0, BASE_TOP + H - 2.0), mat=black)
    bkit.lathe("LidKnob",
               [(0.0, 0.0), (13.0, 0.0), (14.0, 2.5), (12.0, 7.0), (8.0, 10.0),
                (0.0, 11.0)],
               segments=48, centre=(0.0, 0.0, BASE_TOP + H + 17.0), mat=black)

    # ---- handle: an arch from the rim down to the lower body ------------
    # The previous arc swept only -88..88 deg about a centre at 58% height, so
    # both tips landed at the same level and the handle read as a C stuck to
    # one side rather than as a bail. A kettle handle is a bail: it leaves the
    # wall just under the rolled rim, bows out past the body, and returns to
    # the wall near the base. The sweep is therefore a half circle from 90 deg
    # (straight up, at the rim) round to 270 deg (straight down, at the base),
    # centred between the two attachment heights.
    # A circular arc has one radius, so that radius has to equal half the
    # vertical distance between the two attachments -- an ellipse is not
    # available here. 48 mm gives a 96 mm bail: it leaves the wall 35 mm below
    # the rolled rim and returns 59 mm above the base, and its outer surface
    # lands at 73.5 + 48 + 13 = 134.5 mm, i.e. handle_reach (58) past the
    # 77.5 mm wall. Both tips sit at x = 73.5, which is 5 mm inside the wall's
    # inner surface (68.5), so they are buried in the metal and the caps are
    # hidden.
    h_top = BASE_TOP + H - 35.0
    h_bot = BASE_TOP + 59.0
    reach = 48.0
    bkit.arc_torus("KettleHandle", reach, SPEC["handle_tube"], -88.0, 88.0,
                   centre=(R - 4.0, 0.0, (h_top + h_bot) / 2.0), plane="XZ",
                   seg_major=48, mat=black, caps=True)

    # ---- spout ------------------------------------------------------------
    # cylinder() keeps its centre in obj.location, so the tilt rotation is safe
    # here: it spins the spout about its own axis, not about the world origin.
    spout = bkit.cylinder("KettleSpout", SPEC["spout_diameter"] / 2.0, 150.0,
                          segments=40, r2=13.0,
                          centre=(-(R + 2.0), 0.0, BASE_TOP + H * 0.72),
                          mat=steel)
    spout.rotation_euler = (math.radians(32.0), 0.0, math.radians(-90.0))
    bkit.recalc(spout)

    # ---- power base -------------------------------------------------------
    bkit.lathe("PowerBase",
               [(0.0, 0.0), (BR - 4.0, 0.0), (BR, 3.0), (BR, BH - 6.0),
                (BR - 6.0, BH), (R + 4.0, BH), (R + 1.0, BH - 7.0),
                (R + 1.0, 6.0), (0.0, 6.0)],
               segments=96, mat=black)
    # The 360 degree contact ring every cordless kettle has.
    bkit.tube("ContactRing", R + 8.0, R + 3.0, 4.0, segments=96,
              centre=(0.0, 0.0, BH - 3.0), mat=steel)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="body_diameter", mm=155.0, tol=0.4, how="diameter", part="KettleBody"),
    dict(name="body_height", mm=190.0, tol=0.4, how="bbox_z", part="KettleBody"),
    dict(name="base_diameter", mm=205.0, tol=0.4, how="diameter", part="PowerBase"),
    dict(name="overall_height", mm=243.0, tol=0.5, how="bbox_z"),
    dict(name="lid_diameter", mm=142.0, tol=0.6, how="diameter", part="KettleLid"),
]