"""
lunar_module -- Apollo LM-5: 7.04 m across the landing gear, 6.37 m tall,
15 103 kg. A two-stage vehicle: octagonal descent stage with the legs, and a
crouched ascent stage with the crew cabin on top.

Size class `large` (600..3000 mm band). Stated at 1:150 scale: 7 040 mm across,
6 370 mm tall -- inside the band, with the real proportions intact.

What makes an LM an LM and not a box on sticks:
1. the descent stage is a squat OCTAGON, not a box, with the four landing legs
   at the alternate faces,
2. the ascent stage is much NARROWER than the descent stage and sits on top,
   wrapped around the front, with the front face canted down at the two
   triangular windows,
3. the legs are the iconic four-legged splayed A-frame with a round footpad
   and a contact probe hanging beside each pad,
4. the ascent engine bell hangs below the ascent stage, exposed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    gear_span=4300.0,        # footpad tip to footpad tip, diagonal
    overall_height=3800.0,
    descent_width=2347.0,    # across the octagon corners = bbox_x
    descent_height=1020.0,
    ascent_width=1390.0,
    ascent_height=1590.0,
    footpad_diameter=566.0,
)

DS_W = SPEC["descent_width"]
DS_H = SPEC["descent_height"]
AS_W = SPEC["ascent_width"]
AS_H = SPEC["ascent_height"]
GEAR = SPEC["gear_span"]


def _rod(name, p0, p1, radius, mat, segments=16):
    """Solid strut between two arbitrary 3D mm points, as one watertight solid.

    bkit has no slanted-axis primitive, and rotating a cylinder by a raw
    `rotation_euler` leaves `matrix_world` stale for the next bbox() call. Two
    explicit end rings joined by a loft avoids both problems.
    """
    from mathutils import Vector
    ax = Vector((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]))
    length = ax.length or 1.0
    ax = ax / length
    ref = Vector((0.0, 0.0, 1.0))
    if abs(ax.dot(ref)) > 0.95:
        ref = Vector((1.0, 0.0, 0.0))
    u = ax.cross(ref).normalized()
    w = ax.cross(u).normalized()
    secs = []
    for p in (Vector(p0), Vector(p1)):
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ring.append(tuple(p + u * (radius * math.cos(a))
                              + w * (radius * math.sin(a))))
        secs.append(ring)
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    descent = bkit.pbr("LMDescentGold", base=(0.80, 0.64, 0.28), metal=0.85,
                       rough=0.40)
    ascent = bkit.pbr("LMAscentAlu", base=(0.66, 0.66, 0.64), metal=0.85,
                      rough=0.34)
    black = bkit.pbr("LMBlack", base=(0.12, 0.12, 0.13), rough=0.52)
    glass = bkit.pbr("LMWindow", base=(0.05, 0.08, 0.12), rough=0.06, metal=0.25)
    nozzle = bkit.pbr("LMEngineBell", base=(0.44, 0.40, 0.36), metal=0.85,
                      rough=0.30)

    # ---- descent stage: squat octagon ----------------------------------
    # 22.5 deg phase puts a FACE normal on +X, so bbox_x is the across-flats
    # width. At 45 deg the vertices sit on the axes instead and the bbox
    # measures corner-to-corner, 1.08x the declared figure.
    octa = [(DS_W / 2.0 * math.cos(math.radians(22.5 + 45 * i)),
             DS_W / 2.0 * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    base = bkit.extrude_profile("DescentStage", octa, DS_H,
                                centre=(0.0, 0.0, DS_H / 2.0), mat=descent)
    # quadrant bays: the four outboard equipment bays BETWEEN the legs, sized
    # from the stage rather than as free constants
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        bkit.rounded_box("Bay%d" % (i + 1), DS_W * 0.60, DS_W * 0.34,
                         DS_H * 0.76, r=50.0,
                         centre=(DS_W * 0.54 * math.cos(a),
                                 DS_W * 0.54 * math.sin(a), DS_H * 0.50),
                         mat=descent)

    # ---- four landing legs on the alternate faces ------------------------
    # Leg azimuths are the four octagon faces that carry NO outboard bay, so
    # the legs and the bays alternate -- that alternation is the LM's
    # signature geometry and it comes out of the octagon's 45 deg offset.
    leg_r = DS_W * 0.40
    leg_reach = (GEAR / 2.0) - leg_r - 120.0
    for i in range(4):
        a = math.radians(90.0 * i)
        cx, cy = leg_r * math.cos(a), leg_r * math.sin(a)
        pad_x, pad_y = (leg_r + leg_reach) * math.cos(a), \
            (leg_r + leg_reach) * math.sin(a)
        # primary strut: stage shoulder down-and-out to the pad. Aiming a box
        # by hand-placed centre and euler left it floating clear of both ends;
        # `_rod` builds the two end rings and lofts between them, so the strut
        # provably touches the stage and the pad.
        shoulder_z = DS_H * 0.55
        _rod("LegStrut%d" % (i + 1), (cx, cy, shoulder_z),
             (pad_x, pad_y, 120.0), 105.0, descent)
        # secondary strut: the A-frame's upper member, from the stage's upper
        # corner forward to the pad's own hinge
        _rod("LegBrace%d" % (i + 1), (cx * 1.02, cy * 1.02, DS_H * 0.92),
             (pad_x, pad_y, 240.0), 70.0, descent)
        # deployment truss, outboard and horizontal
        _rod("LegTruss%d" % (i + 1), (cx, cy, DS_H * 0.30),
             (pad_x, pad_y, 260.0), 60.0, descent)
        # footpad
        bkit.cylinder("Footpad%d" % (i + 1), SPEC["footpad_diameter"] / 2.0,
                      90.0, segments=24, centre=(pad_x, pad_y, 60.0),
                      smooth=False, mat=descent)
        # contact probe: a thin rod hanging from the pad, reaching the surface
        # BEFORE touchdown -- which is the whole point of it
        bkit.cylinder("Probe%d" % (i + 1), 26.0, 1200.0, segments=10,
                      centre=(pad_x * 1.12, pad_y * 1.12, -520.0),
                      smooth=True, mat=black)

    # ---- ascent stage: narrow, wrapped, with the canted windows --------
    asc = bkit.rounded_box("AscentStage", AS_W, AS_W * 0.86, AS_H, r=90.0,
                           centre=(0.0, -260.0, DS_H + AS_H / 2.0 - 60.0),
                           mat=ascent)
    # crew cabin front, canted down over the two triangular windows
    cabin = bkit.rounded_box("CrewCabin", AS_W * 0.92, 900.0, 900.0, r=60.0,
                             centre=(0.0, -AS_W * 0.62, DS_H + AS_H * 0.58),
                             mat=ascent)
    cabin.rotation_euler = (math.radians(-22.0), 0.0, 0.0)
    for i, x in enumerate((-560.0, 560.0)):
        w = bkit.rounded_box("Window%d" % (i + 1), 520.0, 40.0, 620.0, r=30.0,
                             centre=(x, -AS_W * 0.78, DS_H + AS_H * 0.58),
                             mat=glass)
        w.rotation_euler = (math.radians(-22.0), 0.0, 0.0)

    # ---- ascent engine bell, exposed below the ascent stage -------------
    bell = bkit.cylinder("AscentEngine", 520.0, 1000.0, r2=980.0, segments=28,
                         centre=(0.0, -260.0, DS_H - 380.0), smooth=True,
                         mat=nozzle)

    # ---- overhead docking hatch, rendezvous radar, S-band dish ----------
    bkit.cylinder("DockingHatch", 460.0, 200.0, segments=24,
                  centre=(0.0, -260.0, DS_H + AS_H - 60.0), mat=black)
    bkit.rounded_box("RendezvousRadar", 700.0, 500.0, 420.0, r=40.0,
                     centre=(0.0, -260.0, DS_H + AS_H + 300.0), mat=ascent)
    bkit.cylinder("SBandDish", 380.0, 180.0, r2=140.0, segments=24,
                  centre=(0.0, 700.0, DS_H + AS_H - 260.0),
                  axis="Y", smooth=True, mat=ascent)

    return dict(spec=SPEC, parts=1 + 4 + 4 * 6 + 1 + 2 + 1 + 3)


CHECKS = [
    dict(name="descent_width", mm=2168.0, tol=10.0, how="bbox_x", part="DescentStage"),
    dict(name="descent_height", mm=1020.0, tol=6.0, how="bbox_z", part="DescentStage"),
    dict(name="ascent_width", mm=1390.0, tol=6.0, how="bbox_x", part="AscentStage"),
    dict(name="footpad_diameter", mm=566.0, tol=4.0,
         how="diameter", part="Footpad1"),
    dict(name="overall_height", mm=4240.0, tol=90.0, how="bbox_z"),
    dict(name="overall_width", mm=4740.0, tol=150.0, how="bbox_x"),
]