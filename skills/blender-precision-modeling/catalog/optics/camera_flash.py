"""
camera_flash -- 276 x 80 mm hot-shoe speedlight: battery body, tilt joint,
80 x 60 x 80 mm flash head, bounce card, LCD, hot-shoe foot and a four-key pad.

Small size class, so the whole assembly has to stay under the 300 mm ceiling
that `size_class` allows -- the head is deliberately 80 mm rather than the
larger it could be, which is also what keeps the flash reading as a flash and
not as a studio strobe.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=74.0,
    body_depth=46.0,
    overall_height=276.0,
    head_width=80.0,
    head_depth=60.0,
    head_height=80.0,
    screen_size=44.0,
    keypad_buttons=4,
)

BODY_H = 170.0
BODY_Z = 20.0 + BODY_H / 2.0          # body sits 20 mm up, on the shoe foot


def build():
    shell = bkit.pbr("FlashShell", base=(0.075, 0.076, 0.080), rough=0.40)
    trim = bkit.pbr("FlashTrim", base=(0.58, 0.59, 0.60), metal=0.85,
                    rough=0.30)
    bounce = bkit.pbr("FlashBounce", base=(0.86, 0.86, 0.84), rough=0.30)
    fresnel = bkit.pbr("FlashFresnel", base=(0.78, 0.80, 0.82), rough=0.14,
                       transmission=0.35, ior=1.48)
    lcd = bkit.pbr("FlashLcd", base=(0.10, 0.12, 0.10), rough=0.09,
                   emission=(0.40, 0.58, 0.36), emission_strength=1.1)

    # ---- body and hot-shoe foot. The foot overlaps the body by 4 mm. -----
    bkit.rounded_box("FlashBody", SPEC["body_width"], SPEC["body_depth"],
                     BODY_H, r=8.0, segments=3, centre=(0.0, 0.0, BODY_Z),
                     mat=shell)
    bkit.rounded_box("ShoeFoot", 30.0, 34.0, 12.0, r=2.0, segments=2,
                     centre=(0.0, 0.0, 18.0), mat=trim)
    bkit.rounded_box("BatteryDoor", 58.0, 3.0, 80.0, r=3.0, segments=2,
                     centre=(0.0, 23.5, 90.0), mat=trim)

    # ---- tilt joint, then the head. Each overlaps the next by >= 5 mm. ---
    bkit.cylinder("TiltJoint", 10.0, 58.0, segments=36, axis="Y",
                  centre=(0.0, 0.0, 188.0), mat=trim)
    bkit.rounded_box("FlashHead", SPEC["head_width"], SPEC["head_depth"],
                     SPEC["head_height"], r=6.0, segments=3,
                     centre=(0.0, 0.0, 248.0), mat=shell)

    # ---- bounce card and the fresnel lens behind it ----------------------
    bkit.rounded_box("BouncePanel", 78.0, 4.0, 78.0, r=3.0, segments=2,
                     centre=(0.0, -31.0, 248.0), mat=bounce)
    bkit.rounded_box("FresnelLens", 66.0, 4.0, 68.0, r=2.0, segments=2,
                     centre=(0.0, -33.0, 248.0), mat=fresnel)
    bkit.tube("HeadBezel", 38.0, 33.0, 6.0, segments=40, axis="Y",
              centre=(0.0, -29.0, 248.0), mat=trim)

    # ---- LCD: bezel proud of the body, glass 1 mm behind the bezel -------
    bkit.rounded_box("ScreenBezel", 52.0, 6.0, 36.0, r=3.0, segments=2,
                     centre=(0.0, -22.0, 120.0), mat=trim)
    bkit.rounded_box("FlashScreen", SPEC["screen_size"], 4.0, 28.0, r=2.0,
                     segments=2, centre=(0.0, -22.0, 120.0), mat=lcd)

    # ---- four keys on the back, from one grid ---------------------------
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(2, 2, 24.0, 22.0)):
        keys.append(bkit.rounded_box(
            "FlashKey%d" % i, 18.0, 5.0, 15.0, r=2.5, segments=2,
            centre=(kx, 23.0, 64.0 + kz), mat=trim))
    bkit.join(keys, name="FlashKeypad")

    # ---- PC sync socket and the tilt lock lever --------------------------
    bkit.rounded_box("SyncPort", 14.0, 6.0, 10.0, r=2.0, segments=2,
                     centre=(26.0, -22.0, 172.0), mat=trim)
    bkit.rounded_box("TiltLock", 16.0, 12.0, 8.0, r=3.0, segments=2,
                     centre=(34.0, 0.0, 208.0), mat=trim)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="body_width", mm=74.0, tol=0.5, how="bbox_x", part="FlashBody"),
    dict(name="body_depth", mm=46.0, tol=0.5, how="bbox_y", part="FlashBody"),
    dict(name="overall_height", mm=276.0, tol=0.8, how="bbox_z"),
    dict(name="head_width", mm=80.0, tol=0.5, how="bbox_x", part="FlashHead"),
    dict(name="head_height", mm=80.0, tol=0.5, how="bbox_z", part="FlashHead"),
]