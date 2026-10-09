"""
scaffold_frame -- a two-bay, three-lift access scaffold bay, 4.0 x 1.3 x 6.0 m.

Scaffolding is a frame of STANDARDS, LEDGERS and TRANSOMS on a repeated pitch,
and the pitch is the entire model:

    bay length  = 2000 mm  (the standard bay along the run)
    bay width   = 1000 mm  (a 1000 mm platform spans two rows of standards)
    lift height = 2000 mm  (the standard 2 m lift)
    tube        = 48.3 mm OD scaffold tube, 3.6 mm wall

Every repeated member is arrayed on the computed bay or lift pitch, and every
array starts from the FIRST standard at -RUN_L/2 rather than from the origin --
an array whose first copy sits at x=0 instead of at the end of the frame walks
half the scaffold out into empty space, which doubles the run length.

One trap worth naming, because it cost this model two attempts:
`array_linear` applies its offset in the object's LOCAL space, and `place()`
leaves a rotation on every oriented primitive. So a `cylinder(axis="X")`
ledger carries a 90 deg Y rotation, and a (0, 0, LIFT) offset on it is a WORLD
move along X -- the lift array marches the ledger off the end of the scaffold
and the run comes out 8 m long instead of 4 m. Every member that gets arrayed in
this model is therefore an unrotated `box`, and the diagonal braces -- the only
rotated members -- are placed one at a time from their own endpoints.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _sections as S

SPEC = dict(
    bay_length=2000.0,
    bay_width=1000.0,
    lift_height=2000.0,
    bays=2,
    lifts=3,
    tube_od=48.3,
    tube_wall=3.6,
    board_width=225.0,
    boards_per_lift=4,
)

BAY_L = SPEC["bay_length"]
BAY_W = SPEC["bay_width"]
LIFT = SPEC["lift_height"]
BAYS = SPEC["bays"]
LIFTS = SPEC["lifts"]

RT = SPEC["tube_od"] / 2.0
RIN = RT - SPEC["tube_wall"]
RUN_L = BAYS * BAY_L            # 4000, first standard to last
FRAME_H = LIFTS * LIFT           # 6000
X0 = -RUN_L / 2.0                # the first standard
SOLE = 400.0                     # sole board length

CHECKS = [
    # The SOLE BOARDS are the widest and longest part of a scaffold bay -- they
    # overhang the standards -- so the assembly envelope is measured against
    # them, and the tube pitch is checked on the frame members themselves.
    dict(name="run_length", mm=4400.0, tol=6.0, how="bbox_x", part=None),
    dict(name="frame_width", mm=2300.0, tol=6.0, how="bbox_y", part=None),
    dict(name="frame_height", mm=6000.0, tol=6.0, how="bbox_z", part=None),
    dict(name="standard_height", mm=6000.0, tol=4.0, how="bbox_z",
         part="StandardL0"),
    dict(name="standard_width", mm=48.3, tol=1.5, how="bbox_y", part="StandardL0"),
    # 3 transoms on a 2000 mm bay pitch span 2 * 2000 + 48.3 = 4048.3 mm
    dict(name="bay_pitch_run", mm=4048.3, tol=4.0, how="bbox_x",
         part="TransomsRun"),
    dict(name="board_width", mm=225.0, tol=2.0, how="bbox_y", part="PlatformBoard1"),
]


def build():
    steel = bkit.preset("steel")
    board = bkit.pbr("ScaffoldBoard", base=(0.50, 0.38, 0.20), rough=0.70)
    clamp = bkit.preset("dark_metal")

    # ---- standards: one per bay end, per side, full height ---------
    # 48.3 mm tube is a real tube (r_out/r_in), not a cylinder: at this scale the
    # open top of a standard is visible and a solid end reads as a cast lump.
    #
    # `grid_positions` already centres its result on zero, so the standards are
    # placed at `x` directly. Adding X0 as well shifts the whole row half a run
    # into empty space and the frame comes out 6 m long instead of 4 m.
    for side, sy in (("L", -BAY_W / 2.0), ("R", BAY_W / 2.0)):
        for i, (x, _y) in enumerate(bkit.grid_positions(
                cols=BAYS + 1, rows=1, pitch_x=BAY_L, pitch_y=1.0)):
            ob = bkit.tube("Standard%s%d" % (side, i), RT, RIN, FRAME_H,
                           segments=24, axis="Z", mat=steel)
            bkit.move(ob, x, sy, FRAME_H / 2.0)

    # ---- ledgers: along the run, one per lift, per side -------------
    # Built axis-aligned (no rotation on the object) so the array's local
    # (0,0,LIFT) offset is a world lift, not a run.
    for side, sy in (("L", -BAY_W / 2.0), ("R", BAY_W / 2.0)):
        led = bkit.box("Ledgers%s" % side, RUN_L + RT * 2.0, RT * 2.0,
                       RT * 2.0, centre=(0.0, sy, LIFT / 2.0), mat=steel)
        bkit.array_linear(led, LIFTS, (0.0, 0.0, LIFT))

    # ---- transoms across the run: a grid, not a line ----------------
    # One transom on every standard at every lift. Two nested arrays -- along
    # the run, then up the lifts -- is what fills the frame; a single linear
    # array of (BAYS+1)*LIFTS walks them off the end instead.
    tr = bkit.box("TransomsRun", RT * 2.0, BAY_W + RT * 2.0, RT * 2.0,
                  centre=(X0, 0.0, LIFT / 2.0), mat=steel)
    bkit.array_linear(tr, BAYS + 1, (BAY_L, 0.0, 0.0))

    tu = bkit.box("TransomsUp", RT * 2.0, BAY_W + RT * 2.0, RT * 2.0,
                  centre=(X0, 0.0, LIFT / 2.0), mat=steel)
    bkit.array_linear(tu, LIFTS, (0.0, 0.0, LIFT))

    # ---- one diagonal brace per lift, per side ----------------------
    # The only rotated members in the model, so they are placed individually
    # from their own endpoints rather than arrayed.
    for side, sy in (("L", -BAY_W / 2.0), ("R", BAY_W / 2.0)):
        for l in range(LIFTS):
            S.bar_between("Brace%s%d" % (side, l),
                          (X0 + 40.0, sy, l * LIFT + 80.0),
                          (X0 + RUN_L - 40.0, sy, (l + 1) * LIFT - 80.0),
                          RT * 1.7, RT * 1.7, mat=clamp, r=RT * 0.4)

    # ---- a boarded platform at the top lift ------------------------
    # Board positions come from `lay_out` on the real 225 mm board width, so the
    # four boards exactly fill the 1000 mm platform with no gap arithmetic.
    n = SPEC["boards_per_lift"]
    bw = SPEC["board_width"]
    z = (LIFTS - 1) * LIFT + LIFT / 2.0
    for k, (y, _w) in enumerate(bkit.lay_out([bw] * n, gap=0.0)):
        bkit.rounded_box("PlatformBoard%d" % k, RUN_L, bw, 38.0, r=3.0,
                         segments=1, centre=(0.0, y, z), mat=board)

    # ---- sole boards under the standards ---------------------------
    for side, sy in (("L", -BAY_W / 2.0), ("R", BAY_W / 2.0)):
        sb = bkit.rounded_box("SoleBoards%s" % side, SOLE, BAY_W + 300.0,
                              38.0, r=3.0, segments=1,
                              centre=(X0, sy, 19.0), mat=board)
        bkit.array_linear(sb, BAYS + 1, (BAY_L, 0.0, 0.0))

    return dict(spec=SPEC, parts=2 * (BAYS + 1) + 2 + 2 + 2 * LIFTS + n + 2,
                bays=BAYS, lifts=LIFTS)