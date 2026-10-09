"""
spanner_socket -- 226 mm 3/8 in ratchet handle with a 17 mm socket fitted.

Socket and ratchet head overlap by 2 mm on purpose: a socket that merely
touches the head at x = -74 would render as two separate objects floating a
hair apart under the key light.

The socket is a real TUBE, so its 19 mm bore is visible from the open end and
the model does not read as a solid plug. Bore diameter is not measurable from
a bounding box, so CHECKS declares the outside diameter and the length.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SOCKET_AF = 17.0              # 17 mm socket -> 26.5 mm across the flats
SOCKET_R = 13.5
SOCKET_L = 42.0

SPEC = dict(
    overall_length=226.0,
    socket_length=SOCKET_L,
    socket_outer_diameter=27.0,
    socket_bore=19.0,
    grip_length=126.0,
)


def build():
    chrome = bkit.pbr("SocketChrome", base=(0.80, 0.82, 0.86), metal=0.40,
                      rough=0.18)
    steel = bkit.pbr("RatchetSteel", base=(0.64, 0.66, 0.70), metal=0.30,
                     rough=0.30)
    dark = bkit.pbr("RatchetDark", base=(0.32, 0.33, 0.36), metal=0.25,
                    rough=0.42)

    socket = bkit.tube("SocketWrenchSocket", SOCKET_R, 9.5, SOCKET_L,
                       segments=48, centre=(-93.0, 0, 0), axis="X",
                       mat=chrome)
    head = bkit.cylinder("SocketWrenchHead", 16.0, 20.0, segments=48,
                         axis="Y", centre=(-58.0, 0, 0), mat=steel)
    neck = bkit.rounded_box("SocketWrenchNeck", 34.0, 16.0, 13.0, r=4.0,
                            segments=3, centre=(-28.0, 0, 0), mat=steel)

    grip = ((-14.0, 20.0, 16.0, 6.0), (20.0, 23.0, 19.0, 7.0),
            (80.0, 21.0, 18.0, 7.0), (112.0, 19.0, 16.0, 6.0))
    sections = [[(x, y, z) for (y, z) in
                 bkit.rounded_rect_section(sy, sz, r)]
                for (x, sy, sz, r) in grip]
    handle = bkit.loft("SocketWrenchGrip", sections, mat=steel)
    bkit.recalc(handle)

    lever = bkit.rounded_box("SocketWrenchReverseLever", 10.0, 6.0, 5.0,
                             r=1.5, segments=2, centre=(-58.0, -12.0, 12.0),
                             mat=dark)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="socket_length", mm=42.0, tol=0.5, how="bbox_x",
         part="SocketWrenchSocket"),
    dict(name="socket_outer_diameter", mm=27.0, tol=0.4, how="bbox_y",
         part="SocketWrenchSocket"),
    dict(name="grip_length", mm=126.0, tol=0.6, how="bbox_x",
         part="SocketWrenchGrip"),
    dict(name="overall_length", mm=226.0, tol=1.5, how="bbox_x"),
]