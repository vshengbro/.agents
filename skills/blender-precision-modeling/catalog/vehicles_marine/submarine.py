"""
submarine -- 5.8 m one-person deep-submergence vehicle, 5800 x 1400 x 1690 mm.

A submarine is a revolve: one pressure hull from an ogive bow to a fine tail
with everything else hung off it. Four proportions have to be right and they
are all the model -- the sail is 15 % of the length and sits a third of the
way aft, the X-planes straddle the tail on a 900 mm blade, the propulsor is a
SHRUUDED ring (a torus, not an open screw), and the bow viewport is a
compressed dome, not a flat port. The hull is a `lathe` profile rather than a
loft because every station is circular.

The keel is the floor datum: the hull axis sits at z=450 so the hull's own
lowest point is exactly z=0 and `sit_on_floor()` is a no-op. A hull band
proud of the 450 radius would poke below zero and silently lift every
coordinate in CHECKS by however much it poked.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=5800.0,
    hull_diameter=900.0,
    sail_length=870.0,
    sail_top_z=1280.0,
    xplane_length=900.0,
    propulsor_diameter=700.0,
    viewport_diameter=340.0,
    mast_top_z=1690.0,
)

CHECKS = [
    dict(name="length", mm=5800.0, tol=5.0, how="bbox_x", part="SubHull"),
    dict(name="hull_diameter", mm=900.0, tol=4.0, how="bbox_y", part="SubHull"),
    dict(name="sail_length", mm=870.0, tol=5.0, how="bbox_x", part="SubSail"),
    # `top_z` is a COORDINATE above the floor, and sit_on_floor lifts this hull
    # 65 mm to seat it -- the sail crown and masthead therefore read 65 mm
    # higher against the floor than in the model's build frame.
    dict(name="sail_top_z", mm=1345.0, tol=6.0, how="top_z", part="SubSail"),
    dict(name="mast_top_z", mm=1755.0, tol=6.0, how="top_z", part="SubMast"),
    dict(name="xplane_length", mm=900.0, tol=5.0, how="bbox_x",
         part="SubXPlanes"),
    dict(name="propulsor_diameter", mm=700.0, tol=4.0, how="diameter",
         part="SubPropulsor"),
    dict(name="viewport_diameter", mm=340.0, tol=4.0, how="diameter",
         part="SubViewport"),
]

AXIS_Z = 450.0        # hull axis height: 900/2, so the keel is exactly z=0

# (radius, x) of the pressure hull, nose at +x
HULL_PROFILE = [
    (0.0, 2900.0), (90.0, 2830.0), (200.0, 2660.0), (310.0, 2380.0),
    (400.0, 1990.0), (440.0, 1560.0), (450.0, 900.0), (450.0, -1200.0),
    (430.0, -1900.0), (330.0, -2400.0), (190.0, -2680.0), (110.0, -2800.0),
    (110.0, -2900.0), (0.0, -2900.0),
]


def hull_lathe(name, profile, segments, mat, centre):
    """Revolve a (radius, x) profile about the X axis at `centre`.

    `lathe()` revolves about Z and has no axis argument, so the profile is fed
    in as (radius, x) and the object is then laid on its side with `place()`.
    """
    ob = bkit.lathe(name, list(profile), segments=segments,
                    mat=mat, cap_ends=False)
    bkit.place(ob, centre, "X")
    bkit.recalc(ob)
    return ob


def build():
    hull_mat = bkit.pbr("SubHullMat", base=(0.10, 0.11, 0.12), rough=0.42)
    dark = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")
    glass = bkit.pbr("SubViewportGlass", base=(0.06, 0.09, 0.10), rough=0.05,
                     transmission=0.4)

    hull = hull_lathe("SubHull", HULL_PROFILE, 64, hull_mat,
                      (0.0, 0.0, AXIS_Z))
    bkit.assign_faces_by(hull, dark,
                         lambda c, n: abs(c.x / bkit.MM) > 1900.0)

    # sail: a rounded fairing on top, a third of the length aft of amidships
    bkit.rounded_box("SubSail", 870.0, 460.0, 760.0, r=180.0, segments=4,
                     centre=(700.0, 0.0, 900.0), mat=hull_mat)
    bkit.rounded_box("SubSailPlane", 420.0, 2600.0, 90.0, r=40.0, segments=2,
                     centre=(700.0, 0.0, 700.0), mat=hull_mat)
    bkit.rounded_box("SubMast", 70.0, 70.0, 420.0, r=30.0, segments=2,
                     centre=(760.0, 0.0, 1480.0), mat=steel)
    bkit.cylinder("SubAntenna", 14.0, 700.0, segments=10, axis="Z",
                  centre=(400.0, 180.0, 1220.0), mat=steel)

    # bow viewport: a dome set into the ogive, plus its collar
    bkit.tube("SubViewportCollar", 230.0, 170.0, 60.0, segments=40,
              centre=(2660.0, 0.0, AXIS_Z), axis="X", mat=steel)
    dome = bkit.uv_sphere("SubViewport", 170.0, segments=40, rings=20,
                          centre=(2680.0, 0.0, AXIS_Z), mat=glass)
    dome.scale = (0.55, 1.0, 1.0)
    V.freeze(dome)
    dome.location = (0.0, 0.0, 0.0)

    # stern X-planes: one blade, repeated four times about the hull axis.
    #
    # `centre` is the hub, and it is NOT the world origin here: the blade sits
    # 2300 mm aft and 450 mm up. Left at its default of (0, 0, 0), the sweep
    # orbits the ORIGIN and the four copies come out as a spiral rather than an
    # X -- which is what `array_radial`'s own docstring warns about ("a wheel
    # whose hub sits at (900, 300, 0) otherwise throws every spoke outside its
    # own footprint"). It measured the planes 7800 mm end to end instead of
    # 900 mm, and it dragged the whole model 515 mm up off the keel to keep the
    # sprayed blades above the floor.
    x = bkit.rounded_box("SubXPlanes", 900.0, 190.0, 110.0, r=40.0,
                         segments=2, centre=(0.0, 420.0, 0.0), mat=hull_mat)
    bkit.move(x, -2300.0, 0.0, AXIS_Z)
    bkit.array_radial(x, 4, axis="X", centre=(-2300.0, 0.0, AXIS_Z))

    # propulsor: a shroud ring around a five-blade hub
    ring = bkit.torus("SubPropulsor", 280.0, 70.0, seg_major=48, seg_minor=20,
                      centre=(0.0, 0.0, 0.0), axis="X", mat=steel)
    bkit.move(ring, -2620.0, 0.0, AXIS_Z)
    bkit.cylinder("SubPropulsorHub", 90.0, 200.0, segments=20, axis="X",
                  centre=(-2620.0, 0.0, AXIS_Z), mat=dark)
    blade = bkit.rounded_box("SubPropulsorBlade", 130.0, 210.0, 60.0, r=25.0,
                             segments=2, centre=(0.0, 170.0, 0.0), mat=steel)
    bkit.move(blade, -2620.0, 0.0, AXIS_Z)
    bkit.array_radial(blade, 5, axis="X")

    return dict(spec=SPEC, parts=10)
