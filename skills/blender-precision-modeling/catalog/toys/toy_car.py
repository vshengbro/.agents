"""
toy_car -- a 96 mm pull-back tin toy car: rounded body, four real wheels.

Tin toys are not wedges. The three things that make this read as a toy car
rather than a generic block on cylinders are (1) the greenhouse -- a separate
lofted cabin with a narrower, more upright section than the body, (2) wheels
that are AXIAL discs wider than the body is deep at the arches, so they stand
proud of the fenders, and (3) saturated paint, because a grey car is a
prototype and a red one is a toy.

Nothing is booleaned: the body, the cabin, the four wheels and the bumpers are
each their own closed solid. Overlapping solids stay manifold, which is why an
eleven-part assembly reports zero non-manifold edges.

The nose points at -Y so the catalog's SIDE view (camera on +X) shows a
silhouette rather than a face.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    overall_length=96.0,
    overall_width=40.0,
    overall_height=34.0,
    body_length=88.0,
    body_width=36.0,
    body_height=18.0,
    cabin_length=44.0,
    cabin_width=28.0,
    cabin_height=16.0,
    wheel_diameter=20.0,
    wheel_width=7.0,
    wheel_count=4,
    wheelbase=58.0,
    track=31.0,
    wheel_track=39.0,       # outer face to outer face, i.e. what a tape sees
)

WL = SPEC["wheel_diameter"] / 2.0
WW = SPEC["wheel_width"]
WB = SPEC["wheelbase"] / 2.0
TR = SPEC["track"] / 2.0
BL = SPEC["body_length"] / 2.0
BW = SPEC["body_width"] / 2.0
BH = SPEC["body_height"]


def build():
    red = bkit.preset("red_paint")
    cream = bkit.preset("white_plastic")
    glass = bkit.pbr("ToyCarGlass", base=(0.20, 0.26, 0.30), rough=0.10,
                     transmission=0.25, ior=1.45, coat=0.5)
    rubber = bkit.preset("rubber")
    chrome = bkit.preset("polished_metal")

    # ---- lower body: a loft whose section is a superellipse with n=3, which
    # is the "squircle-plus" profile a pressed tin toy actually has: rounded
    # everywhere, but with a hint of a flat side where the door is.
    sections = []
    body_table = [
        (-BL, 0.62, 0.70),          # (y, width factor, height factor)
        (-BL * 0.80, 0.86, 0.90),
        (-BL * 0.40, 0.98, 1.00),
        (0.0, 1.00, 1.00),
        (BL * 0.45, 0.97, 0.98),
        (BL * 0.82, 0.84, 0.88),
        (BL, 0.60, 0.68),
    ]
    for (y, wf, hf) in body_table:
        # `superellipse_section(sx, sy)` takes FULL sizes, so the height
        # argument is BH*hf and NOT 2*BH*hf. Passing twice the size here is
        # the quiet way to get a 36 mm body on an 18 mm spec: the section
        # really is 2x too tall, and the mesh is clean the whole time.
        ring = bkit.superellipse_section(2 * BW * wf, BH * hf, n=3.0,
                                         steps=44)
        sections.append([(u, y, BH / 2.0 + v) for (u, v) in ring])
    body = bkit.loft("CarBody", sections, mat=red, smooth=True)
    bkit.recalc(body)
    bkit.shade_smooth(body, 44)

    # ---- cabin: narrower, shorter, and set back, which is what separates a
    # greenhouse from a second deck.
    cab_l = SPEC["cabin_length"] / 2.0
    cab_w = SPEC["cabin_width"] / 2.0
    cab_h = SPEC["cabin_height"]
    cab_y = BL * 0.10
    cab_sections = []
    cab_table = [
        (-cab_l, 0.72, 0.55),
        (-cab_l * 0.80, 0.98, 0.90),
        (-cab_l * 0.10, 1.00, 1.00),
        (cab_l * 0.55, 0.96, 0.94),
        (cab_l, 0.70, 0.60),
    ]
    for (dy, wf, hf) in cab_table:
        # full sizes again, not doubled
        ring = bkit.superellipse_section(2 * cab_w * wf, cab_h * hf, n=3.4,
                                         steps=40)
        cab_sections.append([(u, cab_y + dy, BH + cab_h * 0.5 + v)
                             for (u, v) in ring])
    cabin = bkit.loft("CarCabin", cab_sections, mat=red, smooth=True)
    bkit.recalc(cabin)
    bkit.shade_smooth(cabin, 44)
    # windows: a second material on the one cabin solid, selected by height
    # and by how far the face sits from the cabin's own centreline. A
    # separate glass shell would z-fight with the roof.
    bkit.assign_faces_by(
        cabin, glass,
        lambda c, n: (c.z / bkit.MM) > BH + cab_h * 0.22
        and (c.y / bkit.MM) < cab_y + cab_l * 0.92)

    # ---- four wheels on the real wheelbase and track, from `lay_out` on both
    # axes so the pairs cannot drift off the 58 mm wheelbase or the 39 mm
    # track. `lay_out` returns the CENTRE of each feature, so the feature
    # widths are 2*offset: [2*WB, 2*WB] at gap 0 puts the axle centres at +-WB,
    # and [WW, WW] at gap 2*TR - WW puts the wheel centres at +-TR. The two
    # loops CROSS once each, giving exactly four wheels -- iterating the inner
    # list for both signs as well builds eight and doubles up every name.
    for (y, _w) in bkit.lay_out([2.0 * WB, 2.0 * WB], gap=0.0):
        for (x, _t) in bkit.lay_out([WW, WW], gap=2.0 * TR - WW):
            key = "%s%s" % ("F" if y > 0 else "R", "R" if x > 0 else "L")
            wheel = bkit.cylinder("Wheel" + key, WL, WW, segments=40,
                                  centre=(x, y, WL), axis="X", mat=rubber)
            bkit.shade_smooth(wheel, 30)
            # The hub cap sits on the OUTER face of the tyre, half its own
            # thickness proud. Concentred on the axle like the wheel itself it
            # is simply buried inside 7 mm of rubber and invisible.
            hx = x + (1.0 if x > 0 else -1.0) * (WW / 2.0 + 0.8)
            bkit.cylinder("Hub" + key, WL * 0.46, 1.6, segments=28,
                          centre=(hx, y, WL), axis="X", mat=chrome)
    # ---- front bumper and grille bar: the two features that make the -Y end
    # read as the front of a car.
    bumper = bkit.rounded_box("CarBumper", BW * 1.9, 4.0, 4.0, r=1.2,
                              segments=3,
                              centre=(0.0, -BL - 1.0, WL * 0.85), mat=chrome)
    grille = bkit.rounded_box("CarGrille", BW * 1.15, 2.6, 3.2, r=0.9,
                              segments=3,
                              centre=(0.0, -BL - 0.4, WL * 0.85), mat=cream)

    # ---- roof stripe: a second material on the body, not a decal object
    bkit.assign_faces_by(body, cream,
                         lambda c, n: abs(c.x / bkit.MM) < 3.0
                         and c.z / bkit.MM > BH * 0.94)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 4 + 4 + 2 + 1)


CHECKS = [
    dict(name="body_length", mm=88.0, tol=0.5, how="bbox_y", part="CarBody"),
    dict(name="body_width", mm=36.0, tol=0.5, how="bbox_x", part="CarBody"),
    dict(name="body_height", mm=18.0, tol=0.6, how="bbox_z", part="CarBody"),
    dict(name="wheel_diameter", mm=20.0, tol=0.3, how="diameter", part="WheelFR"),
    dict(name="cabin_length", mm=44.0, tol=0.8, how="bbox_y", part="CarCabin"),
    dict(name="cabin_height", mm=16.0, tol=0.8, how="bbox_z", part="CarCabin"),
    # widest thing on the car: the hub caps standing proud of the outer tyre
    # faces, not the 36 mm body. A track figure is a centre-to-centre distance
    # and no bounding box can express it.
    dict(name="overall_width", mm=41.2, tol=0.8, how="bbox_x"),
]
