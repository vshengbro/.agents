"""
buffer_stop -- fixed rail-end buffer stop with a raking strut frame.

A buffer stop is a COMPRESSION member: a head beam that a wagon strikes,
carried on two raking struts leaning back into a ballast-tied base. Build it
as an A-frame and the silhouette is instantly right; build it as an upright
post and it looks like a fence.

450 mm buffer faces on 1,750 mm centres at 1,065 mm over the railhead, a
1,150 mm head beam, and rails clamped through the base. The base timbers sit
on z=0 so `sit_on_floor()` is a no-op.

NOTE ON SIZE CLASS: the catalogue classes this item `medium`, whose gate band
caps the longest dimension at 1,200 mm. No rail buffer stop can be that small
-- its head beam has to span the 1,435 mm gauge -- so this model is built at
its true 2,700 mm width and the size-class check is lost rather than fudged.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    overall_width=2700.0,
    head_beam_height=1150.0,
    head_width=2700.0,
    buffer_face_height=1065.0,
    buffer_pitch=1750.0,
    base_length=1600.0,
    rail_gauge=1435.0,
    stopping_energy_kj=1000.0,
)

CHECKS = [
    dict(name="overall_width", mm=2700.0, tol=4.0, how="bbox_y",
         part="BufferHead"),
    dict(name="head_beam_depth_z", mm=540.0, tol=4.0, how="bbox_z",
         part="BufferHead"),
    dict(name="head_top_z", mm=1150.0, tol=4.0, how="top_z", part="BufferHead"),
    dict(name="base_bottom_z", mm=0.0, tol=0.6, how="z_min", part="BufferBase"),
    dict(name="buffer_face_x", mm=0.0, tol=3.0, how="x_max", part="BufferHeads"),
    dict(name="buffer_head_diameter", mm=450.0, tol=4.0, how="bbox_z",
         part="BufferHeads"),
    dict(name="rail_crown_z", mm=372.0, tol=3.0, how="top_z", part="BufferRailL"),
]

HEAD_W = 2700.0
HEAD_Z = 880.0
HEAD_H = 540.0
HEAD_T = 240.0
BASE_L = 1600.0
RAIL_Z = 200.0


def build():
    frame_m = bkit.pbr("BufferFrameMat", base=(0.42, 0.13, 0.10), rough=0.55)
    steel = bkit.preset("dark_metal")
    worn = bkit.preset("brushed_metal")
    white = bkit.preset("white_plastic")

    # --- base: two cross members, two longitudinal rails, two timbers ------
    base = []
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        base.append(bkit.rounded_box("BufferBaseCross" + tag, 320.0, HEAD_W,
                                     150.0, r=25.0, segments=2,
                                     centre=(s * (BASE_L / 2.0 - 200.0), 0.0,
                                             105.0), mat=steel))
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        base.append(bkit.rounded_box("BufferBaseRail" + tag, BASE_L, 220.0,
                                     150.0, r=25.0, segments=2,
                                     centre=(0.0, s * 1000.0, 105.0),
                                     mat=steel))
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        base.append(bkit.rounded_box("BufferTimber" + tag, 300.0, 2900.0,
                                     150.0, r=20.0, segments=2,
                                     centre=(s * 560.0, 0.0, 75.0),
                                     mat=bkit.pbr("BufferTimberMat",
                                                  base=(0.25, 0.19, 0.13),
                                                  rough=0.85)))
    b_ob = bkit.join(base, "BufferBase")
    bkit.recalc(b_ob)

    # --- rails running through the base ------------------------------------
    R.rail("BufferRailL", 2600.0, centre_x=-300.0, y=R.RAIL_Y, z0=RAIL_Z,
           h=172.0, mat=steel)
    R.rail("BufferRailR", 2600.0, centre_x=-300.0, y=-R.RAIL_Y, z0=RAIL_Z,
           h=172.0, mat=steel)

    # --- raking struts: the head leans BACK off the impact face ------------
    struts = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        struts.append(R.strut("BufferStrut" + tag,
                              (0.0 - BASE_L / 2.0 + 200.0, s * 1000.0, 180.0),
                              (-HEAD_T / 2.0 - 60.0, s * 1120.0, HEAD_Z + 120.0),
                              95.0, steel, seg=16))
        struts.append(R.strut("BufferKnee" + tag,
                              (-HEAD_T / 2.0 - 60.0, s * 1120.0, HEAD_Z + 120.0),
                              (60.0, s * 1150.0, HEAD_Z + 120.0), 80.0, steel,
                              seg=14))
    for zc, h in ((430.0, 90.0), (700.0, 90.0)):
        struts.append(bkit.rounded_box("BufferTie%d" % int(zc), HEAD_T - 40.0,
                                       2300.0, h, r=20.0, segments=2,
                                       centre=(-HEAD_T / 2.0, 0.0, zc),
                                       mat=steel))
    st_ob = bkit.join(struts, "BufferStruts")
    bkit.recalc(st_ob)

    # --- head beam and its target disc -------------------------------------
    head = bkit.rounded_box("BufferHead", HEAD_T, HEAD_W, HEAD_H, r=30.0,
                            segments=3, centre=(0.0, 0.0, HEAD_Z), mat=frame_m)
    # Only the impact face takes the white target board; painting every
    # face whose centre is inside |x| < t/2 whites the back cap too and
    # the beam reads as a plain white block.
    bkit.assign_faces_by(head, white,
                         lambda c, n: c.x / bkit.MM > HEAD_T / 2.0 - 1.0)

    # --- buffer heads on the face ------------------------------------------
    R.buffers("BufferHeads", 0.0, z=1065.0, pitch=1750.0, mat_body=frame_m,
              mat_head=worn)
    bkit.rounded_box("BufferTarget", 40.0, 900.0, 900.0, r=180.0, segments=3,
                     centre=(HEAD_T / 2.0 + 10.0, 0.0, HEAD_Z + 120.0),
                     mat=bkit.preset("red_paint"))

    return dict(spec=SPEC, parts=9)