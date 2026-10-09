"""
router -- 200 x 150 x 38 mm dual-band access point with two antennas.

Repeated-feature discipline: the top vent is 13 louvre slots on one
`array_linear` cutter and a single boolean, and the five front status LEDs
and the four rear LAN ports are both `bkit.lay_out` rows, so their pitch is
computed from the real port width rather than typed in.

The antennas are the one part that needs a transform bkit has no primitive
for: each cylinder is built at the origin, rotated, and only then positioned
with `bkit.move`, which is what refreshes the cached `matrix_world` the
bevel/rounded box radii and the camera framing are computed from.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=200.0,
    depth=150.0,
    height=38.0,
    vents=13,
    lan_ports=4,
    antenna_length=95.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]


def build():
    shell = bkit.pbr("RouterShell", base=(0.80, 0.80, 0.79), rough=0.34,
                     coat=0.2)
    dark = bkit.pbr("RouterDark", base=(0.13, 0.13, 0.15), rough=0.44)
    led = bkit.pbr("RouterLed", base=(0.10, 0.55, 0.30), rough=0.20,
                   emission=(0.10, 0.80, 0.40), emission_strength=1.2)
    ant_mat = bkit.pbr("RouterAntenna", base=(0.34, 0.35, 0.38), rough=0.32,
                       coat=0.3)

    body = bkit.rounded_box("RouterBody", W, D, H, r=11.0, segments=5,
                            centre=(0, 0, H / 2.0), mat=shell)

    # ---- 13 louvre slots across the top, one arrayed cutter -------------
    louvre = bkit.rounded_box("_vent", 130.0, 3.2, 8.0, r=1.4, segments=2,
                              centre=(0, -40.0, H - 1.0), mat=dark)
    bkit.array_linear(louvre, count=SPEC["vents"], offset_mm=(0, 5.6, 0))
    bkit.boolean(body, louvre, "DIFFERENCE")

    # ---- five front status LEDs on one computed pitch --------------------
    leds = []
    for i, (x, w) in enumerate(bkit.lay_out([4.0] * 5, gap=7.0)):
        leds.append(bkit.rounded_box(
            "_led%d" % i, w, 2.0, 1.4, r=0.5, segments=2,
            centre=(x, D / 2.0 - 0.1, 11.0), mat=led))
    bkit.join(leds, name="RouterLeds")

    # ---- four rear LAN ports plus the WAN jack, one computed row ---------
    ports = []
    for i, (x, w) in enumerate(bkit.lay_out([16.0] * 5, gap=5.0)):
        ports.append(bkit.rounded_box(
            "_p%d" % i, w, 3.0, 13.0, r=0.8, segments=2,
            centre=(x - 8.0, -D / 2.0 + 0.2, 12.0), mat=dark))
    bkit.join(ports, name="RouterPorts")

    # ---- two swept-back antennas -----------------------------------------
    # Built at the origin, rotated, then moved: rotating after `move` would
    # swing the part about the world origin and throw it across the scene.
    # Both tilt the SAME way -- +28 degrees sends the antenna's local +Z to
    # (0, -sin28, cos28), i.e. up and toward -Y, which is the back. Mirroring
    # the sign would splay them front and back instead of pairing them.
    tilt = math.radians(28.0)
    axis = (0.0, -math.sin(tilt), math.cos(tilt))
    half = SPEC["antenna_length"] / 2.0
    pivot_y, pivot_z = 68.0, 34.0
    ants = []
    for i, sign in enumerate((1, -1)):
        ant = bkit.cylinder("RouterAntenna%d" % i, 4.2,
                            SPEC["antenna_length"], segments=24,
                            centre=(0, 0, 0), mat=ant_mat, r2=2.6)
        ant.rotation_euler = (tilt, 0.0, 0.0)
        bkit.move(ant, sign * 72.0, pivot_y + axis[1] * half,
                  pivot_z + axis[2] * half)
        ants.append(ant)
        # Pivot boss, so the antenna root meets the shell instead of
        # hovering where the case's 11 mm corner radius curves away.
        ants.append(bkit.cylinder(
            "_boss%d" % i, 6.5, 12.0, segments=24, axis="Y",
            centre=(sign * 72.0, pivot_y + 4.0, pivot_z), mat=ant_mat))
    bkit.join(ants, name="RouterAntennas")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="width", mm=200.0, tol=0.8, how="bbox_x", part="RouterBody"),
    dict(name="depth", mm=150.0, tol=0.8, how="bbox_y", part="RouterBody"),
    dict(name="height", mm=38.0, tol=0.8, how="bbox_z", part="RouterBody"),
]
