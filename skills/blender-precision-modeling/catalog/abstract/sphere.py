"""
sphere -- a 60 mm diameter chrome ball, the reference "perfect surface".

A sphere is the only object in this domain whose silhouette is identical from
every camera angle, so it doubles as the staging check: if a sphere reads dull
or off-centre, the studio rig or the exposure solve is wrong, not the model.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    diameter=60.0,        # across any great-circle section
    latitude_bands=48,    # ring resolution, kept high so the horizon
    longitude_steps=96,   # stays a clean line instead of faceting
)

CHECKS = [
    dict(name="diameter", mm=60.0, tol=0.1, how="diameter", part="Sphere"),
    dict(name="height", mm=60.0, tol=0.1, how="bbox_z", part="Sphere"),
]


def build():
    r = SPEC["diameter"] / 2.0
    # Pearl, not chrome: a metal=1 sphere has no diffuse term, so under this
    # studio's dark upper hemisphere it renders as a black ball with one white
    # highlight. A mostly-diffuse surface keeps the whole silhouette readable.
    mat = bkit.pbr("SpherePearl", base=(0.82, 0.83, 0.85), metal=0.0, rough=0.26,
                   coat=0.35)
    ball = bkit.uv_sphere("Sphere", r,
                          segments=SPEC["longitude_steps"],
                          rings=SPEC["latitude_bands"],
                          centre=(0, 0, r),
                          mat=mat)
    # uv_sphere already welds the pole fans and recalculates normals; the only
    # thing left is to confirm the seam is a welded manifold, which health()
    # does for us. A duplicate seam vertex here would show up as non-manifold.
    bkit.weld(ball, 0.002)

    return dict(spec=SPEC, parts=1)