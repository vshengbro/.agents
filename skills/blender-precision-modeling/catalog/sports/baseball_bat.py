"""
baseball_bat -- 838 mm (33 inch) ash bat: a real turned profile with a knob,
a waisted handle, a barrel and a domed end.

Every bat is one lathe, and the whole silhouette lives in that profile list.
The three features that make a bat read as a bat rather than as a bowling pin
are all explicit points on it: the 46 mm knob at the butt, the 25 mm handle
that stays thin for 150 mm, and the 67 mm barrel that peaks around 560 mm and
then domes over. The grip tape is a second material on the same solid.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=838.0,
    barrel_diameter=67.0,
    barrel_length=300.0,
    handle_diameter=25.0,
    knob_diameter=46.0,
    taper_length=390.0,
    grip_length=260.0,
)

# (radius, height) from the butt face to the crown. Read it as a silhouette.
PROFILE = [
    (0.0, 0.0), (18.0, 0.0), (22.0, 1.5), (23.0, 4.0), (22.0, 6.5),
    (18.0, 8.0), (14.0, 10.0), (13.0, 13.0),          # knob -> handle neck
    (12.6, 30.0), (12.5, 90.0), (12.5, 150.0),        # handle
    (12.9, 200.0), (14.0, 240.0), (16.5, 290.0),      # taper
    (20.0, 340.0), (24.0, 390.0), (28.0, 440.0),
    (31.0, 490.0), (32.8, 540.0), (33.5, 580.0),      # barrel, widest here
    (33.2, 640.0), (32.0, 700.0), (29.5, 750.0),
    (25.0, 790.0), (18.0, 820.0), (10.0, 833.0), (0.0, 838.0),   # dome
]

CHECKS = [
    dict(name="length", mm=838.0, tol=0.5, how="bbox_z", part="Bat"),
    dict(name="barrel_diameter_x", mm=67.0, tol=0.5, how="bbox_x", part="Bat"),
    # the barrel is turned, not oval: measuring the other axis proves it
    dict(name="barrel_diameter_y", mm=67.0, tol=0.5, how="bbox_y", part="Bat"),
]


def build():
    ash = bkit.pbr("AshWood", base=(0.74, 0.60, 0.40), rough=0.42)
    tape = bkit.preset("black_plastic")
    top = bkit.pbr("BatTop", base=(0.30, 0.20, 0.12), rough=0.50)

    bat = bkit.lathe("Bat", PROFILE, segments=96, mat=ash)
    # grip tape and a lacquered cap on the barrel, both on the same solid
    bkit.assign_faces_by(bat, tape,
                         lambda c, n: c.z / bkit.MM < SPEC["grip_length"])
    bkit.assign_faces_by(bat, top,
                         lambda c, n: c.z / bkit.MM > SPEC["grip_length"] + 200.0)
    return dict(spec=SPEC, parts=1)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
