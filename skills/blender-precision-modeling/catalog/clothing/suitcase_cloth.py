"""
suitcase_cloth -- the catalog's "Holdall": a 550 x 260 x 280 mm soft holdall.

Same family as the tote -- a soft bag with a belly and webbing handles -- but a
weekender is a closed bag with a zip all the way round, and that is the
difference the model has to show. So the zip is a real part running the whole
top seam, with two sliders and pull tabs, rather than the open mouth a tote has.

The belly is the point of the loft: a bag that is the same width top and bottom
reads as a box with soft edges.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=550.0,
    depth=260.0,
    height=280.0,
    belly_extra=24.0,
    handle_drop=95.0,
    zip_length=520.0,
    zip_sliders=2,
    panel_thickness=6.0,
)

# sec() takes a FULL section width, so W and D are the bag's own dimensions
# less the belly that the widest section adds -- not half of them.
H = SPEC["height"]
BE = SPEC["belly_extra"]
W = SPEC["length"] - BE
D = SPEC["depth"] - BE * 0.5
STEPS = 56
INNER = 37


def sec(sx, sy, r, z, per_corner=6):
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=per_corner)]


def shell(outer, cavity):
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


def build():
    canvas = bkit.pbr("HoldallCanvas", base=(0.325, 0.375, 0.330), rough=0.90)
    canvas_end = bkit.pbr("HoldallEndPanel", base=(0.255, 0.300, 0.262),
                          rough=0.91)
    webbing = bkit.pbr("HoldallWebbing", base=(0.130, 0.160, 0.145), rough=0.86)
    zip_metal = bkit.preset("brushed_metal")

    # ---- body: lofted with a real belly, and hollowed so the zip has a wall
    body = shell(
        bkit.loft("HoldallBody", [
            sec(W * 0.82, D * 0.80, 26.0, 0.0),
            sec(W * 0.95, D * 0.93, 40.0, H * 0.26),
            sec(W + BE, D + BE * 0.5, 58.0, H * 0.58),
            sec(W + BE * 0.85, D + BE * 0.4, 52.0, H * 0.85),
            sec(W, D, 34.0, H),
        ], smooth=True, mat=canvas),
        bkit.loft("_HoldallBody_cavity", [
            sec(W * 0.70, D * 0.66, 22.0, 8.0, per_corner=6),
            sec(W * 0.82, D * 0.78, 34.0, H * 0.28, per_corner=6),
            sec(W + BE - 12.0, D + BE * 0.5 - 12.0, 48.0, H * 0.60,
                per_corner=6),
            sec(W + BE * 0.85 - 12.0, D + BE * 0.4 - 12.0, 42.0, H * 0.88,
                per_corner=6),
            sec(W - 12.0, D - 12.0, 26.0, H + 70.0, per_corner=6),
        ]),
    )
    # Reinforced end panels, as a material on the real shell.
    bkit.assign_faces_by(
        body, canvas_end,
        lambda c, n: abs(c.x / bkit.MM) > W * 0.72,
    )

    # ---- zip along the whole top seam: tape, teeth line, two sliders ------
    bkit.rounded_box("HoldallZipTape", SPEC["zip_length"], 30.0, 14.0, r=6.0,
                     segments=3, centre=(0.0, 0.0, H + 4.0), mat=webbing)
    bkit.rounded_box("HoldallZipTeeth", SPEC["zip_length"] - 20.0, 10.0, 9.0,
                     r=3.0, segments=3, centre=(0.0, 0.0, H + 12.0),
                     mat=zip_metal)
    # Two sliders, spaced along the zip rather than hand-placed.
    for i, (x, _w) in enumerate(bkit.lay_out([34.0, 34.0], gap=150.0)):
        bkit.rounded_box("HoldallZipSlider%d" % (i + 1), _w, 26.0, 20.0,
                         r=6.0, segments=3, centre=(x, 0.0, H + 20.0),
                         mat=zip_metal)
        bkit.rounded_box("HoldallZipPull%d" % (i + 1), 12.0, 6.0, 44.0,
                         r=3.0, segments=3, centre=(x, 0.0, H + 42.0),
                         mat=zip_metal)

    # ---- two webbing grab handles on the top face -------------------------
    rise = SPEC["handle_drop"]
    a = 150.0
    k = (a * a - rise * rise) / (2.0 * rise)
    for i, sx in enumerate((1.0, -1.0)):
        bkit.arc_torus("HoldallHandle%d" % (i + 1), rise + k, 11.0,
                       math.degrees(math.atan2(k, a)),
                       180.0 - math.degrees(math.atan2(k, a)),
                       centre=(sx * a, 0.0, H + 16.0 - k), plane="XZ",
                       seg_major=36, mat=webbing, caps=True)
        # anchor patches where the handle meets the bag
        for j, dx in enumerate((-1.0, 1.0)):
            bkit.rounded_box("HoldallHandlePatch%d%d" % (i + 1, j + 1),
                             34.0, 22.0, 48.0, r=6.0, segments=3,
                             centre=(sx * a + dx * 20.0, 0.0, H + 6.0),
                             mat=webbing)

    # ---- end grab handles, a vertical arc on each end panel ---------------
    # W is the bag's FULL length less the belly, so the end panel sits at half
    # of it. Placing the handle at W-6 put it 257 mm outboard of the bag it is
    # supposed to be attached to.
    end_x = (W + BE) / 2.0
    for i, sx in enumerate((1.0, -1.0)):
        bkit.arc_torus("HoldallEndHandle%d" % (i + 1), 78.0, 10.0, -80.0,
                       80.0, centre=(sx * (end_x - 6.0), 0.0, H * 0.52),
                       plane="YZ", seg_major=32, mat=webbing, caps=True)

    # ---- a shoulder strap, slung between the two end panels ----------
    # Struck as a half circle of radius = half the bag length from a centre on
    # the end panels' own centre line, so the two tips land ON the panels at
    # z=150 and the crown arcs 145 mm over the zip. Two earlier versions left
    # the strap in mid air: R=230 centred at z=410 (above the bag), and then
    # this arc placed at y=-D+10, which is 114 mm BEHIND the bag's own back
    # face at -D/2 -- so the tips floated clear of the panels they hang from.
    half_len = (W + BE) / 2.0
    bkit.arc_torus("HoldallShoulderStrap", half_len, 11.0, 0.0, 180.0,
                   centre=(0.0, -D / 2.0 + 15.0, 150.0), plane="XZ",
                   seg_major=44, mat=webbing, caps=True)

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="length", mm=550.0, tol=3.0, how="bbox_x", part="HoldallBody"),
    dict(name="depth", mm=260.0, tol=3.0, how="bbox_y", part="HoldallBody"),
    dict(name="height", mm=280.0, tol=3.0, how="bbox_z", part="HoldallBody"),
    dict(name="zip_length", mm=520.0, tol=2.0, how="bbox_x",
         part="HoldallZipTape"),
    # The bag's own envelope is the body; a whole-assembly bbox would additionally
    # report the carried shoulder strap's rise and the handle arches, neither of
    # which is the case's dimensions. Body and zip are checked above.
    dict(name="bag_height", mm=280.0, tol=3.0, how="bbox_z",
         part="HoldallBody"),
]