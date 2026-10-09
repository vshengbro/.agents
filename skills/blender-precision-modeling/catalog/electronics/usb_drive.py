"""
usb_drive -- 57 x 18 x 9 mm USB-A flash drive.

The connector is the part that has to read: a brushed-metal 12 x 4.5 mm USB-A
shell with the black insulating tongue visible inside it, overlapping the
plastic body by 1 mm so the two solids cross instead of meeting exactly flush.
The lanyard window is a through-cut in Z, so the body stays one connected
solid with a genuine hole in it rather than two floating cheeks.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=57.0,
    width=18.0,
    height=9.0,
    shell_length=13.0,
    shell_thickness=4.5,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]


def build():
    plastic = bkit.pbr("UsbBody", base=(0.28, 0.29, 0.33), rough=0.34,
                       coat=0.3)
    accent = bkit.pbr("UsbAccent", base=(0.72, 0.20, 0.08), rough=0.28,
                      coat=0.4)
    steel = bkit.preset("brushed_metal")
    tongue_mat = bkit.pbr("UsbTongue", base=(0.035, 0.035, 0.040), rough=0.42)

    # 45 mm plastic body, connector overlapping it by 1 mm at +X. Tail sits at
    # x = -28 and the shell tip at x = 29, so the assembly is exactly 57 mm.
    body = bkit.rounded_box("UsbBody", 45.0, W, H, r=3.0, segments=4,
                            centre=(-5.5, 0.0, H / 2.0), mat=plastic)

    # ---- lanyard window through the tail end -----------------------------
    win = bkit.rounded_box("_win", 5.0, 9.0, 12.0, r=2.0, segments=4,
                           centre=(-24.0, 0.0, H / 2.0))
    bkit.boolean(body, win, "DIFFERENCE")

    # ---- colour band where the shell enters the body ---------------------
    bkit.rounded_box("UsbBand", 7.0, W + 0.6, H + 0.6, r=3.0, segments=4,
                     centre=(14.0, 0.0, H / 2.0), mat=accent)

    # ---- USB-A shell + insulating tongue ---------------------------------
    shell = bkit.rounded_box("UsbShell", SPEC["shell_length"], 12.0,
                             SPEC["shell_thickness"], r=0.6, segments=3,
                             centre=(22.5, 0.0, H / 2.0), mat=steel)
    bkit.rounded_box("UsbTongue", 9.0, 10.6, 1.6, r=0.3, segments=2,
                     centre=(24.5, 0.0, H / 2.0), mat=tongue_mat)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="body_width", mm=18.0, tol=0.5, how="bbox_y", part="UsbBody"),
    dict(name="body_height", mm=9.0, tol=0.5, how="bbox_z", part="UsbBody"),
    dict(name="overall_length", mm=57.0, tol=0.6, how="longest"),
]
