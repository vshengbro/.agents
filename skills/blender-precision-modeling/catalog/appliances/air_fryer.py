"""
air_fryer -- 300 x 300 x 330 mm countertop air fryer: a rounded-square body on
four feet, a drawer basket with a bar handle, a top control panel with a rotary
dial, a lit display and two keys, and a louvred exhaust on the back.

The rounded-square tub and the deep drawer are the two cues; a plain cylinder
reads as a bin.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=270.0,
    body_depth=260.0,
    body_height=250.0,
    overall_height=268.0,     # feet to the top of the body
    foot_height=18.0,
    corner_radius=38.0,       # generous: the tub is moulded, not folded
    dial_diameter=56.0,
    display_width=84.0,
    key_count=2,
    key_diameter=22.0,
    key_pitch=36.0,
    drawer_handle_width=140.0,
)

W = SPEC["body_width"]
D = SPEC["body_depth"]
H = SPEC["body_height"]
FOOT = SPEC["foot_height"]
TOP = FOOT + H                              # 330, top of the body
FRONT = -(D / 2.0)
DIAL_X = -76.0
KEY_X0 = -16.0


def _on_face(t, proud=4.0):
    """Centre y for a part of thickness t moulded onto the body front."""
    return FRONT - t / 2.0 + proud


# The panel stands 14 mm proud of the shell, so every control mounted on it
# has to clear PANEL_FACE, not the shell front -- otherwise it is buried inside
# the panel it is supposed to sit on.
PANEL_FACE = _on_face(22.0, 8.0) - 11.0
# The basket front sits 8 mm proud of the shell; the handle reaches further
# forward still and bites back into the basket by 8 mm.
HANDLE_Y = FRONT - 13.0


def build():
    shell = bkit.pbr("AirFryerShell", base=(0.16, 0.16, 0.18), metal=0.0,
                     rough=0.34, coat=0.2)
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("brushed_metal")
    lamp = bkit.pbr("AirFryerDisplay", base=(0.03, 0.04, 0.05), rough=0.12,
                    emission=(0.95, 0.72, 0.30), emission_strength=0.9)

    # ---- body -------------------------------------------------------------
    body = bkit.rounded_box("FryerBody", W, D, H, r=SPEC["corner_radius"],
                            segments=8, centre=(0.0, 0.0, FOOT + H / 2.0),
                            mat=shell)

    # ---- drawer: a real aperture with a basket standing inside it ----------
    cut = bkit.rounded_box("_drawer_cut", 200.0, 100.0, 180.0, r=16.0,
                           segments=4, centre=(0.0, FRONT + 40.0, 130.0))
    bkit.boolean(body, cut, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    bkit.rounded_box("DrawerBasket", 188.0, 108.0, 162.0, r=14.0, segments=4,
                     centre=(0.0, FRONT + 46.0, 136.0), mat=dark)
    bkit.rounded_box("DrawerHandle", SPEC["drawer_handle_width"], 26.0, 26.0,
                     r=12.0, segments=4,
                     centre=(0.0, HANDLE_Y, 214.0), mat=steel)
    for i, x in enumerate((-54.0, 54.0)):
        bkit.rounded_box("HandlePost%d" % i, 22.0, 22.0, 44.0, r=8.0,
                         segments=3, centre=(x, HANDLE_Y, 214.0), mat=steel)

    # ---- control panel ----------------------------------------------------
    # Everything on the panel is sized against PANEL_FACE, not the shell front:
    # the panel itself stands proud, and the dial then stands proud of IT.
    bkit.rounded_box("ControlPanel", 236.0, 22.0, 80.0, r=10.0, segments=4,
                     centre=(0.0, _on_face(22.0, 8.0), TOP - 44.0), mat=dark)
    bkit.cylinder("DialKnob", SPEC["dial_diameter"] / 2.0, 20.0, segments=48,
                  axis="Y", centre=(DIAL_X, PANEL_FACE - 4.0, TOP - 44.0),
                  mat=steel)
    bkit.rounded_box("DialPointer", 5.0, 8.0, 16.0, r=2.0, segments=2,
                     centre=(DIAL_X, PANEL_FACE - 16.0, TOP - 30.0),
                     mat=dark)
    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 8.0, 34.0, r=3.0,
                     segments=2, centre=(40.0, PANEL_FACE - 1.0,
                                        TOP - 44.0), mat=lamp)
    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["key_count"], gap=SPEC["key_pitch"] - kd,
                         centre=False)):
        bkit.cylinder("PanelKey%d" % i, kd / 2.0, 12.0, segments=32, axis="Y",
                      centre=(KEY_X0 + x, PANEL_FACE - 2.0, TOP - 44.0),
                      mat=steel)

    # ---- back exhaust louvres --------------------------------------------
    n = 9
    pitch = 22.0
    span = (n - 1) * pitch
    louvre = bkit.rounded_box("RearVent", 14.0, 10.0, 8.0, r=3.0, segments=2,
                              centre=(-span / 2.0, D / 2.0 - 2.0, TOP - 90.0),
                              mat=dark)
    bkit.array_linear(louvre, n, (pitch, 0.0, 0.0))

    # ---- feet -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 18.0, FOOT, segments=28,
                          centre=(sx * (W / 2.0 - 42.0), sy * (D / 2.0 - 42.0),
                                  FOOT / 2.0),
                          mat=dark)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="body_width", mm=270.0, tol=0.4, how="bbox_x", part="FryerBody"),
    dict(name="body_depth", mm=260.0, tol=0.4, how="bbox_y", part="FryerBody"),
    dict(name="overall_height", mm=268.0, tol=0.4, how="bbox_z"),
    dict(name="overall_width", mm=270.0, tol=0.4, how="bbox_x"),
    dict(name="dial_diameter", mm=56.0, tol=0.4, how="diameter", part="DialKnob"),
]