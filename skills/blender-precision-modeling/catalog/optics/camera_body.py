"""
camera_body -- 132 x 115 x 106 mm mirrorless camera body with a 44 mm lens
stub: body, EVF hump and eyecup, sculpted grip, bayonet mount, two dials and a
rear screen.

The mirrorless of `dslr_camera`: same mirror-box furniture, minus the prism,
plus an electronic viewfinder. The EVF cup deliberately overhangs the front
face by 3 mm rather than stopping flush -- a flush eyecup touches the body
along a whole face, and face-to-face contact is a non-manifold generator.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=128.0,
    body_depth=72.0,
    body_height=76.0,
    evf_hump_height=32.0,
    mount_diameter=58.0,
    lens_diameter=58.0,
    lens_length=44.0,
    screen_size=76.0,
)

BODY_W, BODY_D = SPEC["body_width"], SPEC["body_depth"]
BODY_H = SPEC["body_height"]
FRONT_Y = -BODY_D / 2.0 + 6.0            # -30
BACK_Y = FRONT_Y + BODY_D                 # +42


def build():
    shell = bkit.pbr("MirrorlessShell", base=(0.090, 0.090, 0.095),
                     rough=0.40)
    leather = bkit.pbr("MirrorlessGrip", base=(0.040, 0.040, 0.043),
                       rough=0.76)
    trim = bkit.pbr("MirrorlessTrim", base=(0.58, 0.59, 0.60), metal=0.85,
                    rough=0.28)
    glass = bkit.pbr("MirrorlessGlass", base=(0.15, 0.26, 0.42), metal=0.45,
                     rough=0.03)
    screen = bkit.pbr("MirrorlessScreen", base=(0.06, 0.08, 0.10), rough=0.10,
                      emission=(0.34, 0.58, 0.70), emission_strength=0.9)

    # ---- body and grip ----------------------------------------------------
    bkit.rounded_box("MirrorlessBody", BODY_W, BODY_D, BODY_H, r=14.0,
                     segments=4, centre=(0.0, 6.0, BODY_H / 2.0), mat=shell)
    bkit.rounded_box("MlGrip", 44.0, 88.0, 82.0, r=20.0, segments=4,
                     centre=(-46.0, 4.0, 41.0), mat=leather)

    # ---- EVF hump and eyecup ---------------------------------------------
    bkit.rounded_box("EvfHump", 44.0, 50.0, SPEC["evf_hump_height"], r=8.0,
                     segments=3, centre=(2.0, 8.0, 90.0), mat=shell)
    bkit.rounded_box("EvfCup", 28.0, 16.0, 18.0, r=4.0, segments=2,
                     centre=(2.0, -33.0, 92.0), mat=leather)

    # ---- mount ring and lens ---------------------------------------------
    bkit.tube("MirrorlessMount", 29.0, 26.0, 6.0, segments=56,
              centre=(14.0, FRONT_Y - 1.0, 38.0), axis="Y", mat=trim)
    lens = bkit.lathe("MlLens", [(0.0, 0.0), (29.0, 0.0), (29.0, 34.0),
                                 (26.0, 34.0), (26.0, 44.0), (0.0, 44.0)],
                      segments=56, mat=shell)
    lens.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(lens, 14.0, FRONT_Y - 1.0, 38.0)

    front = bkit.lathe("MlFrontElement", [(0.0, 38.0), (24.0, 38.0),
                                          (24.0, 43.0), (0.0, 43.0)],
                       segments=56, mat=glass)
    front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(front, 14.0, FRONT_Y - 1.0, 38.0)

    # ---- top controls: shutter on the grip, one dial behind it ------------
    bkit.cylinder("ShutterButton", 6.5, 5.0, segments=24,
                  centre=(-46.0, -24.0, 83.5), mat=trim)
    bkit.cylinder("CommandDial", 15.0, 11.0, segments=40,
                  centre=(-46.0, 4.0, 86.5), mat=trim)
    bkit.cylinder("ExposureDial", 12.0, 9.0, segments=36,
                  centre=(-14.0, 24.0, 78.5), mat=trim)

    # ---- rear screen and a two-button pad --------------------------------
    bkit.rounded_box("MlScreen", SPEC["screen_size"], 5.0, 52.0, r=3.0,
                     segments=2, centre=(4.0, BACK_Y - 1.0, 42.0), mat=screen)
    for i, (bx, bw) in enumerate(bkit.lay_out([16.0, 16.0], gap=8.0)):
        bkit.rounded_box("RearKey%d" % i, bw, 4.0, 10.0, r=2.0, segments=2,
                         centre=(48.0 + bx, BACK_Y - 1.0, 70.0),
                         mat=trim)

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="body_width", mm=128.0, tol=0.5, how="bbox_x",
         part="MirrorlessBody"),
    dict(name="body_depth", mm=72.0, tol=0.5, how="bbox_y",
         part="MirrorlessBody"),
    dict(name="body_height", mm=76.0, tol=0.5, how="bbox_z",
         part="MirrorlessBody"),
    dict(name="evf_hump_height", mm=32.0, tol=0.5, how="bbox_z", part="EvfHump"),
    dict(name="lens_diameter", mm=58.0, tol=0.5, how="diameter", part="MlLens"),
    # The lens optical axis runs along -Y, so its LENGTH is bbox_y; bbox_x is the
    # 58 mm diameter. `how` must name the axis the dimension actually lies on.
    dict(name="lens_length", mm=44.0, tol=0.5, how="bbox_y", part="MlLens"),
]