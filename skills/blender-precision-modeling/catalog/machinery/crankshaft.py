"""
crankshaft -- two-throw crankshaft: 3 main journals, 2 crank pins, 4 webs.

Proportion is the whole point. The nine axial features (main, web, pin, web,
main, web, pin, web, main) are laid out by bkit.lay_out with a NEGATIVE gap,
which is deliberate: a 2 mm overlap makes every union a clean interpenetrating
solid, while a zero gap puts two cylinders' end caps on the same plane and the
EXACT solver is then free to delete the whole body.

Each web is a real crank web -- a circle at the journal axis, a circle at the
pin axis, and a slightly larger counterweight circle on the opposite side, all
at the same axial station -- so the two throws point 180 deg apart.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    main_diameter=50.0,
    pin_diameter=42.0,
    throw=45.0,               # offset of the pin axis from the journal axis
    main_length=38.0,
    web_thickness=24.0,
    pin_length=42.0,
    throws=2,
    webs=4,
    overall_length=293.0,
    throw_envelope=140.0,
    flange_diameter=76.0,
)


def build():
    r_main = SPEC["main_diameter"] / 2.0
    r_pin = SPEC["pin_diameter"] / 2.0
    throw = SPEC["throw"]

    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- axial layout, overlapped ---------------------------------------
    widths = [SPEC["main_length"], SPEC["web_thickness"], SPEC["pin_length"],
              SPEC["web_thickness"], SPEC["main_length"], SPEC["web_thickness"],
              SPEC["pin_length"], SPEC["web_thickness"], SPEC["main_length"]]
    slots = bkit.lay_out(widths, gap=-2.0)
    x_main1 = slots[0][0]
    x_web = [slots[1][0], slots[3][0], slots[5][0], slots[7][0]]
    x_pin = [slots[2][0], slots[6][0]]
    x_main = [slots[0][0], slots[4][0], slots[8][0]]

    # The throws point along +/-Z, not +/-Y. The studio's side elevation looks
    # down -Y, so a crank whose throws are in Y foreshortens into a row of
    # beads; with them in Z the side view is the classic crankshaft silhouette
    # -- journals as a horizontal line, throws standing up and down.
    # throw 1 points +Z, throw 2 points -Z: 180 deg apart
    pin_off = [throw, -throw]
    # which throw each web belongs to
    web_throw = [0, 0, 1, 1]

    shaft = bkit.cylinder("Main1", r_main, widths[0], segments=72, axis="X",
                          centre=(x_main[0], 0.0, 0.0), mat=steel)
    for i, x in enumerate(x_main[1:]):
        j = bkit.cylinder("Main%d" % (i + 2), r_main, widths[(i + 1) * 4],
                          segments=72, axis="X", centre=(x, 0.0, 0.0), mat=steel)
        bkit.boolean(shaft, j, "UNION")

    for i, x in enumerate(x_pin):
        p = bkit.cylinder("Pin%d" % (i + 1), r_pin, SPEC["pin_length"],
                          segments=72, axis="X",
                          centre=(x, 0.0, pin_off[i]), mat=steel)
        bkit.boolean(shaft, p, "UNION")

    for i, x in enumerate(x_web):
        t = web_throw[i]
        s = 1.0 if t == 0 else -1.0
        # journal-end circle
        hub = bkit.cylinder("WebHub%d" % (i + 1), 30.0, SPEC["web_thickness"],
                            segments=72, axis="X", centre=(x, 0.0, 0.0), mat=dark)
        # pin-end circle
        lobe = bkit.cylinder("WebLobe%d" % (i + 1), 23.0, SPEC["web_thickness"],
                             segments=72, axis="X",
                             centre=(x, 0.0, s * throw), mat=dark)
        # counterweight on the opposite side
        cw = bkit.cylinder("WebCW%d" % (i + 1), 25.0, SPEC["web_thickness"],
                           segments=72, axis="X",
                           centre=(x, 0.0, -s * throw), mat=dark)
        bkit.boolean(shaft, hub, "UNION")
        bkit.boolean(shaft, lobe, "UNION")
        bkit.boolean(shaft, cw, "UNION")

    # ---- end flanges ----------------------------------------------------
    f1 = bkit.cylinder("FlangeA", SPEC["flange_diameter"] / 2.0, 14.0, segments=72,
                       axis="X", centre=(x_main[0] - widths[0] / 2.0 - 4.0, 0, 0),
                       mat=steel)
    bkit.boolean(shaft, f1, "UNION")
    f2 = bkit.cylinder("FlangeB", 30.0, 14.0, segments=72, axis="X",
                       centre=(x_main[2] + widths[8] / 2.0 - 3.0, 0, 0), mat=steel)
    bkit.boolean(shaft, f2, "UNION")

    # keyways in the two outer journals, for flywheel and pulley
    for x in (x_main[0], x_main[2]):
        key = bkit.box("Keyway", 12.0, 6.0, widths[0] * 2.0,
                       centre=(x, 0.0, r_main - 3.0))
        bkit.boolean(shaft, key, "DIFFERENCE")

    bkit.recalc(shaft)
    shaft.name = "Crankshaft"
    bkit.assign_faces_by(shaft, dark, lambda c, n: abs(abs(c.z) - throw) < 4.0)
    # Lay the shaft down along Y. The studio's "side" elevation sits at az=2,
    # which is almost exactly +X -- a crankshaft built along X is therefore
    # photographed end-on and its throws foreshorten into a stack of circles.
    # The rotation has to be composed in WORLD space: this object still carries
    # the axis="X" rotation that place() gave it, so overwriting rotation_euler
    # would tip the shaft upright instead of turning it.
    bkit.move(shaft, 0.0, 0.0, 0.0)          # flush the cached matrix_world
    shaft.matrix_world = (bkit.Matrix.Rotation(math.radians(90.0), 4, "Z")
                          @ shaft.matrix_world)
    return dict(spec=SPEC, parts=1, throws=SPEC["throws"], webs=SPEC["webs"])


CHECKS = [
    dict(name="overall_length", mm=293.0, tol=0.8, how="bbox_y", part="Crankshaft"),
    dict(name="throw_envelope", mm=140.0, tol=0.8, how="bbox_z", part="Crankshaft"),
    dict(name="web_envelope", mm=76.0, tol=0.8, how="bbox_x", part="Crankshaft"),
]
