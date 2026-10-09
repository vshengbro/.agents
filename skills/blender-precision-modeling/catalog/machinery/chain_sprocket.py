"""
chain_sprocket -- 17-tooth roller-chain sprocket, 12.7 mm (1/2 in) pitch.

Chain sprockets are not gears. The tooth is the LAND between two roller seats,
so what identifies a sprocket is the concave seat arc cut by the chain roller,
not a tooth profile. Seat radius = roller radius (3.96 mm for 08B-1), seat
centre on the pitch circle, and the pitch diameter follows
    PD = p / sin(180 / z)
The seat arc is the far half of the roller circle, so the polygon never
self-intersects.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    teeth=17,
    chain_pitch=12.7,
    roller_diameter=7.92,
    pitch_diameter=69.1,         # p / sin(180/z)
    tip_diameter=75.0,
    root_diameter=61.2,          # PD - roller diameter
    thickness=8.0,
    bore_diameter=24.0,
    hub_diameter=40.0,
    hub_length=16.0,
    total_thickness=16.0,
)

SEAT_STEPS = 8                   # points across one roller seat arc


def _sprocket_ring():
    """Closed CCW outline: one roller seat per tooth gap, one tip land per
    tooth. The seat is the inward half of the roller circle centred on the
    pitch circle."""
    z = SPEC["teeth"]
    step = 2.0 * math.pi / z
    r_pitch = SPEC["pitch_diameter"] / 2.0
    rr = SPEC["roller_diameter"] / 2.0
    r_tip = SPEC["tip_diameter"] / 2.0
    a0 = math.radians(265.0)      # seat sweep, measured from the outward radial
    a1 = math.radians(95.0)
    pts = []
    for t in range(z):
        a_tip = t * step
        # tip land of this tooth FIRST, then the roller seat of the gap after
        # it. The seat is the inward half of the roller circle, so it has to be
        # swept from the LARGER angle back to the smaller one or the outline
        # zig-zags and the extrusion self-intersects.
        for s in (-0.09, 0.09):
            ang = a_tip + s * step
            pts.append((r_tip * math.cos(ang), r_tip * math.sin(ang)))
        a_seat = a_tip + step / 2.0
        cx, cy = r_pitch * math.cos(a_seat), r_pitch * math.sin(a_seat)
        for k in range(SEAT_STEPS + 1):
            psi = a0 + (a1 - a0) * k / float(SEAT_STEPS)
            ang = a_seat + psi
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def build():
    steel = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)
    bright = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)

    ring = _sprocket_ring()
    sprocket = bkit.extrude_profile("Sprocket", ring, SPEC["thickness"], mat=steel)
    bkit.recalc(sprocket)

    # web relief: the tooth band keeps full thickness, the web is recessed on
    # both faces the way a cast-and-machined sprocket is
    for zc in (SPEC["thickness"] / 2.0 - 0.7, -SPEC["thickness"] / 2.0 + 0.7):
        cut = bkit.cylinder("Relief", 27.0, 1.4, segments=64, centre=(0, 0, zc))
        bkit.boolean(sprocket, cut, "DIFFERENCE")

    hub = bkit.cylinder("Hub", SPEC["hub_diameter"] / 2.0, SPEC["hub_length"],
                        segments=72, mat=bright)
    bkit.boolean(sprocket, hub, "UNION")

    # one bore cut, last, so it never re-cuts a surface it already made
    bore = bkit.cylinder("Bore", SPEC["bore_diameter"] / 2.0, 40.0, segments=72)
    bkit.boolean(sprocket, bore, "DIFFERENCE")
    key = bkit.box("Keyway", 6.0, 3.5, 40.0,
                   centre=(SPEC["bore_diameter"] / 2.0 - 3.0, 0.0, 0.0))
    bkit.boolean(sprocket, key, "DIFFERENCE")

    bkit.recalc(sprocket)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="tip_diameter", mm=75.0, tol=0.6, how="diameter", part="Sprocket"),
    dict(name="total_thickness", mm=16.0, tol=0.4, how="bbox_z", part="Sprocket"),
    dict(name="tip_diameter_y", mm=75.0, tol=0.6, how="bbox_y", part="Sprocket"),
]
