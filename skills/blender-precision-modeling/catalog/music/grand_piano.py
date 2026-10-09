"""
grand_piano -- baby-grand piano, 2050 x 1520 x 1010 mm, lid open.

The grand's signature is the plan curve: a straight left (bass) side and a bent
right (treble) side that wraps from the keyboard round to the tail. That is a
loft, but the axes have to be right -- the plan ring lies in the XY plane and
the STATIONS advance along Z, so the piano's length runs along Z and its width
along X. Building the ring in XZ instead (the obvious mistake) turns a
2050 x 1520 grand into a 3170 mm one.

The lid is a second loft of the same outline, hinged along the straight bass
side and lifted, because a closed-lid grand renders as a coffin. The 88 keys
reuse the upright's computed keyboard: 52 naturals from one `lay_out`, 36 sharps
from the A#-C#-D#-F#-G#-A# octave offsets at 0.58 of a pitch past each natural.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=2050.0,
    width=1520.0,
    height=1010.0,
    case_height=270.0,
    leg_height=740.0,
    lid_open_deg=36.0,
    keys=88,
    white_keys=52,
    black_keys=36,
    key_pitch=23.5,
    key_gap=1.2,
    key_height=22.0,
)

L, W = SPEC["length"], SPEC["width"]
CASE_H, LEG_H = SPEC["case_height"], SPEC["leg_height"]
PITCH, GAP = SPEC["key_pitch"], SPEC["key_gap"]
STATIONS = 24


def half_at(x):
    """Half width of the plan at station x (tail x=0 -> keyboard x=L).

    The BASS edge is straight and the TREBLE edge bends, so every section is
    anchored at -W/2 and only its far edge sweeps: that asymmetry is the
    grand's signature and a symmetric ellipse cannot express it.
    """
    plan = [(0.0, 320.0), (260.0, 450.0), (600.0, 570.0), (1000.0, 660.0),
            (1400.0, 720.0), (1750.0, 755.0), (1950.0, 760.0), (L, 730.0)]
    for i in range(len(plan) - 1):
        x0, x1 = plan[i][0], plan[i + 1][0]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            t = t * t * (3.0 - 2.0 * t)
            return plan[i][1] + (plan[i + 1][1] - plan[i][1]) * t
    return plan[-1][1]


def case_ring(x, z0, height=CASE_H, r=26.0, per_corner=4):
    """One case cross-section in the YZ plane at station x.

    The ring is a rounded rectangle `height` tall and `2*half_at(x)` wide,
    anchored so its -Y edge stays on the straight bass line at y = -W/2.
    """
    half = half_at(x)
    ring = bkit.rounded_rect_section(half * 2.0, height, r=r,
                                     per_corner=per_corner)
    return [(x, -W / 2.0 + half + u, z0 + height / 2.0 + v) for (u, v) in ring]


def build():
    black = bkit.pbr("GrandCase", base=(0.07, 0.07, 0.08), rough=0.18,
                     coat=0.7)
    rim = bkit.pbr("GrandRim", base=(0.05, 0.05, 0.06), rough=0.22)
    gold = bkit.pbr("GrandGold", base=(0.80, 0.64, 0.30), metal=0.85,
                    rough=0.26)
    hw = bkit.pbr("GrandHardware", base=(0.80, 0.81, 0.83), metal=0.85,
                  rough=0.22)
    nat = bkit.pbr("GrandNatural", base=(0.93, 0.92, 0.88), rough=0.28)
    sharp = bkit.pbr("GrandSharp", base=(0.04, 0.04, 0.045), rough=0.30)
    plate = bkit.pbr("GrandPlate", base=(0.72, 0.66, 0.40), metal=0.85,
                     rough=0.30)

    # ---- case: the plan lofted along the piano's LENGTH (world X) ----------
    # The loft's stations advance in X and each ring lies in the YZ plane, so
    # the case stands on its legs with the keyboard at +X. Building the ring in
    # XZ instead lays the whole instrument on its side.
    secs = [case_ring(L * i / STATIONS, LEG_H) for i in range(STATIONS + 1)]
    case = bkit.loft("GrandCaseBody", secs, mat=black)
    bkit.recalc(case)
    bkit.bevel(case, width_mm=3.0, segments=2, angle_deg=40)

    # Soundboard: a flat plate just under the rim, same plan.
    bkit.loft("GrandSoundboard",
              [case_ring(x, LEG_H + CASE_H - 16.0, height=16.0, r=6.0)
               for x in (0.0, L * 0.5, L)], mat=plate)

    # Rim wall standing on the case, giving the grand its depth.
    bkit.loft("GrandRim",
              [case_ring(x, LEG_H + CASE_H, height=46.0, r=18.0)
               for x in (0.0, L * 0.25, L * 0.5, L * 0.75, L)], mat=rim)

    # ---- lid: same plan, hinged along the straight bass side and lifted ----
    # Built with the hinge edge on y = 0 and z = 0, so ONE rotation about X
    # raises the whole lid about the straight bass line.
    lid_secs = []
    for i in range(9):
        x = L * i / 8.0
        half = half_at(x)
        ring = bkit.rounded_rect_section(half * 2.0, 26.0, r=20.0, per_corner=4)
        lid_secs.append([(x, half + u, v) for (u, v) in ring])
    lid = bkit.loft("GrandLid", lid_secs, mat=black)
    bkit.recalc(lid)
    bkit.bevel(lid, width_mm=2.0, segments=2, angle_deg=40)
    # Hinge along the straight bass edge. Rotation about X is POSITIVE to lift:
    # with the hinge at y = -W/2 and the lid extending in +y, +theta swings that
    # span up. (A negative angle drops the lid through the case -- its bbox then
    # ran from z=128 to z=1033 instead of sitting above the rim at z=1010.)
    lid.rotation_euler = (math.radians(SPEC["lid_open_deg"]), 0.0, 0.0)
    bkit.move(lid, 0.0, -W / 2.0, LEG_H + CASE_H + 12.0)

    # Prop holding the open lid. The lid rotates about the bass line
    # (y = -W/2, z = LEG_H + CASE_H + 12), so the lid's underside at along-lid
    # distance d sits at (hinge_y + d*cos, hinge_z + d*sin). Placing the prop on
    # that arc is what makes its top actually MEET the lid instead of floating
    # above it -- an earlier version used a fixed 300 mm length and floated.
    prop_x = L * 0.30
    prop_d = 2.0 * half_at(prop_x) * 0.70
    th = math.radians(SPEC["lid_open_deg"])
    hinge_y, hinge_z = -W / 2.0, LEG_H + CASE_H + 12.0
    prop_y = hinge_y + prop_d * math.cos(th)
    prop_top_z = hinge_z + prop_d * math.sin(th)
    prop_bot_z = LEG_H + CASE_H - 10.0
    bkit.cylinder("GrandLidProp", 9.0, prop_top_z - prop_bot_z, segments=12,
                  centre=(prop_x, prop_y,
                          (prop_top_z + prop_bot_z) / 2.0), axis="Z", mat=hw)

    # ---- keyboard: 88 keys, same computed layout as the upright ------------
    # Keys run across the WIDTH (Y), so a key's long dimension is in X: it
    # sticks away from the player toward the tail.
    kx = L - 130.0                     # keyboard end of the length axis
    kz = LEG_H - 70.0
    naturals = []
    for i, (y, w) in enumerate(bkit.lay_out([PITCH - GAP] * 52, gap=GAP)):
        # sx is the key's LENGTH (into the instrument, along X) and sy is its
        # width on the run (along Y). Swapping them makes every key 150 mm wide
        # and the keyboard 1348 mm instead of 1219.
        naturals.append(bkit.rounded_box(
            "GrandNaturalKey%02d" % i, 150.0, w, SPEC["key_height"], r=1.2,
            segments=2, centre=(kx - 96.0, y,
                                kz + SPEC["key_height"] / 2.0), mat=nat))
    octave_offsets = [0.58, 1.58, 2.58, 4.58, 5.58, 6.58]
    sharps = []
    n = 0
    for o in range(7):
        base = 1.0 + o * 7.0
        for k in octave_offsets:
            u = base + k
            if u >= 52.0:
                continue
            sharps.append(bkit.rounded_box(
                "GrandSharpKey%02d" % n, 96.0, 11.0, SPEC["key_height"] + 12.0,
                r=1.2, segments=2,
                centre=(kx - 122.0, -52.0 * PITCH / 2.0 + u * PITCH,
                        kz + SPEC["key_height"] + 6.0), mat=sharp))
            n += 1
    bkit.join(naturals, name="GrandNaturalKeys")
    bkit.join(sharps, name="GrandSharpKeys")
    bkit.rounded_box("GrandKeyBed", 250.0, 52 * PITCH + 30.0, 44.0, r=4.0,
                     segments=2, centre=(kx - 30.0, 0.0, kz - 22.0), mat=rim)
    bkit.rounded_box("GrandFallboard", 34.0, 52 * PITCH + 40.0, 200.0, r=4.0,
                     segments=2, centre=(kx + 120.0, 0.0, kz + 150.0),
                     mat=black)
    bkit.rounded_box("GrandMusicDesk", 16.0, 470.0, 330.0, r=4.0, segments=3,
                     centre=(kx + 40.0, 0.0, kz + 420.0), mat=rim)
    bkit.rounded_box("GrandDeskLip", 46.0, 470.0, 30.0, r=4.0, segments=2,
                     centre=(kx + 16.0, 0.0, kz + 268.0), mat=rim)

    # ---- three lathed legs and castors ------------------------------------
    leg_prof = [(0.0, 0.0), (98.0, 0.0), (98.0, 42.0), (74.0, 130.0),
                (62.0, 420.0), (80.0, 640.0), (98.0, 700.0), (98.0, LEG_H),
                (0.0, LEG_H)]
    for i, (x, y) in enumerate(((200.0, 0.0),
                                (L - 120.0, -W / 2.0 + 190.0),
                                (L - 120.0, W / 2.0 - 190.0))):
        leg = bkit.lathe("GrandLeg%d" % i, leg_prof, segments=28,
                         centre=(0, 0, 0), mat=black)
        bkit.move(leg, x, y, 0.0)
        bkit.cylinder("GrandCastor%d" % i, 52.0, 40.0, segments=16,
                      centre=(x, y, 52.0), axis="Y", mat=gold)

    # ---- lyre, pedals, badge ----------------------------------------------
    bkit.rounded_box("GrandLyre", 40.0, 190.0, 250.0, r=8.0, segments=3,
                     centre=(L - 260.0, W / 2.0 - 230.0, 190.0), mat=rim)
    for i, (y, _w) in enumerate(bkit.lay_out([44.0] * 3, gap=22.0)):
        bkit.rounded_box("GrandPedal%d" % i, 180.0, 44.0, 13.0, r=5.0,
                         segments=2,
                         centre=(L - 340.0, W / 2.0 - 230.0 + y, 60.0),
                         mat=gold)
    bkit.box("GrandBadge", 8.0, 150.0, 34.0,
             centre=(L - 30.0, 0.0, LEG_H + CASE_H * 0.55), mat=gold)

    return dict(spec=SPEC, parts=9, keys=52 + len(sharps))


CHECKS = [
    dict(name="length", mm=2050.0, tol=4.0, how="bbox_x", part="GrandCaseBody"),
    dict(name="width", mm=1520.0, tol=4.0, how="bbox_y", part="GrandCaseBody"),
    dict(name="case_height", mm=270.0, tol=2.0, how="bbox_z",
         part="GrandCaseBody"),
    dict(name="keyboard_width", mm=1219.0, tol=2.0, how="bbox_y",
         part="GrandNaturalKeys"),
]