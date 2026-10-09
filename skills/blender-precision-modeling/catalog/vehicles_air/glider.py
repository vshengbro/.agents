"""
glider -- 15 m span competition glider, 6700 x 15000 x 1000 mm.

A glider is the purest aerofoil problem in the catalog: 15 m of span, a 0.75 m
root chord tapering to 0.35 m at the tip (a taper ratio near 2.2), an
aspect ratio of 28, and a fuselage so slender it is a fairing around a pilot.
There is no engine, so everything that reads on a powered aircraft -- prop,
exhaust, cowl -- is absent by design, and the T-tail replaces the fin-and-plane
of a conventional aircraft because a glider's tailplane sits clear of the wake.
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
    length=6700.0,
    span=15000.0,
    wing_chord_root=750.0,
    wing_chord_tip=350.0,
    fuselage_diameter=620.0,
    tailplane_span=2900.0,
    fin_height=520.0,
    top_z=1570.0,
)

CHECKS = [
    dict(name="length", mm=6700.0, tol=10.0, how="bbox_x",
         part="GliderFuselage"),
    dict(name="span", mm=15000.0, tol=12.0, how="bbox_y", part="GliderWing"),
    dict(name="fuselage_width", mm=620.0, tol=8.0, how="bbox_y",
         part="GliderFuselage"),
    dict(name="tailplane_span", mm=2900.0, tol=10.0, how="bbox_y",
         part="GliderTailplane"),
    dict(name="fin_height", mm=520.0, tol=10.0, how="bbox_z",
         part="GliderFin"),
    dict(name="top_z", mm=1570.0, tol=12.0, how="top_z", part=None),
]

FZ = 620.0             # fuselage axis height
R = SPEC["fuselage_diameter"] / 2.0

# (x, half width, z_bottom, z_top, n) -- nose at +x
STATIONS = [
    (3350.0, 40.0, FZ - 70.0, FZ + 60.0, 2.2),
    (3150.0, 140.0, FZ - 200.0, FZ + 190.0, 2.4),
    (2500.0, 250.0, FZ - 320.0, FZ + 330.0, 2.6),
    (1200.0, 310.0, FZ - 350.0, FZ + 420.0, 3.2),
    (0.0, 310.0, FZ - 340.0, FZ + 430.0, 3.4),
    (-1400.0, 270.0, FZ - 300.0, FZ + 380.0, 3.0),
    (-2600.0, 190.0, FZ - 220.0, FZ + 260.0, 2.8),
    (-3200.0, 110.0, FZ - 140.0, FZ + 160.0, 2.6),
    (-3350.0, 40.0, FZ - 60.0, FZ + 70.0, 2.4),
]


def build():
    skin = bkit.pbr("GliderSkin", base=(0.93, 0.93, 0.92), rough=0.18,
                    coat=0.5)
    trim = bkit.pbr("GliderTrim", base=(0.72, 0.06, 0.10), rough=0.24,
                    coat=0.5)
    glass = bkit.pbr("GliderCanopy", base=(0.06, 0.09, 0.12), rough=0.04,
                     transmission=0.4)
    steel = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")

    fus = C.body("GliderFuselage", STATIONS, mat=skin, steps=48)
    C.glass_band(fus, 900.0, 2700.0, FZ + 100.0, FZ + 420.0, glass,
                 max_nz=0.5)
    bkit.assign_faces_by(fus, trim,
                         lambda c, n: (c.x / bkit.MM < -1500.0
                                       and abs(n.z) < 0.3
                                       and c.y / bkit.MM > R * 0.7))

    # wing: 750 mm root chord at y=350, 350 mm tip at y=7500
    C.full_wing("GliderWing", (260.0, SPEC["wing_chord_root"], 0.11, 350.0),
                (600.0, SPEC["wing_chord_tip"], 0.10, 7500.0), skin,
                z_centre=FZ + 480.0, steps=20, dihedral=0.025)

    # T-tail: fin on top of the tailplane
    fin = C.fin("GliderFin", SPEC["fin_height"], 1200.0, 500.0, 0.09, skin,
                sweep=0.45, z0=FZ + 430.0)
    bkit.move(fin, -2450.0, 0.0, 0.0)
    _watertight(fin)
    tail = C.tailplane("GliderTailplane", -2450.0, FZ + 430.0, 1450.0, 700.0,
                       420.0, 0.09, skin, sweep=0.30)
    _watertight(tail)
    bkit.rounded_box("GliderTailSkid", 700.0, 200.0, 160.0, r=70.0,
                     segments=2, centre=(-3000.0, 0.0, 120.0), mat=steel)
    bkit.cylinder("GliderTailWheel", 130.0, 90.0, segments=20, axis="Y",
                  centre=(-3000.0, 0.0, 130.0), mat=rubber)

    # a main wheel half-recessed in the belly, plus a nose skid
    bkit.cylinder("GliderMainWheel", 200.0, 120.0, segments=24, axis="Y",
                  centre=(300.0, 0.0, 200.0), mat=rubber)
    bkit.rounded_box("GliderNoseSkid", 600.0, 120.0, 80.0, r=35.0,
                     segments=2, centre=(3000.0, 0.0, 200.0), mat=steel)
    bkit.rounded_box("GliderWingRootFairing", 1200.0, 700.0, 260.0, r=120.0,
                     segments=3, centre=(500.0, 0.0, FZ + 470.0), mat=skin)
    bkit.recalc(fus)

    return dict(spec=SPEC, parts=10)
