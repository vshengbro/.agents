"""
coffee_machine -- 300 x 400 x 360 mm espresso machine: a rounded stainless body,
a group head with a portafilter whose handle points forward, a drip tray, a
steam wand, a pressure gauge, three keys and a lit brew button, plus a demitasse
standing under the spouts.

The group head plus portafilter plus cup is the silhouette; without the cup the
box on its own reads as a toaster with a spout.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=300.0,
    body_depth=380.0,
    overall_height=360.0,
    corner_radius=22.0,
    group_head_diameter=86.0,
    group_head_height=64.0,
    portafilter_handle_length=90.0,
    gauge_diameter=52.0,
    key_count=3,
    key_diameter=20.0,
    key_pitch=40.0,
    cup_diameter=68.0,
    cup_height=62.0,
    wand_diameter=9.0,
)

W = SPEC["body_width"]
D = SPEC["body_depth"]
H = SPEC["overall_height"]
FRONT = -(D / 2.0)
GH = SPEC["group_head_diameter"] / 2.0
GHZ = 168.0                        # group head centre height
TRAY_Z = 26.0


def _on_face(t, proud=4.0):
    """Centre y for a part of thickness t moulded onto the body front."""
    return FRONT - t / 2.0 + proud


def build():
    steel = bkit.pbr("EspressoSteel", base=(0.84, 0.85, 0.86), metal=0.55,
                     rough=0.24)
    dark = bkit.preset("black_plastic")
    chrome = bkit.preset("polished_metal")
    ceramic = bkit.preset("ceramic")
    lamp = bkit.pbr("BrewButton", base=(0.10, 0.04, 0.03), rough=0.2,
                    emission=(1.0, 0.45, 0.20), emission_strength=1.4)

    # ---- body -------------------------------------------------------------
    body = bkit.rounded_box("EspressoBody", W, D, H, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, H / 2.0), mat=steel)

    # Warm the machine: the cup recess is a real cut, not a painted rectangle.
    cut = bkit.rounded_box("_cup_cut", 150.0, 130.0, 118.0, r=10.0, segments=3,
                           centre=(0.0, FRONT + 52.0, 92.0))
    bkit.boolean(body, cut, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    # ---- group head and portafilter ---------------------------------------
    bkit.cylinder("GroupHead", GH, SPEC["group_head_height"], segments=64,
                  centre=(0.0, FRONT + 6.0, GHZ), mat=chrome)
    bkit.cylinder("Portafilter", GH - 4.0, 26.0, segments=64,
                  centre=(0.0, FRONT - 2.0, GHZ - 34.0), mat=chrome)
    # The handle is horizontal and points at the viewer, like a real one. Its
    # back end is placed 6 mm INSIDE the portafilter, never flush with it.
    bkit.cylinder("PortafilterHandle", 15.0,
                  SPEC["portafilter_handle_length"], segments=32, axis="Y",
                  centre=(0.0, FRONT - 9.0
                          - SPEC["portafilter_handle_length"] / 2.0,
                          GHZ - 40.0), mat=dark)

    # ---- steam wand -------------------------------------------------------
    # A short cylinder is vertical, which would read as a peg; the composite
    # rotation swings it down and out to the right of the group head.
    wand = bkit.cylinder("SteamWand", SPEC["wand_diameter"] / 2.0, 130.0,
                         segments=24, centre=(112.0, FRONT + 4.0, GHZ - 60.0),
                         mat=chrome)
    wand.rotation_euler = (math.radians(-24.0), 0.0, math.radians(18.0))
    bkit.move(wand, 0.0, 0.0, 0.0)
    bkit.cylinder("WandKnob", 15.0, 22.0, segments=28,
                  centre=(128.0, FRONT + 4.0, GHZ + 6.0), mat=dark)

    # ---- drip tray --------------------------------------------------------
    bkit.rounded_box("DripTray", 190.0, 150.0, 24.0, r=6.0, segments=4,
                     centre=(0.0, FRONT + 62.0, TRAY_Z), mat=chrome)
    for i in range(7):                       # grate slots, one computed pitch
        bkit.rounded_box("TraySlot%d" % i, 9.0, 110.0, 8.0, r=3.0, segments=2,
                         centre=(-54.0 + i * 18.0, FRONT + 62.0, TRAY_Z + 12.0),
                         mat=dark)

    # ---- pressure gauge and keys ------------------------------------------
    bkit.cylinder("PressureGauge", SPEC["gauge_diameter"] / 2.0, 22.0,
                  segments=48, axis="Y",
                  centre=(-76.0, _on_face(22.0, 10.0), H - 66.0), mat=chrome)
    bkit.cylinder("GaugeFace", SPEC["gauge_diameter"] / 2.0 - 6.0, 4.0,
                  segments=48, axis="Y",
                  centre=(-76.0, _on_face(22.0, 20.0), H - 66.0),
                  mat=bkit.pbr("GaugeDial", base=(0.92, 0.91, 0.86), rough=0.3))
    bkit.cylinder("BrewButton", 22.0, 16.0, segments=40, axis="Y",
                  centre=(58.0, _on_face(22.0, 14.0), H - 66.0), mat=lamp)
    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["key_count"], gap=SPEC["key_pitch"] - kd)):
        bkit.cylinder("ControlKey%d" % i, kd / 2.0, 14.0, segments=32, axis="Y",
                      centre=(x, _on_face(14.0, 8.0), H - 132.0), mat=dark)

    # ---- demitasse --------------------------------------------------------
    r = SPEC["cup_diameter"] / 2.0
    h = SPEC["cup_height"]
    bkit.lathe("Demitasse",
               [(0.0, 0.0), (r - 8.0, 0.0), (r - 2.0, 3.0), (r, h - 4.0),
                (r - 1.0, h), (r - 5.0, h), (r - 5.0, 5.0), (0.0, 5.0)],
               segments=64, centre=(0.0, FRONT + 62.0, TRAY_Z + 12.0),
               mat=ceramic)

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="body_width", mm=300.0, tol=0.4, how="bbox_x", part="EspressoBody"),
    dict(name="body_depth", mm=380.0, tol=0.4, how="bbox_y", part="EspressoBody"),
    dict(name="overall_height", mm=360.0, tol=0.5, how="bbox_z"),
    dict(name="group_head_diameter", mm=86.0, tol=0.4, how="diameter",
         part="GroupHead"),
    dict(name="cup_diameter", mm=68.0, tol=0.4, how="diameter", part="Demitasse"),
]