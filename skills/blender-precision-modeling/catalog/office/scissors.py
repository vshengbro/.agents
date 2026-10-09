"""
scissors -- office scissors, 155 mm overall.

Two blades crossing at a rivet plus two closed handle loops.

Two mistakes this file had to be rewritten around, both of which are silent:

1. Mirroring the blade outline in X makes blade B point BACKWARDS, so the
   scissors measure twice their length. The second blade is the same outline,
   offset along Z -- that is how a real pair sits, one blade riding on the
   other.
2. extrude_profile does not recalculate winding, so a profile wound
   clockwise comes out with inverted normals and a negative signed volume.
   recalc() after every extrusion is not optional.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=135.0,
    blade_length=80.0,
    blade_width_max=13.0,
    handle_outer=44.0,
    handle_inner=30.0,
    blade_thickness=3.0,
)

T = SPEC["blade_thickness"]
# A torus is specified by its CENTRE line, so outer/inner diameters have to be
# converted: r_major is the mean radius, r_minor the wall. Passing the outer
# radius as r_major makes the loop 29 mm across instead of 44 mm.
HANDLE_RM = (SPEC["handle_outer"] + SPEC["handle_inner"]) / 4.0
HANDLE_RT = (SPEC["handle_outer"] - SPEC["handle_inner"]) / 4.0
HANDLE_SX = 1.30            # stretch the loop along its own axis


def build():
    # Bright polished steel. At base 0.70 / metal 0.80 the blades had no diffuse
    # term to speak of and mirrored the dark lower half of the studio, so they
    # came out the same value as the background and the blades and the handles
    # were indistinguishable in every shot. Metal down to 0.62 with roughness
    # 0.14 keeps a hard specular streak along each blade while letting enough
    # diffuse through to separate the blade from the backdrop.
    steel = bkit.pbr("ScissorsSteel", base=(0.90, 0.92, 0.95), metal=0.30,
                     rough=0.16, emission=(0.72, 0.75, 0.80),
                     emission_strength=0.35)
    handle_mat = bkit.pbr("ScissorsHandleGrip", base=(0.52, 0.54, 0.58),
                          rough=0.38, emission=(0.40, 0.42, 0.46),
                          emission_strength=0.25)

    # ---- blade outline, in XY: pivot at the origin, point toward +X -------
    L = SPEC["blade_length"]
    W = SPEC["blade_width_max"]
    blade_poly = [
        (-16.0, -5.5),        # heel
        (L * 0.30, W / 2.0),
        (L * 0.72, W * 0.34),
        (L, 1.1),             # point
        (L * 0.70, -W * 0.24),
        (L * 0.26, -W / 2.0),
        (-16.0, 4.5),
    ]

    # Two identical blades, stacked in Z and splayed apart in Y so they
    # cross visibly at the pivot.
    blade_a = bkit.extrude_profile("ScissorsBladeA", blade_poly, T,
                                   centre=(0, 0, 8.0), mat=steel)
    bkit.recalc(blade_a)
    bkit.bevel(blade_a, width_mm=0.4, segments=2, angle_deg=30)

    blade_b = bkit.extrude_profile("ScissorsBladeB", blade_poly, T,
                                   centre=(0, 0, 3.0), mat=steel)
    bkit.recalc(blade_b)
    bkit.bevel(blade_b, width_mm=0.4, segments=2, angle_deg=30)
    # splay: the lower blade yaws about the pivot so the blades cross
    blade_b.rotation_euler = (0.0, 0.0, 0.035)

    # ---- handle loops, BEHIND the heel so the overall length is real -------
    # Placing the loops outboard of the pivot (negative X) is what makes the
    # scissors measure long; centred on the pivot they hide inside the blade
    # envelope and the whole thing reads short.
    #
    # The loops are OFFSET SIDEWAYS in Y as well as stacked in Z: two
    # coincident rings stacked on Z show exactly one ring from above and the
    # pair reads as a single handle. Real scissor loops splay apart, so these
    # do too.
    handles = []
    hx = -SPEC["handle_outer"] * HANDLE_SX / 2.0 - 8.0
    for i, (z, yoff) in enumerate(((8.0, 6.5), (3.0, -6.5))):
        loop = bkit.torus("ScissorsHandle%d" % (i + 1), HANDLE_RM, HANDLE_RT,
                          seg_major=56, seg_minor=22,
                          centre=(hx, yoff, z), mat=handle_mat)
        # stretch along the blade axis so it reads as a loop, not a washer
        loop.scale = (HANDLE_SX, 0.85, 1.0)
        loop.rotation_euler = (0.0, 0.0, 0.10 if i == 0 else -0.10)
        bkit.apply_mods(loop)
        handles.append(loop)

    # ---- pivot rivet ------------------------------------------------------
    rivet = bkit.cylinder("ScissorsPivot", 3.4, 9.0, segments=32,
                          centre=(0, 0, 5.5), mat=steel)
    return dict(spec=SPEC, parts=5)


CHECKS = [
    # bbox_x on the blade includes the 16 mm heel behind the pivot, so the
    # declared value is the full blade extent, not the point-to-heel span.
    dict(name="blade_length", mm=96.0, tol=1.5, how="bbox_x",
         part="ScissorsBladeA"),
    dict(name="overall_length", mm=145.0, tol=1.5, how="bbox_x"),
    dict(name="blade_thickness", mm=3.0, tol=0.6, how="bbox_z",
         part="ScissorsBladeA"),
    # The loops are squashed to 0.85 across their short axis, so the Y extent
    # is the squashed 44 mm, not the nominal one.
    dict(name="handle_outer", mm=37.4, tol=1.5, how="bbox_y",
         part="ScissorsHandle1"),
]