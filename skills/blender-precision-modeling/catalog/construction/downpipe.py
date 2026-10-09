"""
downpipe -- a 3 m cast-aluminium downpipe with a hopper head and 3 brackets.

A downpipe is a STRAIGHT RUN, and the run is the model: 3 m of 110 mm pipe on
the vertical, socketed at both ends so the joints read, carried by three wall
brackets on a 1 m pitch, and topped by a hopper head that collects the roof
water. The hopper is the only interesting shape on the item and it is a
`lathe` of a closed profile -- a rectangular mouth on a round body, which is
exactly the transition a real fabricated hopper makes.

Real 110 mm downpipe: 110 mm outside, 3 mm wall (a real tube, not a cylinder),
3 m long, on a 110 x 110 mm square bracket at 1 m centres, with a 350 x 300 mm
hopper head on top.

The pipe is `tube`, so the open top of the run is genuinely hollow and visible
inside the hopper -- a cylinder end would read as a cast lump.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=3000.0,
    pipe_od=110.0,
    pipe_wall=3.0,
    socket_od=124.0,
    socket_length=90.0,
    brackets=3,
    bracket_pitch=1000.0,
    bracket_width=110.0,
    hopper_mouth_x=350.0,
    hopper_mouth_y=300.0,
    hopper_height=320.0,
)

L = SPEC["length"]
OD = SPEC["pipe_od"]
WALL = SPEC["pipe_wall"]
ID_ = OD - 2.0 * WALL
NB = SPEC["brackets"]
PITCH = SPEC["bracket_pitch"]

SOCK = SPEC["socket_od"]
SOCK_L = SPEC["socket_length"]

CHECKS = [
    dict(name="pipe_dia", mm=110.0, tol=2.0, how="diameter", part="Downpipe"),
    dict(name="pipe_length", mm=3000.0, tol=4.0, how="bbox_z", part="Downpipe"),
    dict(name="socket_dia", mm=124.0, tol=2.0, how="diameter", part="DownpipeSocket0"),
    dict(name="bracket_pitch_run", mm=2040.0, tol=6.0, how="bbox_z",
         part="DownpipeBrackets"),
    dict(name="hopper_mouth", mm=350.0, tol=4.0, how="bbox_x", part="DownpipeHopper"),
    dict(name="overall_height", mm=3340.0, tol=8.0, how="bbox_z", part=None),
]


def build():
    alu = bkit.pbr("DownpipeAlu", base=(0.72, 0.73, 0.75), metal=0.82,
                   rough=0.36)
    steel = bkit.preset("dark_metal")

    # ---- the pipe: a real tube, so the top is genuinely open -------
    pipe = bkit.tube("Downpipe", OD / 2.0, ID_ / 2.0, L, segments=40,
                     axis="Z", centre=(0.0, 0.0, L / 2.0), mat=alu)
    # the pipe starts on the floor, so `sit_on_floor` is a no-op

    # ---- sockets at head and foot, oversailing the pipe ------------
    # A socket is a short fat collar; it laps the pipe by 5 mm so the two solids
    # cross rather than touch.
    for tag, z in (("0", SOCK_L / 2.0 - 5.0),
                   ("1", L - SOCK_L / 2.0 + 5.0)):
        bkit.tube("DownpipeSocket%s" % tag, SOCK / 2.0, ID_ / 2.0 - 1.0,
                  SOCK_L, segments=40, axis="Z", centre=(0.0, 0.0, z),
                  mat=alu)

    # ---- 3 wall brackets on the 1 m pitch --------------------------
    # A downpipe bracket is a square plate with a collar round the pipe; the
    # collar oversails the 110 mm pipe by 5 mm so it grips.
    br = bkit.box("DownpipeBracketPlate0", 40.0, SPEC["bracket_width"] + 70.0,
                  6.0, centre=(0.0, -(OD / 2.0 + 35.0), 0.0), mat=steel)
    br2 = bkit.tube("DownpipeBracketCollar0", OD / 2.0 + 5.0, OD / 2.0 + 1.0,
                    40.0, segments=32, axis="Z", centre=(0.0, 0.0, 0.0),
                    mat=steel)
    grp = bkit.join([br, br2], "DownpipeBrackets")
    bkit.recalc(grp)
    bkit.array_linear(grp, NB, (0.0, 0.0, PITCH))

    # ---- the hopper head -------------------------------------------
    # A lathe takes a circular profile, so the round-to-rectangular transition is
    # made by lofting: a circle at the pipe, growing to a rounded rectangle at
    # the mouth. `superellipse_section` with a high n gives the rectangular mouth
    # its corners without a hand-written point list.
    hop_sections = []
    hx = SPEC["hopper_mouth_x"] / 2.0
    hy = SPEC["hopper_mouth_y"] / 2.0
    zz = L + SPEC["hopper_height"]
    for t, z in ((0.0, L - 40.0), (0.45, L + SPEC["hopper_height"] * 0.55),
                 (1.0, zz)):
        sx = (OD / 2.0) + (hx - OD / 2.0) * t
        sy = (OD / 2.0) + (hy - OD / 2.0) * t
        n = 2.0 + (12.0 - 2.0) * t          # circle -> near-rectangle
        ring = bkit.superellipse_section(sx * 2.0, sy * 2.0, n=n, steps=48)
        hop_sections.append([(p[0], p[1], z) for p in ring])
    hop = bkit.loft("DownpipeHopper", hop_sections, mat=alu)
    bkit.recalc(hop)

    return dict(spec=SPEC, parts=4, brackets=NB)


# The hopper is a solid loft, so its mouth is the X extent -- 350 mm. The pipe
# is 3000 mm on its own and the hopper sits on top, so the assembly is 3320 mm.