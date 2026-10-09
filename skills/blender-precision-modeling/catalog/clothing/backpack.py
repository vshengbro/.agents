"""
backpack -- a 480 x 330 x 190 mm rucksack.

A pack is a soft bag with a frame, so the body is a hollow shell rather than a
solid: the cavity is a slightly smaller rounded box that runs out through the
top, which gives the roll-top a real wall thickness. The cavity box is inset by
4 mm on three sides but offset upward so it exits -- inset it symmetrically and
the result is a sealed brick.

Everything that makes it read as a backpack is a separate named part: the front
pocket, the lid, two shoulder straps, a grab handle and the zip with its slider.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    height=470.0,
    width=330.0,
    depth=190.0,
    pocket_width=260.0,
    pocket_height=220.0,
    strap_reach=60.0,
    handle_rise=70.0,
    zip_length=250.0,
)

STEPS = 48


def shell(outer, cavity):
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


def _mm(v):
    return v / bkit.MM


def build():
    shell_fabric = bkit.pbr("PackShell", base=(0.215, 0.290, 0.360), rough=0.88)
    pocket_fabric = bkit.pbr("PackPocket", base=(0.175, 0.240, 0.310), rough=0.90)
    webbing = bkit.pbr("PackWebbing", base=(0.120, 0.140, 0.165), rough=0.90)
    zip_metal = bkit.preset("brushed_metal")

    H, W, D = SPEC["height"], SPEC["width"], SPEC["depth"]

    # ---- body: a real shell, open at the top -----------------------------
    # The cavity has to break out through the top, and because it is wider
    # than the body everywhere in the fillet the difference eats CROWN mm of
    # the outer form before the opening is reached (23.9 mm at r=46). The blank
    # is therefore built CROWN taller, so the FINISHED pack measures its
    # declared height rather than the blank's.
    CROWN = 24.0
    BH = H + CROWN
    body = shell(
        bkit.rounded_box("PackBody", W, D, BH, r=46.0, segments=5,
                         centre=(0.0, 0.0, BH / 2.0), mat=shell_fabric),
        # 4 mm inset on the walls, but pushed up so it breaks out of the top:
        # an inset box of the same height would leave a sealed shell.
        # Same fillet radius as the body: shrinking a filleted box by a uniform
        # 4 mm offset keeps the radius, and a cavity with a SMALLER radius is
        # wider than the body everywhere in the fillet, so the difference eats
        # the top of the pack instead of leaving a rim.
        bkit.rounded_box("_PackBody_cavity", W - 8.0, D - 8.0, BH - 4.0,
                         r=46.0, segments=5,
                         centre=(0.0, 0.0, BH / 2.0 + 90.0)),
    )
    bkit.assign_faces_by(
        body, pocket_fabric,
        lambda c, n: _mm(n.z) < -0.5,      # the underside is a darker panel
    )

    # ---- lid flap over the top ------------------------------------------
    bkit.rounded_box("PackLid", W - 20.0, D - 8.0, 46.0, r=22.0, segments=4,
                     centre=(0.0, -4.0, H - 14.0), mat=shell_fabric)

    # ---- front pocket ----------------------------------------------------
    bkit.rounded_box("PackFrontPocket", SPEC["pocket_width"], 62.0,
                     SPEC["pocket_height"], r=24.0, segments=4,
                     centre=(0.0, -D / 2.0 - 14.0, 168.0), mat=pocket_fabric)

    # ---- two shoulder straps, one arc each, anchored top AND bottom -------
    # A shoulder strap is a loop with BOTH ends on the back panel -- one at the
    # top roll, one down at the base -- bulging outward by its own `strap_reach`.
    # Deriving the radius from the chord (panel between the anchors) and the
    # sagitta (bulge) puts both ends on the pack by construction. The old form
    # derived them from a free horizontal span, so both ends came out at the
    # SAME height and one of them landed 233 mm behind the pack: two lengths of
    # rope floating in mid-air instead of a pair of straps. `arc_torus` sweeps
    # (y, z) = centre + r*(cos a, sin a), so the bulge is at a = 0 and the
    # anchors are at -/+ half.
    reach = SPEC["strap_reach"]
    z_hi, z_lo = 440.0, 90.0            # the two anchors, down the back panel
    y_anchor = D / 2.0 - 7.0            # 7 mm buried inside the 95 mm back face
    chord = z_hi - z_lo
    sagitta = (D / 2.0 + reach) - y_anchor
    rmaj = (chord * chord / 4.0 + sagitta * sagitta) / (2.0 * sagitta)
    half = math.degrees(math.asin((chord / 2.0) / rmaj))
    for i, sx in enumerate((1.0, -1.0)):
        bkit.arc_torus("PackStrap%d" % (i + 1), rmaj, 13.0, -half, half,
                       centre=(sx * 150.0,
                               y_anchor + sagitta - rmaj,
                               (z_hi + z_lo) / 2.0),
                       plane="YZ", seg_major=36, mat=webbing, caps=True)

    # ---- grab handle on the lid -----------------------------------------
    hr, ha = SPEC["handle_rise"], 58.0
    hk = (ha * ha - hr * hr) / (2.0 * hr)
    bkit.arc_torus("PackHandle", hr + hk, 9.0,
                   math.degrees(math.atan2(hk, ha)),
                   180.0 - math.degrees(math.atan2(hk, ha)),
                   centre=(0.0, -4.0, H - 14.0 - hk), plane="XZ",
                   seg_major=32, mat=webbing, caps=True)

    # ---- zip: a real tape line with a slider, plus two pull tabs ----------
    bkit.rounded_box("PackZipTape", SPEC["zip_length"], 16.0, 10.0, r=4.0,
                     segments=3, centre=(0.0, -D / 2.0 - 34.0, 300.0),
                     mat=webbing)
    bkit.rounded_box("PackZipSlider", 30.0, 20.0, 16.0, r=5.0, segments=3,
                     centre=(60.0, -D / 2.0 - 36.0, 300.0), mat=zip_metal)
    for i, sx in enumerate((1.0, -1.0)):
        bkit.rounded_box("PackZipPull%d" % (i + 1), 10.0, 4.0, 46.0, r=2.0,
                         segments=3,
                         centre=(60.0 + sx * 4.0, -D / 2.0 - 44.0, 278.0),
                         mat=zip_metal)

    # ---- compression straps, evenly spaced by lay_out() -----------------
    for i, (x, w) in enumerate(bkit.lay_out([26.0, 26.0], gap=210.0)):
        bkit.rounded_box("PackCompStrap%d" % (i + 1), w, D + 30.0, 20.0,
                         r=5.0, segments=3, centre=(x, 0.0, 96.0),
                         mat=webbing)

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="height", mm=470.0, tol=2.0, how="bbox_z", part="PackBody"),
    dict(name="width", mm=330.0, tol=2.0, how="bbox_x", part="PackBody"),
    dict(name="depth", mm=190.0, tol=2.0, how="bbox_y", part="PackBody"),
    dict(name="pocket_width", mm=260.0, tol=1.0, how="bbox_x",
         part="PackFrontPocket"),
    dict(name="pocket_height", mm=220.0, tol=1.0, how="bbox_z",
         part="PackFrontPocket"),
    dict(name="zip_length", mm=250.0, tol=1.0, how="bbox_x", part="PackZipTape"),
]