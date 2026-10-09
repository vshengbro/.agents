"""
airliner -- 737-800 class narrowbody, 39650 x 35800 x 11800 mm.

Three numbers make an airliner read and all three are the real 737-800's:
39.65 m of length, 35.8 m of span (17900 mm per side) and a 3.76 m fuselage
diameter held constant over the cabin. Everything else follows from how those
three meet: two turbofans at 5900 mm from the centreline slung forward of and
below the wing leading edge, a 25 degree swept wing with 6 % dihedral, and a
fin whose tip is 11.8 m above the ground -- which puts the fuselage centreline
at 4250 mm and the fin root at the crown of the barrel at 6130 mm.

The wing is one loft of airfoil sections from root to tip, mirrored in Y as a
single object, so the span is a plain `bbox_y` and the two halves cannot drift
apart.
"""
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

    This used to also drop the root cap of a panel that sat ON the mirror plane,
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
    length=39650.0,
    span=35800.0,
    fuselage_diameter=3760.0,
    fuselage_axis_z=4250.0,
    wing_chord_root=5800.0,
    wing_chord_tip=1600.0,
    wing_sweep=25.0,
    engine_diameter=2400.0,
    engine_station=5900.0,
    fin_height=5670.0,
    stabiliser_span=12200.0,
    top_z=11800.0,
)

CHECKS = [
    dict(name="length", mm=39650.0, tol=12.0, how="bbox_x",
         part="AirlinerFuselage"),
    dict(name="span", mm=35800.0, tol=15.0, how="bbox_y", part="AirlinerWing"),
    dict(name="fuselage_diameter", mm=3760.0, tol=10.0, how="bbox_y",
         part="AirlinerFuselage"),
    # the nacelle is 4300 mm LONG along X and 2400 across: `diameter` picks the
    # larger of bbox_x/bbox_y and so reports the length
    dict(name="engine_diameter", mm=2400.0, tol=20.0, how="bbox_y",
         part="AirlinerEngine0"),
    dict(name="fin_height", mm=5670.0, tol=20.0, how="bbox_z",
         part="AirlinerFin"),
    dict(name="stabiliser_span", mm=12200.0, tol=20.0, how="bbox_y",
         part="AirlinerStabiliser"),
    dict(name="top_z", mm=11800.0, tol=25.0, how="top_z", part=None),
]

FZ = SPEC["fuselage_axis_z"]
R = SPEC["fuselage_diameter"] / 2.0

# (x, half width, z_bottom, z_top, n) -- nose at +x
STATIONS = [
    (19825.0, 190.0, FZ - 240.0, FZ + 90.0, 2.4),
    (19000.0, 780.0, FZ - 940.0, FZ + 700.0, 2.6),
    (17000.0, 1400.0, FZ - 1650.0, FZ + 1500.0, 2.8),
    (13000.0, 1830.0, FZ - 1870.0, FZ + 1860.0, 4.5),
    (10000.0, R, FZ - R, FZ + R, 6.0),
    (-12000.0, R, FZ - R, FZ + R, 6.0),
    (-16000.0, 1880.0, FZ - 1890.0, FZ + 1880.0, 4.5),
    (-18400.0, 1500.0, FZ - 1750.0, FZ + 1500.0, 3.0),
    (-19600.0, 900.0, FZ - 1200.0, FZ + 600.0, 2.6),
    (-19825.0, 220.0, FZ - 420.0, FZ + 120.0, 2.4),
]


def build():
    skin = bkit.pbr("AirlinerSkin", base=(0.90, 0.90, 0.89), rough=0.24,
                    coat=0.3)
    belly = bkit.pbr("AirlinerBelly", base=(0.58, 0.59, 0.62), rough=0.34)
    glass = bkit.pbr("AirlinerGlass", base=(0.04, 0.05, 0.07), rough=0.05)
    accent = bkit.pbr("AirlinerAccent", base=(0.05, 0.22, 0.48), rough=0.26)
    engine = bkit.pbr("EngineCowl", base=(0.84, 0.85, 0.86), rough=0.22,
                      metal=0.5)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")
    rubber = bkit.preset("rubber")

    fus = C.body("AirlinerFuselage", STATIONS, mat=skin, steps=64)
    C.glass_band(fus, 13000.0, 18600.0, FZ + 200.0, FZ + 1300.0, glass)
    bkit.assign_faces_by(fus, belly, lambda c, n: c.z / bkit.MM < FZ - R * 0.45)
    bkit.assign_faces_by(fus, accent,
                         lambda c, n: (abs(c.x / bkit.MM) < 11000.0
                                       and abs(n.z) < 0.2
                                       and c.y / bkit.MM > R * 0.85))

    # wing: 5800 mm root chord at y=1900, 1600 mm tip at y=17900, 25 deg sweep
    C.full_wing("AirlinerWing",
                (6000.0, SPEC["wing_chord_root"], 0.11, 1900.0),
                (-1720.0, SPEC["wing_chord_tip"], 0.10, 17900.0), skin,
                z_centre=FZ - 700.0, steps=22)

    # two turbofans slung forward of and below the wing leading edge
    C.nacelle_pair("AirlinerEngine", 4200.0, FZ - 2500.0, SPEC["engine_station"],
                   SPEC["engine_diameter"], 4300.0, engine,
                   pylon=(900.0, 420.0, 1000.0), pylon_mat=skin)
    for i, s in enumerate((1, -1)):
        bkit.tube("AirlinerEngineLip%d" % i, 1300.0, 1140.0, 420.0,
                  segments=44, axis="X",
                  centre=(2050.0, s * SPEC["engine_station"], FZ - 2500.0),
                  mat=dark)
        bkit.cylinder("AirlinerFan%d" % i, 1140.0, 200.0, segments=40,
                      axis="X", centre=(2300.0, s * SPEC["engine_station"],
                                        FZ - 2500.0), mat=dark)

    # tail: fin 5670 mm above the crown, stabiliser 12200 mm across
    fin = C.fin("AirlinerFin", SPEC["fin_height"], 6200.0, 2300.0, 0.11, skin,
                sweep=0.46, z0=FZ + R)
    bkit.move(fin, -14000.0, 0.0, 0.0)
    stab = C.tailplane("AirlinerStabiliser", -15600.0, FZ + 2200.0, 6100.0,
                    3400.0, 1400.0, 0.10, skin, sweep=0.42)
    _watertight(stab)
    bkit.rounded_box("AirlinerFinFill", 2600.0, 300.0, 1200.0, r=120.0,
                     segments=2, centre=(-17900.0, 0.0, FZ + 1350.0), mat=skin)

    # undercarriage: two four-wheel bogies on struts, plus a nose wheel
    for i, s in enumerate((1, -1)):
        bkit.cylinder("AirlinerGearStrut%d" % i, 150.0, 2300.0, segments=16,
                      axis="Z", centre=(-2600.0, s * 2500.0, 1200.0), mat=steel)
        bkit.rounded_box("AirlinerGearBay%d" % i, 3200.0, 700.0, 500.0, r=150.0,
                         segments=2, centre=(-2600.0, s * 2500.0, 2100.0),
                         mat=skin)
        for j, (dx, dy) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                          pitch_x=950.0,
                                                          pitch_y=800.0)):
            bkit.cylinder("AirlinerWheel%d%d" % (i, j), 600.0, 380.0,
                          segments=32, axis="Y",
                          centre=(-2600.0 + dx, s * 2500.0 + dy, 600.0),
                          mat=rubber)
    bkit.cylinder("AirlinerNoseStrut", 110.0, 2400.0, segments=14, axis="Z",
                  centre=(14800.0, 0.0, 2000.0), mat=steel)
    for j, dy in enumerate((-170.0, 170.0)):
        bkit.cylinder("AirlinerNoseWheel%d" % j, 400.0, 300.0, segments=28,
                      axis="Y", centre=(14800.0, dy, 400.0), mat=rubber)

    return dict(spec=SPEC, parts=19)
