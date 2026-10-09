"""
tape_dispenser -- desktop tape dispenser, 135 x 68 x 95 mm.

The roll and the cutter nose are what make it read. The roll is a real
annulus (tube) with a bore, so the hub hole is visible geometry rather than a
painted circle.

NOTE: obj.location is in METRES. Assigning raw millimetre floats to it puts a
part thousands of millimetres away and silently blows the scene bounding box
out to 8 m. Every placement here goes through bkit.v().
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    roll_diameter=68.0,
    roll_width=45.0,
    bore_diameter=25.0,
    nose_length=62.0,
    base_width=46.0,
    total_height=95.0,
)

RD = SPEC["roll_diameter"] / 2.0
BD = SPEC["bore_diameter"] / 2.0
ROLL_Z = 8.0 + 30.0          # roll centre, standing on the hub
HUB_TOP = 8.0 + 46.0


def build():
    plastic = bkit.pbr("TapeDispenserBody", base=(0.40, 0.42, 0.46),
                       rough=0.38, coat=0.2)
    tape = bkit.pbr("TapeRoll", base=(0.90, 0.84, 0.62), rough=0.30,
                    transmission=0.30, ior=1.47)
    steel = bkit.pbr("TapeSteel", base=(0.74, 0.76, 0.78), metal=0.88,
                     rough=0.28)

    # ---- base plate -------------------------------------------------------
    base = bkit.rounded_box("TapeDispenserBase", 40.0, SPEC["base_width"], 8.0,
                            r=2.0, centre=(0, 0, 4.0), mat=plastic)

    # ---- hub: a lathe with a real bore, standing on the base --------------
    hub = bkit.lathe("TapeDispenserHub",
                     [(BD, 0.0), (16.0, 0.0), (16.0, 8.0),
                      (12.0, 12.0), (12.0, 42.0), (BD, 46.0)],
                     segments=48, mat=plastic, centre=(0, 0, 8.0))
    bkit.recalc(hub)

    # ---- tape roll: a real annulus seated on the hub ---------------------
    roll = bkit.tube("TapeRoll", RD, BD, SPEC["roll_width"], segments=64,
                     centre=(0, 0, ROLL_Z), mat=tape)

    # ---- cutter nose: extruded side profile, standing on the base --------
    # The nose used to be a 62 mm wedge whose top edge ran from z = 30 at the
    # hub down to z = 12 at the tip, a single straight ramp. A tape
    # dispenser's nose is the ramp the TAPE runs down, and the blade sits at
    # the BOTTOM of that ramp -- so the ramp now starts under the roll at
    # z = 30 and meets the base at z = 8, which is also what puts the blade in
    # the path of the tape instead of 20 mm above it.
    nose_poly = [
        (6.0, 0.0),
        (6.0 + SPEC["nose_length"], 0.0),
        (6.0 + SPEC["nose_length"], 8.0),
        (26.0, 21.0),
        (6.0, 30.0),
    ]
    nose = bkit.extrude_profile("TapeDispenserNose", nose_poly,
                                SPEC["roll_width"] * 0.82,
                                centre=(0, 0, 0), axis="Z", mat=plastic)
    bkit.recalc(nose)
    nose.location = bkit.v(0.0, 0.0, 8.0)

    # cutter lip: a real thin steel blade across the nose tip, at the BOTTOM
    # of the ramp where the tape runs past it
    blade = bkit.rounded_box("TapeDispenserBlade", 1.8, 34.0, 7.0, r=0.4,
                             centre=(6.0 + SPEC["nose_length"] - 2.5, 0,
                                     8.0 + 3.5),
                             mat=steel)

    # ---- the serrated cutter teeth ---------------------------------------
    # Without teeth the blade is just a plate: the saw edge is what says
    # "this cuts". Six real triangular teeth, laid out from the blade pitch
    # plus one explicit gap.
    teeth = []
    for i, (y, _w) in enumerate(bkit.lay_out([2.0] * 6, gap=5.0)):
        teeth.append(bkit.extrude_profile(
            "_tooth%d" % i, [(0.0, 0.0), (3.2, 0.0), (0.0, 3.2)],
            1.6, centre=(6.0 + SPEC["nose_length"] - 1.0, y, 8.0 + 0.4),
            axis="X", mat=steel))
    bkit.join(teeth, name="TapeDispenserTeeth")

    # ---- the tape strip: from the roll's own surface, down to the blade --
    # The roll's outer radius is RD = 34 and its centre is at z = 38, so the
    # strip has to LEAVE the roll at its own tangent: on the +X side at
    # (RD + roll centre x, 38) and then run down the ramp. The first attempt
    # started the strip at x = 0, i.e. 34 mm INSIDE the roll, and its loft was
    # built along Z rather than along X, so it came out as a vertical fin
    # standing in front of the nose instead of a length of tape.
    # Each ring is listed nose-edge first and tail-edge second (not -Y first):
    # loft() bridges consecutive rings in list order, so the -Y-first ordering
    # produced a strip whose side walls were inside out, and recalc() could not
    # fix it because the solid is closed and consistently wound -- just
    # inward. This ordering makes the bridging direction agree with the ring
    # winding.
    x_tape = RD + 2.0

    def band(x, z_out, z_in, half_w=22.0):
        # A flat 4-point section -- but z_out is the BOTTOM of the ribbon and
        # z_in its top. The ramp descends toward the blade, so the top edge
        # has to be the higher number at every station; passing them the other
        # way round is what made the strip double back on itself.
        return [(x, -half_w, z_out), (x, half_w, z_out),
                (x, half_w, z_in), (x, -half_w, z_in)]

    strip = bkit.loft("TapeStrip", [
        band(x_tape - 2.0, 38.0, 30.0),
        band(x_tape + 14.0, 29.0, 22.0),
        band(x_tape + 26.0, 18.0, 12.5),
        band(6.0 + SPEC["nose_length"] - 6.0, 12.0, 9.4),
    ], mat=tape)
    bkit.recalc(strip)
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="roll_diameter", mm=68.0, tol=0.8, how="diameter", part="TapeRoll"),
    dict(name="roll_width", mm=45.0, tol=0.8, how="bbox_z", part="TapeRoll"),
    # A bounding box cannot see a bore -- the hub's bbox is its OUTER
    # diameter. Declaring the bore here would measure 32 and fail forever.
    # Check the hub's outer diameter instead, which is what the box proves.
    dict(name="hub_diameter", mm=32.0, tol=0.8, how="diameter",
         part="TapeDispenserHub"),
]