"""
kite -- a 900 mm flat diamond kite with a real spar cross and a bowed tail.

A kite is a single membrane, and the membrane is what the eye reads: four
triangular panels in alternating saturated colour over a flat diamond 900 mm
on the long diagonal. The outline is extruded once per panel, so the sail is
a set of real closed solids with real thickness -- a zero-thickness plane is
not a sail anybody could hold.

Three things carry it beyond "a coloured diamond":

  * the SPAR, modelled as real sticks. The spine is a straight tapered rod;
    the cross spar is BOWED forward, built as a swept rectangular section
    along an arc rather than a flat bar, because a flat bar is the
    unstrung-kite look.
  * the BRIDLE, the two lines from nose and tail meeting on the spine above
    the cross. That triangle is what holds a kite at its flying angle, and its
    absence is exactly why a sail-plus-spar model looks like a poster.
  * the TAIL, a real bowed line with bows on it. It is the strongest single
    cue that this is a kite.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
from mathutils import Matrix, Vector
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    span=900.0,             # nose to tail, the long diagonal
    width=620.0,            # the short diagonal, wingtip to wingtip
    sail_thickness=1.2,
    spar_width=9.0,
    spar_thickness=3.0,
    spar_bow=28.0,          # how far the cross spar bows off the flat
    tail_length=760.0,
    tail_bow_count=6,
    bridle_height=26.0,     # above the cross, where the two lines meet
    panel_count=4,
)

SPAN = SPEC["span"]
WIDTH = SPEC["width"]
T = SPEC["sail_thickness"]
SN = SPAN / 2.0
SW = WIDTH / 2.0
SWW = SPEC["spar_width"]
ST = SPEC["spar_thickness"]
BOW = SPEC["spar_bow"]
TAIL_L = SPEC["tail_length"]

PANELS = (
    ((0.0, SN), (SW, 0.0), (0.0, 0.0), "red_paint"),
    ((SW, 0.0), (0.0, -SN), (0.0, 0.0), "yellow_paint"),
    ((0.0, -SN), (-SW, 0.0), (0.0, 0.0), "blue_paint"),
    ((-SW, 0.0), (0.0, SN), (0.0, 0.0), "white_plastic"),
)


def _rod(name, p0, p1, radius, mat, segments=12):
    """A capped cylinder spanning two arbitrary 3D points, in millimetres.

    `bkit.cylinder` only takes X/Y/Z axes, and a bridle line or a tail segment
    points along neither. Building the rod at the origin and then aiming it
    with a track quaternion is the same trick the studio lights use.
    """
    a, b = Vector(bkit.v(*p0)), Vector(bkit.v(*p1))
    d = b - a
    length = d.length
    ob = bkit.cylinder(name, radius, length, segments=segments,
                       centre=(0.0, 0.0, 0.0), mat=mat)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = (a + b) / 2.0
    bpy.context.view_layer.update()
    return ob


def build():
    stick = bkit.pbr("KiteSpar", base=(0.42, 0.26, 0.11), rough=0.42)
    line = bkit.pbr("KiteLine", base=(0.90, 0.88, 0.80), rough=0.80)

    # ---- sail: four triangular prisms, each its own closed solid
    for i, (a, b, c, colour) in enumerate(PANELS):
        panel = bkit.extrude_profile("SailPanel%d" % i, [a, b, c], T,
                                     centre=(0.0, 0.0, T / 2.0), axis="Z",
                                     mat=bkit.preset(colour))
        bkit.recalc(panel)

    # ---- spine: a straight stick down the long diagonal, sitting under the
    # sail so it is visible from the edge and hidden from straight above
    bkit.rounded_box("SparSpine", SWW * 0.6, SPAN + 30.0, ST, r=1.2,
                     segments=2, centre=(0.0, 0.0, -ST / 2.0 - 0.4),
                     mat=stick)

    # ---- cross spar: BOWED forward, as a swept rectangular section along a
    # shallow arc. A flat bar would leave the sail slack and reads wrong.
    n = 24
    sections = []
    for i in range(n + 1):
        t = i / n
        y = -SW + 2.0 * SW * t
        z = BOW * math.sin(math.pi * t) - ST / 2.0 - 0.4
        h = SWW / 2.0
        sections.append([(-h, y, z - ST / 2.0), (h, y, z - ST / 2.0),
                         (h, y, z + ST / 2.0), (-h, y, z + ST / 2.0)])
    cross = bkit.loft("SparCross", sections, closed_loop=True, mat=stick)
    bkit.recalc(cross)

    # ---- bridle: nose line and tail line meeting on the spine above the bow
    tow = (0.0, 0.0, BOW + SPEC["bridle_height"] - ST)
    _rod("BridleNose", (0.0, SN * 0.92, -ST), tow, 1.8, line)
    _rod("BridleTail", (0.0, -SN * 0.92, -ST), tow, 1.8, line)

    # ---- tail: a bowed line off the tail, in real segments, with bows
    def _tail_pt(t):
        return (30.0 * math.sin(math.pi * t * 2.5) * t,
                -SN - TAIL_L * t,
                -3.0 - 16.0 * t * t)

    segs = 12
    for i in range(segs):
        # 2.2 mm line, not 1.0: a 1 mm cord on a 1640 mm kite is sub-pixel at
        # catalog framing and the tail simply is not there
        _rod("Tail%02d" % i, _tail_pt(i / segs), _tail_pt((i + 1) / segs),
             2.2, line, segments=8)
    for k in range(SPEC["tail_bow_count"]):
        t = (k + 0.5) / SPEC["tail_bow_count"]
        p = _tail_pt(t)
        bow = bkit.rounded_box("TailBow%d" % k, 96.0, 54.0, 1.6, r=0.8,
                               segments=1, centre=p,
                               mat=bkit.preset("red_paint"
                                               if k % 2 else "yellow_paint"))
        bow.rotation_euler = (0.0, 0.0, math.radians(20.0 * k))
        bpy.context.view_layer.update()

    # ---- stand the kite nose-up. A kite authored flat in the XY plane with
    # a 760 mm tail is 1640 mm long, so a flat render frames 900 mm of sail
    # inside a 1640 mm bounding box and the sail comes out tiny. Standing it
    # puts the whole span in the frame and the diamond reads from any angle.
    #
    # The rotation is about the WORLD origin, applied as
    # (location, rotation) -> (G @ location, G @ rotation). Rotating the
    # object alone is wrong for the swept rods, whose mesh is built at their
    # own centre and positioned with obj.location -- rotating the object spins
    # each rod about itself instead of about the kite.
    g = Matrix.Rotation(math.radians(90.0), 3, "X")
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        loc = g @ ob.location
        rot = (g @ ob.rotation_euler.to_matrix()).to_euler()
        ob.location = loc
        ob.rotation_euler = rot
    bpy.context.view_layer.update()

    return dict(spec=SPEC, parts=4 + 1 + 1 + 2 + segs + SPEC["tail_bow_count"])


CHECKS = [
    # Each SailPanel is ONE QUARTER of the diamond, so a panel's own bbox is
    # half the span and half the width. The kite is then stood nose-up, which
    # swaps X and Y: the span now reads on bbox_z and the width on bbox_x.
    dict(name="panel_quarter_span", mm=450.0, tol=2.0, how="bbox_z",
         part="SailPanel0"),
    dict(name="panel_quarter_width", mm=310.0, tol=2.0, how="bbox_x",
         part="SailPanel0"),
    dict(name="sail_thickness", mm=1.2, tol=0.4, how="bbox_y", part="SailPanel0"),
    dict(name="cross_spar_reach", mm=620.0, tol=2.0, how="bbox_z",
         part="SparCross"),
    dict(name="spar_width", mm=9.0, tol=0.4, how="bbox_x", part="SparCross"),
    dict(name="spine_length", mm=930.0, tol=2.0, how="bbox_z", part="SparSpine"),
    # the bow plus the spar's own thickness, which is what a bbox can see
    dict(name="cross_spar_bow", mm=31.0, tol=1.5, how="bbox_y",
         part="SparCross"),
    # nose to the end of the tail bows: 900 mm of sail plus 760 mm of tail.
    # The tail is BOWED sideways, so it sits a little forward of the straight
    # line and the span comes out about 16 mm short.
    dict(name="overall_span", mm=1643.5, tol=8.0, how="bbox_z"),
]
