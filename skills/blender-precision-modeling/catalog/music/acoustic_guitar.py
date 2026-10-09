"""
acoustic_guitar -- dreadnought steel-string, 1040 mm long, six strings.

The waisted body is a `superellipse_section` loft: the guitar outline is not a
prism, so the body is built as a stack of squarish cross-sections whose width
follows the real lower-bout / waist / upper-bout profile and whose depth tapers
from the tail to the heel. Sections are interpolated through one shared
`sections_at()` function so the depth the strings are measured against and the
depth that was lofted are the same number, not two hand-typed constants.

Strings are the part that reads first and fails first, so they are computed
twice over: `bkit.lay_out` gives the six evenly spaced x positions, and the
fretboard's twenty frets come from the 12th-root-of-two fret law rather than a
constant pitch, because a fretboard with evenly spaced frets looks wrong even at
720 px.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    total_length=1040.0,
    body_length=505.0,
    lower_bout=400.0,
    waist_width=272.0,
    upper_bout=302.0,
    body_depth=120.0,
    scale_length=645.0,
    nut_offset=863.0,        # z of the nut, measured from the tail of the body
    strings=6,
    string_diameter=1.6,
    string_gap=8.0,
    soundhole_diameter=100.0,
    frets=20,
)

BODY_L = SPEC["body_length"]
NUT_Z = SPEC["nut_offset"]
BRIDGE_Z = NUT_Z - SPEC["scale_length"]          # 218 -- the saddle end
STR_N = SPEC["strings"]

# (z, half-width*2, depth) control points of the body loft, tail to heel.
_OUTLINE = [
    (0.0, 210.0, 78.0),
    (20.0, 330.0, 108.0),
    (60.0, 390.0, 118.0),
    (105.0, 400.0, 120.0),     # lower bout, widest and deepest
    (160.0, 385.0, 119.0),
    (215.0, 320.0, 112.0),
    (250.0, 272.0, 108.0),     # waist, narrowest
    (300.0, 288.0, 106.0),
    (350.0, 302.0, 104.0),     # upper bout
    (400.0, 290.0, 102.0),
    (450.0, 230.0, 100.0),
    (505.0, 150.0, 98.0),      # neck joint
]


def _interp(z, col):
    """Monotone-ish piecewise interpolation of the outline control points."""
    pts = [p[col] for p in _OUTLINE]
    if z <= _OUTLINE[0][0]:
        return pts[0]
    if z >= _OUTLINE[-1][0]:
        return pts[-1]
    for i in range(len(_OUTLINE) - 1):
        z0, z1 = _OUTLINE[i][0], _OUTLINE[i + 1][0]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            t = t * t * (3.0 - 2.0 * t)          # smoothstep: no facet creases
            return pts[i] + (pts[i + 1] - pts[i]) * t
    return pts[-1]


def width_at(z):
    return _interp(z, 1)


def depth_at(z):
    return _interp(z, 2)


def soundboard_y(z):
    """Front face of the top at station z: the body is centred on y = 0."""
    return -depth_at(z) / 2.0


def _rod(name, r, p0, p1, mat, segments=12):
    """A capped cylinder spanning two 3D points given in millimetres."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ob = bkit.cylinder(name, r, length, segments=segments, centre=(0, 0, 0),
                       axis="Z", mat=mat)
    # Blender's XYZ euler is R = Rz @ Ry @ Rx, so this pair sends local +Z onto
    # the chord direction exactly: sin(ty) = dx/L and sin(tx) = -dy/L.
    ob.rotation_euler = (-math.atan2(dy, math.hypot(dx, dz)),
                         math.atan2(dx, dz), 0.0)
    bkit.move(ob, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    return ob


def build():
    top = bkit.pbr("GuitarTop", base=(0.62, 0.42, 0.19), rough=0.30, coat=0.5)
    back = bkit.pbr("GuitarBack", base=(0.30, 0.16, 0.07), rough=0.32, coat=0.4)
    neck = bkit.pbr("GuitarNeck", base=(0.42, 0.27, 0.12), rough=0.34)
    board = bkit.pbr("GuitarBoard", base=(0.09, 0.06, 0.04), rough=0.42)
    hw = bkit.pbr("GuitarHardware", base=(0.80, 0.81, 0.82), metal=0.85, rough=0.22)
    steel = bkit.pbr("GuitarStrings", base=(0.72, 0.73, 0.76), metal=0.85,
                     rough=0.26)
    ebony = bkit.pbr("GuitarEbony", base=(0.07, 0.06, 0.05), rough=0.38)

    # ---- body: one loft of squarish sections -----------------------------
    sections = []
    z = 0.0
    while z <= BODY_L + 1e-6:
        ring = bkit.superellipse_section(width_at(z), depth_at(z), n=3.2,
                                         steps=64)
        sections.append([(x, y, z) for (x, y) in ring])
        z += BODY_L / 44.0
    body = bkit.loft("GuitarBody", sections, closed_loop=True,
                     cap_start=True, cap_end=True, mat=back)
    bkit.recalc(body)
    # Soundboard and back are the two faces of the same solid: a second shell
    # for the pale spruce top would z-fight with it and double the non-manifold
    # count, so the material is chosen per face instead.
    bkit.assign_faces_by(body, top,
                         lambda c, n: c.y < bkit.v(0, 0, 0).y)
    bkit.bevel(body, width_mm=2.2, segments=2, angle_deg=40)

    # ---- soundhole: bored, not modelled as a dark disc --------------------
    sh_z, sh_x = 300.0, 0.0
    bkit.bore(body, SPEC["soundhole_diameter"] / 2.0, depth=48.0,
              centre=(sh_x, soundboard_y(sh_z) + 22.0, sh_z), axis="Y",
              host_segments=64)

    # ---- neck, fretboard, frets ------------------------------------------
    joint_y = soundboard_y(BODY_L)
    neck_t, board_t = 25.0, 6.0
    neck_cy = joint_y + board_t + neck_t / 2.0
    nk = []
    for i in range(6):
        t = i / 5.0
        z = BODY_L - 20.0 + t * (NUT_Z - BODY_L + 20.0)
        w = 58.0 + (44.0 - 58.0) * t
        ring = bkit.rounded_rect_section(w, neck_t, r=min(w, neck_t) * 0.42,
                                         per_corner=4)
        nk.append([(x, y + neck_cy, z) for (x, y) in ring])
    neck_obj = bkit.loft("GuitarNeck", nk, mat=neck)
    bkit.recalc(neck_obj)

    # The 20th fret is at 441.8 mm from the nut, which is 54 mm INSIDE the body
    # edge -- the fretboard extension. Starting the board there is what makes the
    # 20th fret exist at all instead of ending the neck at the 14-fret body join.
    f20 = NUT_Z - SPEC["scale_length"] * (1.0 - 2.0 ** (-20.0 / 12.0))
    fb = []
    for z, w in ((f20, 56.0), (BODY_L, 55.0), (NUT_Z, 44.0)):
        ring = bkit.rounded_rect_section(w, board_t, r=2.0, per_corner=3)
        fb.append([(x, y + joint_y - board_t / 2.0, z) for (x, y) in ring])
    bkit.recalc(bkit.loft("GuitarFretboard", fb, mat=board))

    frets = []
    for n in range(1, 21):
        z = NUT_Z - SPEC["scale_length"] * (1.0 - 2.0 ** (-n / 12.0))
        t = (z - f20) / (NUT_Z - f20)
        w = 56.0 + (44.0 - 56.0) * t
        frets.append(bkit.box("gf%02d" % n, w - 0.4, 2.6, 1.4,
                              centre=(0.0, joint_y - board_t - 0.4, z), mat=hw))
    bkit.join(frets, name="GuitarFrets")

    # ---- bridge, saddle, nut, headstock, tuners ---------------------------
    bz = BRIDGE_Z
    bridge = bkit.rounded_box("GuitarBridge", 152.0, 32.0, 9.5, r=3.0,
                              segments=3,
                              centre=(0.0, soundboard_y(bz) - 4.7, bz), mat=ebony)
    bkit.box("GuitarSaddle", 74.0, 5.0, 4.0,
             centre=(0.0, soundboard_y(bz) - 9.0, bz), mat=ebony)
    bkit.box("GuitarNut", 46.0, 8.0, 5.0,
             centre=(0.0, joint_y - board_t - 2.0, NUT_Z + 2.0), mat=ebony)

    hs_poly = [(-20.0, 0.0), (-25.0, 34.0), (-33.0, 120.0), (-28.0, 177.0),
               (28.0, 177.0), (33.0, 120.0), (25.0, 34.0), (20.0, 0.0)]
    hs = bkit.extrude_profile("GuitarHeadstock", hs_poly, 15.0,
                              centre=(0.0, joint_y - 2.0, NUT_Z), axis="Y",
                              mat=neck)
    bkit.recalc(hs)
    bkit.bevel(hs, width_mm=1.6, segments=2)

    # Six machine heads, three per side, driven off the headstock's own width
    # so the posts stay on the paddle as it flares.
    posts = []
    for i, (side, z) in enumerate([(-1, 48.0), (-1, 90.0), (-1, 132.0),
                                    (1, 48.0), (1, 90.0), (1, 132.0)]):
        t = z / 177.0
        x = side * (23.0 + 6.0 * t)
        y = joint_y - 2.0
        posts.append(bkit.cylinder("gp%d" % i, 3.2, 26.0, segments=14,
                                   centre=(x, y, NUT_Z + z), axis="X",
                                   mat=hw))
        posts.append(bkit.box("gk%d" % i, 5.0, 13.0, 9.0,
                              centre=(x + side * 12.0, y, NUT_Z + z), mat=hw))
    bkit.join(posts, name="GuitarTuners")

    # ---- strings: six, evenly spaced, bridge -> nut ------------------------
    d = SPEC["string_diameter"]
    gap = SPEC["string_gap"]
    y_bridge = soundboard_y(bz) - 13.0
    y_nut = joint_y - board_t - 4.0
    strings = []
    for i, (x, _w) in enumerate(bkit.lay_out([d] * STR_N, gap=gap)):
        # Bass strings are fatter; spacing comes from lay_out, gauge from the
        # index. Both together is what makes six strings read as a guitar.
        r = 0.55 + 0.16 * i
        strings.append(_rod("gs%d" % i, r, (x, y_bridge, bz),
                            (x, y_nut, NUT_Z), steel))
    bkit.join(strings, name="GuitarStrings")

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="body_length", mm=505.0, tol=0.6, how="bbox_z", part="GuitarBody"),
    dict(name="lower_bout", mm=400.0, tol=0.6, how="bbox_x", part="GuitarBody"),
    dict(name="body_depth", mm=120.0, tol=1.0, how="bbox_y", part="GuitarBody"),
    dict(name="overall_length", mm=1040.0, tol=1.5, how="bbox_z"),
]