"""
water_tap -- outdoor standpipe tap: a lathed body with a real threaded spout,
a cross handle on a bonnet, and a wall flange.

Small size class (30..150 mm) and 210 mm tall. This is the wall/standpipe tap
you find in a garden: a square backplate flange, a hex bonnet, a cross handle
(4 spokes, computed with array_radial), and a threaded spout with a real
1/2 inch thread cut into it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    # 92 mm backplate: the bolt circle is FLW/2 - 12 = 34, which has to clear
    # the 22 mm body radius by more than the 3.2 mm hole radius. At 64 mm the
    # circle fell INSIDE the body and the assertion fired.
    flange_width=92.0,
    flange_thickness=8.0,
    flange_holes=4,          # screw holes, computed
    body_diameter=44.0,
    body_height=118.0,
    bonnet_diameter=34.0,
    bonnet_height=18.0,
    cross_arms=4,
    cross_length=44.0,
    cross_tube=7.0,
    spout_diameter=26.0,
    spout_reach=76.0,
    spout_height=96.0,
    overall_height=145.0,
)

FLW = SPEC["flange_width"]
FLT = SPEC["flange_thickness"]
BR = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]


def build():
    brass = bkit.preset("polished_metal")
    dark = bkit.preset("dark_metal")

    # ---- backplate flange + body: one lathe --------------------------------
    body = bkit.lathe("TapFlange", [
        (0.0, 0.0),
        (FLW / 2.0, 0.0),                  # backplate face
        (FLW / 2.0, FLT),
        (BR + 4.0, FLT + 5.0),              # fillet into the body
        (BR, FLT + 14.0),
        (BR, BH - 26.0),                   # body barrel
        (BR - 3.0, BH - 16.0),
        (BR - 3.0, BH),                    # top face
        (0.0, BH),
    ], segments=72, mat=brass)

    # ---- four screw holes through the flange, on a computed circle --------
    # Laid out by lay_out-style arithmetic rather than hand-placed: the holes
    # sit on a bolt circle of FLW/2 - 12, so they cannot collide with the
    # body (radius BR) that they surround.
    bc = FLW / 2.0 - 12.0
    assert bc > BR + 6.0, "bolt circle must clear the body"
    for i in range(SPEC["flange_holes"]):
        a = 2.0 * math.pi * i / SPEC["flange_holes"] + math.radians(45.0)
        x, y = bc * math.cos(a), bc * math.sin(a)
        bkit.bore(body, 3.2, depth=FLT + 12.0, centre=(x, y, FLT / 2.0),
                  axis="Z", host_segments=72)

    # ---- hex bonnet: the packing gland the handle turns on ----------------
    bonnet = bkit.cylinder("TapBonnet", SPEC["bonnet_diameter"] / 2.0,
                           SPEC["bonnet_height"], segments=6,
                           centre=(0.0, 0.0, BH - 2.0), mat=dark)

    # ---- cross handle: 4 spokes, swept, not hand-placed -------------------
    # One spoke built on the X axis at z = 0, then array_radial. The sweep is
    # planar only when the object's location is on the Z axis with z = 0 --
    # building it at z = BH would orbit it into a rising helix.
    arm_l = SPEC["cross_length"] / 2.0
    arm = bkit.rounded_box("TapCross", arm_l, SPEC["cross_tube"],
                           SPEC["cross_tube"], r=3.0, segments=3,
                           centre=(arm_l / 2.0, 0.0, 0.0), mat=brass)
    bkit.array_radial(arm, SPEC["cross_arms"])
    bkit.move(arm, 0.0, 0.0, BH + SPEC["bonnet_height"] - 2.0 + 3.0)

    hub = bkit.cylinder("TapCrossHub", 11.0, 16.0, segments=24,
                        centre=(0.0, 0.0, BH + SPEC["bonnet_height"] + 1.0),
                        mat=brass)

    # ---- spout: out of the side of the body, with a real thread ----------
    sz = SPEC["spout_height"]
    spout = bkit.lathe("TapSpout", [
        (0.0, 0.0),
        (BR - 2.0, 0.0),                   # where it leaves the barrel
        (SPEC["spout_diameter"] / 2.0 + 1.0, 10.0),
        (SPEC["spout_diameter"] / 2.0, 16.0),
        (SPEC["spout_diameter"] / 2.0, SPEC["spout_reach"] - 30.0),
        (SPEC["spout_diameter"] / 2.0 + 2.5, SPEC["spout_reach"] - 24.0),
        (SPEC["spout_diameter"] / 2.0 + 2.5, SPEC["spout_reach"]),
        (0.0, SPEC["spout_reach"]),        # open outlet, capped flat
    ], segments=64, mat=brass)
    # Lay the spout along +Y at outlet height, sunk 10 mm into the barrel so
    # the two solids interlock instead of meeting on a tangent circle.
    spout.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bkit.move(spout, 0.0, -10.0, sz)

    # The thread: bkit.thread sweeps a real helix, so the spout is genuinely
    # screw-threaded rather than ringed.
    thr = bkit.thread("TapSpoutThread", SPEC["spout_diameter"] / 2.0 + 1.2,
                      pitch=2.8, length=26.0, thread_h=1.2, mat=brass)
    thr.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(thr, 0.0, SPEC["spout_reach"] - 38.0, sz)

    return dict(spec=SPEC, parts=6, cross_arms=SPEC["cross_arms"])


CHECKS = [
    dict(name="flange_width", mm=92.0, tol=0.5, how="diameter", part="TapFlange"),
    dict(name="body_height", mm=118.0, tol=0.4, how="bbox_z", part="TapFlange"),
    dict(name="spout_reach", mm=76.0, tol=0.6, how="bbox_y", part="TapSpout"),
    dict(name="cross_length", mm=44.0, tol=0.4, how="diameter", part="TapCross"),
    dict(name="overall_height", mm=145.0, tol=0.8, how="bbox_z"),
]
