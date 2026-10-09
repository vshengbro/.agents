"""
socket_screw -- ISO 4762 M6 x 20 socket head cap screw (black oxide).

Every dimension is the ISO 4762 row for M6: head diameter dk = 10, head height
k = 6, hex socket s = 5 across flats, nominal length l = 20 under the head.
The proportion k/dk = 0.6 is what separates a socket cap screw from a button
head at a glance.

THREAD TECHNIQUE. bkit.thread() sweeps a triangular ridge along a helix, which
on its own is an open shell: both end triangles close the sweep, but the two
helical boundary curves running the length of the core stay open, so health()
reports two non-manifold edges per step (1830 of them on the M12 hex_bolt).
Adding a Solidify modifier *in the model script* closes that boundary with a rim
loop and the result is watertight with the outer thread radius unchanged
(verified: nonmanifold = 0, loose_verts = 0, bbox sx exactly 2 * radius). No
change to bkit.py is needed; the thickness is twice the thread depth so the
closed shell spans the whole thread and reads as a solid screw rather than a
finned tube.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND (no shared file is edited). Blender's camera data defaults
# to clip_start = 0.1 m and bkit.frame() parks the camera at
# radius * 1.18 / tan(vfov/2) -- only 105 mm for this 26 mm screw, i.e. 5 %
# clear of the near plane. At a squarer render aspect the vertical FOV widens,
# `frame` moves closer, and the whole screw disappears; auto_exposure then
# reports "probe unreadable" because the calibration ball is clipped too.
# render_shots() resolves `camera` from bkit's module globals at call time, so
# re-binding it with a near plane from the harness's own distance fixes it.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

NOMINAL = 6.0            # d, nominal diameter
PITCH = 1.25             # coarse pitch
HEAD_DIA = 10.0          # dk, ISO 4762
HEAD_HEIGHT = 6.0        # k, ISO 4762
SOCKET_AF = 5.0          # s, hex socket across flats
SOCKET_DEPTH = 3.5       # t, ISO 4762 minimum 3.0 for M6
LENGTH = 20.0            # l, under the head
THREAD_LEN = 13.0        # l1, threaded portion
ROOT_R = 2.55            # d2/2, ISO 4762 minor diameter ~5.15
CREST_R = NOMINAL / 2.0

SPEC = dict(nominal_diameter=NOMINAL,
            pitch=PITCH,
            head_diameter=HEAD_DIA,
            head_height=HEAD_HEIGHT,
            socket_across_flats=SOCKET_AF,
            length=LENGTH,
            thread_length=THREAD_LEN)


def hex_outline(across_flats, phase=30.0):
    r = (across_flats / 2.0) / math.cos(math.radians(30.0))
    return [(math.cos(math.radians(phase + 60.0 * i)) * r,
             math.sin(math.radians(phase + 60.0 * i)) * r) for i in range(6)]


def closed_thread(name, radius, pitch, length, thread_h, z_centre, mat,
                  segments_per_turn=20):
    """bkit.thread() + Solidify: a watertight helical thread.

    Solidify's rim loop closes the open helical boundary of the swept ribbon,
    so the result is a closed shell instead of an open surface. offset=-1 keeps
    the original ridge surface as the outer envelope, so the crest radius is
    exactly the radius passed in.
    """
    ob = bkit.thread(name, radius=radius, pitch=pitch, length=length,
                     thread_h=thread_h, segments_per_turn=segments_per_turn,
                     mat=mat)
    m = ob.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness = bkit.u(2.0 * thread_h)
    m.offset = -1.0
    bkit.apply_mods(ob)
    bkit.recalc(ob)
    ob.location = bkit.v(0, 0, z_centre)
    return ob


def build():
    # Black-oxide finish. metal=0.65 not 1.0: the metal presets have no diffuse
    # term at all and a pure metal reflects only this studio's dark world, which
    # renders a black-on-black blob. The residual diffuse keeps the hex socket
    # and the thread root readable against a dark backdrop.
    oxide = bkit.pbr("BlackOxide", base=(0.21, 0.22, 0.24), metal=0.65,
                     rough=0.33)

    # ---- plain shank, full length under the head, chamfered tip ----------
    shank = bkit.lathe("ScrewShank",
                       [(0.0, 0.0), (ROOT_R - 0.25, 0.0), (ROOT_R, 0.35),
                        (ROOT_R, LENGTH), (0.0, LENGTH)],
                       segments=64, mat=oxide)

    # ---- helical thread on the lower part of the shank ------------------
    # The swept ridge overhangs its own length by +/- 0.375 * pitch at each
    # end, so the centre is offset by the same amount: any part of the helix
    # below z = 0 would make sit_on_floor() lift the whole screw off its tip.
    overhang = 0.375 * PITCH
    closed_thread("ScrewThread", CREST_R, PITCH, THREAD_LEN,
                  CREST_R - ROOT_R, THREAD_LEN / 2.0 + overhang, oxide)

    # ---- head: chamfered cylinder with a real hex socket ----------------
    head = bkit.cylinder("SocketHead", HEAD_DIA / 2.0, HEAD_HEIGHT,
                         segments=64, centre=(0, 0, LENGTH + HEAD_HEIGHT / 2.0),
                         mat=oxide)
    bkit.bevel(head, width_mm=0.55, segments=2, angle_deg=35)
    socket = bkit.extrude_profile(
        "SocketCutter", hex_outline(SOCKET_AF), 4.0,
        centre=(0, 0, LENGTH + HEAD_HEIGHT + 0.5 - 2.0), mat=None)
    bkit.boolean(head, socket, "DIFFERENCE")

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="head_diameter", mm=10.0, tol=0.05, how="bbox_x", part="SocketHead"),
    dict(name="head_height", mm=6.0, tol=0.05, how="bbox_z", part="SocketHead"),
    dict(name="overall_length", mm=26.0, tol=0.20, how="bbox_z", part=None),
]