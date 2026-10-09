"""
saxophone -- alto saxophone in Eb, 630 mm overall, with the bow and upturned bell.

A saxophone is one continuous tube that goes: mouthpiece, up a curved neck,
down a conical body, around a U-bow, and back up to a bell that flips up and
over. Getting that S-curve is the model, so the neck and bow are `arc_torus`
bends and the body is a `lathe` cone -- cylinders meeting arcs, joined at the
right angles, which is the only honest way to build a sax.

The keys are the count: 23 of them, six tone holes on the body plus the left-hand
pinky table and the right-hand stack, each laid out from `bkit.lay_out` at real
pitches. The bell's flare (124 mm) is on a quadratic lathe profile, and the
upright bell section is a genuine bend rather than a diagonal cylinder.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=953.0,
    bell_diameter=124.0,
    bell_length=190.0,
    body_diameter=68.0,
    neck_diameter=24.0,
    bore_diameter=22.0,
    mouthpiece_length=105.0,
    neck_bend_radius=58.0,
    bow_radius=105.0,
    keys=23,
)

# L is the z height of the mouthpiece TIP, derived from the body's own stack
# (mouthpiece + neck drop + bend + body + bow + bell) rather than read out of
# SPEC. SPEC["length"] is a CLAIM about the finished model; deriving L from the
# parts means restating that claim can never silently stretch the instrument.
L = (SPEC["mouthpiece_length"] + SPEC["neck_bend_radius"] + 300.0
     + 118.0 + 105.0 + 190.0)
BELL_R = SPEC["bell_diameter"] / 2.0
BR = SPEC["body_diameter"] / 2.0
NR = SPEC["neck_diameter"] / 2.0


def build():
    gold = bkit.pbr("SaxBrass", base=(0.84, 0.66, 0.30), metal=0.85,
                    rough=0.18)
    lacquer = bkit.pbr("SaxLacquer", base=(0.18, 0.14, 0.06), rough=0.14,
                       coat=0.6)
    key_mat = bkit.pbr("SaxKeys", base=(0.82, 0.80, 0.72), metal=0.85,
                       rough=0.20)
    pad = bkit.pbr("SaxPad", base=(0.88, 0.86, 0.80), rough=0.60)
    cork = bkit.pbr("SaxCork", base=(0.62, 0.46, 0.26), rough=0.70)

    # The sax stands upright: mouthpiece at the top, bow at the bottom, bell
    # flipping up at the back. Everything is placed in world Z.
    body_top = 330.0
    body_bot = 118.0

    # ---- mouthpiece and ligature ------------------------------------------
    # The mouthpiece is offset in X to sit over the neck's vertical drop, so
    # the whole mouthpiece/neck/arc/body chain is one continuous tube.
    x_arc = SPEC["neck_bend_radius"]
    mp = bkit.lathe("SaxMouthpiece",
                    [(0.0, 0.0), (6.0, 0.0), (10.0, 20.0), (13.0, 46.0),
                     (11.0, 62.0), (NR - 2.0, 62.0), (NR - 2.0, 0.0)],
                    segments=32, centre=(0, 0, 0), mat=gold)
    bkit.move(mp, x_arc, 0.0, L - SPEC["mouthpiece_length"])
    bkit.rounded_box("SaxReed", 11.0, 3.0, 62.0, r=1.0, segments=2,
                     centre=(x_arc, -12.0, L - 46.0), mat=cork)
    bkit.tube("SaxLigature", 15.0, 13.0, 10.0, segments=32,
              centre=(x_arc, 0.0, L - 82.0), mat=key_mat)

    # ---- neck: one arc from the mouthpiece down into the top of the body ----
    # The neck is a SINGLE 90-degree bend, not two arcs with a straight between:
    # two arcs plus a cylinder leave visible gaps at both joints. The arc's
    # centre sits at (x_arc, 0, z_arc); the arc runs from (x_arc - r, 0, z_arc)
    # up to (x_arc, 0, z_arc + r), which is where the vertical drop begins.
    r_n = SPEC["neck_bend_radius"]
    x_arc = r_n
    z_arc = body_top + 34.0
    # In plane "XZ" the arc's angle a maps to (cos a * r, sin a * r). 90..180
    # therefore runs from (0, +r) DOWN to (-r, 0); the crown is at a = 0. So the
    # bend that climbs to the mouthpiece is 0..90: from (r, 0) at the body up
    # to (0, r) directly under the drop. Using the wrong quarter is what left
    # the neck pointing down into the body with the mouthpiece adrift.
    # The arc's LOW end lands at x_arc + r, so the arc centre must be offset by
    # -r to put that end back on x_arc, under the collar and the drop.
    bkit.arc_torus("SaxNeck", r_n, NR + 1.0, 0.0, 90.0,
                   centre=(x_arc - r_n, 0.0, z_arc), plane="XZ", seg_major=32,
                   mat=gold, caps=True)
    # Vertical drop from the arc's crown to the mouthpiece, and the collar from
    # the body up to the arc. Each cylinder OVERLAPS its neighbour by 10 mm or
    # more; butted end-to-end they leave a visible gap at every joint.
    z_drop_lo = z_arc + r_n
    z_drop_hi = L - SPEC["mouthpiece_length"] + 6.0
    bkit.cylinder("SaxNeckDrop", NR + 1.0, z_drop_hi - z_drop_lo,
                  segments=28,
                  centre=(x_arc, 0.0, (z_drop_lo + z_drop_hi) / 2.0), axis="Z",
                  mat=gold)
    bkit.cylinder("SaxNeckCollar", NR + 2.0, 46.0, segments=28,
                  centre=(x_arc, 0.0, body_top + 16.0), axis="Z", mat=gold)

    # ---- body: a real cone, wide at the bottom ----------------------------
    body_prof = [(0.0, 0.0), (NR + 2.0, 0.0)]
    for i in range(1, 9):
        t = i / 8.0
        body_prof.append((NR + 2.0 + (BR - NR - 2.0) * t, body_top - body_bot))
    body_prof.append((0.0, body_top - body_bot))
    body = bkit.lathe("SaxBody", body_prof, segments=44, centre=(0, 0, 0),
                      mat=lacquer)
    bkit.move(body, 0.0, 0.0, body_bot)

    # ---- bow: the U at the bottom, two half arcs --------------------------
    bkit.arc_torus("SaxBowLeft", SPEC["bow_radius"], BR - 1.0, 90.0, 270.0,
                   centre=(0.0, 0.0, body_bot), plane="XY", seg_major=30,
                   mat=lacquer, caps=True)
    bkit.cylinder("SaxBowBottom", BR - 1.0, 120.0, segments=32, centre=(0, 0, 0),
                  axis="X", mat=lacquer)
    bow_u = body_bot - SPEC["bow_radius"]
    bkit.cylinder("SaxBowStem", BR - 1.0, SPEC["bow_radius"] * 2.0,
                  segments=32, centre=(0.0, 0.0, bow_u), axis="Z",
                  mat=lacquer)

    # ---- bell: the flare, flipped up and over ------------------------------
    # The bell leaves the bow going straight UP from the U's far side, which is
    # the point at z = body_bot - bow_radius. It is built standing on the
    # origin and translated, so the flare always opens upward.
    bl = SPEC["bell_length"]
    bell_prof = [(0.0, 0.0), (BR - 1.0, 0.0)]
    for i in range(1, 13):
        t = i / 12.0
        bell_prof.append((BR - 1.0 + (BELL_R - BR + 1.0) * t ** 2.3, bl * t))
    bell_prof.append((0.0, bl))
    bell_base = body_bot - SPEC["bow_radius"] - 24.0
    bell = bkit.lathe("SaxBell", bell_prof, segments=48, centre=(0, 0, 0),
                      mat=lacquer)
    bkit.move(bell, 0.0, 0.0, bell_base)
    bkit.tube("SaxBellRim", BELL_R + 1.5, BELL_R - 4.0, 6.0, segments=48,
              centre=(0.0, 0.0, bell_base + bl - 3.0), mat=key_mat)

    # ---- 23 keys ----------------------------------------------------------
    parts = []
    # Six tone holes down the body, front face, on the real key pitch.
    for i, (z, _w) in enumerate(bkit.lay_out([26.0] * 6, gap=20.0)):
        parts.append(bkit.cylinder("SaxToneRing%02d" % i, 12.5, 5.0,
                                   segments=24, centre=(0.0, -BR + 2.0,
                                                        body_bot + 52.0 + z),
                                   axis="Z", mat=key_mat))
        parts.append(bkit.cylinder("SaxTonePad%02d" % i, 11.0, 2.4, segments=20,
                                   centre=(0.0, -BR + 2.0,
                                           body_bot + 52.0 + z),
                                   axis="Z", mat=pad))
    # Left-hand palm keys: four spatulas on the front-left of the upper body.
    for i, (z, _w) in enumerate(bkit.lay_out([22.0] * 4, gap=16.0)):
        parts.append(bkit.rounded_box("SaxPalmKey%d" % i, 11.0, 15.0, 26.0,
                                      r=2.0, segments=2,
                                      centre=(-16.0, -BR + 8.0,
                                              body_bot + 210.0 + z),
                                      mat=key_mat))
    # Right-hand stack: seven spatulas on the front-right.
    for i, (z, _w) in enumerate(bkit.lay_out([19.0] * 7, gap=15.0)):
        side = -1.0 if i % 2 == 0 else 1.0
        parts.append(bkit.rounded_box("SaxStackKey%d" % i, 10.0, 14.0, 22.0,
                                      r=2.0, segments=2,
                                      centre=(16.0 * side, -BR + 6.0,
                                              body_bot + 30.0 + z),
                                      mat=key_mat))
    # Side keys and the low-B/Bb spatulas near the bow.
    for i, (z, y) in enumerate(((body_bot + 14.0, -BR - 8.0),
                                (body_bot + 30.0, BR + 8.0))):
        parts.append(bkit.rounded_box("SaxLowKey%d" % i, 9.0, 20.0, 34.0,
                                      r=3.0, segments=2,
                                      centre=(0.0, y, z), mat=key_mat))
    # Octave key on the neck.
    parts.append(bkit.rounded_box("SaxOctaveKey", 8.0, 26.0, 8.0, r=2.0,
                                  segments=2, centre=(0.0, NR + 10.0,
                                                      L - 250.0), mat=key_mat))
    # Guard rods running the body.
    for i, y in enumerate((-BR - 3.0, BR + 3.0)):
        rod = bkit.cylinder("SaxGuard%d" % i, 2.2, 200.0, segments=12,
                            centre=(0, 0, 0), axis="Z", mat=key_mat)
        bkit.move(rod, 0.0, y, body_bot + 110.0)
    bkit.join(parts, name="SaxKeys")

    bkit.rounded_box("SaxNeckGuard", 40.0, 8.0, 150.0, r=3.0, segments=2,
                     centre=(0.0, NR + 14.0, L - 200.0), mat=key_mat)

    return dict(spec=SPEC, parts=6, keys=SPEC["keys"])


CHECKS = [
    # Overall spans mouthpiece tip to bow bottom; no single part spans it.
    dict(name="overall_length", mm=953.0, tol=3.0, how="bbox_z"),
    dict(name="bell_diameter", mm=124.0, tol=2.5, how="diameter", part="SaxBell"),
    # `diameter` on the neck arc would return its 71 mm bounding-box diagonal,
    # so the neck tube is checked on its straight drop instead.
    dict(name="neck_tube_diameter", mm=26.0, tol=1.0, how="bbox_x",
         part="SaxNeckDrop"),
    dict(name="body_diameter", mm=68.0, tol=1.5, how="diameter", part="SaxBody"),
]