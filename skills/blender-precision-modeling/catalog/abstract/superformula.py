"""
superformula -- a superellipse-deformed body of revolution, 126 mm tall.

Gielis' superformula, sampled over the full 0..2pi in theta with z following
theta, so one lathe call produces the whole closed solid:

    r(theta) = ( |cos(m*theta/4)/a|^n2 + |sin(m*theta/4)/b|^n3 )^(-1/n1)

m sets the lobe count and n1/n2/n3 set how square or how spiky each lobe is.
m = 6 with n2 well below n3 gives six soft flutes at the waist that relax
toward circular at the poles, which is the classic vase/gourd reading.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height=126.0,
    m=6.0,                 # lobes
    n1=1.0,                # overall roundness
    n2=0.40,               # cosine exponent -> square-ish lobes
    n3=1.60,               # sine exponent
    waist_diameter=104.0,  # widest section, at theta = pi
    width=104.0,
    depth=104.0,
)

M, N1, N2, N3 = SPEC["m"], SPEC["n1"], SPEC["n2"], SPEC["n3"]
H = SPEC["height"]

CHECKS = [
    dict(name="height", mm=126.0, tol=0.6, how="bbox_z", part="Superformula"),
    dict(name="width", mm=104.0, tol=1.0, how="bbox_x", part="Superformula"),
    dict(name="depth", mm=104.0, tol=1.0, how="bbox_y", part="Superformula"),
]


def _radius(theta):
    """Superformula radius, normalised so the waist is the SPEC diameter/2."""
    t1 = abs(math.cos(M * theta / 4.0)) ** N2
    t2 = abs(math.sin(M * theta / 4.0)) ** N3
    return (t1 + t2) ** (-1.0 / N1)


def build():
    steps = 256
    waist = _radius(math.pi)          # radius at the widest point
    scale = SPEC["waist_diameter"] / 2.0 / waist

    prof = [(0.0, 0.0)]
    for k in range(steps + 1):
        th = 2.0 * math.pi * k / steps
        prof.append((_radius(th) * scale, H * k / steps))
    prof.append((0.0, H))

    mat = bkit.pbr("SuperBody", base=(0.86, 0.40, 0.28), metal=0.20, rough=0.24,
                   coat=0.3)
    solid = bkit.lathe("Superformula", prof, segments=192, mat=mat)
    bkit.recalc(solid)
    bkit.shade_smooth(solid, 40)

    return dict(spec=SPEC, parts=1)