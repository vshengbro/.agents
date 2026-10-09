"""
sand_dune -- a barchan dune: 980 mm horn tip to horn tip, 84 mm high, with a
long windward slope and a steep lee slip face.

Size class `large` (600..3000 mm): a real barchan dune is kilometres across,
so this is a scale model of a 60 m dune whose real asymmetry and proportions
are preserved.
The thing that has to survive the scaling is the ASYMMETRY: a barchan has a
long gentle stoss slope and a short steep slip face at the lee, and two horns
pointing downwind. A symmetric cone reads as a hill, so the profile is
explicitly asymmetric and the crest line bows upwind at the centre.

The dune is a `loft` of transverse profiles. Each cross-section is a computed
asymmetric wedge whose span shrinks toward the tips, so the horns grow out of
the body rather than being stuck on. Ten wind-ripple ridges lie on the stoss
slope at a computed pitch.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    span_horns=980.0,        # horn tip to horn tip, across the wind
    height=84.0,             # crest above the sand plain
    stoss_length=430.0,      # windward slope, gentle
    lee_length=190.0,        # slip face, steep
    ripples=10,
)

SPAN = SPEC["span_horns"]
H = SPEC["height"]
STOSS = SPEC["stoss_length"]
LEE = SPEC["lee_length"]


def _profile(x, stoss, lee):
    """Height of one transverse section at along-wind position x."""
    if x <= -stoss:
        return 0.0
    if x <= 0.0:
        # windward: slow climb, accelerating toward the crest
        return H * ((x + stoss) / stoss) ** 1.6
    # lee: steep, straight drop -- the avalanche face, angle of repose
    return H * max(0.0, 1.0 - (x / lee) ** 0.85) ** 1.15


def build():
    sand = bkit.pbr("DuneSand", base=(0.74, 0.62, 0.41), rough=0.94)
    sand_dark = bkit.pbr("DuneSandSlipFace", base=(0.55, 0.44, 0.28), rough=0.96)
    ripple_mat = bkit.pbr("DuneRipple", base=(0.80, 0.69, 0.49), rough=0.90)

    # ---- transverse sections lofted across the wind ---------------------
    # Span shrinks toward the tips (the horns) and the crest bows upwind at
    # the centre. Both are computed from the section index, so the two ends
    # are symmetric by construction rather than by hand.
    # `loft(closed_loop=False)` leaves BOTH long edges of the surface open --
    # one boundary edge per section end, exactly 2*NY bad edges, which is
    # what the first pass reported. Each section is therefore a CLOSED ring:
    # over the sand, then straight back along z=0. The loft then has no
    # boundary at all and the two end caps close it.
    NY, NX = 46, 56
    sections = []
    for j in range(NY):
        y = -SPAN / 2.0 + SPAN * j / (NY - 1.0)
        s = abs(y) / (SPAN / 2.0)                 # 0 centre, 1 at a horn
        # Height falls WITH the span. Scaling only the span leaves full-height
        # 84 mm end walls at the horns, which renders the dune as a canoe: the
        # crescent only reads when both the span and the height taper out.
        span_scale = max(0.02, 1.0 - 0.98 * s ** 1.5)
        # The crest line TRAILS downwind as the horns narrow: a barchan's two
        # horns point downwind, so the crest must sweep aft toward the tips.
        # Bowing it the other way (or leaving it straight) gives a symmetric
        # leaf shape, which is not a dune.
        crest_x = 58.0 * s ** 1.6
        stoss = STOSS * span_scale
        lee = LEE * span_scale
        ring = []
        for i in range(NX):
            x = -stoss + (stoss + lee) * i / (NX - 1.0)
            ring.append((x + crest_x, y, _profile(x, stoss, lee) * span_scale))
        # Back along z=0, in REVERSE order. Running the base pass forwards
        # too makes the ring jump from the lee toe diagonally to the stoss toe
        # and back again, which crosses the closing quads and turns the dune
        # into a boat shape. The base run has to retrace the surface run.
        for i in range(NX - 1, -1, -1):
            x = -stoss + (stoss + lee) * i / (NX - 1.0)
            ring.append((x + crest_x, y, 0.0))
        sections.append(ring)
    dune = bkit.loft("DuneBody", sections, closed_loop=True,
                     cap_start=True, cap_end=True, mat=sand)
    bkit.recalc(dune)

    # ---- wind ripples on the stoss slope --------------------------------
    # Ten shallow ridges at a computed pitch, each following the surface.
    # Overlapping solids rather than differences: a thin lens reads as a ripple
    # at this scale, and the booleans would buy nothing.
    n = SPEC["ripples"]
    pitch = (STOSS - 60.0) / float(n)
    for i in range(n):
        x = -STOSS + 60.0 + pitch * (i + 0.5)
        h = _profile(x, STOSS, LEE)
        # each ripple is a short arc whose length follows the dune's width at
        # that station: a full-width slab stands proud of the low stoss toe
        # and reads as a corrugated plate rather than as wind ripples
        s2 = min(1.0, abs(x) / (SPAN * 0.5))
        hw = 0.5 * SPAN * max(0.02, 1.0 - 0.98 * s2 ** 1.5)
        bkit.rounded_box("Ripple%02d" % (i + 1), 18.0, max(60.0, hw * 0.62),
                         2.2, r=1.0, segments=3,
                         centre=(x + 9.0, 0.0, h - 0.8), mat=ripple_mat)

    # Slip face reads darker and coarser: the steeper lee sheds its fines.
    bkit.assign_faces_by(dune, sand_dark,
                         lambda c, n: c.x / bkit.MM > 20.0 and n.z < 0.75)

    return dict(spec=SPEC, parts=1 + n)


CHECKS = [
    dict(name="span_horns", mm=980.0, tol=4.0, how="bbox_y", part="DuneBody"),
    dict(name="height", mm=84.0, tol=2.0, how="bbox_z", part="DuneBody"),
    dict(name="length", mm=620.0, tol=4.0, how="bbox_x", part="DuneBody"),
    dict(name="overall_height", mm=84.0, tol=3.0, how="bbox_z"),
    dict(name="overall_span", mm=980.0, tol=6.0, how="bbox_y"),
]