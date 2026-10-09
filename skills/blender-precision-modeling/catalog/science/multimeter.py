"""
multimeter -- 90 x 50 x 190 mm handheld digital multimeter: rubber overmould
case, recessed 64 x 42 mm LCD, a 48 mm sixteen-position rotary selector, a
four-key pad, three input jacks and two test-lead stubs.

The selector is the point of the model. Sixteen detents is not decoration: the
tick ring is one `box` built at radius 30 from the world Y axis, swept by one
`array_radial`, then moved onto the dial. Building the dial in place and
sweeping there is the documented failure -- the sweep orbits the world origin,
not the dial centre.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    case_width=90.0,
    case_depth=50.0,
    case_height=190.0,
    screen_width=64.0,
    screen_height=42.0,
    switch_diameter=48.0,
    switch_positions=16,
    keypad_buttons=4,
    input_jacks=3,
)

CW, CD, CH = SPEC["case_width"], SPEC["case_depth"], SPEC["case_height"]
FRONT = -CD / 2.0                    # -25


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("DmmShell", base=(0.10, 0.10, 0.11), rough=0.44)
    overmould = bkit.pbr("DmmOvermould", base=(0.82, 0.30, 0.08), rough=0.68)
    dark = bkit.pbr("DmmDark", base=(0.055, 0.055, 0.060), rough=0.40)
    lcd = bkit.pbr("DmmLcd", base=(0.10, 0.14, 0.11), rough=0.08,
                   emission=(0.55, 0.80, 0.45), emission_strength=1.3)
    nickel = bkit.preset("brushed_metal")

    # ---- overmoulded case, recessed 3 mm into the front bezel ------------
    bkit.rounded_box("DmmCase", CW, CD, CH, r=10.0, segments=4,
                     centre=(0.0, 0.0, CH / 2.0), mat=shell)
    bkit.rounded_box("DmmBezel", 84.0, 6.0, 150.0, r=8.0, segments=3,
                     centre=(0.0, FRONT + 2.0, 96.0), mat=dark)

    # ---- recessed LCD ------------------------------------------------------
    _recess("DmmScreen", bpy.data.objects["DmmBezel"], SPEC["screen_width"],
            SPEC["screen_height"], 0.0, 146.0, lcd)

    # ---- 48 mm sixteen-position rotary selector ---------------------------
    bkit.cylinder("DmmSwitch", SPEC["switch_diameter"] / 2.0, 18.0,
                  segments=48, axis="Y", centre=(0.0, FRONT + 8.0, 86.0),
                  mat=overmould)
    bkit.box("SwitchPointer", 2.4, 3.0, 18.0, mat=shell,
             centre=(0.0, FRONT - 1.5, 96.0))
    # Tick ring built at radius 30 from the world Y axis so array_radial has a
    # real axis to orbit, then moved onto the dial centre.
    tick = bkit.box("_tick", 4.0, 8.0, 1.4, centre=(0.0, 0.0, 30.0),
                    mat=shell)
    bkit.array_radial(tick, count=SPEC["switch_positions"], axis="Y")
    bkit.move(tick, 0.0, FRONT + 2.0, 86.0)

    # ---- four keys on one grid -------------------------------------------
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(2, 2, 28.0, 18.0)):
        keys.append(bkit.rounded_box(
            "_key%d" % i, 20.0, 6.0, 13.0, r=2.5, segments=2, mat=shell,
            centre=(kx, FRONT + 2.0, 36.0 + kz)))
    bkit.join(keys, name="DmmKeypad")

    # ---- three input jacks and two lead stubs ----------------------------
    jacks = []
    for i, (jx, jw) in enumerate(bkit.lay_out([16.0] * SPEC["input_jacks"],
                                               gap=8.0)):
        jacks.append(bkit.cylinder("_jack%d" % i, 6.0, 6.0, segments=24,
                                   axis="Y", mat=nickel,
                                   centre=(jx, FRONT + 1.0, 12.0)))
        jacks.append(bkit.cylinder("_jackr%d" % i, 3.0, 8.0, segments=20,
                                   axis="Y", mat=dark,
                                   centre=(jx, FRONT + 1.0, 12.0)))
    bkit.join(jacks, name="DmmJacks")

    for side, mx in ((-1, overmould), (1, dark)):
        bkit.cylinder("LeadStub" + ("R" if side < 0 else "K"), 3.5, 26.0,
                      segments=20, axis="Y", mat=mx,
                      centre=(side * 30.0, FRONT - 13.0, 12.0))

    # ---- battery hatch on the back and a hold switch ---------------------
    bkit.rounded_box("BatteryHatch", 60.0, 4.0, 96.0, r=3.0, segments=2,
                     centre=(0.0, CD / 2.0 - 0.5, 100.0), mat=overmould)
    bkit.rounded_box("HoldSwitch", 16.0, 5.0, 10.0, r=2.0, segments=2,
                     centre=(28.0, FRONT + 2.0, 168.0), mat=overmould)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="case_width", mm=90.0, tol=0.5, how="bbox_x", part="DmmCase"),
    dict(name="case_depth", mm=50.0, tol=0.5, how="bbox_y", part="DmmCase"),
    dict(name="case_height", mm=190.0, tol=0.6, how="bbox_z", part="DmmCase"),
    dict(name="screen_width", mm=64.0, tol=0.5, how="bbox_x",
         part="DmmScreen"),
    dict(name="switch_diameter", mm=48.0, tol=0.5, how="diameter",
         part="DmmSwitch"),
]