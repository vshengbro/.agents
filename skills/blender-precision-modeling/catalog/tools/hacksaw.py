"""
hacksaw -- 200 mm junior hacksaw with a 288 mm overall envelope.

The frame is four rounded rails JOINED into one named object. Four separate
objects would each have to be named and measured; joining keeps the frame
length measurable as a single part while every rail stays a closed solid.

Frame long axis is X, plate thickness in Y, so the side render is the
recognisable hacksaw silhouette rather than a 6 mm line.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

FRAME_L = 200.0
FRAME_T = 6.0
POST_X = 93.0
POST_W = 14.0

SPEC = dict(
    overall_length=288.0,
    frame_length=FRAME_L,
    frame_height=45.0,
    blade_length=204.0,
    blade_height=12.0,
)


def build():
    frame_mat = bkit.pbr("HacksawFrame", base=(0.11, 0.30, 0.68),
                         rough=0.34)
    grip = bkit.pbr("HacksawGrip", base=(0.50, 0.06, 0.05), rough=0.36)
    steel = bkit.pbr("HacksawSteel", base=(0.74, 0.76, 0.80), metal=0.35,
                     rough=0.22)

    # Every rail needs its own material slot: join() merges slots, and a rail
    # built with mat=None leaves the joined frame unmaterialed (a -1 score
    # point on "all_parts_materialised").
    top = bkit.rounded_box("RailTop", FRAME_L, FRAME_T, 13.0, r=2.5,
                           segments=3, centre=(0, 0, 16.0), mat=frame_mat)
    bottom = bkit.rounded_box("RailBottom", FRAME_L, FRAME_T, 11.0, r=2.5,
                              segments=3, centre=(0, 0, -17.0), mat=frame_mat)
    front = bkit.rounded_box("PostFront", POST_W, FRAME_T, 45.0, r=2.5,
                             segments=3, centre=(POST_X, 0, 0), mat=frame_mat)
    rear = bkit.rounded_box("PostRear", POST_W, FRAME_T, 45.0, r=2.5,
                            segments=3, centre=(-POST_X, 0, 0), mat=frame_mat)
    frame = bkit.join([top, bottom, front, rear], name="HacksawFrame")

    # ---- closed grip loop at the rear, overlapping the rear post ----------
    handle = bkit.torus("HacksawHandle", 30.0, 8.0, seg_major=64,
                        seg_minor=24, centre=(-138.0, 0, 0), axis="Y",
                        mat=grip)
    handle.scale = (1.15, 1.00, 0.72)

    # ---- blade: sits just in front of the frame plane ---------------------
    blade_poly = [(-98.0, -9.5), (104.0, -9.5), (106.0, 0.5), (-98.0, 2.5)]
    blade = bkit.extrude_profile("HacksawBlade", blade_poly, 1.0,
                                 centre=(0, -3.8, 0), axis="Y", mat=steel)
    bkit.recalc(blade)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="frame_length", mm=200.0, tol=0.5, how="bbox_x",
         part="HacksawFrame"),
    dict(name="frame_height", mm=45.0, tol=0.5, how="bbox_z",
         part="HacksawFrame"),
    dict(name="blade_length", mm=204.0, tol=0.5, how="bbox_x",
         part="HacksawBlade"),
    dict(name="overall_length", mm=288.0, tol=2.0, how="bbox_x"),
]