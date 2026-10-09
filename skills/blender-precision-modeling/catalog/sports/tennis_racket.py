"""
tennis_racket -- 685 mm adult racket: elliptical frame, twin throat struts,
tapered shaft, wrapped grip, and a real 18 x 20 string bed.

The string bed is the whole point. 18 mains run the long axis and 20 crosses
the short one, laid out from the strung area's own dimensions, and every string
is trimmed to the ellipse it actually meets -- so the outermost mains are short
and the bed is a lens, not a rectangle. Both counts come from grid_positions,
never from hand-placed constants: a solid paddle with a handful of lines drawn
across it is the single most common way a racket model gives itself away.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=685.0,
    head_length=327.0,      # outer, frame centreline 158 + half beam 5.5
    head_width=275.0,       # outer, 132 + 5.5
    beam_radial=11.0,       # beam thickness in the plane of the hoop
    beam_thickness=7.0,     # beam thickness across the face
    mains=18,
    crosses=20,
    string_diameter=1.4,
    string_pitch_main=14.06,
    string_pitch_cross=15.25,
    grip_length=167.0,
)

A = 158.0                 # frame centreline semi-axis, long (z)
B = 132.0                 # frame centreline semi-axis, short (x)
HR = SPEC["beam_radial"] / 2.0      # 5.5
A_IN, B_IN = A - HR, B - HR         # 152.5, 126.5 -- the strung ellipse
Z_TOP = A + HR                      # 163.5, the highest point
Z_BUTT = Z_TOP - SPEC["overall_length"]   # -521.5, the flat butt face
SR = SPEC["string_diameter"] / 2.0        # 0.7
BITE = 1.5                           # how far a string enters the frame

CHECKS = [
    dict(name="overall_length", mm=685.0, tol=0.6, how="bbox_z"),
    dict(name="head_length", mm=327.0, tol=0.6, how="bbox_z", part="RacketFrame"),
    dict(name="head_width", mm=275.0, tol=0.6, how="bbox_x", part="RacketFrame"),
    dict(name="grip_length", mm=193.0, tol=0.6, how="bbox_z", part="Grip"),
]


# ---- local vector helpers (mm) -------------------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    ln = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1.0 / ln)


def _bar(name, p0, p1, w, t, r, mat=None, ref=(0.0, 0.0, 1.0)):
    """A straight structural member: rounded-rect section swept from p0 to p1.

    w is measured along (d x ref), t along the remaining in-plane axis, so a
    member lying in the XZ plane can be given a blade-like section.

    The reference axis MUST be re-chosen when d is parallel to it: d x ref is
    then the zero vector, both section axes collapse, and the whole member
    becomes a zero-area line that builds cleanly, passes every mesh check and
    renders as nothing at all.
    """
    d = _norm(_sub(p1, p0))
    if abs(_dot(d, ref)) > 0.95:
        ref = (1.0, 0.0, 0.0) if abs(d[0]) < 0.9 else (0.0, 1.0, 0.0)
    ex = _norm(_cross(d, ref))
    ey = _cross(d, ex)
    ring = bkit.rounded_rect_section(w, t, r, per_corner=4)
    s0 = [tuple(_add(_add(p0, _mul(ex, u)), _mul(ey, v))) for (u, v) in ring]
    s1 = [tuple(_add(_add(p1, _mul(ex, u)), _mul(ey, v))) for (u, v) in ring]
    ob = bkit.loft(name, [s0, s1], mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    frame_mat = bkit.pbr("RacketFrame", base=(0.12, 0.30, 0.60), rough=0.24)
    # a pale shaft: at 685 mm tall the shaft is only 8 px wide in frame, and a
    # dark one disappears against the backdrop entirely
    shaft_mat = bkit.pbr("RacketShaft", base=(0.78, 0.79, 0.81), rough=0.30)
    grip_mat = bkit.preset("black_plastic")
    string_mat = bkit.pbr("TennisString", base=(0.90, 0.90, 0.88), rough=0.42)
    butt_mat = bkit.pbr("ButtCap", base=(0.16, 0.16, 0.17), rough=0.35)

    # ---- elliptical hoop: one closed swept tube, welded at the seam ------
    ring = bkit.rounded_rect_section(SPEC["beam_radial"], SPEC["beam_thickness"],
                                    r=3.0, per_corner=6)
    nring = len(ring)
    sections = []
    steps = 96
    for i in range(steps + 1):
        t = 2.0 * math.pi * i / steps
        cx, cz = B * math.cos(t), A * math.sin(t)
        rx, rz = B * math.cos(t), A * math.sin(t)      # outward radial
        ln = math.sqrt(rx * rx + rz * rz)
        rx, rz = rx / ln, rz / ln
        sections.append([(cx + rx * u, v, cz + rz * u) for (u, v) in ring])
    frame = bkit.loft("RacketFrame", sections, closed_loop=True,
                      cap_start=False, cap_end=False, mat=frame_mat,
                      smooth=True)
    bkit.weld(frame)
    bkit.recalc(frame)

    # ---- throat: two struts off the bottom of the hoop into the shaft ----
    # Built from mirrored endpoints rather than a Mirror modifier: the strut's
    # object origin sits on the strut, so a local-space mirror would land the
    # copy at 48 - x instead of -x.
    strut = _bar("ThroatStrut", (48.0, 0.0, -150.0), (9.0, 0.0, -232.0),
                 17.0, 8.0, 3.0, frame_mat, ref=(0.0, 1.0, 0.0))
    strut2 = _bar("ThroatStrutB", (-48.0, 0.0, -150.0), (-9.0, 0.0, -232.0),
                  17.0, 8.0, 3.0, frame_mat, ref=(0.0, 1.0, 0.0))
    shaft = _bar("Shaft", (0.0, 0.0, -222.0), (0.0, 0.0, -352.0),
                 18.0, 15.0, 4.0, shaft_mat)
    throat = bkit.join([strut, strut2, shaft], name="Throat")

    # ---- grip: a slightly waisted handle with a flat butt cap -----------
    gh = SPEC["grip_length"]
    gz0 = Z_BUTT + 26.0                 # butt overlaps the handle
    grip_prof = [
        (0.0, 0.0), (16.0, 0.0), (18.5, 6.0), (19.0, 30.0), (18.2, 110.0),
        (17.4, 130.0), (18.6, gh - 5.0), (18.0, gh), (0.0, gh),
    ]
    grip = bkit.lathe("Grip", grip_prof, segments=64,
                      centre=(0.0, 0.0, gz0), mat=grip_mat)
    butt = bkit.rounded_box("ButtCap", 36.0, 26.0, 14.0, r=3.0, segments=3,
                            centre=(0.0, 0.0, Z_BUTT + 7.0), mat=butt_mat)
    handle = bkit.join([grip, butt], name="Grip")

    # ---- string bed: 18 mains along z, 20 crosses along x ---------------
    # The bed lies in the XZ plane, so the grid's second axis is read as z.
    # Every string is trimmed to the ellipse it actually meets, which is what
    # makes the outer mains short and the bed a lens rather than a rectangle.
    strings = []
    n_main = SPEC["mains"]
    n_cross = SPEC["crosses"]
    pitch_m = 2.0 * B_IN / n_main                 # mains spread across x
    pitch_c = 2.0 * A_IN / n_cross                # crosses spread along z
    for (x, _y) in bkit.grid_positions(cols=n_main, rows=1,
                                       pitch_x=pitch_m, pitch_y=1.0):
        k = min(0.999, abs(x) / B_IN)
        half = A_IN * math.sqrt(1.0 - k * k) + BITE
        strings.append(bkit.cylinder("Main", SR, 2.0 * half, segments=8,
                                     centre=(x, 0.0, 0.0), axis="Z",
                                     mat=string_mat, smooth=False))
    for (_x, z) in bkit.grid_positions(cols=1, rows=n_cross,
                                       pitch_x=1.0, pitch_y=pitch_c):
        k = min(0.999, abs(z) / A_IN)
        half = B_IN * math.sqrt(1.0 - k * k) + BITE
        strings.append(bkit.cylinder("Cross", SR, 2.0 * half, segments=8,
                                     centre=(0.0, 0.0, z), axis="X",
                                     mat=string_mat, smooth=False))
    bed = bkit.join(strings, name="StringBed")

    return dict(spec=SPEC, parts=5)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
