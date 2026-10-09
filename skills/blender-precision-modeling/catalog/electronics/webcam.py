"""
webcam -- 98 x 46 x 74 mm clip-mounted 1080p webcam.

The lens stack is the part that makes it read: a barrel, a recessed bore
cut with `bkit.bore` (so the cutter's segment count is deliberately 7 above
the host's, instead of coincident with it), and a glass element at the bottom
of that bore. The clip is a real `arc_torus` partial ring, not a bent plate,
because its tips have to disappear into the back shell -- and it is capped,
because an open-ended tube is non-manifold even when both ends are buried.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=98.0,
    depth=46.0,
    height=53.1,
    lens_diameter=30.0,
    clip_reach=26.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
LR = SPEC["lens_diameter"] / 2.0


def build():
    shell = bkit.pbr("WebcamShell", base=(0.34, 0.35, 0.38), rough=0.30,
                     coat=0.3)
    dark = bkit.pbr("WebcamDark", base=(0.10, 0.10, 0.12), rough=0.42)
    # Partial, not full, transmission with a lifted base: a fully transmissive
    # lens has nothing bright behind it in a dark studio and renders as a
    # black disc, which is the opposite of a lens.
    glass = bkit.pbr("WebcamGlass", base=(0.30, 0.38, 0.48), rough=0.05,
                     transmission=0.35, ior=1.5, coat=0.6)
    chrome = bkit.preset("polished_metal")

    body = bkit.rounded_box("WebcamBody", W, D, 52.0, r=12.0, segments=5,
                            centre=(0, 0, 26.0), mat=shell)

    # ---- lens barrel standing proud of the front face --------------------
    barrel = bkit.cylinder("WebcamBarrel", LR, 10.0, segments=64,
                           axis="Y", centre=(0.0, D / 2.0 + 3.0, 28.0),
                           mat=dark)
    # bore_segments picks host+7: a cutter sharing the barrel's own 64
    # segments puts coincident facets on both surfaces and the EXACT solver
    # returns bad edges where intuition says zero.
    bkit.bore(barrel, radius=LR - 4.0, depth=14.0, axis="Y",
              centre=(0.0, D / 2.0 + 5.0, 28.0), host_segments=64)
    bkit.cylinder("WebcamLens", LR - 4.4, 1.6, segments=48, axis="Y",
                  centre=(0.0, D / 2.0 + 4.2, 28.0), mat=glass)

    # ---- privacy shutter slider across the top of the barrel ------------
    bkit.rounded_box("WebcamShutter", 34.0, 8.0, 3.0, r=1.0, segments=3,
                     centre=(0.0, D / 2.0 - 4.0, 45.0), mat=dark)

    # ---- tally LED -------------------------------------------------------
    bkit.cylinder("WebcamLed", 1.8, 2.0, segments=20, axis="Y",
                  centre=(-32.0, D / 2.0 - 0.4, 40.0),
                  mat=bkit.pbr("WebcamLedMat", base=(0.15, 0.60, 0.30),
                               rough=0.2, emission=(0.10, 0.80, 0.40),
                               emission_strength=1.5))

    # ---- clip: a partial ring whose tips bury in the back shell ---------
    reach = SPEC["clip_reach"] - 5.0
    clip = bkit.arc_torus("WebcamClip", reach, 5.0, -75.0, 75.0,
                          centre=(0.0, -D / 2.0 - 1.0, 24.0), plane="YZ",
                          seg_major=40, mat=dark, caps=True)
    # Pivot knuckle between body and clip.
    bkit.cylinder("WebcamPivot", 7.0, 30.0, segments=28, axis="X",
                  centre=(0.0, -D / 2.0 - 1.0, 36.0), mat=chrome)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="width", mm=98.0, tol=0.8, how="bbox_x", part="WebcamBody"),
    dict(name="body_depth", mm=46.0, tol=0.8, how="bbox_y", part="WebcamBody"),
    dict(name="overall_height", mm=53.1, tol=0.8, how="bbox_z"),
]
