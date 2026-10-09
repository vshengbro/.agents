"""doorstop -- a 130 mm rubber doorstop wedge: the wedge body with a real
tapered profile, the hollow underside that lets it grip a carpet, and the
moulded ribs on the two side faces.

The taper is the model. A doorstop is a triangular prism whose roof rises from
2 mm at the toe to 60 mm at the heel, and the hollow underneath is what makes
it grip -- so the profile is authored as a closed outline with the cavity in
it, not as a solid triangle.

Construction: a closed wedge outline with its underside cavity extruded as one
solid, plus the grip ribs laid out at a pitch derived from the rib count.

Orientation: the toe at -X, the heel at +X, Z up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    length=130.0,
    width=44.0,
    heel_height=62.0,
    toe_height=6.0,
    cavity_height=44.0,
    rib_count=5,
)

L, W = 130.0, 44.0
HEEL, TOE = 62.0, 6.0
CAV = 44.0


def build():
    rubber = bkit.pbr("DoorstopRubber", base=(0.045, 0.045, 0.05), rough=0.78)
    grip = bkit.pbr("DoorstopGrip", base=(0.10, 0.10, 0.11), rough=0.70)

    # ---- the wedge outline in the X-Z plane, then extruded across the width.
    # The cavity is part of the outline, so the grip is one closed solid.
    x0, x1 = -L / 2.0, L / 2.0
    roof = [(x0, 0.0), (x0 + 14.0, TOE * 0.45), (x1, HEEL),
            (x1, 0.0), (x1 - 26.0, 0.0)]
    cav = [(x1 - 26.0, 0.0), (x1 - 26.0, CAV), (x0 + 6.0, 3.0), (x0, 3.0)]
    poly = roof + cav
    wedge = bkit.extrude_profile("Wedge", poly, W, centre=(0.0, 0.0, 0.0),
                                axis="Y", mat=rubber)
    F.orient_outward(wedge)

    # ---- the moulded ribs: a computed row down each side face, the pitch
    # derived from the rib count so no two share a station
    n = SPEC["rib_count"]
    pitch = (L - 24.0) / (n - 1)
    for i in range(n):
        x = -L / 2.0 + 12.0 + i * pitch
        # rib height follows the wedge's own taper
        t = (x + L / 2.0) / L
        h = TOE + (HEEL - TOE) * t
        for side, sy in (("L", 1.0), ("R", -1.0)):
            bkit.rounded_box("Rib%s%d" % (side, i), 3.0, 1.6,
                             max(2.0, h * 0.55), r=0.5, segments=2,
                             centre=(x, sy * (W / 2.0 - 0.4), h * 0.42),
                             mat=grip)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="length", mm=130.0, tol=1.0, how="bbox_x", part="Wedge"),
    dict(name="width", mm=44.0, tol=1.0, how="bbox_y", part="Wedge"),
    dict(name="heel_height", mm=62.0, tol=1.5, how="bbox_z", part="Wedge"),
    dict(name="overall_height", mm=62.0, tol=2.0, how="bbox_z"),
    dict(name="overall_length", mm=130.0, tol=1.5, how="bbox_x"),
]