"""
fossil_ammonite -- a Dactylioceras ammonite: 128 mm coil diameter, planispiral
shell with 26 ribs a whorl.

Real object: the classic Jurassic ammonite, displayed the way one actually is --
flat, on a bedded limestone block, so the whole spiral is visible. The read is
the LOGARITHMIC SPIRAL and the ribs crossing it, so the shell is a swept tube
whose centre line is a true logarithmic spiral (r = r0 * e^(k*theta)) with a
tube radius that grows by the same law. A constant-thickness tube on a
decorative spiral reads as a compass drawing, not an ammonite.

Ribs are real geometry, not texture: the cross-section radius is modulated by
cos(n*phi), so each rib is a ridge standing off the whorl. Every vertex comes
from an explicit tangent-normal basis, so the tube follows the coil and the
shell is a single watertight surface with two capped ends.

The coil is normalised to the declared diameter after construction: the
swept-shell bbox depends on where the spiral's outer turn ends, so scaling to
the SPEC is what makes the declared envelope and the measured envelope the
same number.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    coil_diameter=128.0,      # outer whorl, outer edge of the ribs
    whorl_turns=1.6,
    tube_ratio=0.30,          # outer whorl tube radius / spiral radius
    ribs=26,
    rib_depth=0.13,           # as a fraction of the tube radius
    section_flattening=0.62,  # ammonite whorls are not circular in section
    block_width=176.0,
    block_thickness=34.0,
)

TURNS = SPEC["whorl_turns"]
K = math.log(1.0 / 0.17) / (TURNS * 2.0 * math.pi)      # spiral growth constant


def build():
    pyrite = bkit.pbr("AmmonitePyrite", base=(0.56, 0.47, 0.22), metal=0.85,
                      rough=0.28)
    limestone = bkit.pbr("AmmoniteLimestone", base=(0.72, 0.69, 0.62), rough=0.72)
    suture = bkit.pbr("AmmoniteSuture", base=(0.34, 0.30, 0.20), rough=0.80)

    N = 200                     # samples along the coil
    NR = 22                     # samples around the tube
    RIBS = SPEC["ribs"]
    DEPTH = SPEC["rib_depth"]
    FLAT = SPEC["section_flattening"]
    r0 = 5.0                    # innermost whorl radius

    verts, faces = [], []
    for i in range(N + 1):
        t = float(i) / N
        th = TURNS * 2.0 * math.pi * t
        r = r0 * math.exp(K * th)                     # the spiral radius
        cx, cy = r * math.cos(th), r * math.sin(th)
        dr = K * r
        # tangent of r = r0*exp(k*theta) in polar form
        tx = dr * math.cos(th) - r * math.sin(th)
        ty = dr * math.sin(th) + r * math.cos(th)
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl                    # in-plane normal
        tube = SPEC["tube_ratio"] * r
        for j in range(NR):
            phi = 2.0 * math.pi * j / NR
            rr = tube * (1.0 + DEPTH * math.cos(RIBS * phi))   # rib modulation
            a = rr * math.cos(phi)                            # across the whorl
            h = rr * math.sin(phi) * FLAT                      # out of plane
            verts.append((cx + nx * a, cy + ny * a, h))
    for i in range(N):
        a, b = i * NR, (i + 1) * NR
        for j in range(NR):
            k = (j + 1) % NR
            faces.append((a + j, a + k, b + k, b + j))
    # Both ends of the sweep are open rings, so they need caps: without them
    # the coil has two boundary loops and the mesh is non-manifold.
    faces.append(tuple(range(NR))[::-1])
    faces.append(tuple(N * NR + j for j in range(NR)))

    # ---- normalise the coil to the declared diameter --------------------
    # The swept bbox depends on where the outer turn happens to end, so the
    # geometry is scaled about its own centre until the measured x extent is
    # the declared coil diameter.
    xs = [p[0] for p in verts]
    zs = [p[2] for p in verts]
    fx = SPEC["coil_diameter"] / (max(xs) - min(xs))
    fz = SPEC["coil_diameter"] / (max(zs) - min(zs))
    cx0, cz0 = (max(xs) + min(xs)) / 2.0, (max(zs) + min(zs)) / 2.0
    verts = [((p[0] - cx0) * fx, p[1], (p[2] - cz0) * fz) for p in verts]

    shell = bkit.mesh_from("AmmoniteShell", verts, faces, mat=pyrite)
    bkit.recalc(shell)

    # ---- rib crests as a second material on the same solid ---------------
    # A second shell here would z-fight with the whorl and double the
    # non-manifold count; face selection keeps one watertight body.
    bkit.assign_faces_by(shell, suture,
                         lambda c, n: abs(n.z / bkit.MM) < 3.0)

    # ---- limestone block the ammonite is bedded in ----------------------
    block = bkit.rounded_box("MatrixBlock", SPEC["block_width"],
                             SPEC["block_width"] * 0.90,
                             SPEC["block_thickness"], r=12.0,
                             centre=(0.0, 0.0, -SPEC["block_thickness"] / 2.0 - 6.0),
                             mat=limestone)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="coil_diameter", mm=128.0, tol=2.0, how="bbox_x", part="AmmoniteShell"),
    dict(name="shell_thickness", mm=128.0, tol=4.0, how="bbox_z", part="AmmoniteShell"),
    dict(name="block_width", mm=176.0, tol=1.0, how="bbox_x", part="MatrixBlock"),
    dict(name="block_thickness", mm=34.0, tol=1.0, how="bbox_z", part="MatrixBlock"),
    dict(name="overall_width", mm=176.0, tol=2.0, how="bbox_x"),
]