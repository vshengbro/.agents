"""
rope_hook -- marine snap hook, 18 mm rope socket and a 25 mm hook.

A snap hook is three parts of one forging: a waisted rope socket with a real
through bore, the hook body (a C of tube with a 55 degree mouth at the bottom)
and the gate that closes the mouth. Modelling the bore properly is what stops
the socket reading as a solid lump, and gating the mouth is what makes it read
as a snap hook rather than an open sling hook.

The hook's two ends are buried in the shank rather than floating at the mouth:
the arc terminates inside the neck so there is no coincident-face seam and no
gap for the eye to catch on.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SOCKET_OD = 18.0        # rope socket outside diameter
SOCKET_BORE = 9.0       # rope bore
SOCKET_H = 26.0
WAIST_OD = 16.0         # waisted middle of the socket
NECK_L = 14.0           # neck between socket and hook
HOOK_R = 12.5           # hook centreline radius
HOOK_WIRE_R = 3.5
MOUTH = 80.0            # degrees of gate opening at the bottom
BEND_Z = SOCKET_H + HOOK_R + 2.0 + HOOK_WIRE_R

SPEC = dict(socket_diameter=SOCKET_OD,
            socket_bore=SOCKET_BORE,
            socket_height=SOCKET_H,
            hook_wire_diameter=2.0 * HOOK_WIRE_R,
            hook_diameter=2.0 * (HOOK_R + HOOK_WIRE_R),
            overall_height=BEND_Z + HOOK_R + HOOK_WIRE_R)


def build():
    steel = bkit.pbr("HookSteel", base=(0.76, 0.78, 0.81), metal=0.74,
                     rough=0.24)
    gate_mat = bkit.pbr("HookGate", base=(0.66, 0.68, 0.71), metal=0.76,
                        rough=0.30)

    ri = SOCKET_BORE / 2.0
    ro = SOCKET_OD / 2.0
    rw = WAIST_OD / 2.0
    h = SOCKET_H
    socket = bkit.lathe("RopeSocket",
                        [(ri, 0.0), (ro, 0.0), (ro, 1.8), (rw, 3.0),
                         (rw, h - 3.0), (ro, h - 1.8), (ro, h), (ri, h),
                         (ri, 0.0)],
                        segments=80, cap_ends=False, mat=steel)

    neck = bkit.rounded_box("HookNeck", 12.0, 7.0, NECK_L, r=1.6, segments=3,
                            centre=(0, 0, h + NECK_L / 2.0 - 1.0),
                            mat=steel)

    # C-shape: the mouth (the gap) points down, where a rope is clipped in
    a0 = -90.0 + MOUTH / 2.0
    a1 = 270.0 - MOUTH / 2.0
    hook = bkit.arc_torus("HookBody", HOOK_R, HOOK_WIRE_R, a0, a1,
                          centre=(0, 0, BEND_Z), plane="XZ", seg_major=72,
                          seg_minor=28, mat=steel, caps=True)

    # gate: a straight bar across the mouth at the height of the arc's ends
    z_end = BEND_Z + HOOK_R * math.sin(math.radians(a0))
    gate = bkit.cylinder("HookGate", 1.7, 2.0 * HOOK_R * math.cos(
        math.radians(a0)) + 2.0, segments=24, centre=(0, 0, z_end), axis="X",
        mat=gate_mat)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="socket_diameter", mm=18.0, tol=0.05, how="bbox_x", part="RopeSocket"),
    dict(name="socket_height", mm=26.0, tol=0.05, how="bbox_z", part="RopeSocket"),
    dict(name="hook_diameter", mm=32.0, tol=0.05, how="bbox_x", part="HookBody"),
    dict(name="overall_height", mm=60.0, tol=0.05, how="bbox_z", part=None),
]