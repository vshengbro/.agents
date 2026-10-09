"""
rice_cooker -- 280 mm diameter, 250 mm tall countertop rice cooker: a lathed
vessel with a real wall, a domed lid with a skirt and a bail handle, a flat
control boss on the front with a lit display and four keys on one pitch, a
steam valve, and three feet.

The bowl-shape is the whole identity here, so it comes out of one lathe profile
and flat-panel tricks would actively hurt.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=280.0,     # widest point of the vessel
    body_height=205.0,       # vessel floor to the lid seat
    foot_height=8.0,
    wall=3.5,
    panel_width=120.0,
    panel_height=96.0,
    key_diameter=17.0,
    key_pitch=28.0,
    key_count=4,
    display_width=78.0,
    handle_tube=9.0,
    overall_height=250.0,    # floor to the top of the bail handle
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]
FOOT = SPEC["foot_height"]
WALL = SPEC["wall"]
TOP = FOOT + H                             # 213, lid seat
PANEL_Z = 126.0


def build():
    steel = bkit.pbr("RiceCookerShell", base=(0.86, 0.87, 0.88), metal=0.45,
                     rough=0.26)
    black = bkit.preset("black_plastic")
    lamp = bkit.pbr("RiceCookerDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.95, 0.60, 0.28), emission_strength=1.5)

    # ---- vessel: one closed profile, base -> outside -> rim -> inside ------
    prof = [
        (0.0, 0.0),
        (R - 18.0, 0.0),
        (R - 4.0, 3.0),
        (R, 16.0),                 # widest, low
        (R, H - 44.0),
        (R - 6.0, H - 16.0),       # shoulder in toward the lid seat
        (R - 16.0, H - 6.0),
        (R - 22.0, H),             # lid seat rim
        (R - 22.0 - WALL, H),
        (R - 24.0 - WALL, H - 8.0),
        (R - 10.0 - WALL, H - 20.0),
        (R - 5.0 - WALL, 18.0),
        (0.0, 12.0),               # across the inner floor
    ]
    bkit.lathe("RiceCookerBody", prof, segments=96, centre=(0.0, 0.0, FOOT),
               mat=steel)

    # ---- lid: dished pan with a domed crown --------------------------------
    LR = SPEC["body_diameter"] / 2.0 - 4.0
    bkit.lathe("RiceCookerLid",
               [(0.0, 0.0), (LR - 26.0, 0.0), (LR - 2.0, 3.0),
                (LR, 9.0), (LR, 15.0),
                (LR - 8.0, 24.0), (90.0, 30.0), (48.0, 34.0), (0.0, 38.0)],
               segments=96, centre=(0.0, 0.0, TOP - 8.0), mat=black)
    # The skirt drops OVER the body rim, so the two parts cross each other
    # instead of meeting on one circle.
    bkit.tube("LidSkirt", LR + 1.0, LR - 12.0, 16.0, segments=96,
              centre=(0.0, 0.0, TOP - 6.0), mat=steel)

    # ---- steam valve ------------------------------------------------------
    bkit.lathe("SteamValve",
               [(0.0, 0.0), (14.0, 0.0), (15.0, 2.0), (13.0, 7.0), (9.0, 9.0),
                (0.0, 10.0)],
               segments=40, centre=(0.0, 0.0, TOP + 24.0), mat=steel)

    # ---- bail handle ------------------------------------------------------
    # An arc in the YZ plane rising over the lid, with both tips buried inside
    # the lid dome. reach + tube is the arc's own height, so centring it at
    # overall_height - reach - tube puts the crown exactly on the datum.
    reach = 37.0
    bkit.arc_torus("BailHandle", reach, SPEC["handle_tube"], 18.0, 162.0,
                   centre=(0.0, 0.0, SPEC["overall_height"] - reach
                           - SPEC["handle_tube"]),
                   plane="YZ", seg_major=48, mat=black, caps=True)

    # ---- control boss -----------------------------------------------------
    # Kept narrow (120 mm) on purpose: a wide flat plate on a 280 mm cylinder
    # leaves its corners floating off the curve, while 120 mm sinks cleanly.
    panel = bkit.rounded_box("ControlPanel", SPEC["panel_width"], 34.0,
                             SPEC["panel_height"], r=10.0, segments=4,
                             centre=(0.0, -(R - 6.0), PANEL_Z), mat=black)
    bkit.recalc(panel)
    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 8.0, 34.0, r=3.0,
                     segments=2,
                     centre=(0.0, -(R + 11.0), PANEL_Z + 24.0), mat=lamp)
    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["key_count"], gap=SPEC["key_pitch"] - kd)):
        bkit.cylinder("PanelKey%d" % i, kd / 2.0, 10.0, segments=28, axis="Y",
                      centre=(x, -(R + 11.0), PANEL_Z - 24.0), mat=steel)

    # ---- feet -------------------------------------------------------------
    for i, a in enumerate((30.0, 150.0, 270.0)):
        ar = math.radians(a)
        bkit.cylinder("Foot%d" % i, 13.0, FOOT, segments=28,
                      centre=(math.cos(ar) * (R - 34.0),
                              math.sin(ar) * (R - 34.0), FOOT / 2.0), mat=black)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="body_diameter", mm=280.0, tol=0.4, how="diameter",
         part="RiceCookerBody"),
    dict(name="body_height", mm=205.0, tol=0.4, how="bbox_z", part="RiceCookerBody"),
    dict(name="overall_height", mm=250.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=280.0, tol=0.5, how="bbox_x"),
]