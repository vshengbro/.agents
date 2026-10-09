"""
torch -- LED hand torch, 142 mm long with a 36 mm head.

What makes a torch a torch and not a tube is the head-to-body step: the barrel
steps UP in diameter into a crenellated bezel, and the reflector lens is a
separate disc sitting proud inside it. Modelled standing on its tail cap,
because that is how a torch is photographed and it puts the whole silhouette in
frame against the floor.

The knurled grip band is generated as a real zig-zag lathe profile rather than a
painted stripe: at 28 mm across, a textureless grip does not read at all.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    overall_length=146.0,
    barrel_diameter=28.0,
    head_diameter=40.0,     # a clear step over the 28 mm barrel
    lens_diameter=27.0,
    barrel_length=104.0,
    head_length=34.0,
    switch_diameter=9.0,
    knurl_pitch=2.5,        # fine enough to read as knurling, not corrugation
    tail_flare_diameter=31.0,
)


def build():
    alu = bkit.pbr("TorchAlu", base=(0.42, 0.44, 0.47), metal=0.85, rough=0.34)
    anod = bkit.preset("dark_metal")
    rubber = bkit.preset("rubber")
    lens = bkit.pbr("TorchLens", base=(0.80, 0.88, 0.95), rough=0.08,
                    emission=(1.0, 0.96, 0.88), emission_strength=5.0)

    barrel_len = SPEC["barrel_length"]
    head_len = SPEC["head_length"]
    rb = SPEC["barrel_diameter"] / 2.0
    rh = SPEC["head_diameter"] / 2.0

    # ---- barrel with a real knurled grip band ---------------------------
    # The knurl cuts INWARD from the 28 mm barrel rather than standing proud
    # of it: a ribbed band outside the nominal diameter makes the part measure
    # 31.2 mm across and the barrel stops being 28 mm.
    prof = [(0.0, 0.0), (13.5, 0.0), (14.0, 3.0), (14.0, 12.0)]
    knurl_start, knurl_end = 26.0, 74.0
    prof += [(rb, knurl_start)]
    pitch = SPEC["knurl_pitch"]
    z = knurl_start
    up = True
    while z < knurl_end:
        z = min(z + pitch, knurl_end)
        prof.append((rb if up else rb - 0.8, z))
        up = not up
    prof += [(rb, barrel_len), (0.0, barrel_len)]
    body = bkit.lathe("TorchBody", prof, segments=64, mat=anod)

    # ---- tail cap: a flared end so the torch stands up ------------------
    tail = bkit.lathe("TorchTail", [
        (0.0, 0.0),
        (13.0, 0.0),
        (15.5, 2.0),
        (15.5, 9.0),
        (14.5, 12.0),
        (0.0, 12.0),
    ], segments=64, mat=alu)

    # ---- crenellated head ------------------------------------------------
    prof = [(0.0, 0.0)]
    z = 0.0
    up = True
    while z < head_len:
        z = min(z + 4.0, head_len)
        prof.append((rh if up else rh - 2.2, z))
        up = not up
    prof += [(rh, head_len), (0.0, head_len)]
    head = bkit.lathe("TorchHead", prof, segments=72,
                      centre=(0.0, 0.0, barrel_len), mat=anod)

    # ---- reflector lens sitting proud in the head mouth ----------------
    lens_ob = bkit.lathe("TorchLens", [
        (0.0, 0.0),
        (11.0, 1.0),
        (13.0, 4.5),
        (13.5, 7.0),
        (0.0, 8.0),
    ], segments=64, centre=(0.0, 0.0, barrel_len + head_len + 1.0), mat=lens)

    # ---- side switch -----------------------------------------------------
    switch = bkit.cylinder("TorchSwitch", SPEC["switch_diameter"] / 2.0, 6.0,
                           segments=32, centre=(0.0, -rb - 1.6, 16.0), mat=rubber)
    bkit.move(switch, 0.0, 0.0, 0.0)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="barrel_diameter", mm=28.0, tol=0.4, how="diameter", part="TorchBody"),
    dict(name="barrel_length", mm=104.0, tol=0.4, how="bbox_z", part="TorchBody"),
    dict(name="head_diameter", mm=40.0, tol=0.4, how="diameter", part="TorchHead"),
    dict(name="head_length", mm=34.0, tol=0.4, how="bbox_z", part="TorchHead"),
    dict(name="lens_diameter", mm=27.0, tol=0.4, how="diameter", part="TorchLens"),
]