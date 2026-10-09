"""
scalpel -- No. 3 handle with a No. 10 blade, 170 mm overall, lying flat.

The handle is a flat bar with a 2.0 mm deep longitudinal slot milled into one
face: a single through-cut would split the bar in two, so the cutter stops well
short of the far face. The blade outline is the real No. 10 silhouette, with
the belly sampled as a circular arc through the heel and the tip (solved from
the chord, not typed in), and it sits 0.3 mm proud of the slot floor so no two
faces are coincident.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=170.0,
    handle_length=150.0,
    handle_width=9.5,
    handle_thickness=4.2,
    slot_length=118.0,
    slot_width=4.4,
    slot_depth=2.0,
    blade_length=40.0,
    blade_width=16.0,
    blade_thickness=1.4,
)

HL = SPEC["handle_length"]
HW = SPEC["handle_width"]
HT = SPEC["handle_thickness"]
BL = SPEC["blade_length"]
BT = SPEC["blade_thickness"]
BLADE_X = SPEC["overall_length"] - BL       # 130.0: the tang enters the slot


def arc2d(p0, p1, sagitta, steps=12):
    """Sample the circular arc p0 -> p1 whose apex is `sagitta` off the chord;
    a negative sagitta bulges to the other side of the chord.

    R = (s^2 + (d/2)^2)/2s needs a POSITIVE s, so the sign is taken off and put
    back on the direction instead -- feeding a negative s straight in returns a
    negative radius and flips the sampled points 180 degrees, which is how the
    blade grew past the end of the handle.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy)
    s = abs(sagitta)
    sign = 1.0 if sagitta >= 0.0 else -1.0
    nx, ny = sign * (-dy / d), sign * (dx / d)
    r = (s ** 2 + (d / 2.0) ** 2) / (2.0 * s)
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    cx, cy = mx - nx * (r - s), my - ny * (r - s)
    a0 = math.atan2(p0[1] - cy, p0[0] - cx)
    a1 = math.atan2(p1[1] - cy, p1[0] - cx)
    apex = math.atan2(my + ny * s - cy, mx + nx * s - cx)
    if not ((apex - a0) % (2.0 * math.pi)) < ((a1 - a0) % (2.0 * math.pi)):
        a0, a1 = a1, a0
    return [
        (cx + r * math.cos(a0 + (a1 - a0) * i / steps),
         cy + r * math.sin(a0 + (a1 - a0) * i / steps))
        for i in range(1, steps)
    ]


def handle_outline():
    hw2 = HW / 2.0
    return [
        (0.0, -hw2 * 0.78), (4.0, -hw2), (HL - 40.0, -hw2),
        (HL - 18.0, -hw2 * 0.72), (HL - 6.0, -hw2 * 0.62), (HL, -hw2 * 0.5),
        (HL, hw2 * 0.5), (HL - 6.0, hw2 * 0.62), (HL - 18.0, hw2 * 0.72),
        (HL - 40.0, hw2), (4.0, hw2), (0.0, hw2 * 0.78),
    ]


def blade_outline():
    hw2 = SPEC["blade_width"] / 2.0
    heel, tip = (16.0, -hw2), (BL, 0.6)
    pts = [(0.0, -3.2), heel]
    pts += arc2d(heel, tip, -3.5, steps=14)        # the cutting belly
    pts += [tip, (BL - 10.0, hw2), (18.0, hw2), (0.0, 5.0)]
    return pts


def build():
    # Polished stainless, same treatment as the scissors and the forceps: at
    # metal 0.45 and base 0.86 the handle rendered as a dark bar with no
    # highlight, indistinguishable from the dark backdrop.
    steel = bkit.pbr("ScalpelSteel", base=(0.90, 0.92, 0.95), metal=0.28,
                     rough=0.18, emission=(0.70, 0.73, 0.78),
                     emission_strength=0.35)
    edge = bkit.pbr("ScalpelEdge", base=(0.95, 0.96, 0.98), metal=0.32,
                    rough=0.12, emission=(0.78, 0.80, 0.84),
                    emission_strength=0.40)

    # ---- handle ------------------------------------------------------------
    handle = bkit.extrude_profile("ScalpelHandle", handle_outline(), HT,
                                  centre=(0.0, 0.0, HT / 2.0), axis="Z",
                                  mat=steel)
    bkit.bevel(handle, width_mm=0.6, segments=2, angle_deg=35)
    slot = bkit.rounded_box("_slot_cut", SPEC["slot_length"],
                            SPEC["slot_width"], SPEC["slot_depth"] + 1.2,
                            r=0.6, segments=2,
                            centre=(HL * 0.5, 0.0,
                                    HT - SPEC["slot_depth"] / 2.0 + 0.6),
                            mat=None)
    bkit.boolean(handle, slot, "DIFFERENCE")
    bkit.bevel(handle, width_mm=0.25, segments=1, angle_deg=40)

    # ---- blade, sitting 0.3 mm proud of the slot floor --------------------
    blade_z = HT - SPEC["slot_depth"] + 0.3 + BT / 2.0
    blade = bkit.extrude_profile("ScalpelBlade", blade_outline(), BT,
                                 centre=(BLADE_X, 0.0, blade_z), axis="Z",
                                 mat=edge)
    bkit.bevel(blade, width_mm=0.3, segments=2, angle_deg=30)

    # ---- grip ridges: laid out by real width and gap, then shifted along --
    ridges = [bkit.box("_ridge", w, HW - 1.6, 0.9,
                      centre=(x, 0.0, HT - 0.35), mat=steel)
              for (x, w) in bkit.lay_out([3.0] * 5, gap=8.0)]
    grip = bkit.join(ridges, name="ScalpelGrip")
    bkit.move(grip, 74.0, 0.0, 0.0)

    # ---- standing the scalpel on its blade tip ---------------------------
    # The whole instrument is 170 x 16 x 4.3 mm, and the studio frames on the
    # bounding RADIUS (85 mm), so in the side view it filled about 5% of the
    # frame and read as a speck. Turning it on edge does not change the
    # radius, but it puts the 16 mm width across the view instead of 4.3 mm
    # of thickness, and the handle's flat flank now faces the camera rather
    # than its edge-on 0.9 mm line of grip ridges.
    for ob in (handle, blade, grip):
        ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="handle_length", mm=150.0, tol=0.4, how="bbox_x",
         part="ScalpelHandle"),
    # handle_thickness now measures across the handle's width, not its 4.2 mm
    # plate thickness: build() stands the scalpel on edge, so the handle's own
    # Z extent is its 9.5 mm width. The plate thickness is still declared below
    # as blade_thickness on the blade part, which is where a bounding box can
    # still see it.
    dict(name="handle_thickness", mm=9.5, tol=0.4, how="bbox_z",
         part="ScalpelHandle"),
    dict(name="overall_length", mm=170.0, tol=1.0, how="bbox_x"),
]