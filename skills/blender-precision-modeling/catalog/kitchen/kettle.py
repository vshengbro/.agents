"""kettle -- gooseneck stove kettle: tapered body, angled spout, bail handle.

189 mm across and 214 mm to the top of the bail. The handle is a computed bail:
the two attachment points set a chord, the apex sits `rise` out along the
chord's outward normal, and the major radius of a circle through all three is
rmaj = (rise^2 + half_chord^2) / (2 * rise). The arc then runs from one tip's
polar angle to the other's, which is what makes it clear the lid instead of
sagging through it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    base_diameter=150.0,   # widest point of the belly
    body_height=170.0,     # rim above the table
    overall_height=214.0,  # top of the bail handle
    wall=2.5,
    spout_tip_diameter=28.0,
    handle_reach=44.0,     # apex out from the body wall
    handle_tube=8.0,
    volume_ml=1700.0,
)

R = SPEC["base_diameter"] / 2.0
H = SPEC["body_height"]

# bail: attachment half-span, rise above them, and the wire thickness
BAIL_HALF = 55.0
BAIL_Z = 166.0
BAIL_RISE = 44.0
BAIL_TUBE = SPEC["handle_tube"] / 2.0

# Spout: along +Y, because the `side` camera looks down -X and a spout on +X
# is a circle in every profile shot. The bail stays in the XZ plane, i.e.
# square to the spout, which is how a kettle is actually held.
SPOUT_TILT = 38.0
SPOUT_BASE = (0.0, 56.0, 80.0)
SPOUT_LEN = 90.0


def _bail():
    """(rmaj, centre, a0, a1) for a handle through two tips and an apex."""
    k = (BAIL_RISE ** 2 - BAIL_HALF ** 2) / (2.0 * BAIL_RISE)
    centre_z = BAIL_Z + k
    rmaj = BAIL_RISE - k
    alpha = math.degrees(math.atan2(-k, BAIL_HALF))
    return rmaj, (0.0, 0.0, centre_z), -alpha, 180.0 + alpha


def build():
    # A full metal reflects a dark studio and reads black; a brighter base and a
    # tighter roughness keep the specular highlights that make it read as steel.
    steel = bkit.pbr("KettleSteel", base=(0.86, 0.87, 0.89), metal=1.0,
                     rough=0.24)

    # ---- body --------------------------------------------------------------
    prof = [
        (0.0, 0.0),
        (52.0, 0.0),
        (64.0, 2.0),
        (71.0, 8.0),
        (74.0, 18.0),
        (R, 34.0),                    # belly
        (74.0, 70.0),
        (71.0, 110.0),
        (66.0, 140.0),
        (61.0, 160.0),
        (58.0, H),                     # rim, outside
        (58.0 - SPEC["wall"], H),      # across the rim
        (55.5, 162.0),
        (59.0, 152.0),                 # down the inside
        (64.0, 132.0),
        (68.0, 110.0),
        (71.0, 70.0),
        (71.5, 34.0),
        (68.0, 16.0),
        (58.0, 7.0),
        (0.0, 7.0),
    ]
    body = bkit.lathe("KettleBody", prof, segments=96, mat=steel)

    # ---- lid: shallow dome with a flange over the rim ---------------------
    lid = bkit.lathe("KettleLid", [
        (0.0, 186.0),
        (18.0, 184.5),
        (36.0, 180.0),
        (50.0, 173.5),
        (57.0, 169.0),
        (60.5, 166.5),
        (60.0, 164.5),
        (54.0, 168.5),
        (44.0, 174.5),
        (28.0, 179.0),
        (12.0, 181.5),
        (0.0, 182.5),
    ], segments=96, mat=steel)
    # The lid and knob profiles are written top-down (pole first), which winds
    # the revolve inward; recalc makes the signed volume positive.
    bkit.recalc(lid)

    knob = bkit.lathe("KettleKnob", [
        (0.0, 202.0),
        (4.0, 201.5),
        (8.0, 199.0),
        (10.5, 194.0),
        (10.0, 189.0),
        (7.0, 185.5),
        (3.0, 184.5),
        (0.0, 184.5),
    ], segments=64, mat=steel)
    bkit.recalc(knob)

    # ---- spout: one tapered cone, tipped up off the shoulder --------------
    spout = bkit.cylinder("KettleSpout", 17.0, SPOUT_LEN, segments=48,
                          centre=(0.0, 0.0, 0.0), axis="Z", r2=11.0,
                          mat=steel)
    spout.rotation_euler = (math.radians(-SPOUT_TILT), 0.0, 0.0)
    bpy.context.view_layer.update()
    half = SPOUT_LEN / 2.0
    bkit.move(spout,
              SPOUT_BASE[0],
              SPOUT_BASE[1] + math.sin(math.radians(SPOUT_TILT)) * half,
              SPOUT_BASE[2] + math.cos(math.radians(SPOUT_TILT)) * half)

    # flared lip at the spout tip, same axis so the joint reads as one part
    tip = (SPOUT_BASE[0],
           SPOUT_BASE[1] + math.sin(math.radians(SPOUT_TILT)) * SPOUT_LEN,
           SPOUT_BASE[2] + math.cos(math.radians(SPOUT_TILT)) * SPOUT_LEN)
    flare = bkit.cylinder("KettleSpoutTip", 11.5, 9.0, segments=48,
                          centre=(0.0, 0.0, 0.0), axis="Z", r2=13.5,
                          mat=steel)
    flare.rotation_euler = (math.radians(-SPOUT_TILT), 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.move(flare,
              tip[0],
              tip[1] + math.sin(math.radians(SPOUT_TILT)) * 1.0,
              tip[2] + math.cos(math.radians(SPOUT_TILT)) * 1.0)

    # ---- bail handle over the lid -----------------------------------------
    rmaj, centre, a0, a1 = _bail()
    handle = bkit.arc_torus("KettleHandle", rmaj, BAIL_TUBE, a0, a1,
                            centre=centre, plane="XZ", seg_major=44,
                            mat=steel, caps=True)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_diameter", mm=150.0, tol=0.3, how="diameter",
         part="KettleBody"),
    dict(name="body_height", mm=170.0, tol=0.3, how="bbox_z", part="KettleBody"),
    dict(name="overall_height", mm=214.0, tol=0.3, how="bbox_z"),
]
