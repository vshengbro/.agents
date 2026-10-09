"""
fighter_jet -- F/A-18 class single-seat fighter, 18500 x 13500 x=4800 mm.

A fighter's read is three ratios: a 13.5 m span against 18.5 m of length, a
leading-edge sweep of 20 deg that continues into the wing root and out to the
canted tails, and a fuselage that is much deeper than it is wide (a 2.0 m
diameter barrel carrying fuel, sitting on a spine above it). The LEX, the
canted twin tails and the twin ventral intakes are the three details that stop
it reading as a passenger jet with a pointy nose.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bmesh
import _craft as C


def _watertight(ob):
    """Fix the INSIDE-OUT winding the shared aerofoil helpers leave in a foil.

    The same lofts -- and `_craft.fin`, which stands a panel on end by rewriting
    its vertex coordinates -- can come out wound inside-out;
    `recalc_face_normals` leaves an already-consistent winding alone, so the
    signed volume decides and the faces are reversed when it comes out negative.

    This used to also drop the root cap of a tail that sat ON the mirror plane,
    compensating for `bkit.mirror()` welding the two halves together. `bkit.mirror`
    now picks its merge per object and keeps the halves separate when the source
    only sits on the plane, so that cap is what closes each half and dropping it
    is what left 76 open boundary edges behind.
    """
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob

SPEC = dict(
    length=18500.0,
    span=13500.0,
    fuselage_diameter=2000.0,
    wing_area_span=6000.0,
    canard_span=3400.0,
    tail_cant=20.0,
    fin_height=1800.0,
    top_z=5250.0,
)

CHECKS = [
    dict(name="length", mm=18500.0, tol=10.0, how="bbox_x",
         part="FighterFuselage"),
    dict(name="span", mm=13500.0, tol=12.0, how="bbox_y", part="FighterWing"),
    dict(name="fuselage_diameter", mm=2000.0, tol=10.0, how="bbox_y",
         part="FighterFuselage"),
    dict(name="canard_span", mm=3400.0, tol=10.0, how="bbox_y",
         part="FighterCanard"),
    dict(name="fin_height", mm=1800.0, tol=20.0, how="bbox_z",
         part="FighterFin"),
    dict(name="top_z", mm=5250.0, tol=20.0, how="top_z", part=None),
]

FZ = 2450.0            # fuselage axis height; the twin tails sit on top of it
R = SPEC["fuselage_diameter"] / 2.0

# (x, half width, z_bottom, z_top, n) -- nose at +x, spine rising aft
STATIONS = [
    (9250.0, 120.0, FZ - 200.0, FZ + 60.0, 2.2),
    (9000.0, 380.0, FZ - 380.0, FZ + 240.0, 2.4),
    (8200.0, 700.0, FZ - 780.0, FZ + 620.0, 2.6),
    (7000.0, 900.0, FZ - 980.0, FZ + 900.0, 3.0),
    (5400.0, 1000.0, FZ - 1050.0, FZ + 1080.0, 3.6),
    (3000.0, 1000.0, FZ - 1080.0, FZ + 1120.0, 4.0),
    (0.0, 940.0, FZ - 1000.0, FZ + 1050.0, 3.8),
    (-3600.0, 860.0, FZ - 900.0, FZ + 1000.0, 3.4),
    (-7000.0, 800.0, FZ - 820.0, FZ + 900.0, 3.2),
    (-8600.0, 700.0, FZ - 700.0, FZ + 700.0, 3.0),
    (-9250.0, 480.0, FZ - 480.0, FZ + 460.0, 2.8),
]


def build():
    skin = bkit.pbr("FighterSkin", base=(0.34, 0.36, 0.40), rough=0.34,
                    metal=0.35)
    canopy = bkit.pbr("FighterCanopy", base=(0.05, 0.07, 0.10), rough=0.04,
                      transmission=0.3)
    panel = bkit.pbr("FighterPanel", base=(0.16, 0.17, 0.19), rough=0.46)
    intake = bkit.pbr("FighterIntake", base=(0.10, 0.10, 0.11), rough=0.52)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")
    rubber = bkit.preset("rubber")

    fus = C.body("FighterFuselage", STATIONS, mat=skin, steps=56)
    C.glass_band(fus, 5400.0, 8400.0, FZ + 380.0, FZ + 1000.0, canopy,
                 max_nz=0.55)

    # wing: 20 deg leading-edge sweep, thin, slight anhedral inboard
    C.full_wing("FighterWing", (2600.0, 4300.0, 0.07, 900.0),
                (-2050.0, 1100.0, 0.06, 6750.0), skin, z_centre=FZ - 250.0,
                steps=18)

    # canards, ahead of the wing on the intake shoulders
    canard = C.full_wing("FighterCanard", (5400.0, 1900.0, 0.07, 500.0),
                         (4300.0, 900.0, 0.06, 1700.0), skin,
                         z_centre=FZ + 250.0, steps=12)
    _watertight(canard)

    # twin ventral intakes with a splitter plate each
    for i, s in enumerate((1, -1)):
        box = bkit.rounded_box("FighterIntake%d" % i, 4200.0, 700.0, 1200.0,
                               r=120.0, segments=2,
                               centre=(4000.0, s * 1150.0, FZ - 900.0),
                               mat=intake)
        box.name = "FighterIntake%d" % i
        bkit.rounded_box("FighterSplitter%d" % i, 4200.0, 80.0, 1400.0, r=30.0,
                         segments=2, centre=(4000.0, s * 780.0, FZ - 820.0),
                         mat=steel)
        lip = bkit.tube("FighterIntakeLip%d" % i, 420.0, 300.0, 700.0,
                        segments=20, axis="Y",
                        centre=(6050.0, s * 1150.0, FZ - 900.0), mat=dark)
        lip.name = "FighterIntakeLip%d" % i

    # single vertical fin plus two outward-canted tails
    fin = C.fin("FighterFin", SPEC["fin_height"], 3000.0, 1300.0, 0.08, panel,
                sweep=0.50, z0=FZ + 1000.0)
    bkit.move(fin, -6000.0, 0.0, 0.0)
    _watertight(fin)
    for i, s in enumerate((1, -1)):
        t = C.wing("FighterTail%d" % i, (0.0, 2300.0, 0.08, 0.0),
                   (-760.0, 1000.0, 0.07, 1100.0), panel, steps=12)
        C.freeze(t)
        bkit.mirror(t, "Y")
        t.location = (0.0, 0.0, 0.0)
        _watertight(t)
        bkit.move(t, -7400.0, s * 900.0, FZ + 1000.0)
        # cant 20 deg outward about the tail's own root, which is where the
        # object origin now sits -- the mesh is baked, so rotation is safe here
        t.rotation_euler = (math.radians(20.0) * s, 0.0, 0.0)
        t.name = "FighterTail%d" % i

    # undercarriage: nose wheel on a strut, two mains in the wing roots
    bkit.cylinder("FighterNoseStrut", 70.0, 1600.0, segments=12, axis="Z",
                  centre=(4800.0, 0.0, 900.0), mat=steel)
    bkit.cylinder("FighterNoseWheel", 300.0, 200.0, segments=24, axis="Y",
                  centre=(4800.0, 0.0, 300.0), mat=rubber)
    for i, s in enumerate((1, -1)):
        bkit.cylinder("FighterMainStrut%d" % i, 90.0, 1500.0, segments=12,
                      axis="Z", centre=(500.0, s * 1200.0, 900.0), mat=steel)
        bkit.cylinder("FighterMainWheel%d" % i, 420.0, 300.0, segments=28,
                      axis="Y", centre=(500.0, s * 1200.0, 420.0), mat=rubber)
    bkit.rounded_box("FighterNozzle", 1400.0, 1500.0, 1100.0, r=260.0,
                     segments=3, centre=(-8600.0, 0.0, FZ), mat=dark)
    bkit.cylinder("FighterExhaust", 260.0, 300.0, segments=20, axis="X",
                  centre=(-9250.0, 0.0, FZ), mat=dark)
    bkit.recalc(fus)

    return dict(spec=SPEC, parts=20)
