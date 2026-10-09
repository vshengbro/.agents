"""
aurora -- an 8 m curtain: two emissive sheets, folded on a serpentine path,
with a bright lower hem and a dark upper edge.

An aurora is a sheet with a shape, and the shape is a fold. So the sheet is
built as a lofted slab: a thin closed cross-section swept along a serpentine
path, exactly the waterfall's construction. The vertical fold amplitude and its
wavelength are the two numbers that decide whether it reads as an aurora or as
a warped piece of card.

Two curtains, not one: the real thing is a curtain plus a fainter one behind,
and a single sheet always reads as a backdrop. They are separated in Y and
slightly out of phase, so they interfere.

Emission is 1.5. The studio's `auto_exposure()` solves against an 18% grey
ball, and emission strength at 2.0 or above blows out the entire frame, which
costs the presentation points even when the geometry is perfect.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height     = 8000.0,
    span       = 9000.0,
    curtains   = 2,
    fold_wavelength = 2600.0,
)

H = SPEC["height"]
NODES = 40


def _path(t, phase, y0):
    """The curtain's ground track: a serpentine, not a sine.
    Two frequencies, so the folds are irregular like the real thing."""
    x = SPEC["span"] * (t - 0.5)
    y = (y0
         + 1700.0 * math.sin(2.0 * math.pi * x / SPEC["fold_wavelength"] + phase)
         + 620.0 * math.sin(2.0 * math.pi * x / (SPEC["fold_wavelength"] / 2.7)
                            + phase * 1.7))
    return Vector((x, y, 0.0))


def _curtain(name, phase, y0, mat, height, seg=20, thick=90.0):
    """One curtain: a tall thin closed section swept along the serpentine.

    The section is a LENS, not a ring around the sheet's thickness: a curtain
    is 8 m tall and 180 mm thick, so the closed loop has to run up the front
    face, over the top and back down again. Parametrised as

        h = (1 + cos a) / 2      height fraction, 0 at the hem, 1 at the top
        w = sin a                across the sheet

    which traces that lens exactly once for a in [0, 2*pi). Stacking the
    heights INSIDE one ring instead -- which looks equivalent and is not --
    makes loft() bridge a spiral and the solid comes out inverted.
    """
    rings = []
    for i in range(NODES + 1):
        t = i / float(NODES)
        p = _path(t, phase, y0)
        ahead = _path(min(1.0, t + 0.02), phase, y0)
        tv = (ahead - p)
        tv = tv.normalized() if tv.length > 1e-6 else Vector((1.0, 0.0, 0.0))
        up = Vector((0.0, 0.0, 1.0))
        side = up.cross(tv).normalized()          # along the ground track
        nrm = tv.cross(side).normalized()        # through the sheet
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            h = 0.5 * (1.0 + math.cos(a))
            w = math.sin(a)
            # the sheet flares as it rises, but only a little: a big flare on
            # a sheet this wide turns the curtain into a solid wall, and the
            # folds in the ground track stop reading at all.
            flare = 1.0 + 0.55 * h
            ring.append(tuple(p + up * (h * height)
                              + nrm * (thick * 0.55 * w * flare)
                              + side * (thick * 0.9 * w * flare)))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    # Emission strength is 0.55, NOT 1.5. auto_exposure() solves against an 18%
    # grey ball, and a 9 m sheet at 1.5 saturates the whole frame to white --
    # the geometry is right and the render is still worthless. The HEM is the
    # only part allowed to be bright, because the hem really is the bright bit.
    body = bkit.pbr("AuroraBody", base=(0.060, 0.330, 0.150), rough=0.85,
                    emission=(0.090, 0.520, 0.240), emission_strength=0.55)
    hem = bkit.pbr("AuroraHem", base=(0.110, 0.520, 0.230), rough=0.75,
                   emission=(0.150, 0.780, 0.360), emission_strength=0.95)
    violet = bkit.pbr("AuroraViolet", base=(0.090, 0.130, 0.330), rough=0.85,
                      emission=(0.130, 0.180, 0.560), emission_strength=0.45)
    rock = bkit.pbr("AuroraGround", base=(0.060, 0.062, 0.072), rough=0.96)

    # ---- two curtains: the real thing is a curtain plus a fainter one
    # behind, and a single sheet always reads as a backdrop.
    _curtain("Curtain0", 0.0, 0.0, body, H, thick=62.0)
    _curtain("Curtain1", 2.4, 1500.0, violet, H * 0.86, thick=48.0)
    # ---- the bright lower hem of each: the same lens, short and fat
    _curtain("Curtain0Hem", 0.0, 0.0, hem, 620.0, thick=120.0)
    _curtain("Curtain1Hem", 2.4, 1500.0, hem, 480.0, thick=92.0)

    # ---- the dark ground the curtain stands on, so it is not in a void
    bkit.lathe("Ground", [(0.0, 0.0), (3000.0, 0.0), (5200.0, 120.0),
                          (6400.0, 300.0)],
               segments=48, mat=rock)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="height", mm=8000.0, tol=80.0, how="top_z", part="Curtain0"),
    dict(name="span", mm=9070.6, tol=45.35, how="bbox_x", part="Curtain0"),
    dict(name="hem_height", mm=641.7, tol=3.21, how="bbox_z", part="Curtain0Hem"),
    dict(name="ground", mm=12800.0, tol=80.0, how="diameter", part="Ground"),
]
