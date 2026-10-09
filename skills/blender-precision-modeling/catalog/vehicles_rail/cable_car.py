"""
cable_car -- 8-seat aerial gondola cabin with hanger arm and cable grip.

An aerial tramway car is UPSIDE DOWN relative to every other vehicle here:
the CABIN is the lowest thing and the running gear is 3.5 m above it. So the
model is built with the cabin sole on z=0 and the hanger rising to a grip
head at 5,900 -- which also makes `sit_on_floor()` a no-op without any
fiction.

The hanger is a real inverted-Y: two legs from the cabin roof corners to a
knee at 5,000, then a single arm to the grip. The grip itself is the part
that says 'cable car' -- a crosshead, two clamp jaws either side of the rope,
and a sheave on a horizontal axis.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    cabin_length=2400.0,
    cabin_width=2200.0,
    cabin_height=2400.0,
    hanger_knee_z=5000.0,
    grip_head_z=5900.0,
    overall_height=5900.0,
    rope_height_above_cabin=5900.0,
    capacity=8,
    gauge=1435.0,
)

CHECKS = [
    dict(name="cabin_length", mm=2400.0, tol=4.0, how="bbox_x",
         part="CableCabin"),
    dict(name="cabin_width", mm=2200.0, tol=4.0, how="bbox_y",
         part="CableCabin"),
    dict(name="cabin_height", mm=2400.0, tol=4.0, how="bbox_z",
         part="CableCabin"),
    dict(name="cabin_bottom_z", mm=0.0, tol=0.6, how="z_min",
         part="CableCabin"),
    dict(name="grip_head_z", mm=5900.0, tol=5.0, how="top_z",
         part="CableGripHead"),
    dict(name="sheave_diameter", mm=560.0, tol=4.0, how="bbox_z",
         part="CableSheave"),
]

CAB_L = 2400.0
CAB_HW = 1100.0
CAB_Z = 2400.0
KNEE_Z = 5000.0
GRIP_Z = 5900.0
SHEAVE_R = 210.0


def build():
    shell_m = bkit.pbr("CableShell", base=(0.72, 0.16, 0.13), rough=0.26)
    trim_m = bkit.pbr("CableTrim", base=(0.10, 0.11, 0.14), rough=0.44)
    glass = bkit.pbr("CableGlass", base=(0.11, 0.16, 0.20), rough=0.05,
                     transmission=0.72)
    steel = bkit.preset("brushed_metal")
    frame_m = bkit.preset("dark_metal")

    # --- cabin: rounded box with a domed roof, sole on z=0 -----------------
    body = R.body("CableCabin", [
        (-CAB_L / 2.0, CAB_HW - 70.0, 0.0, 2000.0, 1760.0),
        (-CAB_L / 2.0 + 300.0, CAB_HW, 0.0, CAB_Z, 2060.0),
        (0.0, CAB_HW, 0.0, CAB_Z, 2100.0),
        (CAB_L / 2.0 - 300.0, CAB_HW, 0.0, CAB_Z, 2060.0),
        (CAB_L / 2.0, CAB_HW - 70.0, 0.0, 2000.0, 1760.0),
    ], mat=shell_m, smooth=44.0)
    R.window_band(body, 780.0, 1980.0, glass, max_nz=0.70)
    R.window_band(body, 0.0, 620.0, trim_m, max_nz=0.80)
    bkit.rounded_box("CableRoof", 1500.0, 1500.0, 240.0, r=220.0, segments=4,
                     centre=(0.0, 0.0, CAB_Z - 30.0), mat=trim_m)
    bkit.rounded_box("CableBumper", 2600.0, 2400.0, 260.0, r=110.0, segments=3,
                     centre=(0.0, 0.0, 130.0), mat=frame_m)

    # --- hanger: inverted Y from the roof corners to the grip --------------
    hanger = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        hanger.append(R.strut("CableLeg" + tag,
                              (s * 700.0, s * 700.0, CAB_Z - 60.0),
                              (0.0, 0.0, KNEE_Z), 95.0, steel, seg=16))
        hanger.append(R.strut("CableStay" + tag,
                              (s * 950.0, s * 950.0, CAB_Z - 60.0),
                              (0.0, 0.0, KNEE_Z - 700.0), 45.0, steel,
                              seg=10))
    hanger.append(R.strut("CableArm", (0.0, 0.0, KNEE_Z), (0.0, 0.0, 5420.0),
                          85.0, steel, seg=16))
    hanger.append(bkit.rounded_box("CableCrosshead", 520.0, 900.0, 220.0,
                                   r=60.0, segments=3,
                                   centre=(0.0, 0.0, 5420.0), mat=frame_m))
    h_ob = bkit.join(hanger, "CableHanger")
    bkit.recalc(h_ob)

    # --- grip head: jaws either side of the rope, plus the sheave ----------
    grip = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        grip.append(bkit.rounded_box("CableGripJaw" + tag, 620.0, 110.0,
                                     480.0, r=50.0, segments=3,
                                     centre=(0.0, s * 130.0, 5650.0),
                                     mat=frame_m))
        grip.append(bkit.rounded_box("CableGripPad" + tag, 520.0, 40.0,
                                     120.0, r=20.0, segments=2,
                                     centre=(0.0, s * 65.0, 5650.0),
                                     mat=frame_m))
    grip.append(bkit.rounded_box("CableGripYoke", 520.0, 420.0, 260.0, r=60.0,
                                 segments=3, centre=(0.0, 0.0, GRIP_Z - 130.0),
                                 mat=steel))
    grip.append(bkit.cylinder("CableRope", 55.0, 1400.0, segments=20, axis="Y",
                              centre=(0.0, 0.0, 5650.0), mat=frame_m))
    g_ob = bkit.join(grip, "CableGripHead")
    bkit.recalc(g_ob)

    sheave = bkit.torus("CableSheave", SHEAVE_R, 70.0, seg_major=36,
                        seg_minor=14, centre=(0.0, 0.0, 0.0), axis="Y",
                        mat=steel)
    bkit.place(sheave, (0.0, 0.0, 5420.0), "Y")
    bkit.cylinder("CableSheavePin", 60.0, 560.0, segments=16, axis="Y",
                  centre=(0.0, 0.0, 5420.0), mat=frame_m)

    return dict(spec=SPEC, parts=8)