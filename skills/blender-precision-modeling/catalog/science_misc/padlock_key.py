"""padlock_key -- a 90 mm brass padlock key: the bow with its bow hole, the
blade, and the BITTING -- the real cut pattern along the blade's edge, with
the shoulder and the tip.

The bitting is the model. A key with a plain rectangular blade is a strip of
brass; a key's identity is its cut pattern, and here the cuts are generated
from a real ward profile -- a depth table per station -- so the blade edge is
a stepped silhouette rather than a box.

Construction: a lathed bow with a bore through it, an extruded blade whose
edge follows the ward depth table, and a shoulder. The bow's bore is cut with
`bkit.bore`, which deliberately uses a different segment count from the host
so the two surfaces never share a facet.

Orientation: the bow at -Y, the blade running toward +Y, Z up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_length=86.0,
    bow_diameter=26.0,
    bow_hole_diameter=11.0,
    blade_width=9.0,
    blade_thickness=2.4,
    ward_count=7,
)

BOW_R = 13.0
BOW_Y = -30.0
BLADE_L = 47.0
# The ward profile: one cut DEPTH per station along the blade, in mm. This
# table IS the key; the blade's edge outline is generated from it, so the
# bitting can never be a plain rectangle.
WARD_DEPTH = [0.0, 2.2, 1.1, 3.4, 1.8, 0.6, 2.8, 1.4]
WARD_PITCH = 5.2


def build():
    brass = bkit.pbr("KeyBrass", base=(0.82, 0.66, 0.28), metal=0.85,
                     rough=0.24)
    dark = bkit.pbr("KeyDark", base=(0.42, 0.33, 0.14), metal=0.85,
                    rough=0.38)

    # ---- the bow: a flat paddle, built as a lathe whose AXIS is the key's
    # thickness, so the 26 mm diameter lies in the X-Y plane and the bow lies
    # flat on the bench like the blade
    bow = bkit.lathe("Bow",
                     [(0.0, -2.6), (7.0, -2.5), (11.5, -1.8), (13.0, 0.0),
                      (11.5, 1.8), (7.0, 2.5), (0.0, 2.6)],
                     segments=64, centre=(0.0, BOW_Y, 2.6), mat=brass)

    # ---- the bow hole, cut with a deliberately different segment count from
    # the host lathe so the two surfaces never share a facet
    bkit.bore(bow, radius=5.5, depth=20.0, centre=(0.0, BOW_Y, 2.6),
              axis="Z", host_segments=64)

    # ---- the blade outline, generated from the ward table
    half_w = 4.5
    edge = [(-half_w, -6.0), (-half_w, BLADE_L)]
    for i, d in enumerate(WARD_DEPTH):
        y = 2.0 + i * WARD_PITCH
        if y > BLADE_L:
            break
        edge.append((half_w - d * 0.62, y))
        edge.append((half_w, y - 1.4))
    edge.append((half_w, -6.0))
    blade = bkit.extrude_profile("Blade", edge, 2.4, centre=(0.0, 0.0, 0.0),
                                 axis="Z", mat=brass)
    # The outline is authored with its length on +Y in the XY plane and the
    # extrusion along Z, which is already the layout the key wants -- it only
    # needs re-seating along Y. Swapping the axes here puts the blade's
    # LENGTH in Z and its thickness in Y, which is the 53 x 2.4 x 9 result.
    for v in blade.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        # mesh vertices are METRES: adding the millimetre offset BOW_Y + 26
        # unconverted puts the blade at -4 METRES, i.e. 4000 mm away
        v.co = (x, y + bkit.u(BOW_Y + 26.0), z)
    blade.data.update()
    bkit.recalc(blade)

    # ---- the shoulder between bow and blade
    bkit.rounded_box("Shoulder", 11.0, 8.0, 2.4, r=0.8, segments=3,
                     centre=(0.0, BOW_Y + 24.0, 1.2), mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_length", mm=86.0, tol=3.0, how="bbox_y"),
    dict(name="bow_diameter", mm=26.0, tol=1.0, how="bbox_y", part="Bow"),
    # A BORE IS NOT A BOUNDING-BOX MEASUREMENT: `how="diameter"` on the bow
    # returns the outer 26 mm, never the 11 mm hole. So the bore is declared
    # in the SPEC and cut with bkit.bore(), and CHECKS measures what a bbox can
    # actually prove.
    dict(name="bow_thickness", mm=5.0, tol=0.4, how="bbox_z", part="Bow"),
    dict(name="blade_width", mm=9.0, tol=0.6, how="bbox_x", part="Blade"),
    dict(name="blade_thickness", mm=2.4, tol=0.3, how="bbox_z", part="Blade"),
    dict(name="blade_length", mm=53.0, tol=2.0, how="bbox_y", part="Blade"),
]