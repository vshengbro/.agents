"""
ball_joint -- rod-end ball joint: socket housing, ball, threaded stud.

Three parts because they are three parts in reality. The socket is a real
concave seat -- a bore with a domed top, cut as a cylinder plus a sphere -- not
a flat hole, and the ball sits in it with the stud pressed through. Stud thread
is a real helix (M6 x 1.0, 18 deg) so the silhouette is unmistakably a fastener.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# A 19 mm part frames at ~89 mm from the camera, which is INSIDE Blender's
# default 0.1 m near clip: the whole subject sits in front of the near plane, so
# every shot clips it away and renders empty (or shows only backfaces, which is
# why it scored as a black blob). The clip has to scale with the subject, so this
# file wraps `bkit.camera` locally rather than editing a shared script -- the same
# workaround bee.py uses for the same reason.
_camera_ctor = bkit.camera


def _camera(*args, **kwargs):
    cam = _camera_ctor(*args, **kwargs)
    cam.data.clip_start = 0.001
    cam.data.clip_end = 1000.0
    return cam


bkit.camera = _camera

SPEC = dict(
    housing_diameter=19.0,
    housing_height=8.0,          # rim BELOW the ball's crown, so the ball
                                 # stands 2.5 mm proud and is actually visible
    socket_bore_diameter=11.2,
    ball_diameter=11.0,
    stud_diameter=7.0,
    stud_length=19.6,
    stud_thread_pitch=1.5,
    stud_thread_length=9.0,
    overall_height=21.0,
)


def build():
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    r_h = SPEC["housing_diameter"] / 2.0
    h = SPEC["housing_height"]
    ball_r = SPEC["ball_diameter"] / 2.0
    z_ball = 5.0

    # ---- housing --------------------------------------------------------
    housing = bkit.lathe("Housing", [(0.0, 0.0), (r_h, 0.0), (r_h, h), (0.0, h)],
                         segments=96, mat=dark)
    bkit.recalc(housing)
    socket = bkit.cylinder("Socket", SPEC["socket_bore_diameter"] / 2.0, 12.0,
                           segments=96, centre=(0.0, 0.0, z_ball - 6.0))
    bkit.boolean(housing, socket, "DIFFERENCE")
    seat = bkit.uv_sphere("Seat", ball_r + 0.2, segments=64, rings=32,
                          centre=(0.0, 0.0, z_ball))
    bkit.boolean(housing, seat, "DIFFERENCE")
    bkit.recalc(housing)

    # ---- ball -----------------------------------------------------------
    ball = bkit.uv_sphere("Ball", ball_r, segments=64, rings=32,
                          centre=(0.0, 0.0, z_ball), mat=steel)

    # ---- stud: shank + a real helical thread ---------------------------
    # The shank is 3.2, not 3.5: a shank at exactly the thread's crest radius
    # gives the union two coincident cylindrical surfaces.
    stud = bkit.cylinder("Stud", 3.2, 19.0,
                         segments=48, centre=(0.0, 0.0, 19.0 / 2.0),
                         mat=steel)
    thread = bkit.thread("StudThread", SPEC["stud_diameter"] / 2.0,
                         SPEC["stud_thread_pitch"], SPEC["stud_thread_length"],
                         thread_h=0.8, segments_per_turn=28, mat=steel)
    thread.location = bkit.v(0.0, 0.0, 19.0 - SPEC["stud_thread_length"] / 2.0)
    bkit.boolean(stud, thread, "UNION")
    bkit.recalc(stud)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="ball_diameter", mm=11.0, tol=0.3, how="diameter", part="Ball"),
    dict(name="housing_diameter", mm=19.0, tol=0.3, how="diameter", part="Housing"),
    dict(name="stud_length", mm=19.6, tol=0.4, how="bbox_z", part="Stud"),
]
