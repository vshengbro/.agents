"""
propeller_plane -- 172 class high-wing single, 8200 x 11000 x 2700 mm.

A light single is four decisions: an 11 m span carried on a HIGH wing with a
lift strut, a fixed tricycle gear with wheel fairings instead of retracts, a
two-blade tractor propeller on a spinner, and a slab-sided cabin with a rear
window. The wing is the model -- 1.55 m root chord tapering to 1.13 m at the
tip, 1.7 deg of washout-free straight taper and 2 deg of dihedral, with the
lift strut as the strut that makes a high wing structurally possible.
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
    length=8200.0,
    span=11000.0,
    wing_chord_root=1550.0,
    wing_chord_tip=1130.0,
    fuselage_diameter=1000.0,
    propeller_diameter=1930.0,
    wheel_diameter=620.0,
    top_z=2700.0,
)

CHECKS = [
    dict(name="length", mm=8200.0, tol=10.0, how="bbox_x",
         part="PropPlaneFuselage"),
    dict(name="span", mm=11000.0, tol=12.0, how="bbox_y", part="PropPlaneWing"),
    dict(name="fuselage_width", mm=1000.0, tol=10.0, how="bbox_y",
         part="PropPlaneFuselage"),
    # a two-blade disc has no bounding box: bbox_x/bbox_y report the axial
    # envelope and `diameter` reports the chord. swept_x sweeps about the disc's
    # own axis and returns a RADIUS: 1930/2 - 300/2.
    dict(name="propeller_radius", mm=815.0, tol=10.0, how="swept_x",
         part="PropPlanePropeller"),
    dict(name="wheel_diameter", mm=620.0, tol=8.0, how="diameter",
         part="PropPlaneWheelN"),
    dict(name="top_z", mm=2700.0, tol=15.0, how="top_z", part=None),
]

FZ = 1250.0            # fuselage axis height, 1000/2 above the wheels
R = SPEC["fuselage_diameter"] / 2.0

# (x, half width, z_bottom, z_top, n) -- nose at +x
STATIONS = [
    (4100.0, 260.0, FZ - 260.0, FZ + 230.0, 2.6),
    (3800.0, 430.0, FZ - 450.0, FZ + 430.0, 3.0),
    (3000.0, 500.0, FZ - 540.0, FZ + 560.0, 3.6),
    (1500.0, 500.0, FZ - 560.0, FZ + 620.0, 4.2),
    (0.0, 500.0, FZ - 560.0, FZ + 620.0, 4.2),
    (-1500.0, 460.0, FZ - 520.0, FZ + 560.0, 4.0),
    (-3000.0, 330.0, FZ - 380.0, FZ + 380.0, 3.2),
    (-3900.0, 140.0, FZ - 180.0, FZ + 160.0, 2.6),
    (-4100.0, 60.0, FZ - 90.0, FZ + 80.0, 2.4),
]


def build():
    skin = bkit.pbr("PropPlaneSkin", base=(0.88, 0.06, 0.05), rough=0.24,
                    coat=0.4)
    stripe = bkit.pbr("PropPlaneStripe", base=(0.92, 0.92, 0.90), rough=0.26)
    glass = bkit.pbr("PropPlaneGlass", base=(0.05, 0.07, 0.09), rough=0.05)
    cowl = bkit.pbr("PropPlaneCowl", base=(0.86, 0.87, 0.88), rough=0.20,
                    coat=0.5)
    steel = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")
    prop_mat = bkit.pbr("PropBlade", base=(0.05, 0.05, 0.06), rough=0.34)

    fus = C.body("PropPlaneFuselage", STATIONS, mat=skin, steps=52)
    C.glass_band(fus, 1500.0, 3600.0, FZ + 120.0, FZ + 560.0, glass)
    bkit.assign_faces_by(fus, stripe,
                         lambda c, n: (abs(c.x / bkit.MM) < 2200.0
                                       and abs(n.z) < 0.25
                                       and c.y / bkit.MM > R * 0.8))
    bkit.rounded_box("PropPlaneEngineCowl", 1300.0, 900.0, 900.0, r=380.0,
                     segments=4, centre=(3350.0, 0.0, FZ), mat=cowl)
    bkit.rounded_box("PropPlaneSpinner", 800.0, 700.0, 700.0, r=340.0,
                     segments=4, centre=(4400.0, 0.0, FZ), mat=stripe)

    # tractor propeller, two blades on an X axis
    prop = C.rotor("PropPlanePropeller", SPEC["propeller_diameter"], 2, 300.0,
                   prop_mat, chord=210.0, thick=16.0, twist=16.0)
    bkit.place(prop, (4450.0, 0.0, FZ), "X")

    # high wing with a lift strut each side
    C.full_wing("PropPlaneWing", (700.0, SPEC["wing_chord_root"], 0.13, 480.0),
                (1050.0, SPEC["wing_chord_tip"], 0.11, 5500.0), skin,
                z_centre=FZ + 700.0, steps=18)
    for i, s in enumerate((1, -1)):
        C.strut("PropPlaneLiftStrut%d" % i, (900.0, s * 500.0, FZ + 680.0),
                (700.0, s * 2450.0, FZ - 250.0), 55.0, steel, 12)

    # vertical fin and tailplane
    fin = C.fin("PropPlaneFin", 1100.0, 1600.0, 800.0, 0.11, skin, sweep=0.55,
                z0=FZ + 300.0)
    bkit.move(fin, -3100.0, 0.0, 0.0)
    _watertight(fin)
    tail = C.tailplane("PropPlaneTailplane", -3200.0, FZ + 300.0, 1650.0, 1000.0,
                       700.0, 0.10, skin, sweep=0.40)
    _watertight(tail)
    bkit.rounded_box("PropPlaneHorizontalFinFillet", 1200.0, 120.0, 700.0,
                     r=60.0, segments=2, centre=(-3150.0, 0.0, FZ + 300.0),
                     mat=skin)

    # fixed tricycle gear: two mains in fairings, a nose wheel, a tailwheel
    for i, (x, y) in enumerate(((300.0, 900.0), (300.0, -900.0))):
        C.strut("PropPlaneGearLeg%d" % i, (x, y, FZ - 300.0), (x, y * 0.8, 340.0),
                55.0, steel, 10)
        bkit.cylinder("PropPlaneWheelF%d" % i, SPEC["wheel_diameter"] / 2.0,
                      180.0, segments=32, axis="Y",
                      centre=(x, y, SPEC["wheel_diameter"] / 2.0), mat=rubber)
        pant = bkit.rounded_box("PropPlaneWheelPant%d" % i, 1250.0, 420.0, 700.0,
                                r=330.0, segments=3,
                                centre=(x + 80.0, y,
                                        SPEC["wheel_diameter"] / 2.0),
                                mat=cowl)
        pant.name = "PropPlaneWheelPant%d" % i
    bkit.rounded_box("PropPlaneNosePant", 1500.0, 400.0, 620.0, r=300.0,
                     segments=3,
                     centre=(3150.0, 0.0, SPEC["wheel_diameter"] / 2.0),
                     mat=cowl)
    bkit.cylinder("PropPlaneWheelN", SPEC["wheel_diameter"] / 2.0, 160.0,
                  segments=28, axis="Y",
                  centre=(3150.0, 0.0, SPEC["wheel_diameter"] / 2.0),
                  mat=rubber)
    bkit.rounded_box("PropPlaneTailwheel", 500.0, 160.0, 300.0, r=140.0,
                     segments=2, centre=(-3850.0, 0.0, 250.0), mat=cowl)
    bkit.recalc(fus)

    return dict(spec=SPEC, parts=18)
