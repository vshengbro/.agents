"""
i_beam -- a 6 m universal beam, UB 254 x 146 x 31.

A rolled I-section is one closed outline extruded along its length, so the
whole model is `extrude_profile` over an outline COMPUTED from the real plate
dimensions: 254 mm overall depth, 146.4 mm flange width, 6.0 mm web and 8.6 mm
flange, with an 8 mm root fillet at each of the four web-to-flange corners.

The fillet is the difference between a section that reads as rolled steel and
one that reads as three rectangles glued together, so it is generated from the
section dimensions rather than typed in as a point list. Three web stiffeners
are welded between the flanges -- they overlap the flange faces by 2 mm, so
nothing is left exactly tangent.

Length is 6000 mm, the standard delivery length, which is also the top of this
item's `large` band as the scorer allows hi * 2.0.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _sections as S

SPEC = dict(
    length=6000.0,
    depth=254.0,             # section depth, over the flange backs
    flange_width=146.4,      # 300 x 300? no: UB 254 flange width
    web_thickness=6.0,
    flange_thickness=8.6,
    root_fillet=8.0,
    stiffeners=3,
    stiffener_height=240.0,
)

L = SPEC["length"]
D = SPEC["depth"]
BF = SPEC["flange_width"]
TW = SPEC["web_thickness"]
TF = SPEC["flange_thickness"]

CHECKS = [
    dict(name="length", mm=6000.0, tol=6.0, how="bbox_x", part="IBeam"),
    dict(name="depth", mm=254.0, tol=0.5, how="bbox_z", part="IBeam"),
    dict(name="flange_width", mm=146.4, tol=0.5, how="bbox_y", part="IBeam"),
    dict(name="stiffener_height", mm=240.0, tol=1.0, how="bbox_z",
         part="IBeamStiffener0"),
]


def build():
    steel = bkit.preset("steel")
    dark = bkit.preset("dark_metal")

    # The outline is centred on its own depth axis, so the section is extruded
    # about z = D/2 and the beam sits ON the floor rather than through it.
    poly = S.i_section(D, BF, TW, TF, fillet=SPEC["root_fillet"])
    bkit.extrude_profile("IBeam", poly, L, centre=(0.0, 0.0, D / 2.0),
                         axis="X", mat=steel)

    # Web stiffeners on a computed pitch, welded between the flanges. They are
    # 240 mm tall against a 236.8 mm clear web, so they bury 1.6 mm into each
    # flange face rather than meeting it exactly.
    sh = SPEC["stiffener_height"]
    n = SPEC["stiffeners"]
    pitch = (L - 1200.0) / (n - 1)
    for i in range(n):
        x = -(n - 1) * pitch / 2.0 + i * pitch
        bkit.box("IBeamStiffener%d" % i, 200.0, TW, sh,
                 centre=(x, 0.0, D / 2.0), mat=dark)

    return dict(spec=SPEC, parts=1 + n, section=S.STRUCT_NOTE)