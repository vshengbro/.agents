"""
telescope -- 1105 x 606 x 810 mm 150 mm Newtonian reflector on an alt-az tripod:
700 mm optical tube, 200 mm dew shield, focuser with drawtube and eyepiece, a
finder scope, a saddle, and three splayed legs.

Same leg trick as `tripod`, for the same reason: the splay has to be baked into
the mesh so `array_radial` can orbit the world origin. The optical tube is the
long axis (X) and the finder sits on the tube's +Y face, which is where a
Newtonian actually carries it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tube_length=700.0,
    tube_diameter=220.0,
    dew_shield_length=200.0,
    dew_shield_diameter=230.0,
    eyepiece_diameter=60.0,
    finder_length=230.0,
    overall_height=818.0,
)

TUBE_R = SPEC["tube_diameter"] / 2.0
TUBE_Z = 700.0                       # optical axis height
LEG_TOP_Z = 500.0
LEG_SPREAD = 340.0


def _ring(r, cx, cz, n=18):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             r * math.sin(2 * math.pi * i / n),
             cz) for i in range(n)]


def _leg():
    steps = [(0.0, 16.0), (0.06, 14.0), (0.45, 12.0), (0.50, 13.0),
             (0.55, 13.0), (0.60, 9.0), (0.94, 7.5), (0.97, 8.5),
             (1.0, 4.0)]
    return [_ring(r, LEG_SPREAD * t, LEG_TOP_Z * (1.0 - t))
            for (t, r) in steps]


def build():
    tube_mat = bkit.pbr("ScopeTube", base=(0.090, 0.105, 0.115), rough=0.38)
    alu = bkit.pbr("ScopeAlu", base=(0.56, 0.57, 0.59), metal=0.85,
                   rough=0.34)
    dark = bkit.pbr("ScopeDark", base=(0.065, 0.065, 0.070), rough=0.44)
    glass = bkit.pbr("ScopeGlass", base=(0.14, 0.26, 0.42), metal=0.45,
                     rough=0.03)

    # ---- three splayed legs, splay baked into the mesh -------------------
    leg = bkit.loft("ScopeLegs", _leg(), mat=alu)
    bkit.array_radial(leg, count=3, axis="Z")
    # loft() does not recalc, and the swept copies can come out inside-out.
    # health() reports it per part, so name the fix rather than hunting later.
    bkit.recalc(leg)

    # ---- hub and saddle, each overlapping the next -----------------------
    bkit.cylinder("TripodHub", 45.0, 70.0, segments=44,
                  centre=(0.0, 0.0, 525.0), mat=dark)
    bkit.rounded_box("Saddle", 120.0, 240.0, 40.0, r=8.0, segments=3,
                     centre=(0.0, 0.0, 575.0), mat=alu)

    # ---- optical tube, dew shield and objective -------------------------
    bkit.cylinder("OpticalTube", TUBE_R, SPEC["tube_length"], segments=72,
                  axis="X", centre=(0.0, 0.0, TUBE_Z), mat=tube_mat)
    bkit.tube("DewShield", 115.0, 110.0, SPEC["dew_shield_length"],
              segments=72, axis="X", centre=(450.0, 0.0, TUBE_Z), mat=dark)
    bkit.cylinder("ObjectiveLens", 109.0, 8.0, segments=64, axis="X",
                  centre=(354.0, 0.0, TUBE_Z), mat=glass)

    # ---- two tube rings holding the OTA on the saddle -------------------
    rings = []
    for i, rx in enumerate((-180.0, 180.0)):
        rings.append(bkit.tube("TubeRing%d" % i, 118.0, 111.0, 30.0,
                               segments=72, axis="X", centre=(rx, 0.0, TUBE_Z),
                               mat=alu))
    bkit.join(rings, name="TubeRings")

    # ---- focuser, drawtube and eyepiece at the -X end --------------------
    bkit.rounded_box("Focuser", 80.0, 90.0, 90.0, r=10.0, segments=3,
                     centre=(-380.0, 0.0, TUBE_Z), mat=alu)
    bkit.cylinder("DrawTube", 32.0, 110.0, segments=48, axis="X",
                  centre=(-470.0, 0.0, TUBE_Z), mat=dark)
    bkit.cylinder("FocusKnob", 14.0, 46.0, segments=32, axis="Z",
                  centre=(-390.0, 0.0, TUBE_Z + 56.0), mat=dark)

    # lathe profiles carry ABSOLUTE z; rotated +90 deg about Y so the optical
    # axis of the eyepiece runs along +X.
    eye = bkit.lathe("ScopeEyepiece", [(0.0, 0.0), (17.0, 0.0), (17.0, 20.0),
                                       (30.0, 20.0), (30.0, 30.0),
                                       (0.0, 30.0)], segments=48, mat=dark)
    eye.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(eye, -550.0, 0.0, TUBE_Z)

    # ---- finder scope on the +Y face, in two rings -----------------------
    bkit.cylinder("FinderScope", 22.0, SPEC["finder_length"], segments=40,
                  axis="X", centre=(170.0, 130.0, 790.0), mat=dark)
    bkit.cylinder("FinderLens", 19.0, 4.0, segments=40, axis="X",
                  centre=(287.0, 130.0, 790.0), mat=glass)
    frings = [bkit.tube("FinderRing%d" % i, 26.0, 22.0, 14.0, segments=40,
                        axis="X", centre=(fx, 130.0, 790.0), mat=alu)
              for i, fx in enumerate((90.0, 250.0))]
    bkit.join(frings, name="FinderRings")

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="tube_length", mm=700.0, tol=0.8, how="bbox_x",
         part="OpticalTube"),
    # `diameter` is max(bbox_x, bbox_y) and on a 700 mm tube reads the 700 mm
    # length. bbox_min is the honest transverse extent.
    dict(name="tube_diameter", mm=220.0, tol=0.8, how="bbox_min",
         part="OpticalTube"),
    dict(name="dew_shield_diameter", mm=230.0, tol=0.8, how="diameter",
         part="DewShield"),
    dict(name="eyepiece_diameter", mm=60.0, tol=0.6, how="diameter",
         part="ScopeEyepiece"),
    dict(name="overall_height", mm=818.0, tol=2.0, how="bbox_z"),
]