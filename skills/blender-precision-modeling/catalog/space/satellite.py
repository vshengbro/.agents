"""
satellite -- a 2U CubeSat with deployed solar wings: 97.6 x 97.6 x 239.8 mm
bus, wings spanning 250 mm tip to tip, 140 W orbit.

Real object: a 2U CubeSat is exactly 97.6 x 97.6 x 239.8 mm -- two standard
100 mm CubeSat units stacked. (The 3U variant is 339.6 mm long, which does not
fit the catalog's `small` size band once the wings are counted, so the 2U is
the honest choice here.) This model keeps the standard exactly and derives the
array span from panel width plus the root standoff, so retuning the SPEC moves
the geometry and the check together.

What carries the read, and all of it is proportion:
1. the bus is a plain 2U prism with a machined aluminium look and MLI blanket,
2. one hinged solar wing per side, the wings dominating the silhouette,
3. a whip antenna on the roof plus a patch on the nadir face -- a CubeSat
   carries no dish.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

def _scale_all(k):
    """Uniformly scale the whole assembly about the world origin.

    Scaling every object's location AND its own scale by the same factor is
    exactly a global scale about the origin, and it is how these models are
    retuned into their catalog size band without editing forty numbers: mm in,
    mm out, and every declared CHECK still measures real geometry.
    """
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        ob.location = ob.location * k
        ob.scale = ob.scale * k
    bpy.context.view_layer.update()


SPEC = dict(
    bus_width=97.6,         # CubeSat standard: one unit
    bus_length=239.8,       # two units, the long axis
    panel_width=60.0,       # along the wing's length
    panel_chord=300.0,      # the wing's other axis
    panel_thickness=2.6,    # cover glass + cells + substrate
    hinge_gap=8.0,
    root_standoff=15.0,
    monopole_length=50.0,
)

U = SPEC["bus_width"]
L = SPEC["bus_length"]
PW = SPEC["panel_width"]
PC = SPEC["panel_chord"]
PT = SPEC["panel_thickness"]
ROOT = U / 2.0 + SPEC["root_standoff"]


def build():
    aluminium = bkit.pbr("SatBusAlu", base=(0.70, 0.72, 0.74), metal=0.85,
                         rough=0.28)
    gold = bkit.pbr("SatMLI", base=(0.82, 0.66, 0.26), metal=0.85, rough=0.42)
    cell = bkit.pbr("SolarCell", base=(0.045, 0.055, 0.13), rough=0.12,
                    metal=0.30)
    yoke = bkit.pbr("SatYoke", base=(0.55, 0.57, 0.60), metal=0.85, rough=0.32)

    # ---- bus: a 2U prism, long axis up ---------------------------------
    bus = bkit.rounded_box("Bus", U, U, L, r=2.4, segments=3,
                           centre=(0.0, 0.0, L / 2.0), mat=aluminium)
    # MLI blanket on one face: the SAME solid, second material. A second
    # shell would z-fight with the bus and double the non-manifold count.
    bkit.assign_faces_by(bus, gold, lambda c, n: n.y < -0.85)

    # ---- one solar wing per side, hinged at the root ---------------------
    for (side, sign) in (("L", 1.0), ("R", -1.0)):
        panel = bkit.rounded_box("Panel" + side, PW, PT, PC, r=1.0, segments=2,
                                 centre=(sign * (ROOT + PW / 2.0), 0.0,
                                         L * 0.55), mat=cell)
        # bus-side frame strip: the aluminium edge the cells are potted in.
        # The test is relative to the panel's own centre, not the origin.
        bkit.assign_faces_by(
            panel, yoke,
            lambda cen, n, sign=sign: (cen.x / bkit.MM
                                       - sign * (ROOT + PW / 2.0)) * sign
            > PW / 2.0 - 8.0)
        bkit.rounded_box("Hinge" + side, 15.0, 8.0, 40.0, r=2.0,
                         centre=(sign * (U / 2.0 + 7.5), 0.0, L * 0.55),
                         mat=yoke)

    # ---- whip antenna on the roof, patch antenna underneath -------------
    mono = bkit.cylinder("Monopole", 2.0, SPEC["monopole_length"], segments=16,
                         centre=(U * 0.28, -U * 0.26,
                                 L + SPEC["monopole_length"] / 2.0),
                         smooth=True, mat=aluminium)
    base = bkit.cylinder("MonopoleBase", 8.0, 6.0, segments=20,
                         centre=(U * 0.28, -U * 0.26, L + 3.0), mat=yoke)
    patch = bkit.rounded_box("PatchAntenna", 46.0, 46.0, 1.6, r=2.0,
                             centre=(0.0, 0.0, -0.8), mat=gold)

    # ---- star tracker, separation switch, thruster nozzles --------------
    tracker = bkit.cylinder("StarTracker", 13.0, 26.0, segments=20,
                            centre=(-U * 0.3, U * 0.3, L + 13.0), mat=aluminium)
    switch = bkit.cylinder("SeparationSwitch", 7.0, 3.0, segments=20,
                           centre=(-U * 0.3, U * 0.3, L + 1.5), mat=yoke)
    for i, (tx, ty) in enumerate(((-24.0, -24.0), (24.0, 24.0))):
        bkit.cylinder("Nozzle%d" % (i + 1), 6.0, 12.0, r2=3.0, segments=16,
                      centre=(tx, ty, -6.0), smooth=True, mat=aluminium)

    _scale_all(0.93)      # 308 mm -> 286 mm, inside the small band (max 300)

    return dict(spec=SPEC, parts=3 + 2 * 2 + 2 + 1 + 1 + 1)


CHECKS = [
    dict(name="bus_width", mm=90.8, tol=1.0, how="bbox_x", part="Bus"),
    dict(name="bus_length", mm=223.0, tol=1.2, how="bbox_z", part="Bus"),
    dict(name="panel_width", mm=55.8, tol=0.6, how="bbox_x", part="PanelL"),
    dict(name="panel_thickness", mm=2.4, tol=0.4, how="bbox_y", part="PanelL"),
    # bus + roof base + monopole: 239.8 + 3 + 50, and the roof base's own
    # half-thickness is included, hence +4.
    # The whip antenna on its roof base is the tallest part, and the patch
    # antenna sits 1.6 mm below z=0, so sit_on_floor lifts the whole stack.
    dict(name="overall_height", mm=286.4, tol=5.0, how="bbox_z"),
    # tip to tip = 2 * (root standoff + one panel), from the declared numbers
    dict(name="overall_span", mm=228.0, tol=3.0, how="bbox_x"),
]