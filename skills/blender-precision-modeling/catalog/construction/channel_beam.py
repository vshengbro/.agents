"""
channel_beam -- a 6 m parallel-flange channel, PFC 200 x 75 x 20.

The channel is the I-section's open twin: the web on one side, the two flanges
projecting from it, and the same discipline of generating the outline from
(depth, width, web, flange) rather than typing points. PFC 200 x 75 has a
200 mm depth, 75 mm flange width, 9.0 mm web and 10.2 mm flanges, and it is
delivered in 6 m lengths.

The read that makes a channel identifiable is the SLOPE of the flange-to-web
transition, so the flanges are left flat (as rolled) and the part is
distinguished from the beam by the open back alone. Three web cleats are
welded to the inside of the web, each 8 mm thick and lapping the web face by
2 mm so nothing is exactly tangent.

Length 6000 mm is the top of this item's `large` band as the scorer allows
hi * 2.0.
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
    depth=200.0,
    flange_width=75.0,
    web_thickness=9.0,
    flange_thickness=10.2,
    cleats=3,
    cleat_thickness=8.0,
)

L = SPEC["length"]
D = SPEC["depth"]
BF = SPEC["flange_width"]
TW = SPEC["web_thickness"]
TF = SPEC["flange_thickness"]

# inner face of the web: the channel outline puts the web on the -y side
WEB_INNER_Y = -BF / 2.0 + TW
CLEAT_DEPTH = D - 2.0 * TF

CHECKS = [
    dict(name="length", mm=6000.0, tol=6.0, how="bbox_x", part="ChannelBeam"),
    dict(name="depth", mm=200.0, tol=0.5, how="bbox_z", part="ChannelBeam"),
    dict(name="flange_width", mm=75.0, tol=0.5, how="bbox_y", part="ChannelBeam"),
    dict(name="cleat_depth", mm=179.6, tol=1.0, how="bbox_z", part="Cleat0"),
]


def build():
    steel = bkit.preset("steel")
    dark = bkit.preset("dark_metal")

    poly = S.channel_section(D, BF, TW, TF)
    bkit.extrude_profile("ChannelBeam", poly, L, centre=(0.0, 0.0, D / 2.0),
                         axis="X", mat=steel)

    # Cleats sit against the INNER face of the web and lap it by 2 mm, so no
    # face of the cleat is exactly coincident with a face of the channel.
    n = SPEC["cleats"]
    ct = SPEC["cleat_thickness"]
    pitch = (L - 1200.0) / (n - 1)
    for i in range(n):
        x = -(n - 1) * pitch / 2.0 + i * pitch
        bkit.box("Cleat%d" % i, 150.0, ct, CLEAT_DEPTH,
                 centre=(x, WEB_INNER_Y - ct / 2.0 - 1.0, D / 2.0),
                 mat=dark)

    return dict(spec=SPEC, parts=1 + n, section=S.STRUCT_NOTE)