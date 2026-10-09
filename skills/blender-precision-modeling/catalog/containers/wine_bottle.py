"""
wine_bottle -- 750 ml Bordeaux bottle with a real punt, a heavy shoulder and a
foil capsule over the cork.

The punt is the reason this profile is not a plain revolve: the outside of the
base is pushed *up* into the bottle on the axis, and the inside of the floor
follows it, so the glass has a constant thickness right over the dome. Get the
order wrong and the base reads as a solid plug.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=76.0,       # Bordeaux body, outside
    body_height=286.0,        # base to the lip of the bore
    wall=3.5,                 # Bordeaux glass
    neck_diameter=25.0,
    bore_diameter=19.0,
    punt_depth=20.0,          # the dome pushed up into the base
    capsule_diameter=27.6,
    capsule_height=36.0,
    overall_height=292.0,
    volume_ml=750.0,
)

R = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]
CAP_Z = SPEC["overall_height"] - SPEC["capsule_height"]


def build():
    # Dark green Bordeaux glass. Transmission is held at 0.62 rather than 1.0:
    # fully transmissive glass in this dark studio renders as a black cut-out,
    # and the specular reflection is what actually reads as glass.
    glass = bkit.pbr("WineGlass", base=(0.09, 0.20, 0.11), rough=0.05,
                     transmission=0.62, ior=1.52, coat=0.6)
    foil = bkit.pbr("CapsuleFoil", base=(0.10, 0.11, 0.14), metal=0.75, rough=0.34)
    foil_top = bkit.pbr("CapsuleTop", base=(0.72, 0.16, 0.14), metal=0.55, rough=0.38)
    cork = bkit.preset("wood")

    # ---- one closed cross-section ------------------------------------------
    # Outside first (axis -> base -> wall -> shoulder -> neck -> lip), then the
    # bore and the inside of the floor back down to the axis, over the punt.
    prof = [
        (0.0, 20.0),                 # punt apex, outside surface
        (16.0, 18.5),
        (27.0, 11.0),
        (34.0, 2.0),
        (36.0, 0.0),
        (R, 0.0),                    # flat base annulus
        (R, 175.0),                  # straight body
        (37.5, 190.0),
        (30.0, 212.0),               # shoulder
        (18.0, 228.0),
        (12.5, 238.0),               # neck
        (12.5, 268.0),
        (13.6, 268.0),               # the ring below the lip
        (13.6, 276.0),
        (12.5, 276.0),
        (12.5, BH),                  # lip, outer
        (9.5, BH),                   # across the lip
        (9.5, 240.0),                # down the bore
        (16.0, 228.0),               # inside of the shoulder
        (26.0, 210.0),
        (35.5, 172.0),               # down the inside wall
        (36.0, 4.0),
        (30.0, 6.0),                 # inside floor curving up into the punt
        (18.0, 13.0),
        (0.0, 18.0),                 # punt apex, inside surface
    ]
    body = bkit.lathe("WineBody", prof, segments=96, mat=glass)

    # ---- capsule: a foil sleeve over the neck and cork ----------------------
    cap_prof = [
        (0.0, 0.0),
        (13.0, 0.0),
        (13.8, 1.5),
        (13.8, 32.0),
        (12.4, 36.0),
        (0.0, 36.0),                 # across the top
    ]
    capsule = bkit.lathe("WineCapsule", cap_prof, segments=96,
                         centre=(0.0, 0.0, CAP_Z), mat=foil)
    bkit.assign_faces_by(
        capsule, foil_top,
        lambda c, n: c.z / bkit.MM > CAP_Z + 30.0,
    )

    # ---- cork, just visible below the capsule skirt -------------------------
    cork_obj = bkit.lathe("WineCork", [
        (0.0, 0.0), (9.6, 0.0), (9.6, 44.0), (0.0, 44.0),
    ], segments=48, centre=(0.0, 0.0, CAP_Z - 12.0), mat=cork)

    # ---- a plain label, as a second material on the real body ---------------
    label = bkit.pbr("WineLabel", base=(0.86, 0.84, 0.78), rough=0.55)
    bkit.assign_faces_by(
        body, label,
        lambda c, n: 62.0 < c.z / bkit.MM < 150.0,
    )

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="body_diameter", mm=76.0, tol=0.4, how="diameter", part="WineBody"),
    dict(name="capsule_diameter", mm=27.6, tol=0.4, how="diameter",
         part="WineCapsule"),
    dict(name="overall_height", mm=292.0, tol=0.5, how="bbox_z"),
]
