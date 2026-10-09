"""
fan -- 400 mm cage, 1050 mm tall pedestal fan: a weighted base, a column, a
motor housing, three swept blades on a radial array, a rear motor grille, a
front wire guard built from rings and evenly spaced spokes, and a tilt knob.

The guard is the identity: concentric rings plus a spoke ring at a computed
pitch, never a hand-counted fan of lines.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=1050.0,  # floor to the crown of the guard bead
    guard_diameter=400.0,  # cage centreline; the bead adds 2 x bead_tube on top
    bead_tube=4.5,
    base_width=320.0,
    base_depth=320.0,
    base_height=42.0,
    column_diameter=44.0,
    motor_diameter=150.0,
    blade_count=3,
    blade_length=170.0,
    guard_rings=5,
    spoke_count=28,
)

GR = SPEC["guard_diameter"] / 2.0
BW = SPEC["base_width"]
BD = SPEC["base_depth"]
BH = SPEC["base_height"]
OH = SPEC["overall_height"]
MD = SPEC["motor_diameter"] / 2.0
BEAD = SPEC["bead_tube"]
COL_BOT = BH - 4.0
# The hub height is derived, not chosen: the OUTERMOST thing in the model is
# the guard bead, not the cage centreline, so the bead's own tube has to come
# out of the budget. Centre the cage at overall - GR - bead_tube and the crown
# lands exactly on the datum.
HUB_Z = OH - GR - BEAD
COL_TOP = HUB_Z - MD + 15.0
GUARD_FRONT = -(MD + 26.0) - 26.0


def build():
    shell = bkit.pbr("FanShell", base=(0.88, 0.89, 0.90), metal=0.0, rough=0.26,
                     coat=0.3)
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("brushed_metal")
    blade_mat = bkit.pbr("FanBlade", base=(0.86, 0.87, 0.88), metal=0.0,
                         rough=0.18, coat=0.4)

    # ---- base and column --------------------------------------------------
    bkit.rounded_box("FanBase", BW, BD, BH, r=18.0, segments=5,
                     centre=(0.0, 0.0, BH / 2.0), mat=shell)
    bkit.lathe("BaseDome",
               [(0.0, 0.0), (70.0, 0.0), (76.0, 6.0), (66.0, 26.0),
                (40.0, 36.0), (0.0, 38.0)],
               segments=64, centre=(0.0, 0.0, BH - 2.0), mat=shell)
    bkit.cylinder("FanColumn", SPEC["column_diameter"] / 2.0,
                  COL_TOP - COL_BOT, segments=48,
                  centre=(0.0, 0.0, (COL_BOT + COL_TOP) / 2.0), mat=steel)

    # ---- motor housing ----------------------------------------------------
    bkit.cylinder("MotorHousing", MD, 130.0, segments=64, axis="Y",
                  centre=(0.0, 0.0, HUB_Z), mat=shell)
    bkit.cylinder("HubCap", 46.0, 40.0, segments=48, axis="Y",
                  centre=(0.0, GUARD_FRONT + 14.0, HUB_Z), mat=dark)

    # ---- three blades on a radial array ------------------------------------
    # array_radial applies the pivot empty's INVERSE rotation to the object, so
    # the source MUST sit on the array axis (location 0) or every copy spirals
    # outward instead of orbiting. The radial offset is therefore baked into the
    # VERTICES by rounded_box, the pitch comes from rotation_euler, and the
    # whole swept assembly is moved into place afterwards.
    blade = bkit.rounded_box("FanBlade_0", SPEC["blade_length"], 74.0, 9.0,
                             r=8.0, segments=3,
                             centre=(SPEC["blade_length"] / 2.0 - 12.0, 0.0, 0.0),
                             mat=blade_mat)
    blade.rotation_euler = (math.radians(22.0), 0.0, 0.0)
    bkit.array_radial(blade, SPEC["blade_count"], axis="Y")
    bkit.move(blade, 0.0, GUARD_FRONT + 14.0, HUB_Z)

    # ---- rear motor grille -------------------------------------------------
    # Both the span AND the bar length stay inside the 150 mm housing: ribs
    # that overhang the housing silhouette read as a comb stuck on the side.
    n = 7
    pitch = 20.0
    span = (n - 1) * pitch
    assert span / 2.0 + 6.0 < MD, "grille ribs must stay inside the housing"
    rib = bkit.rounded_box("MotorGrilleRib", 8.0, 8.0, MD * 1.7, r=3.0,
                           segments=2, centre=(-span / 2.0, 68.0, HUB_Z),
                           mat=steel)
    bkit.array_linear(rib, n, (pitch, 0.0, 0.0))

    # ---- front wire guard: concentric rings plus a spoke ring --------------
    for i in range(SPEC["guard_rings"]):
        f = (i + 1) / float(SPEC["guard_rings"])
        bkit.torus("GuardRing%d" % i, GR * f, 3.2, seg_major=80, seg_minor=10,
                   axis="Y", centre=(0.0, GUARD_FRONT, HUB_Z), mat=steel)
    bkit.torus("GuardBead", GR, BEAD, seg_major=96, seg_minor=12, axis="Y",
               centre=(0.0, GUARD_FRONT, HUB_Z), mat=steel)
    # Each spoke is a full DIAMETER bar centred on the hub, so the source sits on
    # the array axis and there is no radial offset for array_radial to distort:
    # half the copies' ends give the 28 spokes. The bar reaches 3 mm past the
    # bead at both ends.
    spoke = bkit.rounded_box("GuardSpoke_0", 5.2, 5.2, 2.0 * (GR + 3.0),
                             r=2.0, segments=2, centre=(0.0, 0.0, 0.0),
                             mat=steel)
    bkit.array_radial(spoke, SPEC["spoke_count"] // 2, axis="Y")
    bkit.move(spoke, 0.0, GUARD_FRONT, HUB_Z)

    # ---- tilt knob --------------------------------------------------------
    bkit.cylinder("TiltKnob", 30.0, 46.0, segments=40,
                  centre=(0.0, 90.0, HUB_Z - MD - 14.0), mat=dark)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="base_width", mm=320.0, tol=0.4, how="bbox_x", part="FanBase"),
    dict(name="base_depth", mm=320.0, tol=0.4, how="bbox_y", part="FanBase"),
    dict(name="overall_height", mm=1050.0, tol=0.8, how="bbox_z"),
    dict(name="overall_width", mm=409.0, tol=0.8, how="bbox_x"),
    dict(name="guard_diameter", mm=409.0, tol=0.8, how="bbox_x", part="GuardBead"),
    dict(name="motor_diameter", mm=150.0, tol=0.4, how="diameter",
         part="MotorHousing"),
]