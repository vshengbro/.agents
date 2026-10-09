"""
monitor -- 27" 16:9 display, 615 x 361 mm panel on a stand, 465 mm overall.

The panel is a thin slab, so like the laptop and the phone it is an
`extrude_profile` of a `rounded_rect_section` rather than a `rounded_box`: the
bezel's 6 mm corner radius is a 2D property and a uniform bevel would clamp
it to half the 20 mm depth. The display sits in a 4 mm recess cut into the
front bezel, and the OSD control row is a `lay_out` of six keys.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=615.0,
    panel_height=361.0,
    panel_depth=20.0,
    overall_height=465.0,
    active_width=597.0,
    active_height=336.0,
    osd_keys=6,
)

W, PH = SPEC["width"], SPEC["panel_height"]
PD = SPEC["panel_depth"]
H = SPEC["overall_height"]
BASE_Z = 18.0                       # top of the stand foot
PANEL_Z0 = H - PH                  # 104 mm


def build():
    bezel = bkit.pbr("MonitorBezel", base=(0.13, 0.13, 0.15), rough=0.36)
    screen = bkit.pbr("MonitorScreen", base=(0.030, 0.033, 0.042), rough=0.05,
                      coat=0.85)
    stand = bkit.pbr("MonitorStand", base=(0.34, 0.35, 0.38), metal=0.85,
                     rough=0.30)
    key_mat = bkit.pbr("MonitorKeys", base=(0.30, 0.30, 0.33), rough=0.40)
    led = bkit.pbr("MonitorLed", base=(0.12, 0.60, 0.32), rough=0.20,
                   emission=(0.10, 0.80, 0.40), emission_strength=1.2)

    # axis="Y" stands the panel up: extrude_profile builds the section in XY
    # and extrudes along +Z, so left alone a 615 x 361 panel comes out lying
    # flat on the bench with its 20 mm thickness vertical -- a slab, not a
    # display. With axis="Y" the section's Y becomes world Z (361 mm tall) and
    # the extrusion axis points at -Y, which is the front of the screen.
    panel = bkit.extrude_profile(
        "MonitorPanel", bkit.rounded_rect_section(W, PH, 6.0), PD,
        centre=(0, 0, PANEL_Z0 + PH / 2.0), axis="Y", mat=bezel)
    bkit.bevel(panel, 0.8, segments=2)

    # ---- active display in a 6 mm recess in the front bezel --------------
    FRONT = -PD / 2.0
    ZC = PANEL_Z0 + PH / 2.0
    bkit.boolean(panel, bkit.rounded_box(
        "_rec", SPEC["active_width"], 8.0, SPEC["active_height"], r=2.0,
        segments=3, centre=(0, FRONT + 2.0, ZC)), "DIFFERENCE")
    bkit.rounded_box("MonitorScreen", SPEC["active_width"] - 1.0, 1.4,
                     SPEC["active_height"] - 1.0, r=1.5, segments=2,
                     centre=(0, FRONT + 1.6, ZC), mat=screen)

    # ---- stand: neck off the panel back, foot on the bench --------------
    bkit.rounded_box("MonitorNeck", 62.0, 46.0, PANEL_Z0 + 40.0, r=6.0,
                     segments=4,
                     centre=(0, PD / 2.0 + 16.0,
                             (BASE_Z + PANEL_Z0 + 40.0) / 2.0), mat=stand)
    foot = bkit.rounded_box("MonitorFoot", 260.0, 210.0, BASE_Z, r=10.0,
                            segments=5, centre=(0, 20.0, BASE_Z / 2.0),
                            mat=stand)
    bkit.bevel(foot, 1.2, segments=3)

    # ---- six OSD keys and a power LED on the lower bezel ----------------
    keys = []
    for i, (x, w) in enumerate(bkit.lay_out([9.0] * SPEC["osd_keys"], gap=7.0)):
        keys.append(bkit.rounded_box(
            "_k%d" % i, w, 3.0, 2.4, r=0.8, segments=2,
            centre=(x + 20.0, FRONT + 0.6, PANEL_Z0 + 6.0), mat=key_mat))
    bkit.join(keys, name="MonitorOsdKeys")
    bkit.cylinder("MonitorPowerLed", 2.0, 2.0, segments=20, axis="Y",
                  centre=(-W / 2.0 + 26.0, FRONT + 0.4, PANEL_Z0 + 6.0),
                  mat=led)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="width", mm=615.0, tol=0.8, how="bbox_x", part="MonitorPanel"),
    dict(name="panel_height", mm=361.0, tol=0.8, how="bbox_z",
         part="MonitorPanel"),
    dict(name="overall_height", mm=465.0, tol=0.8, how="bbox_z"),
]
