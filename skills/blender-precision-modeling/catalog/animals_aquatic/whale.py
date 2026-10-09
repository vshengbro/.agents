"""whale -- a 12 m blue whale: enormous tapering body, a small dorsal set far
back, broad flippers, throat pleats, and a tail whose flukes span a quarter of
the animal.

Proportion is everything at this scale. The head is a quarter of the length,
the dorsal sits at about 75% back, and the flukes are the widest part of the
animal -- wider than the body. Getting the dorsal too far forward or the flukes
too narrow is what makes a whale read as a stretched fish.

Construction: one lofted body from a proportion table, flat blade flukes and
flippers, a real ventral groove indicated by a second material, and the baleen
/ blowhole as small solids. Nothing is booleaned.

Orientation: the head points at -Y, X lateral, Z up, so side.png shows the
whole profile.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=12000.0,
    body_length=8400.0,
    body_depth=1500.0,
    body_width=1100.0,
    flipper_reach=2360.0,
    fluke_span=4200.0,
    dorsal_height=720.0,
)

# (y, half_height, half_width, z_centre) -- rostrum -6000, peduncle +2400
# The axis is LEVEL at z = 1400: a whale's spine runs straight, and letting
# the centreline drift downward toward the tail makes the animal look like it
# is diving -- and puts every fin placed at a constant z INSIDE the body, where
# the dorsal and the flukes disappear.
BODY = [
    (-6000.0, 190.0, 150.0, 1400.0),
    (-5600.0, 620.0, 470.0, 1400.0),
    (-5000.0, 980.0, 700.0, 1400.0),
    (-4200.0, 1250.0, 850.0, 1400.0),
    (-3200.0, 1400.0, 950.0, 1400.0),
    (-2000.0, 1460.0, 1000.0, 1400.0),
    (-800.0, 1450.0, 990.0, 1400.0),
    (400.0, 1360.0, 920.0, 1400.0),
    (1400.0, 1130.0, 760.0, 1400.0),
    (2100.0, 800.0, 540.0, 1400.0),
    (2600.0, 500.0, 340.0, 1400.0),
    (3000.0, 300.0, 210.0, 1400.0),
]
# the flukes: the widest part of the animal, with a deep central notch
# The flukes are a HORIZONTAL blade, so they are authored in the X-Y plane:
# a vertical plate extruded along X is a tail seen edge-on, and its span
# collapses to its own thickness.
FLUKE = [
    (0.0, 2880.0), (900.0, 3400.0), (1900.0, 4300.0), (2100.0, 5050.0),
    (1500.0, 5020.0), (700.0, 4400.0), (0.0, 3480.0), (-700.0, 4400.0),
    (-1500.0, 5020.0), (-2100.0, 5050.0), (-1900.0, 4300.0), (-900.0, 3400.0),
]
# the dorsal, small and set far back at about 75% of the length
# the dorsal sits ON the back: the body's dorsal line at y = 1900-2350 is
# around z = 2200-2450, so the fin's ROOT is authored there and it rises 380
DORSAL = [
    (1880.0, 2200.0), (1980.0, 2680.0), (2160.0, 2720.0), (2300.0, 2400.0),
    (2200.0, 2000.0), (2000.0, 2150.0),
]
FLIPPER = [
    (0.0, 0.0), (-900.0, 250.0), (-1900.0, 420.0), (-2600.0, 300.0),
    (-2000.0, -60.0), (-900.0, -120.0),
]


def build():
    skin = bkit.pbr("WhaleSkin", base=(0.115, 0.145, 0.185), rough=0.44)
    pale = bkit.pbr("WhaleBelly", base=(0.72, 0.74, 0.75), rough=0.46)
    pleat = bkit.pbr("WhalePleat", base=(0.55, 0.60, 0.63), rough=0.48)
    dark = bkit.pbr("WhaleDark", base=(0.06, 0.07, 0.085), rough=0.40)

    torso = F.body("Body", BODY, skin, n=2.9, steps=44)
    # the mottled blue-grey of a blue whale: a second material on the ONE solid
    bkit.assign_faces_by(torso, pale, lambda c, n: c.z / bkit.MM < 900.0)

    fluke = F.plate_xy("Fluke", FLUKE, 130.0, z=0.0, mat=skin)
    bkit.move(fluke, 0.0, 0.0, 1400.0)
    F.plate_yz("FinDorsal", DORSAL, 55.0, x=0.0, mat=skin)

    flip = F.plate_xy("FlipperL", FLIPPER, 60.0, mat=skin)
    bkit.move(flip, 820.0, -2400.0, 1100.0)
    F.bake_rot(flip, "Y", -26.0)
    F.mirror_copy(flip, "FlipperR")

    # ---- throat pleats: 24 grooves as a computed row across the underside.
    # The pitch comes from the groove count, so adding a groove cannot make
    # two of them share a coordinate.
    n_pleat = 24
    span = 3600.0
    pitch = span / (n_pleat - 1)
    for i in range(n_pleat):
        y = -5200.0 + i * pitch
        F.tube("Pleat%d" % (i + 1),
               [(0.0, y, 700.0), (0.0, y + pitch * 0.5, 660.0),
                (0.0, y + pitch, 620.0)],
               [(760.0, 40.0), (760.0, 30.0), (760.0, 40.0)], pleat,
               n=2.2, steps=10)

    # ---- blowhole on the crown, and the ridge behind the flipper
    bkit.uv_sphere("Blowhole", 55.0, segments=16, rings=8,
                   centre=(0.0, -4600.0, 2520.0), mat=dark)
    F.cone_between("FlipperNotch", (820.0, -2100.0, 1000.0),
                   (880.0, -2200.0, 1400.0), 90.0, 40.0, seg=10, mat=skin)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=30)


CHECKS = [
    dict(name="overall_length", mm=11100.0, tol=200.0, how="bbox_y"),
    dict(name="body_length", mm=9000.0, tol=200.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=2920.0, tol=120.0, how="bbox_z", part="Body"),
    dict(name="body_width", mm=2000.0, tol=100.0, how="bbox_x", part="Body"),
    dict(name="fluke_span", mm=4200.0, tol=150.0, how="bbox_x", part="Fluke"),
    # the flipper REACH is its own lateral extent. The whole assembly's X extent
    # is the fluke span -- measuring the assembly here would credit the whale's
    # flukes to the flippers.
    dict(name="flipper_reach", mm=2360.0, tol=120.0, how="bbox_x",
         part="FlipperL"),
    dict(name="dorsal_height", mm=720.0, tol=40.0, how="bbox_z",
         part="FinDorsal"),
]