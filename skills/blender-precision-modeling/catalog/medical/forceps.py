"""
forceps -- 150 mm dissecting forceps, lying flat, jaws slightly open.

Both arms come from one centreline function: a curve from the grip end to the
tip, sampled at 21 stations and offset either side by a half-width that tapers
from 3.0 mm at the grip to 1.1 mm at the jaw. Mirroring that polygon about the
axis is what makes the two arms match exactly -- a hand-placed second arm drifts
by a fraction of a millimetre and the joint stops closing cleanly.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=150.0,
    # A 1.6 mm x 2.2 mm section is real for dissecting forceps and useless in a
    # render: at 150 mm long the arms are hairline and the whole instrument
    # reads as a wire. A 2.4 x 3.4 mm section is still a slim surgical arm but
    # it holds a highlight and a silhouette.
    arm_thickness=2.4,
    jaw_gap=6.4,           # clear gap between the two jaw tips
    grip_width=7.2,        # outside width across both arms at the grip end
    tip_width=3.4,         # outside width of one arm at the tip
    serrations=6,
)

L = SPEC["overall_length"]
TH = SPEC["arm_thickness"]
GAP = SPEC["jaw_gap"] / 2.0        # centreline offset of one arm at the tip
STATIONS = 21


def centre(t):
    """Centreline of one arm: t=0 at the jaw tip, t=1 at the grip end."""
    return L * t, GAP * (1.0 - t) ** 1.7


def half_width(t):
    return SPEC["tip_width"] / 2.0 + \
        (SPEC["grip_width"] / 2.0 - SPEC["tip_width"] / 2.0) * t ** 0.85


def arm_polygon(sign):
    """Offset the centreline both ways to get one arm's outline.

    Offsetting the negative arm swaps which side is "outside", so the winding
    is normalised to anticlockwise: without it the second arm revolves to
    inverted normals and the joined pair has a volume of ~0.
    """
    pts = []
    for i in range(STATIONS):
        t = i / (STATIONS - 1.0)
        x, y = centre(t)
        w = half_width(t)
        pts.append((x, sign * (y + w)))
    for i in range(STATIONS - 1, -1, -1):
        t = i / (STATIONS - 1.0)
        x, y = centre(t)
        w = half_width(t)
        pts.append((x, sign * (y - w)))
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
               - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    return pts if area > 0.0 else pts[::-1]


def build():
    # Polished stainless, not a half-metallic grey. At metal 0.45 the arms had
    # neither the dark mirror of steel nor the diffuse of a dielectric and came
    # out looking like grey plastic; 0.72 with roughness 0.13 gives the
    # specular streak along each arm that says "instrument".
    steel = bkit.pbr("ForcepsSteel", base=(0.90, 0.92, 0.95), metal=0.72,
                     rough=0.13)
    dark = bkit.pbr("ForcepsJaw", base=(0.74, 0.76, 0.79), metal=0.72,
                    rough=0.26)

    # ---- the two arms ------------------------------------------------------
    arms = []
    for side, sign in (("A", 1.0), ("B", -1.0)):
        poly = arm_polygon(sign)
        ob = bkit.extrude_profile("ForcepsArm" + side, poly, TH,
                                  centre=(0.0, 0.0, TH / 2.0), axis="Z",
                                  mat=steel)
        bkit.bevel(ob, width_mm=0.35, segments=2, angle_deg=40)
        arms.append(ob)
    arms_ob = bkit.join(arms, name="ForcepsArms")

    # ---- serrations on the gripping faces of the jaws ----------------------
    serrs = []
    for side, sign in (("A", 1.0), ("B", -1.0)):
        for i in range(SPEC["serrations"]):
            t = 0.06 + i * 0.026
            x, y = centre(t)
            w = half_width(t)
            serrs.append(bkit.box("_serr", 1.8, 0.7, TH + 0.8,
                                  centre=(x, sign * (y - w), TH / 2.0 - 0.35),
                                  mat=dark))
    serr_ob = bkit.join(serrs, name="ForcepsSerrations")

    # ---- the spring bow that closes the arms at the grip end ---------------
    bkit.rounded_box("ForcepsBow", 9.0, SPEC["grip_width"] + 2.2, TH + 0.6,
                     r=1.6, segments=3,
                     centre=(L - 5.0, 0.0, TH / 2.0 - 0.3), mat=steel)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_length", mm=150.0, tol=0.6, how="bbox_x",
         part="ForcepsArms"),
    dict(name="arm_thickness", mm=2.4, tol=0.25, how="bbox_z",
         part="ForcepsArms"),
    dict(name="assembly_length", mm=150.0, tol=0.6, how="bbox_x"),
]