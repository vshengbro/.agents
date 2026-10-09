"""
sailboat -- 4.2 m open daysailer with a 4.0 m luff, 4200 x 1800 x 5900 mm.

A sailboat is a hull plus a triangle, and the triangle is what the render
judges. Two numbers fix it: the masthead is 5900 mm above the keel -- 1.4x the
hull length, which is what a single-masted open boat looks like -- and the
mainsail's foot runs 2600 mm AFT of the mast at 1900 mm above the keel, so the
sail is a right triangle leaning back over the cockpit with a roached leech.
The hull is keel-less (a Laser-class daysailer): hard bilges at a bottom ratio
of 0.72, a transom-hung spade rudder and a transom-hung rudder blade that
reaches the floor, so the boat rests on hull and rudder exactly as it rests on
a cradle.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _vessel as V

SPEC = dict(
    length=4200.0,
    beam=1800.0,
    hull_depth=900.0,
    masthead_z=5900.0,
    sail_luff=4000.0,
    boom_length=2600.0,
    jib_luff=5600.0,
    rudder_span=620.0,
)

CHECKS = [
    dict(name="length", mm=4200.0, tol=4.0, how="bbox_x", part="SailboatHull"),
    dict(name="beam", mm=1800.0, tol=4.0, how="bbox_y", part="SailboatHull"),
    dict(name="hull_depth", mm=900.0, tol=4.0, how="bbox_z",
         part="SailboatHull"),
    dict(name="masthead_z", mm=5900.0, tol=8.0, how="top_z", part="SailMast"),
    dict(name="sail_luff", mm=4000.0, tol=8.0, how="bbox_z",
         part="SailMainsail"),
    dict(name="boom_length", mm=2600.0, tol=6.0, how="bbox_x",
         part="SailBoom"),
    dict(name="rudder_span", mm=620.0, tol=4.0, how="bbox_z",
         part="SailRudder"),
]

# (x, half beam, keel, sheer, bottom ratio)
STATIONS = [
    (-2100.0, 700.0, 380.0, 700.0, 0.80),
    (-1800.0, 830.0, 150.0, 780.0, 0.76),
    (-1000.0, 890.0, 0.0, 850.0, 0.72),
    (0.0, 900.0, 0.0, 900.0, 0.72),
    (900.0, 860.0, 0.0, 860.0, 0.70),
    (1600.0, 700.0, 40.0, 780.0, 0.64),
    (2000.0, 400.0, 190.0, 700.0, 0.58),
    (2100.0, 190.0, 300.0, 660.0, 0.55),
]


def mainsail():
    """Mainsail in mast-local coordinates: luff on +z, foot running aft (-x)."""
    return [(0.0, 0.0), (0.0, 4000.0), (-780.0, 3150.0), (-1550.0, 1900.0),
            (-2150.0, 330.0), (-2600.0, 0.0)]


def jib():
    """Jib relative to its tack at the stemhead: head up the forestay, clew aft."""
    return [(0.0, 0.0), (-2280.0, 5120.0), (-1500.0, 760.0)]


def build():
    hull_mat = bkit.pbr("SailboatHullMat", base=(0.86, 0.87, 0.88), rough=0.16,
                        coat=0.6)
    deck_mat = bkit.pbr("SailboatDeckMat", base=(0.80, 0.78, 0.72), rough=0.40)
    inside = bkit.pbr("SailboatCockpit", base=(0.10, 0.11, 0.13), rough=0.55)
    sail_mat = bkit.pbr("SailCanvas", base=(0.90, 0.89, 0.85), rough=0.65)
    spar = bkit.pbr("SailSpar", base=(0.62, 0.63, 0.65), metal=0.70, rough=0.30)
    steel = bkit.preset("brushed_metal")
    wood = bkit.preset("wood")

    hull = V.hull("SailboatHull", STATIONS, mat=hull_mat, smooth=34.0)
    # cockpit: a box pocket cut down into the afterdeck. The cutter overshoots
    # the deck by 80 mm so it crosses the surface instead of ending flush.
    cut = bkit.rounded_box("_cockpit", 1500.0, 900.0, 500.0, r=40.0,
                           segments=2, centre=(-1250.0, 0.0, 720.0))
    bkit.boolean(hull, cut, "DIFFERENCE")
    bkit.recalc(hull)
    bkit.assign_faces_by(hull, deck_mat, lambda c, n: n.z > 0.55)
    bkit.assign_faces_by(hull, inside,
                         lambda c, n: (c.x / bkit.MM < -400.0 and n.z > 0.3
                                       and c.z / bkit.MM < 860.0))
    bkit.shade_smooth(hull, 34.0)

    bkit.rounded_box("SailRudder", 460.0, 60.0, 620.0, r=28.0, segments=2,
                     centre=(-2070.0, 0.0, 310.0), mat=hull_mat)
    bkit.rounded_box("SailRudderPintle", 90.0, 90.0, 220.0, r=30.0,
                     segments=2, centre=(-2070.0, 0.0, 700.0), mat=steel)
    bkit.rounded_box("SailTiller", 900.0, 50.0, 50.0, r=24.0, segments=2,
                     centre=(-1620.0, 0.0, 800.0), mat=wood)

    bkit.cylinder("SailMast", 70.0, 5200.0, r2=45.0, segments=24, axis="Z",
                  centre=(-300.0, 0.0, 3300.0), mat=spar)
    bkit.rounded_box("SailBoom", 2600.0, 90.0, 110.0, r=45.0, segments=2,
                     centre=(-1600.0, 0.0, 1900.0), mat=spar)
    bkit.rounded_box("SailMastStep", 200.0, 260.0, 240.0, r=40.0, segments=2,
                     centre=(-300.0, 0.0, 860.0), mat=spar)
    bkit.rounded_box("SailGooseneck", 240.0, 160.0, 200.0, r=50.0,
                     segments=2, centre=(-300.0, 0.0, 1880.0), mat=spar)

    bkit.extrude_profile("SailMainsail", mainsail(), 14.0, axis="Y",
                         mat=sail_mat)
    bkit.move(bpy.data.objects["SailMainsail"], -300.0, 0.0, 1900.0)
    bkit.extrude_profile("SailJib", jib(), 12.0, axis="Y", mat=sail_mat)
    bkit.move(bpy.data.objects["SailJib"], 1980.0, 0.0, 780.0)

    # standing rigging: forestay up to the stemhead, two shrouds to the
    # chainplates. Thin, but not zero -- zero-radius struts fail to build.
    V.strut("SailForestay", (1980.0, 0.0, 780.0), (-300.0, 0.0, 5900.0), 8.0,
            steel, 8)
    for i, s in enumerate((1, -1)):
        V.strut("SailShroud%d" % i, (-300.0, 0.0, 5100.0),
                (-150.0, s * 850.0, 860.0), 8.0, steel, 8)
    bkit.rounded_box("SailHikingStrap", 200.0, 40.0, 40.0, r=20.0,
                     segments=2, centre=(-1250.0, 0.0, 880.0), mat=deck_mat)

    return dict(spec=SPEC, parts=16)
