"""
washing_machine -- 600 x 600 x 850 mm front-loading washer: enamelled cabinet
on four feet, a dished glass porthole door standing proud of the front, a
recessed control fascia with a programme dial, a lit display and a row of
option keys, plus a detergent drawer.

The porthole is what makes it a washing machine and not a dishwasher, so the
bezel is a real ring with a wall thickness and the glass is a truncated cone
that domes into the drum.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=600.0,
    cabinet_depth=600.0,
    cabinet_height=820.0,
    overall_height=850.0,     # feet to the top of the cabinet
    foot_height=30.0,
    corner_radius=14.0,
    porthole_diameter=344.0,  # outer diameter of the door bezel
    bezel_width=24.0,         # ring wall
    glass_diameter=300.0,
    dial_diameter=68.0,
    option_keys=4,
    key_diameter=22.0,
    key_pitch=40.0,
    display_width=120.0,
    display_x=60.0,
    dial_x=-50.0,
    key_row_x=138.0,
    drawer_x=-195.0,
    drawer_width=170.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
H = SPEC["cabinet_height"]
FOOT = SPEC["foot_height"]
TOP = FOOT + H
FRONT = -(D / 2.0)
BORE = SPEC["porthole_diameter"] / 2.0        # 172, the bezel outer radius
GLASS = SPEC["glass_diameter"] / 2.0          # 150, the glass radius
DOOR_Z = FOOT + 420.0                         # porthole centre height
# The fascia only occupies the right two thirds of the front; the detergent
# drawer owns the left third, and they must never share the same band of z.
FASCIA_X = 94.0
FASCIA_W = 376.0
FASCIA_Z = TOP - 70.0


def _on_face(t, proud=4.0):
    """Centre y for a part of thickness t moulded onto the cabinet front.

    `proud` is how far it still sinks into the skin. Without a real sink the
    part floats a hair in front of the face and reads as a decal.
    """
    return FRONT - t / 2.0 + proud


def build():
    enamel = bkit.pbr("WasherEnamel", base=(0.91, 0.91, 0.90),
                      metal=0.0, rough=0.22, coat=0.35)
    trim = bkit.preset("polished_metal")
    dark = bkit.preset("black_plastic")
    glass = bkit.preset("glass")
    lamp = bkit.pbr("WasherDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.35, 0.72, 0.95), emission_strength=1.5)

    # ---- cabinet ----------------------------------------------------------
    body = bkit.rounded_box("WasherCabinet", W, D, H, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, FOOT + H / 2.0),
                            mat=enamel)

    # ---- porthole: cut the aperture, then hang a ring on it ---------------
    cut = bkit.cylinder("_porthole_cut", BORE - SPEC["bezel_width"] - 2.0, 90.0,
                        segments=96, axis="Y", centre=(0.0, FRONT + 25.0, DOOR_Z))
    bkit.boolean(body, cut, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    # A dark drum throat behind the glass: without it the aperture is a window
    # into the bright inside of the cabinet and the door reads as a hole.
    bkit.cylinder("DrumThroat", BORE - SPEC["bezel_width"] - 2.0, 12.0,
                  segments=96, axis="Y", centre=(0.0, FRONT + 38.0, DOOR_Z),
                  mat=dark)

    # ---- door ring and glass ---------------------------------------------
    # The ring's back face is 6 mm inside the cabinet skin, so the two surfaces
    # cross instead of meeting tangentially.
    bkit.tube("DoorBezel", BORE, BORE - SPEC["bezel_width"], 40.0, segments=96,
              axis="Y", centre=(0.0, FRONT - 14.0, DOOR_Z), mat=trim)
    # r2 lands on the +Z end of the local cylinder, and place(axis="Y") maps
    # local +Z to world -Y, so r2 is the diameter seen from the front: the glass
    # bulges toward the viewer and narrows back into the drum, like a real
    # porthole. Reversing the two radii would dish the glass the wrong way.
    bkit.cylinder("DoorGlass", GLASS - 26.0, 26.0, segments=96, axis="Y",
                  r2=GLASS, centre=(0.0, FRONT - 30.0, DOOR_Z), mat=glass)
    bkit.rounded_box("DoorGrip", 30.0, 26.0, 130.0, r=10.0, segments=3,
                     centre=(BORE - 12.0, FRONT - 44.0, DOOR_Z), mat=trim)

    # ---- control fascia ---------------------------------------------------
    # A recessed strip, not a sticker: it is set back into the cabinet top so
    # the fascia reads as a separate moulding. It covers only the right two
    # thirds; the detergent drawer gets the left third to itself.
    fz = FASCIA_Z
    cut2 = bkit.rounded_box("_fascia_cut", FASCIA_W, 40.0, 96.0, r=8.0,
                            segments=3, centre=(FASCIA_X, FRONT + 12.0, fz))
    bkit.boolean(body, cut2, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    bkit.rounded_box("ControlFascia", FASCIA_W - 4.0, 16.0, 92.0, r=6.0,
                     segments=3, centre=(FASCIA_X, _on_face(16.0), fz),
                     mat=dark)

    # ---- programme dial, display and option keys --------------------------
    bkit.cylinder("ProgramDial", SPEC["dial_diameter"] / 2.0, 26.0, segments=48,
                  axis="Y", centre=(SPEC["dial_x"], _on_face(26.0), fz), mat=trim)
    bkit.rounded_box("DialPointer", 5.0, 10.0, 18.0, r=1.5, segments=2,
                     centre=(SPEC["dial_x"], _on_face(26.0, 15.0), fz + 22.0),
                     mat=dark)

    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 8.0, 46.0, r=3.0,
                     segments=2, centre=(SPEC["display_x"], _on_face(8.0), fz),
                     mat=lamp)

    # The option keys are spaced from the real key diameter plus the real gap,
    # so the row can never come out uneven or hand-placed off the fascia.
    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["option_keys"], gap=SPEC["key_pitch"] - kd,
                         centre=False)):
        bkit.cylinder("OptionKey%d" % i, kd / 2.0, 12.0, segments=32, axis="Y",
                      centre=(SPEC["key_row_x"] + x, _on_face(12.0), fz), mat=trim)

    # ---- detergent drawer -------------------------------------------------
    bkit.rounded_box("DetergentDrawer", SPEC["drawer_width"], 34.0, 70.0,
                     r=8.0, segments=4,
                     centre=(SPEC["drawer_x"], _on_face(34.0, 6.0), TOP - 48.0),
                     mat=enamel)
    bkit.rounded_box("DrawerHandle", 120.0, 12.0, 14.0, r=4.0, segments=2,
                     centre=(SPEC["drawer_x"], _on_face(34.0, 34.0), TOP - 78.0),
                     mat=trim)

    # ---- feet -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 24.0, FOOT, segments=32,
                          centre=(sx * (W / 2.0 - 56.0), sy * (D / 2.0 - 56.0),
                                  FOOT / 2.0),
                          mat=dark)

    return dict(spec=SPEC, parts=17)


CHECKS = [
    dict(name="cabinet_width", mm=600.0, tol=0.5, how="bbox_x", part="WasherCabinet"),
    dict(name="cabinet_depth", mm=600.0, tol=0.5, how="bbox_y", part="WasherCabinet"),
    dict(name="overall_height", mm=850.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=600.0, tol=0.5, how="bbox_x"),
    dict(name="porthole_diameter", mm=344.0, tol=0.5, how="diameter",
         part="DoorBezel"),
    dict(name="dial_diameter", mm=68.0, tol=0.4, how="diameter", part="ProgramDial"),
]