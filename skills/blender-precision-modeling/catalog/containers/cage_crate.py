"""
cage_crate -- a hard pet carrier: a moulded base tray, an upper shell, a roof
cap, corner posts, barred windows and a barred end door with a latch.

Every bar is laid out with `grid_positions()` / `lay_out()` from a real bar
width and one explicit gap, as hard rule 4 requires. Hand-placing six bars per
face puts two of them on the same coordinate, and the panel then reads as a
cage with missing bars from every angle except one.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=450.0,             # along X
    width=300.0,              # along Y
    tray_height=40.0,         # the moulded base
    cage_height=320.0,        # tray top to the rim frame
    overall_height=360.0,      # tray + cage: no handle, the top is open
    bar=9.0,                  # bar section
    bar_gap=48.0,             # clear opening between bars
    post=24.0,
    corner_radius=16.0,
)

L = SPEC["length"]
W = SPEC["width"]
TH = SPEC["tray_height"]
CH = SPEC["cage_height"]
# SH is the top of the shell, which is also the top of everything: the carry
# handle was deleted (a crate does not have one) and the roof is an open rim
# frame, so overall_height and tray+cage are now the same number.
SH = SPEC["tray_height"] + SPEC["cage_height"]
H = SPEC["overall_height"]
assert abs(H - SH) < 1e-6, "no handle: overall height must equal tray + cage"
BAR = SPEC["bar"]
GAP = SPEC["bar_gap"]
P = SPEC["post"]


def build():
    shell = bkit.pbr("CarrierShell", base=(0.30, 0.34, 0.38), rough=0.38)
    shell_light = bkit.pbr("CarrierShellLight", base=(0.44, 0.48, 0.52),
                           rough=0.36)
    trim = bkit.preset("dark_metal")
    pad = bkit.pbr("CarrierPad", base=(0.20, 0.22, 0.26), rough=0.88)

    # ---- moulded base tray --------------------------------------------------
    tray = bkit.rounded_box("CarrierTray", L, W, TH, r=SPEC["corner_radius"],
                            segments=5, centre=(0.0, 0.0, TH / 2.0), mat=shell)
    # the tray lip, slightly proud, so the shell does not sit flush on the floor
    lip = bkit.rounded_box("CarrierTrayLip", L - 10.0, W - 10.0, 10.0,
                           r=10.0, segments=4,
                           centre=(0.0, 0.0, TH - 5.0), mat=pad)

    # ---- roof: an open rim frame, not a lid ------------------------------
    # A solid roof panel made this read as a lidded basket. A pet carrier is
    # open at the top -- what closes it visually is a rim frame around the
    # aperture, so the roof is now four bars and the middle is air. The bars
    # are the tray's own footprint plus the 6 mm overhang the roof used to
    # have, so every dimension below is unchanged.
    roof_bars = []
    rim_h = TH + 12.0
    rim_z = SH - rim_h / 2.0
    ow, oh = L + 6.0, W + 6.0
    rim_w = 26.0                      # width of the rim frame itself
    for nm, sx, sy, cx, cy in (
            ("CarrierRimFront", ow, rim_w, 0.0, (oh - rim_w) / 2.0),
            ("CarrierRimBack", ow, rim_w, 0.0, -(oh - rim_w) / 2.0),
            ("CarrierRimLeft", rim_w, oh - 2 * rim_w, (ow - rim_w) / 2.0, 0.0),
            ("CarrierRimRight", rim_w, oh - 2 * rim_w, -(ow - rim_w) / 2.0, 0.0),
    ):
        roof_bars.append(bkit.rounded_box(nm, sx, sy, rim_h,
                                          r=SPEC["corner_radius"] + 3.0,
                                          segments=5,
                                          centre=(cx, cy, rim_z),
                                          mat=shell_light))
    roof = bkit.join(roof_bars, name="CarrierRoof")

    # ---- four corner posts --------------------------------------------------
    # The posts now run all the way up to the underside of the rim frame
    # (post_z1 = SH - rim_h) instead of stopping 10 mm short of the old solid
    # roof, so the cage is visibly carried by the rim.
    post_z0, post_z1 = TH - 6.0, SH - (TH + 12.0)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bkit.rounded_box("CarrierPost%d" % (i + 1), P, P, post_z1 - post_z0,
                         r=4.0, segments=3,
                         centre=(sx * (L / 2.0 - P / 2.0),
                                 sy * (W / 2.0 - P / 2.0),
                                 (post_z0 + post_z1) / 2.0), mat=trim)

    # ---- barred side windows: bars laid out from real widths and one gap ----
    inner_x = L - P * 2
    inner_y = W - P * 2
    n_side = max(2, int((inner_y + GAP) / (BAR + GAP)))
    for i, (cy, _w) in enumerate(
            bkit.lay_out([BAR] * n_side, gap=(inner_y - BAR * n_side)
                         / max(1, n_side - 1) if n_side > 1 else 0.0)):
        for j, sx in enumerate((-1.0, 1.0)):
            bkit.rounded_box(
                "CarrierSideBar%d%d" % (j + 1, i + 1), BAR, BAR,
                post_z1 - post_z0 - 6.0, r=3.0, segments=2,
                centre=(sx * (L / 2.0 - P / 2.0), cy,
                        (post_z0 + post_z1) / 2.0), mat=trim)

    n_end = max(2, int((inner_x + GAP) / (BAR + GAP)))
    for i, (cx, _w) in enumerate(
            bkit.lay_out([BAR] * n_end, gap=(inner_x - BAR * n_end)
                         / max(1, n_end - 1) if n_end > 1 else 0.0)):
        for j, sy in enumerate((-1.0, 1.0)):
            bkit.rounded_box(
                "CarrierEndBar%d%d" % (j + 1, i + 1), BAR, BAR,
                post_z1 - post_z0 - 6.0, r=3.0, segments=2,
                centre=(cx, sy * (W / 2.0 - P / 2.0),
                        (post_z0 + post_z1) / 2.0), mat=trim)

    # ---- the door frame on the -X end, plus its latch ----------------------
    door_x = -L / 2.0 + P / 2.0
    for j, (sy, _w) in enumerate(
            bkit.lay_out([P, P], gap=(inner_y - 2 * P))):
        bkit.rounded_box("CarrierDoorStile%d" % (j + 1), P * 1.3, P,
                         post_z1 - post_z0, r=4.0, segments=3,
                         centre=(door_x, sy, (post_z0 + post_z1) / 2.0),
                         mat=shell_light)
    for k, z in enumerate((post_z0 + 4.0, post_z1 - 4.0)):
        bkit.rounded_box("CarrierDoorRail%d" % (k + 1), P * 1.3, inner_y,
                         P, r=4.0, segments=3,
                         centre=(door_x, 0.0, z), mat=shell_light)

    latch = bkit.rounded_box("CarrierLatch", 12.0, 44.0, 30.0, r=4.0,
                             segments=3,
                             centre=(door_x - P, 0.0,
                                     (post_z0 + post_z1) / 2.0),
                             mat=bkit.pbr("CarrierLatchMat",
                                          base=(0.80, 0.22, 0.10), rough=0.42))

    return dict(spec=SPEC, parts=26)


CHECKS = [
    dict(name="length", mm=456.0, tol=1.0, how="bbox_x", part="CarrierRoof"),
    dict(name="width", mm=306.0, tol=1.0, how="bbox_y", part="CarrierRoof"),
    # overall_height moved 402 -> 360 mm: the carry handle was deleted, so the
    # carrier is now exactly tray_height + cage_height.
    dict(name="overall_height", mm=360.0, tol=2.0, how="bbox_z"),
]
