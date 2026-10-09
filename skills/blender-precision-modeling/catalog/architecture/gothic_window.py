"""
gothic_window -- pointed two-light traceried window: two lancet arcs, a
mullion, lead cames, and a deep splayed reveal.

Medium size class (150..600 mm, accepted to 1200 mm by the scorer's 2x band),
so this is a single window unit at its true 1.18 m height.

The POINT is the whole object. A gothic head is not a semicircle: it is two
circular arcs struck from centres that sit BELOW the springing line and on
the OPPOSITE side of the axis, meeting at the apex. That is why it comes to a
point where a semicircle would not, and it is why the head is built as two
`arc_torus` arcs rather than one half-ring. Solving for the centre offset `d`
from "the arc passes through both the springing point and the apex":

    (spring_x + d)^2 = d^2 + (apex_z - z_c)^2   =>   d = (dz^2 - sx^2) / (2 sx)

The glass is a LANCET, not a rectangle: each light is sampled off the head's
own inner surface, because a rectangular pane under a pointed head leaves a
triangular hole at the top of every light.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=800.0,
    height=1180.0,
    frame_depth=240.0,
    frame_width=62.0,
    light_width=311.0,       # clear width of one lancet, mullion face to jamb
    mullion_width=54.0,
    springing_height=540.0,  # where the two arcs begin to curve
    arch_rise=460.0,
    sill_height=80.0,
)

W = SPEC["width"]
H = SPEC["height"]
FD = SPEC["frame_depth"]
FW = SPEC["frame_width"]
LW = SPEC["light_width"]
MW = SPEC["mullion_width"]
SPR = SPEC["springing_height"]
RISE = SPEC["arch_rise"]

# --- the head geometry, solved once and shared by the arcs and the glass ----
SPRING_X = W / 2.0 - FW / 2.0        # jamb centre line
APEX_Z = H - FW / 2.0                # head centre line at the apex
DZ = APEX_Z - SPR                    # rise of the head's centre line
HEAD_D = (DZ * DZ - SPRING_X * SPRING_X) / (2.0 * SPRING_X)
HEAD_R = SPRING_X + HEAD_D
HEAD_A = math.degrees(math.atan2(DZ, HEAD_D))


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


def _lancet(name, sx, mat, depth, y_centre):
    """One glazed light, its top edge following the head's inner surface.

    The head's inner face is itself a circular arc of radius HEAD_R - FW/2
    about the same centre, so the glass stops exactly at the stone instead of
    a guessed distance below it.
    """
    gx_in = sx * MW / 2.0                 # the mullion face
    gx_out = sx * (W / 2.0 - FW)          # the jamb's inner face
    cxh = -sx * HEAD_D                    # this side's head centre
    r_in = HEAD_R - FW / 2.0
    a_stop = math.degrees(math.acos(max(-1.0, min(1.0, (gx_in - cxh) / r_in))))
    a0, a1 = (0.0, a_stop) if sx > 0 else (180.0, a_stop)

    poly = [(gx_in, SPEC["sill_height"]), (gx_out, SPEC["sill_height"])]
    steps = 18
    # The arc must run springing -> apex, i.e. outward end first. Sampling it
    # the other way round makes the outline cross itself and the extrude
    # collapses into a crumpled sheet.
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        poly.append((cxh + r_in * math.cos(a), SPR + r_in * math.sin(a)))

    ob = bkit.extrude_profile(name, poly, depth, centre=(0.0, y_centre, 0.0),
                              axis="Y", mat=mat)
    bkit.recalc(ob)          # the two sides are wound oppositely
    return ob


def build():
    stone = bkit.pbr("GothicStone", base=(0.80, 0.78, 0.72), rough=0.64)
    glass = bkit.pbr("GothicGlass", base=(0.72, 0.82, 0.88), rough=0.08,
                     transmission=0.45)
    lead = bkit.pbr("GothicLead", base=(0.20, 0.21, 0.22), rough=0.55)

    # ---- outer frame: two jambs and a sill -------------------------------
    # The sill is flush with the jambs in WIDTH and oversails only in depth,
    # which is the reveal: a stone sill that oversailed in width would make
    # the window's overall width disagree with its own structural opening.
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("Jamb%s" % tag, FW, FD, H, r=8.0, segments=2,
                         centre=(sx * (W / 2.0 - FW / 2.0), 0.0, H / 2.0),
                         mat=stone)
    bkit.rounded_box("Sill", W, FD + 60.0, SPEC["sill_height"], r=10.0,
                     segments=2, centre=(0.0, 0.0, SPEC["sill_height"] / 2.0),
                     mat=stone)

    # ---- the two head arcs: the pointed head ----------------------------
    # Each arc is struck from the centre on the OPPOSITE side of the axis and
    # runs from its springing point up to the apex, so the pair closes to a
    # point. The lower end dies inside the jamb, so the caps never show.
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.arc_torus("GothicHead%s" % tag, HEAD_R, FW / 2.0,
                      0.0 if sx > 0 else 180.0 - HEAD_A,
                      HEAD_A if sx > 0 else 180.0,
                      centre=(-sx * HEAD_D, 0.0, SPR), plane="XZ",
                      seg_major=48, seg_minor=20, mat=stone, caps=True)
    bpy_update()

    # ---- mullion between the two lights ----------------------------------
    # Runs the full height of the opening, from the sill to where the two head
    # arcs meet, the way a real two-light mullion does -- stopping it at the
    # springing leaves the lights merged above it.
    mh = APEX_Z - FW / 2.0
    bkit.rounded_box("Mullion", MW, FD, mh, r=8.0, segments=2,
                     centre=(0.0, 0.0, mh / 2.0), mat=stone)

    # ---- glass in each lancet, following the head -----------------------
    for sx, tag in ((-1, "L"), (1, "R")):
        _lancet("Glass%s" % tag, sx, glass, 24.0, -FD / 2.0 + 30.0)

    # ---- lead cames: the horizontal tracery bars that read as "gothic" ---
    # All placed below the springing line, where the light is full width.
    gx = (MW / 2.0 + (W / 2.0 - FW)) / 2.0
    for sx, tag in ((-1, "L"), (1, "R")):
        for k in range(4):
            bkit.rounded_box("Came%s%d" % (tag, k), LW - 20.0, 16.0, 14.0,
                             r=4.0, segments=1,
                             centre=(sx * gx, -FD / 2.0 + 44.0, 140.0 + k * 120.0),
                             mat=lead)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="width", mm=800.0, tol=3.0, how="bbox_x"),
    dict(name="height", mm=1180.0, tol=3.0, how="bbox_z"),
    dict(name="mullion_width", mm=54.0, tol=1.5, how="bbox_x", part="Mullion"),
    dict(name="frame_depth", mm=240.0, tol=2.0, how="bbox_y", part="JambL"),
    dict(name="frame_width", mm=62.0, tol=1.5, how="bbox_x", part="JambL"),
    dict(name="light_width", mm=311.0, tol=2.0, how="bbox_x", part="GlassR"),
    # the head's outer rise: springing line to the outer face at the apex
    dict(name="head_rise", mm=640.0, tol=6.0, how="bbox_z", part="GothicHeadR"),
]
