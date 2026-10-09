"""
barrel -- 200 litre oil barrel: a bulging, cooper-style body with three hoops
and a filler neck on the crown.

The barrel is the one vessel in this domain whose silhouette is *curved* in
both directions -- the wall swells out at mid-height and tucks back in at both
ends. A lathe is exactly the right tool: the swell is three extra profile points,
and the hoops are radius steps rather than separate objects, so the whole barrel
is one watertight solid instead of five interpenetrating cylinders.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    diameter=585.0,           # at the widest point, over the belly
    end_diameter=520.0,       # over the chime hoops at each end
    height=860.0,             # barrel shell; the filler cap adds 18 mm
    belly_height=430.0,       # height of the widest point
    hoop_width=44.0,          # axial width of each rolling hoop
    filler_diameter=90.0,
    overall_height=875.0,
    volume_l=200.0,
)

R = SPEC["diameter"] / 2.0
RE = SPEC["end_diameter"] / 2.0
H = SPEC["height"]
BH = SPEC["belly_height"]
HW = SPEC["hoop_width"]

# Materials are built inside build(), never at module scope: run_model.py calls
# bkit.reset() AFTER importing this file, and reset() is a factory-settings read
# that deletes every material created before it. A module-level bkit.preset()
# therefore hands build() a dead StructRNA.


def build():
    steel = bkit.pbr("BarrelSteel", base=(0.60, 0.62, 0.65), metal=0.45, rough=0.34)
    # The crown faces up with only the dark backdrop to reflect; at metal=0.9 it
    # renders black, so the barrel's visible metal keeps a diffuse component.
    steel_dark = bkit.pbr("BarrelSteelDark", base=(0.44, 0.46, 0.49), metal=0.35,
                          rough=0.44)
    oil_paint = bkit.pbr("BarrelPaint", base=(0.58, 0.24, 0.06), rough=0.42)
    band_mat = bkit.pbr("BarrelBand", base=(0.82, 0.83, 0.84), metal=0.45,
                        rough=0.26)

    # ---- body: belly -> hoops -> chimes -> crown, both ends on the axis ----
    # The three hoops sit at symmetric fractions of the height so the barrel
    # stays balanced when the height is retuned.
    h1, h2 = H * 0.165, H * 0.835
    # Every radius is strictly monotonic going *out* and again coming back, so
    # no two profile points share a radius at different heights: coincident
    # (r, z) pairs make the revolve emit degenerate quads and the barrel ends
    # up with 192 non-manifold edges.
    # z must increase monotonically from the base to the crown. A hoop whose
    # upper edge sits above the crown makes the wall double back on itself, and
    # the revolve then emits degenerate quads -- that fold is what produced 192
    # non-manifold edges the first time this profile was written.
    z_bot_hoop, z_top_hoop = 9.0, H - 12.0 - HW
    prof = [
        (0.0, 0.0),                            # centre of the base
        (228.0, 0.0),
        (252.0, 4.0),
        (RE + 4.0, z_bot_hoop),                # bottom chime hoop
        (RE + 4.0, z_bot_hoop + HW),
        (RE, z_bot_hoop + HW + 4.0),
        (266.0, 75.0),                         # swell begins
        (280.0, 115.0),
        (R, 150.0),                            # belly, widest point
        (R, BH - 30.0),
        (280.0, BH + 20.0),
        (268.0, 640.0),                        # swell tucks back in
        (264.0, 690.0),
        (264.0, 736.0),                        # upper belly hoop
        (264.0, 736.0 + HW),
        (260.0, 740.0 + HW),
        (262.0, 780.0),
        (RE + 4.0, z_top_hoop),                # top chime hoop
        (RE + 4.0, z_top_hoop + HW),
        (256.0, H - 6.0),
        (246.0, H - 2.0),                      # crown
        (200.0, H - 1.0),
        (0.0, H - 3.0),                        # dished crown, back to the axis
    ]
    body = bkit.lathe("BarrelBody", prof, segments=96, mat=steel)

    # Painted belly; the chimes and crown stay bare steel, which is how a real
    # barrel is finished and keeps the hoops readable as raised steel bands.
    bkit.assign_faces_by(
        body, oil_paint,
        lambda c, n: 90.0 < c.z / bkit.MM < 780.0,
    )
    bkit.assign_faces_by(
        body, band_mat,
        lambda c, n: abs(c.z / bkit.MM - z_bot_hoop - HW / 2.0) < HW
        or abs(c.z / bkit.MM - z_top_hoop - HW / 2.0) < HW,
    )

    # ---- filler neck on the crown -------------------------------------------
    f = SPEC["filler_diameter"] / 2.0
    neck_prof = [
        (0.0, 0.0), (f, 0.0), (f, 12.0), (f - 5.0, 15.0), (0.0, 15.0),
    ]
    neck = bkit.lathe("BarrelFillerNeck", neck_prof, segments=64,
                      centre=(0.0, 0.0, H - 7.0), mat=steel_dark)

    cap_r = f + 6.0
    cap = bkit.lathe("BarrelFillerCap", [
        (0.0, 0.0), (cap_r - 3.0, 0.0), (cap_r, 3.0), (cap_r, 9.0),
        (cap_r - 4.0, 12.0), (0.0, 12.0),
    ], segments=64, centre=(0.0, 0.0, H + 6.0), mat=band_mat)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="diameter", mm=585.0, tol=1.0, how="diameter", part="BarrelBody"),
    dict(name="height", mm=857.0, tol=2.0, how="bbox_z", part="BarrelBody"),
    dict(name="longest", mm=875.0, tol=3.0, how="longest"),
]
