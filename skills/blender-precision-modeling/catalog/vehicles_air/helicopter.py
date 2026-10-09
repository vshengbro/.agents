"""
helicopter -- light single (R44 class) helicopter, 6500 long x 11400 rotor
across x 2900 high.

A helicopter is three things and their relationship is the whole model: a
two-blade main rotor on a mast that stands taller than the cabin, a cabin that
is a box with a bubble canopy and skids under it, and a tail boom long enough
that the tail rotor clears the main disc. The disc is the number that matters
-- 11.4 m across -- and it must lie HORIZONTAL, so the machine's height is set
by the mast head at 2900 mm, not by the rotor.

The skids are the floor datum: the skid tubes' undersides are at z=0 exactly,
so `sit_on_floor()` is a no-op and every `top_z` in CHECKS is the number that
was authored. A skid 140 mm below the datum silently lifts the whole aircraft.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _craft as C

SPEC = dict(
    cabin_length=2500.0,
    cabin_width=1300.0,
    rotor_diameter=11400.0,
    rotor_head_z=2900.0,
    tail_rotor_diameter=2400.0,
    skid_top_z=120.0,
    fin_height=1100.0,
)

CHECKS = [
    # `swept_*` is a RADIUS about the rotor's own axis, so an 11400 mm disc
    # reads 5700 - hub/2. A rotor has no bounding box: bbox_x/bbox_y report the
    # axial envelope and `diameter` reports the chord.
    dict(name="rotor_radius", mm=5400.0, tol=20.0, how="swept_z",
         part="HeliMainRotor"),
    dict(name="rotor_head_z", mm=2900.0, tol=15.0, how="top_z",
         part="HeliRotorMast"),
    dict(name="cabin_length", mm=2500.0, tol=10.0, how="bbox_x",
         part="HeliCabin"),
    dict(name="cabin_width", mm=1300.0, tol=10.0, how="bbox_y",
         part="HeliCabin"),
    # the tail disc lies in the XZ plane: its axis is Y
    dict(name="tail_rotor_radius", mm=1050.0, tol=15.0, how="swept_y",
         part="HeliTailRotor"),
    dict(name="skid_top_z", mm=120.0, tol=6.0, how="top_z", part="HeliSkidP"),
    dict(name="fin_height", mm=1100.0, tol=10.0, how="bbox_z",
         part="HeliFin"),
]

FZ = 1550.0            # cabin centre height; the skids carry the floor

# (x, half width, z_bottom, z_top, n) -- nose at +x
STATIONS = [
    (1200.0, 500.0, FZ - 400.0, FZ + 250.0, 3.0),
    (900.0, 620.0, FZ - 520.0, FZ + 420.0, 3.4),
    (200.0, 650.0, FZ - 600.0, FZ + 480.0, 3.6),
    (-600.0, 620.0, FZ - 560.0, FZ + 420.0, 3.4),
    (-1300.0, 500.0, FZ - 440.0, FZ + 300.0, 3.0),
]


def build():
    skin = bkit.pbr("HeliSkin", base=(0.86, 0.87, 0.88), rough=0.20, coat=0.5)
    accent = bkit.pbr("HeliAccent", base=(0.68, 0.14, 0.09), rough=0.26)
    glass = bkit.pbr("HeliGlass", base=(0.05, 0.07, 0.09), rough=0.05)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")
    rotor_mat = bkit.pbr("HeliRotorBlade", base=(0.06, 0.06, 0.07), rough=0.32)

    cabin = C.body("HeliCabin", STATIONS, mat=skin, steps=48)
    C.glass_band(cabin, -800.0, 1150.0, FZ - 380.0, FZ + 400.0, glass,
                 max_nz=0.55)
    bkit.assign_faces_by(cabin, accent,
                         lambda c, n: (c.x / bkit.MM > 700.0 and n.z < -0.3))

    # tail boom: a tapering tube from the cabin back to the rotor
    C.body("HeliTailBoom", [
        (-1250.0, 420.0, FZ - 340.0, FZ + 340.0, 3.0),
        (-2400.0, 300.0, FZ - 240.0, FZ + 240.0, 3.0),
        (-4200.0, 200.0, FZ - 170.0, FZ + 170.0, 3.0),
        (-5000.0, 150.0, FZ - 130.0, FZ + 130.0, 3.0),
    ], mat=skin, steps=32)

    # main rotor: mast, swashplate, transmission, hub, two blades -- all in a
    # horizontal disc, so the height of the machine is the mast head
    bkit.cylinder("HeliRotorMast", 150.0, 900.0, segments=20, axis="Z",
                  centre=(0.0, 0.0, 2450.0), mat=steel)
    bkit.cylinder("HeliSwashplate", 330.0, 200.0, segments=28, axis="Z",
                  centre=(0.0, 0.0, 2130.0), mat=dark)
    bkit.rounded_box("HeliTransmission", 1100.0, 900.0, 700.0, r=200.0,
                     segments=3, centre=(-100.0, 0.0, 1950.0), mat=skin)
    bkit.cylinder("HeliRotorHub", 300.0, 340.0, segments=28, axis="Z",
                  centre=(0.0, 0.0, 2780.0), mat=steel)
    rotor = C.rotor("HeliMainRotor", SPEC["rotor_diameter"], 2, 600.0,
                    rotor_mat, chord=300.0, thick=60.0, twist=6.0)
    bkit.move(rotor, 0.0, 0.0, 2900.0)

    # tail rotor: the same rotor stood on its edge, 300 mm left of the fin
    tail = C.rotor("HeliTailRotor", SPEC["tail_rotor_diameter"], 2, 300.0,
                   rotor_mat, chord=180.0, thick=30.0, twist=6.0)
    bkit.move(tail, -4600.0, 300.0, 2400.0)
    tail.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.torus("HeliTailRotorGuard", 1250.0, 60.0, seg_major=44, seg_minor=10,
               centre=(-4600.0, 300.0, 2400.0), axis="Y", mat=steel)
    fin = C.fin("HeliFin", SPEC["fin_height"], 1100.0, 500.0, 0.08, skin,
                sweep=0.40, z0=FZ + 250.0)
    bkit.move(fin, -5000.0, 0.0, 0.0)
    bkit.rounded_box("HeliHorizontalFin", 900.0, 2400.0, 120.0, r=60.0,
                     segments=2, centre=(-5200.0, 0.0, 1000.0), mat=skin)
    bkit.rounded_box("HeliTailSkidGuard", 400.0, 400.0, 400.0, r=120.0,
                     segments=2, centre=(-4800.0, 0.0, 700.0), mat=steel)

    # skids: two tubes on two cross-tubes, undersides at z=0
    for s in (1, -1):
        tag = "P" if s > 0 else "S"
        b = bkit.rounded_box("HeliSkid%s" % tag, 3200.0, 120.0, 120.0, r=58.0,
                             segments=3, centre=(-100.0, s * 780.0, 60.0),
                             mat=steel)
        b.name = "HeliSkid%s" % tag
        bkit.rounded_box("HeliCabinRail%s" % tag, 2600.0, 120.0, 500.0, r=55.0,
                         segments=2, centre=(-100.0, s * 780.0, 700.0),
                         mat=steel)
    for i, (x, _y) in enumerate(bkit.grid_positions(cols=2, rows=1,
                                                     pitch_x=1200.0,
                                                     pitch_y=1.0)):
        bkit.rounded_box("HeliSkidCross%d" % i, 120.0, 1600.0, 120.0, r=55.0,
                         segments=2, centre=(-100.0 + x, 0.0, 180.0), mat=steel)
    bkit.recalc(cabin)

    return dict(spec=SPEC, parts=17)
