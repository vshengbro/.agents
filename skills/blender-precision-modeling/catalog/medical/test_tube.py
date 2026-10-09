"""
test_tube -- 16 x 100 mm borosilicate test tube: hemispherical closed bottom,
1.0 mm wall, 5 mm rim bead, and three engraved fill lines.

The wall is real because the profile walks out along the outside, over the rim
and back down the inside through a second, smaller hemisphere -- a single-surface
revolve would give a paper-thin tube that reads as film. Both hemispheres are
computed from the real radii, so the wall is 1.0 mm at the dome as well as at
the straight section.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tube_diameter=16.0,      # outside diameter
    tube_length=100.0,       # bottom of the dome to the rim
    wall=1.0,
    rim_bead=17.0,           # rim bead diameter (a flare just outside the tube)
    fill_lines=3,
)

D = SPEC["tube_diameter"] / 2.0          # 8.0
L = SPEC["tube_length"]
WALL = SPEC["wall"]
RI = D - WALL                           # 6.5
CENTRE_Z = D                            # dome sphere centre -> tangent to wall
BEAD = SPEC["rim_bead"] / 2.0
MARK_D = 0.35                           # engraving depth


def build():
    glass = bkit.pbr("TubeGlass", base=(0.88, 0.91, 0.90), rough=0.05,
                     transmission=0.74, ior=1.47, coat=0.5)
    ink = bkit.pbr("TubeInk", base=(0.08, 0.08, 0.09), rough=0.45)

    prof = []
    # ---- outside: hemisphere, then ONE smooth straight wall ---------------
    # The fill lines used to be cut INTO the lathe profile, so the profile
    # stepped in and out three times and shade_smooth drew each step as a
    # visible ring: the tube read as four stacked segments rather than one
    # glass cylinder. The wall is now a single station from z_lo to the rim;
    # the fill lines are printed on afterwards with assign_faces_by, which is
    # the same trick used for the inside/outside colour split.
    z_lo = CENTRE_Z + 2.0
    z_hi = L - 5.0
    n = SPEC["fill_lines"]
    marks = [z_lo + (z_hi - z_lo) * (i + 1) / float(n + 1) for i in range(n)]
    for i in range(9):                      # r = 0 -> D
        a = (math.pi / 2.0) * i / 8.0
        prof.append((D * math.sin(a), CENTRE_Z - D * math.cos(a)))
    prof.append((D, z_lo))

    # ---- a rolled lip: the wall thickens into a bead over the last 3 mm ---
    # A square-cut rim is what made the top look broken off. The lip is a real
    # half-round bead of the bead radius, so the silhouette at the mouth is
    # rounded rather than a knife edge.
    prof.append((D, L - 3.2))
    for i in range(1, 7):
        a = (math.pi / 2.0) * i / 6.0
        prof.append((BEAD - 0.35 + (BEAD - (BEAD - 0.35)) * math.sin(a),
                     L - 3.2 + 1.6 * (1.0 - math.cos(a))))
    prof.append((BEAD, L))
    prof.append((D, L))                     # across the bead
    prof.append((RI, L - 0.6))
    prof.append((RI, CENTRE_Z))
    # ---- inside: the inner hemisphere back to the axis ----------------------
    for i in range(8, -1, -1):
        a = (math.pi / 2.0) * i / 8.0
        prof.append((RI * math.sin(a), CENTRE_Z - RI * math.cos(a)))

    tube = bkit.lathe("TestTube", prof, segments=96, mat=glass)

    # The three fill lines, printed on the outside wall as a second material
    # rather than cut into the profile. Each line owns the ring of faces whose
    # centre falls inside a 0.9 mm band at its own height.
    def on_line(c, _n):
        z = c.z / bkit.MM
        r = _rad(c) / bkit.MM
        if r < D - 0.6 or r > D + 0.6:
            return False
        return any(abs(z - m) < 0.55 for m in marks)

    bkit.assign_faces_by(tube, ink, on_line)

    return dict(spec=SPEC, parts=1)


def _rad(c):
    return (c.x ** 2 + c.y ** 2) ** 0.5


CHECKS = [
    # The rim bead flares past the 16 mm barrel, so the widest measurable
    # dimension of this part is the 17 mm bead -- declare that, not the barrel.
    dict(name="rim_bead_diameter", mm=17.0, tol=0.2, how="diameter",
         part="TestTube"),
    dict(name="tube_length", mm=100.0, tol=0.3, how="bbox_z", part="TestTube"),
    dict(name="overall_height", mm=100.0, tol=0.3, how="bbox_z"),
]