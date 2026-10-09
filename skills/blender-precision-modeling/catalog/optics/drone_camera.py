"""
drone_camera -- 42 x 32 mm gimbal-stabilised drone camera in a two-axis cage.

The optics domain in miniature: a small camera body, a real tubular lens with
glass inside it, a ball joint on a post, and two `arc_torus` half-cages on
perpendicular planes -- roll and pitch axes -- plus the two brushless motors
that would actually drive them.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    camera_body_width=42.0,
    camera_body_depth=42.0,
    camera_body_height=32.0,
    lens_barrel_diameter=24.0,
    lens_diameter=19.0,
    cage_outer_diameter=70.0,
    motor_diameter=20.0,
)

BODY_Z = 100.0
ARM_Z = 132.0


def build():
    shell = bkit.pbr("DroneCamShell", base=(0.085, 0.086, 0.092), rough=0.34)
    dark = bkit.pbr("DroneCamDark", base=(0.050, 0.050, 0.055), rough=0.40)
    alu = bkit.preset("anodized")
    glass = bkit.pbr("DroneCamGlass", base=(0.14, 0.22, 0.36), metal=0.40,
                     rough=0.03)
    led = bkit.pbr("DroneCamLed", base=(0.35, 0.05, 0.05),
                   emission=(0.95, 0.18, 0.12), emission_strength=1.8)

    # ---- camera body -----------------------------------------------------
    bkit.rounded_box("DroneCameraBody", SPEC["camera_body_width"],
                     SPEC["camera_body_depth"], SPEC["camera_body_height"],
                     r=6.0, segments=4, centre=(0.0, 0.0, BODY_Z), mat=shell)

    # ---- lens: a real tube so the glass inside it is visible -------------
    bkit.tube("DroneLensBarrel", 12.0, 9.5, 14.0, segments=48,
              centre=(26.0, 0.0, BODY_Z), axis="X", mat=dark)
    bkit.cylinder("DroneLensGlass", 9.5, 3.0, segments=48,
                  centre=(31.0, 0.0, BODY_Z), axis="X", mat=glass)
    bkit.tube("DroneLensRing", 13.0, 11.0, 3.0, segments=48,
              centre=(33.5, 0.0, BODY_Z), axis="X", mat=alu)

    # ---- ball joint on a post that overlaps the body top by 2 mm ---------
    bkit.rounded_box("GimbalPost", 16.0, 16.0, 20.0, r=3.0, segments=2,
                     centre=(0.0, 0.0, 124.0), mat=alu)
    bkit.uv_sphere("BallJoint", 9.0, segments=32, rings=20,
                   centre=(0.0, 0.0, 138.0), mat=dark)

    # ---- roll cage in XZ and pitch cage in YZ, on the same centre --------
    bkit.arc_torus("RollCage", 30.0, 5.0, 8.0, 172.0, plane="XZ",
                   centre=(0.0, 0.0, ARM_Z), seg_major=40, mat=alu, caps=True)
    bkit.arc_torus("PitchCage", 30.0, 5.0, 188.0, 352.0, plane="YZ",
                   centre=(0.0, 0.0, ARM_Z), seg_major=40, mat=alu, caps=True)

    # ---- drive motors on the two axes ------------------------------------
    bkit.cylinder("RollMotor", 10.0, 12.0, segments=40,
                  centre=(-36.0, 0.0, ARM_Z), axis="X", mat=dark)
    bkit.cylinder("PitchMotor", 10.0, 12.0, segments=40,
                  centre=(0.0, 36.0, ARM_Z), axis="Y", mat=dark)

    # ---- drone-side mount plate and status lamp --------------------------
    bkit.rounded_box("MountPlate", 48.0, 48.0, 8.0, r=3.0, segments=2,
                     centre=(0.0, 0.0, 168.0), mat=alu)
    bkit.cylinder("StatusLed", 3.0, 2.0, segments=12,
                  centre=(0.0, -21.5, 96.0), axis="Y", mat=led)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="camera_body_width", mm=42.0, tol=0.4, how="bbox_x",
         part="DroneCameraBody"),
    dict(name="camera_body_depth", mm=42.0, tol=0.4, how="bbox_y",
         part="DroneCameraBody"),
    dict(name="camera_body_height", mm=32.0, tol=0.4, how="bbox_z",
         part="DroneCameraBody"),
    dict(name="lens_barrel_diameter", mm=24.0, tol=0.4, how="diameter",
         part="DroneLensBarrel"),
    dict(name="mount_plate_width", mm=48.0, tol=0.4, how="bbox_x",
         part="MountPlate"),
]