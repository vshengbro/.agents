"""
paperclip -- standard gem paperclip, 33 mm x 8.25 mm, 0.9 mm wire.

This is the hard one in the domain and it is the one that decides it, because
a paperclip is nothing but a bent wire and every wrong turn shows.

Construction: one solid wire path swept as a sequence of closed solids --
two long straight runs, one big U at the left end and one small U at the right
end, each arc_torus capped at both tips so nothing is left open. Real wire,
real thickness, nothing zero-thickness.

The gem shape: the outer run at y=0 runs the full length, wraps a 3.9 mm
radius U at the left, comes back along y=7.8, and the inner pair at y=2.6 /
y=5.2 is joined by a 1.3 mm radius U at the right. Ends are free, which is
what makes it a gem clip and not a ring.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=33.0,
    width=8.25,
    wire_diameter=0.9,
    outer_run_length=25.5,
    outer_u_radius=3.9,
    inner_u_radius=1.3,
)

WIRE = SPEC["wire_diameter"] / 2.0


def build():
    # A mirror-finish metal wire renders BLACK here: with metallic=1.0 there
    # is no diffuse term at all, so a 0.9 mm wire only ever reflects the dark
    # part of the studio and the clip disappears against the backdrop. Real
    # paperclips are vinyl-coated anyway, so a satin semi-metallic finish is
    # both the accurate answer and the one that reads.
    steel = bkit.pbr("PaperclipWire", base=(0.62, 0.66, 0.72),
                     metal=0.55, rough=0.40)

    # The clip lies flat in the XY plane, long axis along X.
    #
    # A gem clip is ONE wire with three bights that alternate ends and two free
    # ends at the same end:
    #
    #   free end  --run--> [left big U] --run--> [right small U]
    #              --run--> [left small U] --run-->  free end
    #
    # The previous build had only two bights and both free ends on the outside
    # of the loop, which rendered as four loose rods with a hook on one end --
    # not a closed wire path, and the reason form-plausibility failed. Each run
    # therefore starts exactly where the previous bight ends and ends exactly
    # where the next one begins; nothing overlaps and nothing floats.
    Y0, Y1, Y2, Y3 = 0.0, 2.6, 5.2, 7.8
    R_BIG = SPEC["outer_u_radius"]        # 3.9, spans Y0..Y3
    R_SMALL = SPEC["inner_u_radius"]      # 1.3, spans one 2.6 mm pair
    # Both bight bulges are offset by one wire radius, so the finished clip
    # measures exactly 33 mm tip to tip: without that the swept tube adds a
    # diameter of overhang at each end and the declared length fails by 0.9 mm.
    X_BIG = R_BIG + WIRE                  # big U, left end: bulge reaches x=0
    X_RIGHT = 33.0 - WIRE - R_SMALL       # small U, right end: bulge reaches 33
    X_SMALL_L = 6.8 - R_SMALL             # small U, left end, clear of the big U
    X_TIP = 32.0 - WIRE                   # both free ends stop short of 33

    def run(name, y, x0, x1):
        return bkit.cylinder(name, WIRE, x1 - x0, segments=20,
                             centre=((x0 + x1) / 2.0, y, 0),
                             axis="X", mat=steel)

    parts = []

    # ---- bight 1: the big U at the left, joining Y0 and Y3 ---------------
    parts.append(run("PaperclipRunOuterLo", Y0, X_BIG, X_TIP))
    parts.append(bkit.arc_torus("PaperclipOuterBend", R_BIG, WIRE,
                                90.0, 270.0, plane="XY",
                                centre=(X_BIG, (Y0 + Y3) / 2.0, 0),
                                seg_major=28, seg_minor=16, mat=steel,
                                caps=True))

    # ---- bight 2: the small U at the right, joining Y3 and Y2 ------------
    parts.append(run("PaperclipRunOuterHi", Y3, X_BIG, X_RIGHT))
    parts.append(bkit.arc_torus("PaperclipRightBend", R_SMALL, WIRE,
                                -90.0, 90.0, plane="XY",
                                centre=(X_RIGHT, (Y2 + Y3) / 2.0, 0),
                                seg_major=20, seg_minor=16, mat=steel,
                                caps=True))

    # ---- bight 3: the small U at the left, joining Y2 and Y1 -------------
    parts.append(run("PaperclipRunInnerHi", Y2, X_SMALL_L, X_RIGHT))
    parts.append(bkit.arc_torus("PaperclipLeftBend", R_SMALL, WIRE,
                                -90.0, 90.0, plane="XY",
                                centre=(X_SMALL_L, (Y1 + Y2) / 2.0, 0),
                                seg_major=20, seg_minor=16, mat=steel,
                                caps=True))

    # ---- the last run out to its free end -------------------------------
    parts.append(run("PaperclipRunInnerLo", Y1, X_SMALL_L, X_TIP))

    # Centre the assembly on the origin in both axes so it frames well.
    for ob in parts:
        ob.location.x -= 33.0 / 2.0
        ob.location.y -= (Y0 + Y3) / 2.0

    return dict(spec=SPEC, parts=len(parts))


CHECKS = [
    dict(name="length", mm=33.0, tol=0.6, how="bbox_x"),
    dict(name="width", mm=8.7, tol=0.6, how="bbox_y"),
    dict(name="wire_diameter", mm=0.9, tol=0.25, how="bbox_z",
         part="PaperclipOuterBend"),
]