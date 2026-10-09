"""
skateboard -- 800 x 205 mm popsicle deck with real nose and tail kicks, two
trucks and four 54 mm wheels.

The deck is the hard part. A flat extrusion reads as a chopping board, so the
sections are rotated about a pivot at the start of each kick: the nose and tail
swing up 14 degrees while the middle stays flat, which is what makes a popsicle
deck recognisable. The four wheels come out of one part through
grid_positions, and the truck pair through array_linear at the wheelbase.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=800.0,
    width=205.0,
    thickness=11.0,
    kick_angle=14.0,
    kick_length=112.0,
    kick_rise=30.0,
    wheelbase=380.0,
    track=224.0,
    wheel_diameter=54.0,
    wheel_width=32.0,
    wheels=4,
)

L = SPEC["length"]
Z_MID = SPEC["thickness"] / 2.0

# (x from the tail, width, thickness)
DECK = [
    (0.0, 70.0, 8.0), (12.0, 120.0, 9.5), (32.0, 150.0, 10.5),
    (80.0, 172.0, 11.0), (200.0, 196.0, 11.0), (400.0, 205.0, 11.0),
    (600.0, 196.0, 11.0), (720.0, 172.0, 11.0), (768.0, 150.0, 10.5),
    (788.0, 120.0, 9.5), (800.0, 70.0, 8.0),
]
X_PIVOT = SPEC["kick_length"]          # 112, where each kick begins

# A rigid deck kicked `kick_angle` about a transverse axis loses
# kick_length*(1 - cos a) of x run at each end, and the tip's own half
# thickness swings outward by (t/2)*sin a. Correcting for both is what makes
# the finished deck measure 800 mm from tip to tip.
_A = math.radians(SPEC["kick_angle"])
_H = (DECK[-1][2] / 2.0) * math.sin(_A)
ARC = L + 2.0 * X_PIVOT * (1.0 - math.cos(_A)) - 2.0 * _H

CHECKS = [
    dict(name="deck_length", mm=800.0, tol=0.6, how="bbox_x", part="Deck"),
    dict(name="deck_width", mm=205.0, tol=0.6, how="bbox_y", part="Deck"),
    dict(name="wheel_diameter", mm=54.0, tol=0.5, how="bbox_z", part="Wheels"),
    # outer track: the 224 mm wheel-centre grid plus one wheel width each side
    dict(name="outer_track", mm=256.0, tol=0.6, how="bbox_y"),
]


def _interp(table, x):
    for i in range(len(table) - 1):
        x0 = table[i][0]
        x1 = table[i + 1][0]
        if x <= x1 or i == len(table) - 2:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            t = min(1.0, max(0.0, t))
            return (table[i][1] + (table[i + 1][1] - table[i][1]) * t,
                    table[i][2] + (table[i + 1][2] - table[i][2]) * t)
    return table[-1][1], table[-1][2]


def build():
    ply = bkit.pbr("DeckPly", base=(0.78, 0.20, 0.09), rough=0.24, coat=0.5)
    grip = bkit.pbr("GripTape", base=(0.045, 0.045, 0.05), rough=0.88)
    truck = bkit.preset("anodized")
    wheel = bkit.pbr("Urethane", base=(0.88, 0.88, 0.86), rough=0.42)
    bearing = bkit.preset("steel")

    # ---- deck: sections rotated about the start of each kick --------------
    ang = math.radians(SPEC["kick_angle"])
    sections = []
    n = 44
    for i in range(n + 1):
        x = ARC * i / n
        w, t = _interp(DECK, x)
        pivot = X_PIVOT if x < X_PIVOT else (ARC - X_PIVOT)
        k = max(0.0, (pivot - x) / X_PIVOT) if x < X_PIVOT else \
            max(0.0, (x - pivot) / X_PIVOT)
        a = ang * min(1.0, k)
        ca, sa = math.cos(a), math.sin(a)
        dx = x - pivot
        r = min(3.0, t / 2.2)
        ring = bkit.rounded_rect_section(w, t, r, per_corner=5)
        sections.append([(pivot + dx * ca + v * sa, u,
                          Z_MID - dx * sa + v * ca) for (u, v) in ring])
    deck = bkit.loft("Deck", sections, mat=ply, smooth=True)
    bkit.recalc(deck)
    bkit.assign_faces_by(deck, grip, lambda c, n: n.z > 0.55)

    # ---- one truck, arrayed at the wheelbase ------------------------------
    # The deck's sections run from x = 0 to x = ARC, i.e. it is NOT centred on
    # the origin -- its nose is at +ARC and its tail at 0. The truck pair and
    # the wheel grid were both placed at +-wheelbase/2 about the ORIGIN, which
    # put the tail truck at x = -190, entirely off the back of the board: the
    # render showed a truck and two wheels floating in mid-air behind the deck.
    # Everything that bolts to the deck is therefore offset by the deck's own
    # mid-length, so the wheelbase is centred on the BOARD, not on the world.
    x_mid = ARC / 2.0
    x_t = x_mid + SPEC["wheelbase"] / 2.0
    truck = bkit.join([
        bkit.rounded_box("Baseplate", 76.0, 96.0, 9.0, r=3.0, segments=2,
                         centre=(x_t, 0.0, 14.5), mat=truck),
        bkit.rounded_box("Hanger", 46.0, 74.0, 30.0, r=10.0, segments=3,
                         centre=(x_t, 0.0, 30.0), mat=truck),
        bkit.cylinder("Kingpin", 7.0, 34.0, segments=16,
                      centre=(x_t - 20.0, 0.0, 32.0), axis="Y", mat=truck),
        bkit.cylinder("Axle", 6.0, 236.0, segments=16,
                      centre=(x_t, 0.0, 32.0), axis="Y", mat=bearing),
    ], name="Truck")
    bkit.array_linear(truck, 2, offset_mm=(-SPEC["wheelbase"], 0.0, 0.0))

    # ---- four wheels: one turned part placed at a computed 2 x 2 grid -----
    wr = SPEC["wheel_diameter"] / 2.0
    ww = SPEC["wheel_width"]
    wheel_prof = [
        (6.0, -ww / 2.0), (10.0, -ww / 2.0), (16.0, -ww / 2.0 + 3.0),
        (22.0, -ww / 2.0 + 5.0), (wr, -ww / 2.0 + 7.0),
        (wr, ww / 2.0 - 7.0), (22.0, ww / 2.0 - 5.0),
        (16.0, ww / 2.0 - 3.0), (10.0, ww / 2.0), (6.0, ww / 2.0),
    ]
    wheels = []
    for i, (gx, y) in enumerate(bkit.grid_positions(
            cols=2, rows=2, pitch_x=SPEC["wheelbase"],
            pitch_y=SPEC["track"])):
        # same offset as the trucks: the grid is centred, the board is not
        x = gx + x_mid
        # the grid pitch is the distance between the two wheel centres, and
        # the axle passes through both of them
        loc = (x, y, wr)
        if i == 0:
            w = bkit.lathe("Wheel", wheel_prof, segments=48,
                           centre=(0.0, 0.0, 0.0), mat=wheel)
            bkit.place(w, loc, axis="Y")
        else:
            # duplicate() sets an ABSOLUTE location AND resets rotation_euler
            # to identity unless rot_deg is given. The turned wheel's axis has
            # to be restated here, matching place(..., "Y")'s 90 deg X
            # rotation, or the copy lands with its 32 mm width across the
            # board instead of along it.
            w = bkit.duplicate(wheels[0], "Wheel%d" % (i + 1), offset_mm=loc,
                               rot_deg=(90.0, 0.0, 0.0))
        wheels.append(w)
    bkit.join(wheels, name="Wheels")

    return dict(spec=SPEC, parts=4)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
