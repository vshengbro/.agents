"""
welder -- 180 A inverter arc welder, 460 x 240 x 330 mm with the torch lead.

A stick welder is a steel case with a carry strap, a control panel on the front
and TWO output terminals -- a twist-lock dinse and a work clamp -- because
that pair is what distinguishes a welder from a generator. The case's feet are
z = 0, so it stands on four rubber feet the way a site welder does.

The torch lead is a real coiled helix (`thread`) and the electrode holder is a
lathed jaw on a moulded grip, not a plain rod.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    case_length=460.0,
    case_width=240.0,
    case_height=260.0,
    carry_handle_height=362.0,
    terminal_diameter=32.0,
    torch_cord_diameter=16.0,
    holder_grip_diameter=38.0,
    panel_width=170.0,
    panel_height=140.0,
    display_width=92.0,
)

CHECKS = [
    dict(name="case_length", mm=460.0, tol=1.0, how="bbox_x",
         part="WeldCase"),
    dict(name="case_width", mm=240.0, tol=1.0, how="bbox_y",
         part="WeldCase"),
    dict(name="case_height", mm=260.0, tol=1.0, how="bbox_z",
         part="WeldCase"),
    dict(name="carry_handle_height", mm=362.0, tol=2.0, how="top_z",
         part="WeldHandle"),
    dict(name="terminal_diameter", mm=32.0, tol=0.8, how="bbox_x",
         part="WeldTerminalA"),
    dict(name="panel_height", mm=140.0, tol=1.0, how="bbox_z",
         part="WeldPanel"),
    dict(name="display_width", mm=92.0, tol=0.8, how="bbox_x",
         part="WeldDisplay"),
]

FZ = 22.0                  # foot height: the feet are the floor datum
CZ = FZ + SPEC["case_height"] / 2.0


def build():
    body = bkit.pbr("WeldBody", base=(0.62, 0.16, 0.09), rough=0.30)
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")
    panel_mat = bkit.pbr("WeldPanelMat", base=(0.07, 0.07, 0.08),
                         rough=0.35)
    led = bkit.pbr("WeldLed", base=(0.1, 0.9, 0.3), rough=0.2,
                   emission=(0.1, 0.9, 0.3), emission_strength=3.0)

    # ---- case on four feet -------------------------------------------------
    T.shell("WeldCase", SPEC["case_length"], SPEC["case_width"],
            SPEC["case_height"], centre=(0.0, 0.0, CZ), r=10.0, mat=body)
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=380.0,
                                                   pitch_y=170.0)):
        bkit.rounded_box("WeldFoot%d" % i, 70.0, 50.0, FZ, r=5.0, segments=2,
                         centre=(x, y, FZ / 2.0), mat=rubber)

    # ---- front panel: a real control face with a display and two dials ----
    T.shell("WeldPanel", SPEC["panel_width"], 14.0, 140.0,
            centre=(-60.0, -SPEC["case_width"] / 2.0 - 2.0, CZ + 10.0),
            r=5.0, mat=panel_mat)
    bkit.rounded_box("WeldDisplay", 92.0, 6.0, 42.0, r=2.0, segments=1,
                     centre=(-96.0, -SPEC["case_width"] / 2.0 - 10.0,
                             CZ + 42.0), mat=led)
    for i, (x, z) in enumerate(bkit.grid_positions(cols=2, rows=1,
                                                   pitch_x=56.0, pitch_y=1.0)):
        T.knob("WeldDial%d" % i, 24.0, 24.0,
               (x - 10.0, -SPEC["case_width"] / 2.0 - 10.0, CZ - 34.0),
               mat=dark)
    T.vent_panel("WeldVent", 6, 3, 18.0, 18.0, 5.0, 104.0, 50.0, 6.0,
                 centre=(120.0, SPEC["case_width"] / 2.0 - 2.0, CZ),
                 axis="Y", mat=dark)

    # ---- carry handle ------------------------------------------------------
    bkit.arc_torus("WeldHandle", 84.0, 14.0, -12.0, 192.0,
                   centre=(-30.0, 0.0, CZ + 96.0), plane="XZ",
                   seg_major=30, mat=dark)

    # ---- the two output terminals ----------------------------------------
    for i, x in enumerate((-150.0, 60.0)):
        t = bkit.lathe("WeldTerminal%s" % "AB"[i],
                       [(0.0, 0.0), (16.0, 0.0), (16.0, 16.0),
                        (13.0, 22.0), (13.0, 34.0), (0.0, 34.0)],
                       segments=28, centre=(0, 0, 0), mat=steel)
        bkit.move(t, x, -SPEC["case_width"] / 2.0 - 12.0, CZ - 130.0)
    bkit.rounded_box("WeldTermBlock", 300.0, 26.0, 76.0, r=5.0, segments=2,
                     centre=(-45.0, -SPEC["case_width"] / 2.0 - 6.0,
                             CZ - 130.0), mat=body)

    # ---- torch lead + electrode holder ------------------------------------
    cord = bkit.thread("WeldCord", SPEC["torch_cord_diameter"] / 2.0,
                       46.0, 150.0, thread_h=2.0, segments_per_turn=18,
                       mat=rubber)
    cord.rotation_euler = (1.5708, 0.0, 0.0)
    cord.location = bkit.v(-300.0, 150.0, 130.0)
    T.grip("WeldHolder", (-300.0, 150.0, 130.0), (-320.0, 240.0, 96.0),
           38.0, 38.0, 34.0, 34.0, mat=dark, bow=5.0)
    T.rod("WeldElectrode", (-318.0, 236.0, 98.0), (-330.0, 262.0, 86.0), 3.2,
          mat=steel)

    return dict(spec=SPEC, parts=15)