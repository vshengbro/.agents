"""
moai -- Rapa Nui moai, 4000 mm tall on a 1400 mm ahu platform.

The proportions are the model.  A moai is a COLUMNAR body with the mass pushed
up into an oversized head: the head is 43 per cent of the total height, the
shoulders are narrow, and the nose runs down past the mouth.  The statue is
therefore lofted from superellipse stations (n = 2.6 at the body, n = 3.2 at the
blocky head) with a separate extruded brow, nose and lip, because those three
features are what make a moai a moai rather than a cylinder.

The platform's top face is z = 0 for the statue, so the statue stands on the
ahu and the ahu's own thickness is below it.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _ritual as R

SPEC = dict(
    height=4000.0,
    head_height=1720.0,
    head_width=1100.0,
    shoulder_width=940.0,
    base_width=1360.0,
    nose_length=420.0,
    nose_width=210.0,
    ahu_height=700.0,
    ahu_width=2600.0,
)

CHECKS = [
    dict(name="height", mm=4000.0, tol=8.0, how="top_z", part="MoaiHead"),
    dict(name="head_height", mm=1720.0, tol=4.0, how="bbox_z",
         part="MoaiHead"),
    dict(name="head_width", mm=1100.0, tol=4.0, how="bbox_x", part="MoaiHead"),
    dict(name="base_width", mm=1360.0, tol=4.0, how="bbox_x",
         part="MoaiBody"),
    dict(name="nose_length", mm=420.0, tol=3.0, how="bbox_z",
         part="MoaiNose"),
    dict(name="brow_width", mm=980.0, tol=4.0, how="bbox_x",
         part="MoaiBrow"),
    dict(name="ahu_height", mm=700.0, tol=3.0, how="bbox_z", part="MoaiAhu"),
    dict(name="ahu_width", mm=2600.0, tol=5.0, how="bbox_x", part="MoaiAhu"),
]

H = SPEC["height"]
HH = SPEC["head_height"]
BZL = H - HH              # where the head starts

# (z, half width, half depth, n) -- the statue faces +y
STATIONS = [
    (0.0, 680.0, 520.0, 3.0),
    (BZL * 0.16, 620.0, 470.0, 2.8),
    (BZL * 0.55, 520.0, 400.0, 2.6),
    (BZL * 0.88, 470.0, 370.0, 2.6),
    (BZL, 490.0, 390.0, 2.8),
    (BZL + HH * 0.28, 550.0, 420.0, 3.0),
    (BZL + HH * 0.62, 550.0, 430.0, 3.2),
    (BZL + HH * 0.88, 500.0, 420.0, 3.4),
    (H - 140.0, 420.0, 370.0, 3.6),
    (H, 300.0, 260.0, 3.6),
]


def build():
    stone = R.basalt("MoaiStone", base=(0.36, 0.35, 0.33))
    dark = R.basalt("MoaiAhuStone", base=(0.22, 0.22, 0.21))
    shade = bkit.pbr("MoaiShade", base=(0.10, 0.09, 0.08), rough=0.70)

    # ---- ahu: the platform the statue stands on ---------------------------
    bkit.rounded_box("MoaiAhu", SPEC["ahu_width"], 1800.0,
                     SPEC["ahu_height"], r=30.0, segments=2,
                     centre=(0.0, 0.0, -SPEC["ahu_height"] / 2.0), mat=dark)

    # ---- the statue: one loft, head included -----------------------------
    secs = []
    for (z, hw, hd, n) in STATIONS:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hd, n=n, steps=48)
        secs.append([(x, y, z) for (x, y) in ring])
    body = bkit.loft("MoaiBody", secs[:5], mat=stone)
    bkit.recalc(body)
    bkit.shade_smooth(body, 34.0)
    head = bkit.loft("MoaiHead", secs[4:], mat=stone)
    bkit.recalc(head)
    bkit.shade_smooth(head, 34.0)

    # ---- the three features that make a moai a moai ----------------------
    bkit.rounded_box("MoaiBrow", 980.0, 300.0, 260.0, r=70.0, segments=3,
                     centre=(0.0, 300.0, BZL + HH * 0.60), mat=stone)
    for i, x in enumerate((-250.0, 250.0)):
        bkit.uv_sphere("MoaiEye%d" % i, 92.0, segments=20, rings=12,
                       centre=(x, 360.0, BZL + HH * 0.44), mat=shade)
    nose = bkit.rounded_box("MoaiNose", SPEC["nose_width"], 340.0,
                            SPEC["nose_length"], r=70.0, segments=3,
                            centre=(0.0, 380.0, BZL + HH * 0.24), mat=stone)
    bkit.rounded_box("MoaiLip", 720.0, 260.0, 130.0, r=48.0, segments=3,
                     centre=(0.0, 340.0, BZL + HH * 0.05), mat=stone)
    bkit.rounded_box("MoaiChin", 640.0, 220.0, 120.0, r=48.0, segments=3,
                     centre=(0.0, 320.0, BZL - 40.0), mat=stone)
    for i, s in enumerate((1, -1)):
        bkit.rounded_box("MoaiEar%d" % i, 150.0, 200.0, 460.0, r=60.0,
                         segments=3,
                         centre=(s * 530.0, -40.0, BZL + HH * 0.46),
                         mat=stone)

    # ---- arms: thin carved ridges down the flanks ------------------------
    for i, s in enumerate((1, -1)):
        bkit.rounded_box("MoaiArm%d" % i, 150.0, 150.0, BZL * 0.80, r=60.0,
                         segments=3,
                         centre=(s * 430.0, 190.0, BZL * 0.44), mat=stone)

    return dict(spec=SPEC, parts=11)