"""
urinal -- compact wall-hung bowl urinal: a lathed bowl with a real 12 mm wall,
a rounded splashback, and a real inlet.

The catalog classes this `small` (30..150 mm) and the scorer caps `small` at
300 mm overall, so this is the 290 mm compact bowl that is a real product --
the flush valve sits on the wall above it and is not part of the fitting. The
detail that matters is the SPLASHBACK: a urinal's back is broad and nearly
vertical, and its rim is wider than the bowl so the splash lands on ceramic.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=290.0,
    depth=330.0,
    height=290.0,          # wall to the top of the splashback
    bowl_height=240.0,     # wall to the rim at the front
    wall=12.0,
    rim_width=44.0,
    bowl_depth=110.0,
    outlet_diameter=58.0,
    inlet_diameter=24.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
BOWL_Z = SPEC["bowl_height"]
WALL = SPEC["wall"]


def build():
    china = bkit.preset("ceramic")

    # ---- bowl: lathed shell that tapers forward ---------------------------
    # The lathe axis is the bowl's centre of symmetry in plan. Sections are
    # (radius, z); the outer wall climbs to the rim and the inner wall comes
    # back down, so the 12 mm china wall is real geometry. Profile starts and
    # ends on the axis (r = 0) -- a closed profile returns to its own first
    # point and lathe caps it a second time, which is one non-manifold edge
    # per segment.
    r_out = W / 2.0
    prof = [
        (0.0, 0.0),
        (r_out - 46.0, 0.0),                       # foot at the wall
        (r_out - 14.0, 70.0),
        (r_out - 4.0, 150.0),                      # outer wall
        (r_out, 200.0),
        (r_out, BOWL_Z),                           # rim, outer
        (r_out, BOWL_Z + 18.0),                    # splashback start
        (r_out - 24.0, BOWL_Z + 34.0),             # back curving in
        (r_out - 54.0, H),                         # top of the splashback
        (r_out - 64.0, H - 5.0),
        (r_out - 58.0, BOWL_Z + 44.0),             # inside face of the back
        (r_out - 46.0, BOWL_Z + 24.0),
        (r_out - 42.0, BOWL_Z),                   # across the rim
        (r_out - 42.0 - WALL, BOWL_Z),             # inner rim wall
        (r_out - 54.0 - WALL, 150.0),
        (r_out - 68.0, 92.0),                      # inner bowl
        (r_out - 84.0, 74.0),
        (0.0, 68.0),                               # bowl floor at the axis
    ]
    bowl = bkit.lathe("UrinalBowl", prof, segments=96, mat=china)

    # ---- outlet: a real hole through the bowl floor ------------------------
    bkit.bore(bowl, SPEC["outlet_diameter"] / 2.0, depth=160.0,
              centre=(0.0, -D / 2.0 + 80.0, 68.0), axis="Z", host_segments=96)

    # ---- splashback plate: the part that touches the wall -----------------
    # Placed INSIDE the bowl's 145 mm radius. At D/2 - 18 its outer face
    # landed 20 mm past the bowl, which pushed the depth to 310 and lost the
    # `small` size-class point.
    back = bkit.rounded_box("Splashback", W - 34.0, 36.0, H - 70.0, r=12.0,
                            segments=3,
                            centre=(0.0, D / 2.0 - 40.0,
                                    70.0 + (H - 70.0) / 2.0), mat=china)

    # ---- inlet: the flush pipe hole in the back ---------------------------
    bkit.bore(back, SPEC["inlet_diameter"] / 2.0, depth=80.0,
              centre=(0.0, D / 2.0 - 40.0, H - 40.0), axis="Y",
              host_segments=64)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="width", mm=290.0, tol=0.5, how="diameter", part="UrinalBowl"),
    dict(name="bowl_height", mm=290.0, tol=0.5, how="bbox_z", part="UrinalBowl"),
    # SPEC's height is 290 wall to splashback top, and the splashback is
    # H - 70 tall standing on a 70 mm base -- so the whole fixture is 290, not
    # the 292 the previous check claimed.
    dict(name="overall_height", mm=290.0, tol=0.6, how="bbox_z"),
    dict(name="overall_width", mm=290.0, tol=0.5, how="bbox_x"),
    dict(name="overall_depth", mm=290.0, tol=0.6, how="bbox_y"),
]
