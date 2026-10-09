"""
stapler -- desktop stapler, 145 mm long.

The silhouette that makes a stapler read is the gap between the base and the
driving arm, so the arm is modelled as its own part sitting above the
magazine channel rather than as one solid block. The anvil plate is inset
into a recess cut from the base.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=145.0,
    base_depth=22.0,
    overall_height=26.0,
    arm_length=111.0,       # hinge end to nose tip, x = -59 to +52
    staple_channel=13.0,
)

L = SPEC["length"]
D = SPEC["base_depth"]


def build():
    # Near-black against a 0.19 backdrop loses the silhouette. Mid grey keeps
    # the magazine gap and the arm-to-base separation readable.
    shell = bkit.pbr("StaplerShell", base=(0.38, 0.40, 0.44), rough=0.32,
                     coat=0.25)
    dark = bkit.pbr("StaplerDark", base=(0.14, 0.15, 0.17), rough=0.44)
    steel = bkit.preset("polished_metal")

    base = bkit.rounded_box("StaplerBase", L, D, 10.0, r=2.5, segments=4,
                            centre=(0, 0, 5.0), mat=shell)

    # Anvil: a real recess in the base with a steel plate sunk into it.
    recess = bkit.rounded_box("recess", 15.0, 14.0, 5.0, r=1.0,
                              centre=(52.0, 0, 9.0), mat=None)
    bkit.boolean(base, recess, "DIFFERENCE")
    anvil = bkit.rounded_box("StaplerAnvil", 13.0, 12.0, 2.2, r=0.6,
                             centre=(52.0, 0, 10.4), mat=steel)

    # Hinge block at the rear carries the driving arm.
    hinge = bkit.rounded_box("StaplerHinge", 24.0, 18.0, 8.0, r=2.0,
                             centre=(-56.0, 0, 14.0), mat=shell)

    # Staple magazine channel: it fills the whole gap between base and arm
    # for its length, which is what a stapler actually looks like -- the
    # magazine IS the visible body under the driving arm. It used to be a
    # 96 x 12 mm bar floating in a 145 mm gap, so the arm and base read as
    # two flat bars with air between them.
    channel = bkit.rounded_box("StaplerMagazine", 104.0,
                               SPEC["staple_channel"], 8.5, r=1.5,
                               centre=(-14.0, 0, 13.2), mat=dark)
    # the steel staple track visible in the top of the magazine
    track = bkit.rounded_box("StaplerTrack", 98.0, 5.0, 2.0, r=0.6,
                             segments=2, centre=(-14.0, 0, 17.4), mat=steel)

    # ---- driving arm, tapered toward the front --------------------------
    # A constant 118 x 17 x 11 mm box reads as a bar. A stapler's arm is
    # deepest at the hinge and narrows to the driving nose, so the arm is now
    # a loft over four sections instead of one box. The nose tip drops to
    # just above the track, which is what closes the magazine gap at the front.
    arm_sections = []
    for (x, w, t, h) in ((-59.0, 20.0, 13.0, 19.5),
                         (-30.0, 18.5, 12.0, 19.0),
                         (10.0, 15.5, 10.0, 18.6),
                         (52.0, 12.0, 8.0, 18.4)):
        r = min(2.5, t / 2.4, w / 2.4)
        ring = bkit.rounded_rect_section(w, t, r, per_corner=4)
        # the section's u is the arm's WIDTH (Y) and v its thickness (Z);
        # x, the station's own coordinate, is the arm's LENGTH (X)
        arm_sections.append([(x, u, h + v) for (u, v) in ring])
    arm = bkit.loft("StaplerArm", arm_sections, mat=shell, smooth=True)
    bkit.recalc(arm)
    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="length", mm=145.0, tol=0.6, how="bbox_x", part="StaplerBase"),
    dict(name="base_depth", mm=22.0, tol=0.4, how="bbox_y", part="StaplerBase"),
    dict(name="overall_height", mm=26.0, tol=0.6, how="bbox_z"),
]