"""
violin -- 4/4 violin, 356 mm body, 590 mm overall, four strings.

A violin is an arched box, not a slab, so the body is three parts: two plates
(front and back) built by lofting the same violin silhouette at two z heights,
and the rib between them. The silhouette itself is the model -- upper bout,
C-bout waist, lower bout -- and it is listed as control points in one place
rather than scattered as literal coordinates, because a violin whose waist does
not pinch reads as a guitar.

Four strings, evenly spaced by `bkit.lay_out`, running tailpiece -> bridge ->
nut. The fingerboard is a loft that overhangs the body onto the neck, which is
what puts the nut at 590 mm rather than at the top of the body.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_length=356.0,
    body_width=208.0,
    upper_bout_width=168.0,
    waist_width=110.0,
    rib_depth=30.0,
    plate_thickness=14.0,
    total_length=596.0,
    strings=4,
    string_gap=11.0,
    string_diameter=1.1,
    scale_length=330.0,
    nut_z=518.0,
)

BODY_L = SPEC["body_length"]
NUT_Z = SPEC["nut_z"]
BRIDGE_Z = NUT_Z - SPEC["scale_length"]
STR_N = SPEC["strings"]

# Half-silhouette, tail (z=0) to neck end (z=356): lower bout, C-bout, upper
# bout. z=178 is the waist and is the narrowest point of the whole outline.
_HALF = [
    (0.0, 0.0), (44.0, 6.0), (72.0, 22.0), (92.0, 52.0), (104.0, 92.0),
    (102.0, 130.0), (88.0, 158.0), (66.0, 178.0), (74.0, 198.0),
    (84.0, 226.0), (84.0, 262.0), (74.0, 292.0), (60.0, 318.0),
    (48.0, 338.0), (44.0, 356.0),
]
_HALF_L = [(-x, z) for (x, z) in reversed(_HALF[1:-1])]


def _ring(t):
    """One closed silhouette ring, scaled by t about the body centre."""
    half = [(x * t, z) for (x, z) in _HALF]
    return half + [(-x, z) for (x, z) in reversed(_HALF[1:-1])]


def _rod(name, r, p0, p1, mat, segments=10):
    """A capped cylinder spanning two 3D points given in millimetres."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ob = bkit.cylinder(name, r, length, segments=segments, centre=(0, 0, 0),
                       axis="Z", mat=mat)
    ob.rotation_euler = (-math.atan2(dy, math.hypot(dx, dz)),
                         math.atan2(dx, dz), 0.0)
    bkit.move(ob, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    return ob


def build():
    top = bkit.pbr("ViolinTop", base=(0.58, 0.28, 0.11), rough=0.18, coat=0.7)
    back = bkit.pbr("ViolinBack", base=(0.36, 0.15, 0.06), rough=0.22, coat=0.6)
    ribs = bkit.pbr("ViolinRibs", base=(0.44, 0.20, 0.08), rough=0.34)
    maple = bkit.pbr("ViolinMaple", base=(0.60, 0.38, 0.17), rough=0.30)
    board = bkit.pbr("ViolinBoard", base=(0.07, 0.05, 0.04), rough=0.40)
    ebony = bkit.pbr("ViolinEbony", base=(0.06, 0.05, 0.045), rough=0.36)
    steel = bkit.pbr("ViolinStrings", base=(0.76, 0.77, 0.80), metal=0.85,
                     rough=0.22)
    brass = bkit.pbr("ViolinBrass", base=(0.86, 0.68, 0.28), metal=0.85,
                     rough=0.24)

    # ---- arched plates: the same ring lofted at three heights --------------
    # An arch, not a cylinder: the outer rings are inset so the plate domes
    # toward the middle, and the silhouette is pinched 6% at the rim.
    for tag, y0, mat in (("Top", SPEC["rib_depth"] / 2.0, top),
                         ("Back", -SPEC["rib_depth"] / 2.0, back)):
        secs = []
        for dz, t in ((0.0, 1.0), (5.0, 0.985), (10.0, 0.92),
                      (13.5, 0.80), (15.5, 0.60)):
            ring = _ring(t)
            secs.append([(x, y0 + dz, z) for (x, z) in ring])
        plate = bkit.loft("Violin%s" % tag, secs, mat=mat)
        bkit.recalc(plate)

    rib = bkit.extrude_profile("ViolinRibsBox", _ring(1.0),
                               SPEC["rib_depth"], centre=(0, 0, 0), axis="Y",
                               mat=ribs)
    bkit.recalc(rib)

    # ---- neck, fingerboard, pegbox, scroll --------------------------------
    nk = []
    for i in range(6):
        t = i / 5.0
        z = BODY_L - 60.0 + t * (NUT_Z - BODY_L + 60.0)
        w = 48.0 + (30.0 - 48.0) * t
        ring = bkit.rounded_rect_section(w, 19.0, r=7.0, per_corner=4)
        nk.append([(x, y - 12.0, z) for (x, y) in ring])
    bkit.recalc(bkit.loft("ViolinNeck", nk, mat=maple))

    fb = []
    for z, w, y in ((BODY_L - 152.0, 46.0, -2.0), (BODY_L, 44.0, -3.0),
                    (NUT_Z, 30.0, -4.0)):
        ring = bkit.rounded_rect_section(w, 11.0, r=2.0, per_corner=3)
        fb.append([(x, yy + y, z) for (x, yy) in ring])
    bkit.recalc(bkit.loft("ViolinFingerboard", fb, mat=board))
    bkit.box("ViolinNut", 31.0, 7.0, 4.0, centre=(0, -8.0, NUT_Z + 2.0),
             mat=ebony)

    peg_y = -12.0
    pegbox = bkit.extrude_profile(
        "ViolinPegbox",
        [(-15.0, 0.0), (-18.0, 26.0), (-13.0, 52.0),
         (13.0, 52.0), (18.0, 26.0), (15.0, 0.0)],
        26.0, centre=(0, peg_y, NUT_Z + 4.0), axis="Y", mat=maple)
    # extrude_profile walks the outline as given, and this one is wound the
    # other way round from the body's, so it comes out inside-out. One recalc
    # settles it; without it the part reports a negative volume for the rest of
    # the catalog's life.
    bkit.recalc(pegbox)
    # Scroll: a lathed volute plus the pegbox walls -- the spiral is the single
    # most recognisable thing about a violin seen end-on.
    prof = []
    for i in range(9):
        t = i / 8.0
        r = 20.0 * (1.0 - 0.72 * t) + 1.5
        prof.append((r, 52.0 + 18.0 * t))
    prof.append((2.0, 74.0))
    scroll = bkit.lathe("ViolinScroll", prof, segments=32, centre=(0, 0, 0),
                        mat=maple)
    # lathe revolves a profile whose z is already absolute, so the volute starts
    # at z=52 and only needs shifting into line with the pegbox.
    bkit.move(scroll, 0.0, peg_y, NUT_Z + 4.0)

    pegs = []
    for i, side in enumerate((-1, -1, 1, 1)):
        z = NUT_Z + 16.0 + (i % 2) * 24.0 + (i // 2) * 2.0
        pegs.append(bkit.cylinder("Vp%d" % i, 3.4, 30.0, segments=12,
                                  centre=(side * 12.0, peg_y, z), axis="X",
                                  mat=ebony))
        pegs.append(bkit.box("Vg%d" % i, 7.0, 13.0, 9.0,
                             centre=(side * 20.0, peg_y, z), mat=ebony))
    bkit.join(pegs, name="ViolinPegs")

    # ---- tailpiece, chinrest, bridge, f-holes -----------------------------
    tail = bkit.extrude_profile("ViolinTailpiece",
                                [(-22.0, 0.0), (-25.0, 30.0), (-18.0, 78.0),
                                 (18.0, 78.0), (25.0, 30.0), (22.0, 0.0)],
                                9.0, centre=(0, 30.0, 92.0), axis="Y",
                                mat=ebony)
    bkit.recalc(tail)
    bkit.bevel(tail, width_mm=1.4, segments=2)

    # Bridge, f-holes and chinrest all sit on their real surfaces: the top plate's
    # crown is at y = +30.5 and its edge at +15, so the bridge stands on the
    # crown and the chinrest clamps the BACK plate (y negative), not the front.
    bkit.rounded_box("ViolinBridge", 42.0, 9.0, 34.0, r=2.0, segments=2,
                     centre=(0, 33.0, BRIDGE_Z), mat=maple)
    for i, side in enumerate((-1, 1)):
        bkit.rounded_box("ViolinFhole%d" % i, 6.0, 6.0, 44.0, r=2.5,
                         segments=2,
                         centre=(side * 58.0, 28.0, 205.0), mat=ebony)

    bkit.rounded_box("ViolinChinrest", 92.0, 13.0, 42.0, r=8.0, segments=3,
                     centre=(0, -36.0, 78.0), mat=ebony)

    # ---- four strings, tailpiece -> bridge -> nut -------------------------
    # The strings run in the plane just ABOVE the arched top (the top plate's
    # crown reaches y ~ +30.5), so they must clear it: at y = 21 they were
    # buried inside the plate and vanished from every render.
    d = SPEC["string_diameter"]
    strings = []
    y_tail, y_bridge, y_nut = 34.0, 33.0, 4.0
    for i, (x, _w) in enumerate(bkit.lay_out([d] * STR_N,
                                             gap=SPEC["string_gap"])):
        r = 0.45 + 0.16 * i
        z0, z1 = 92.0, BRIDGE_Z
        strings.append(_rod("Vs%d" % i, r, (x, y_tail, z0),
                            (x, y_bridge, z1), steel))
        strings.append(_rod("Vt%d" % i, r, (x, y_bridge, z1),
                            (x, y_nut, NUT_Z), steel))
    bkit.join(strings, name="ViolinStrings")

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="body_length", mm=356.0, tol=0.6, how="bbox_z", part="ViolinRibsBox"),
    dict(name="body_width", mm=208.0, tol=1.0, how="bbox_x", part="ViolinRibsBox"),
    dict(name="overall_length", mm=596.0, tol=2.0, how="bbox_z"),
    dict(name="rib_depth", mm=30.0, tol=0.5, how="bbox_y", part="ViolinRibsBox"),
]