"""
flute -- Boehm-system concert flute, 662 mm long, C foot.

A flute is a tube with three joints and seventeen keys, and the count is the
model: 17 key cups for the C-foot mechanism, 6 finger holes on the body, and a
correctly sized embouchure hole in the headjoint. It lies along X so the key
rods and cups read from the top view, which is the only angle where a flute is
recognisable.

Every repeated feature is computed. The 17 keys come from one `lay_out` on the
key's real 14 mm pitch, the rod from a `thread`-style helical cylinder, and the
three joints from one `cylinder` each at one bore diameter -- the tube is a
real hollow `tube`, not a solid rod, so the bore is visible at the foot end.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=695.0,
    tube_diameter=19.0,
    bore_diameter=15.5,
    wall=1.75,
    keys=17,
    key_diameter=15.0,
    key_pitch=14.0,
    headjoint_length=162.0,
    body_length=300.0,
    foot_length=200.0,
    embouchure_diameter=16.0,
)

L = SPEC["length"]
R = SPEC["tube_diameter"] / 2.0
RI = SPEC["bore_diameter"] / 2.0
NKEYS = SPEC["keys"]


def build():
    silver = bkit.pbr("FluteSilver", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.16)
    gold = bkit.pbr("FluteGold", base=(0.80, 0.66, 0.32), metal=0.85,
                    rough=0.20)
    pad = bkit.pbr("FlutePad", base=(0.86, 0.84, 0.78), rough=0.60)
    cork = bkit.pbr("FluteCork", base=(0.62, 0.46, 0.26), rough=0.70)

    # ---- three joints: a real tube each, so the bore is real --------------
    head = bkit.tube("FluteHeadjoint", R, RI, SPEC["headjoint_length"],
                     segments=40, centre=(0, 0, 0), axis="X", mat=silver)
    bkit.move(head, SPEC["headjoint_length"] / 2.0, 0.0, 0.0)
    # The crown: a lathed cap with the tuning-rib taper.
    crown_prof = [(0.0, 0.0), (8.0, 0.0), (9.5, 6.0), (R, 18.0), (R, 26.0),
                  (0.0, 26.0)]
    crown = bkit.lathe("FluteCrown", crown_prof, segments=40, centre=(0, 0, 0),
                       mat=silver)
    # -90 deg about Y sends the lathe's +Z (its 26 mm profile length) onto -X,
    # so the crown occupies x = 26 down to 0 -- the instrument starts at x=0.
    crown.rotation_euler = (0.0, math.radians(-90.0), 0.0)
    bkit.move(crown, 26.0, 0.0, 0.0)

    body = bkit.tube("FluteBody", R, RI, SPEC["body_length"], segments=40,
                     centre=(0, 0, 0), axis="X", mat=silver)
    bkit.move(body, SPEC["headjoint_length"] + SPEC["body_length"] / 2.0,
              0.0, 0.0)
    foot = bkit.tube("FluteFoot", R, RI, SPEC["foot_length"], segments=40,
                     centre=(0, 0, 0), axis="X", mat=silver)
    bkit.move(foot, L - SPEC["foot_length"] / 2.0, 0.0, 0.0)

    # ---- embouchure: a real hole cut through the headjoint wall ----------
    bkit.bore(head, SPEC["embouchure_diameter"] / 2.0, depth=40.0,
              centre=(96.0, 0.0, 0.0), axis="Z", host_segments=40)
    lip = bkit.lathe("FluteLipPlate",
                     [(0.0, 0.0), (13.0, 0.0), (13.0, 2.6), (9.0, 4.2),
                      (0.0, 4.2)],
                     segments=32, centre=(0, 0, 0), mat=silver)
    lip.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(lip, 96.0, 0.0, R - 1.0)
    bkit.rounded_box("FluteEmbouchureRiser", 34.0, 22.0, 9.0, r=3.0, segments=2,
                     centre=(96.0, 0.0, -R + 2.0), mat=silver)

    # ---- 17 keys on their real 14 mm pitch --------------------------------
    # Keys alternate left/right of the tube, which is what makes a flute read as
    # a flute and not as a recorder. `centre=False` matters: the 17 keys run
    # from x=200 to x=432 along the BODY, not centred on the origin -- a
    # centred lay_out would scatter them 248 mm past each end of the flute.
    body_x0 = SPEC["headjoint_length"]
    cups = []
    for i, (dx, _w) in enumerate(bkit.lay_out([SPEC["key_pitch"]] * NKEYS,
                                              gap=16.0, centre=False)):
        x = body_x0 + 38.0 + dx
        side = -1.0 if i % 2 == 0 else 1.0
        # Long keys dip below the tube (the trill keys), most sit on top.
        drop = -1.0 if i in (2, 5, 8, 11, 14) else 1.0
        y = side * (R + 5.0)
        z = drop * (R + 3.0)
        cups.append(bkit.cylinder("FluteKeyCup%02d" % i, R - 1.2, 4.0,
                                  segments=20, centre=(x, y * 0.55, z * 0.55),
                                  axis="Z", mat=gold))
        cups.append(bkit.rounded_box("FluteKeyArm%02d" % i, 5.0, 12.0, 3.0,
                                     r=1.0, segments=2,
                                     centre=(x, y, z), mat=silver))
    bkit.join(cups, name="FluteKeys")

    # Key rods: two long rods running the length of the mechanism.
    for i, (y, z) in enumerate(((R + 3.0, -6.0), (-R - 3.0, -6.0))):
        rod = bkit.cylinder("FluteRod%d" % i, 1.8, L - 240.0, segments=12,
                            centre=(0, 0, 0), axis="X", mat=silver)
        bkit.move(rod, 240.0, y, z)

    # ---- finger holes on the body, and the foot's two keys ----------------
    for i, (x, _y) in enumerate(bkit.lay_out([26.0] * 3, gap=22.0)):
        bkit.bore(body, 4.6, depth=40.0, centre=(240.0 + x, 0.0, 0.0),
                  axis="Z", host_segments=40)

    # Open end cap with the two C-foot key holes. The two holes are at DIFFERENT x
    # (70 mm apart) as well as different y: two cutters on the same x through the
    # same thin wall leave a 3-edge sliver and the shell goes non-manifold.
    bkit.tube("FluteEndCap", R + 1.0, RI, 16.0, segments=40,
              centre=(L - 8.0, 0.0, 0.0), axis="X", mat=silver)
    for i, (x, y) in enumerate(((L - 100.0, -4.6), (L - 40.0, 4.6))):
        bkit.bore(foot, 5.0, depth=40.0, centre=(x, y, 0.0), axis="Z",
                  host_segments=40)

    bkit.cylinder("FluteCork", R - 1.0, 40.0, segments=32,
                  centre=(L - 20.0, 0.0, 0.0), axis="X", mat=cork)
    bkit.rounded_box("FluteBfoot", 30.0, 16.0, 12.0, r=4.0, segments=2,
                     centre=(L - 30.0, 0.0, -R - 4.0), mat=silver)

    return dict(spec=SPEC, parts=8, keys=NKEYS)


CHECKS = [
    # A flute is three joints end to end, so the overall length only exists on
    # the whole assembly -- no single part spans it.
    dict(name="overall_length", mm=695.0, tol=2.0, how="bbox_x"),
    # `diameter` is max(sx, sy), which on a tube lying along X would measure its
    # 300 mm LENGTH rather than its 19 mm bore. These use the cross-axis.
    dict(name="tube_diameter", mm=19.0, tol=0.5, how="bbox_y", part="FluteBody"),
    dict(name="headjoint_length", mm=162.0, tol=1.0, how="bbox_x",
         part="FluteHeadjoint"),
    dict(name="foot_length", mm=200.0, tol=1.0, how="bbox_x", part="FluteFoot"),
]