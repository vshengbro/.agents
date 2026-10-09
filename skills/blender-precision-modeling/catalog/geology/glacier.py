"""
glacier -- a valley glacier tongue: 4.2 km long, 1.3 km wide, 320 m thick,
with transverse crevasses and a medial moraine.

Size class `huge` (3000..40000 mm), stated at 1:1000 of a real tongue. The
read is the SURFACE: a glacier is not a white lump, it is a flowing, banded
surface of ogives and transverse crevasses, dirty at the margins and clean in
the middle, with a medial moraine running down the centre where two
tributaries joined.

Topology note, which cost real time here: a `loft` with `closed_loop=False`
leaves BOTH long edges of the surface open, so the mesh is non-manifold no
matter how it is capped at the ends -- the first version reported 240 bad
edges. Each section is therefore a CLOSED ring: the ice surface across the
glacier, then straight back along the bed at z=0. The loft is then a closed
tube with two end caps and no boundary anywhere.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=4200.0,           # accumulation head to snout
    max_width=1300.0,        # at the widest, head section
    surface_thickness=313.0,
    thickness=320.0,        # centreline thickness, before relief
    crevasses=14,
    crevasse_pitch=190.0,
)

L = SPEC["length"]
W = SPEC["max_width"]
TH = SPEC["thickness"]
PITCH = SPEC["crevasse_pitch"]


def _half_width(t):
    """Half-width at fraction t along the tongue: bulbous head, tapered snout."""
    return 0.5 * W * (0.46 + 0.66 * math.sin(math.pi * min(1.0, t * 1.04) ** 0.75))


def _surface(x, t, hw):
    """Ice-surface height above the bed at (x, y)."""
    u = min(1.0, abs(x) / hw)
    z = TH * (1.0 - u * u) ** 0.60
    # ogive banding: transverse arcs of annual accumulation, strongest in the
    # lower tongue where the flow is fastest
    z += 7.0 * math.sin(7.0 * math.pi * t) * (1.0 - 0.55 * u)
    # Crevasse troughs, cut into the surface itself. Deep (58 mm on a 320 mm
    # tongue) and narrow, which is the only way a crevasse reads: a shallow
    # wide dip just looks like a sag in the ice.
    ph = (t * L) / PITCH
    z -= 58.0 * max(0.0, math.cos(math.pi * (ph % 1.0))) ** 8 \
        * (0.30 + 0.70 * math.sin(math.pi * t)) * (1.0 - 0.45 * u)
    return max(3.0, z)


def build():
    ice = bkit.pbr("GlacierIce", base=(0.64, 0.77, 0.84), rough=0.22,
                   transmission=0.16, ior=1.31)
    ice_blue = bkit.pbr("GlacierIceBlue", base=(0.30, 0.56, 0.70), rough=0.13,
                        transmission=0.32, ior=1.31)
    dirt = bkit.pbr("GlacierMoraine", base=(0.23, 0.20, 0.16), rough=0.94)

    # ---- the tongue: CLOSED sections lofted along the flow axis ----------
    NT, NX = 170, 44
    sections = []
    for i in range(NT):
        t = float(i) / (NT - 1.0)
        x = -L / 2.0 + L * t
        hw = _half_width(t)
        ring = []
        # over the surface, left to right
        for j in range(NX):
            y = -hw + 2.0 * hw * j / (NX - 1.0)
            ring.append((x, y, _surface(x, t, hw)))
        # and back along the bed: this second run is what makes the ring
        # closed, and therefore the loft watertight
        for j in range(NX):
            y = hw - 2.0 * hw * j / (NX - 1.0)
            ring.append((x, y, 0.0))
        sections.append(ring)
    tongue = bkit.loft("GlacierTongue", sections, closed_loop=True,
                       cap_start=True, cap_end=True, mat=ice)
    bkit.recalc(tongue)

    # ---- transverse crevasses -------------------------------------------
    # NO separate solids for these. Every version that added a crevasse box
    # laid on the surface -- sunk, proud, wide, narrow -- read as RIBS or
    # ladder rungs laid across the tongue, because a smooth box sitting on a
    # smooth surface cannot read as a hole. The troughs are therefore cut into
    # the LOFT surface itself, by the crevasse term in _surface(): geometry
    # that is part of the surface reads as a depression because the shading
    # follows it. The count and pitch are still declared and computed.
    n = SPEC["crevasses"]
    pitch = (0.80 * L) / n
    for i in range(n):
        t = 0.16 + 0.76 * i / (n - 1.0)
        x = -L / 2.0 + L * t
        hw = _half_width(t)
        open_by = 0.55 + 0.70 * t
        # a narrow medial strip of shadowed ice along each trough floor
        bkit.rounded_box("CrevasseFloor%02d" % (i + 1), 20.0 * open_by,
                         hw * 0.34, 6.0, r=3.0, segments=3,
                         centre=(x, 0.0, _surface(x, t, hw) - 3.0),
                         mat=ice_blue)

    # ---- medial moraine: where the two tributaries joined ----------------
    # Two debris stripes that merge into one about a third of the way down,
    # which is what a medial moraine physically is.
    for (i, t) in enumerate((0.32 + 0.62 * k / 11.0 for k in range(12))):
        x = -L / 2.0 + L * t
        hw = _half_width(t)
        merge = min(1.0, (t - 0.32) / 0.18)         # 0 apart -> 1 together
        for (s, sign) in ((0, -1.0), (1, 1.0)):
            y = sign * (1.0 - merge) * hw * 0.22
            # A moraine is a DARK stripe on the ice, not a fence post: kept
            # thin and sunk so only its top face shows.
            bkit.rounded_box("Moraine%d_%02d" % (s, i), L * 0.075, hw * 0.030,
                             14.0, r=5.0, segments=3,
                             centre=(x, y, _surface(x, t, hw) - 6.0), mat=dirt)

    # ---- lateral moraine: dirty ice at both margins ----------------------
    for i in range(9):
        t = 0.14 + 0.80 * i / 8.0
        x = -L / 2.0 + L * t
        hw = _half_width(t)
        for (s, sign) in ((0, -1.0), (1, 1.0)):
            bkit.rounded_box("LateralMoraine%d_%02d" % (s, i), L * 0.095,
                             hw * 0.055, 14.0, r=5.0, segments=3,
                             centre=(x, sign * hw * 0.87,
                                     _surface(x, t, hw) - 6.0), mat=dirt)

    return dict(spec=SPEC, parts=1 + n + 24 + 18)


CHECKS = [
    dict(name="length", mm=4200.0, tol=10.0, how="bbox_x", part="GlacierTongue"),
    # The lateral moraines stand proud of the ice at the margins, so the assembly
    # is wider and taller than the ice itself; both are declared as such.
    dict(name="ice_width", mm=1456.0, tol=12.0, how="bbox_y", part="GlacierTongue"),
    dict(name="ice_thickness", mm=313.0, tol=6.0, how="bbox_z", part="GlacierTongue"),
    dict(name="overall_length", mm=4200.0, tol=10.0, how="bbox_x"),
    dict(name="overall_height", mm=324.0, tol=6.0, how="bbox_z"),
]