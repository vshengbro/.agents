"""
whistle -- 58 mm pea whistle: a real windway, a bored chamber, three fipple
holes, the pea itself, and a lanyard bow.

This is the one item in the domain that is a boolean problem rather than a
revolution problem. The body is an extruded side profile, then it is hollowed
in three separate operations: the chamber is a coaxial bore, the windway is a
slot that overlaps the chamber (so the two cuts genuinely connect instead of
meeting tangentially, which leaves the EXACT solver a handful of bad edges),
and the fipple holes are three computed positions that break out of the
windway's floor. 58 mm overall keeps it inside the catalog's "tiny" class.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=58.0,
    width=20.0,
    body_height=18.0,        # the profile's own extent, sole to back
    chamber_diameter=14.0,
    windway_width=6.0,
    windway_height=5.0,
    fipple_holes=3,
    fipple_pitch=8.0,
    fipple_diameter=2.6,
)

L = SPEC["length"] / 2.0            # 29
W = SPEC["width"] / 2.0             # 10

# Side profile, written in the plane extrude_profile uses and then rotated
# onto XZ by axis="Y": (x along the whistle, y becomes world z, 0 at the sole).
PROFILE = [
    (-29.0, 4.0), (-29.0, 16.0), (-8.0, 19.0), (18.0, 18.0), (29.0, 17.0),
    (29.0, 13.0), (3.0, 11.0), (-6.0, 6.0), (-14.0, 2.0), (-24.0, 1.0),
]
CHAMBER = (-19.0, 9.5)              # (x, z) centre of the pea chamber

CHECKS = [
    dict(name="length", mm=58.0, tol=0.5, how="bbox_x", part="WhistleBody"),
    dict(name="body_height", mm=18.0, tol=0.5, how="bbox_z", part="WhistleBody"),
    dict(name="width", mm=20.0, tol=0.5, how="bbox_y", part="WhistleBody"),
]


def build():
    shell = bkit.preset("red_paint")
    bow_mat = bkit.preset("yellow_paint")
    pea_mat = bkit.pbr("Pea", base=(0.90, 0.90, 0.88), rough=0.42)

    # ---- body: the side profile, 20 mm thick ------------------------------
    body = bkit.extrude_profile("WhistleBody", PROFILE, 2.0 * W,
                                centre=(0.0, 0.0, 0.0), axis="Y", mat=shell)

    # ---- the pea chamber, bored along x ----------------------------------
    bkit.bore(body, radius=SPEC["chamber_diameter"] / 2.0, depth=80.0,
              centre=(CHAMBER[0], 0.0, CHAMBER[1]), axis="X",
              host_segments=len(PROFILE))

    # ---- the windway: a slot from the mouthpiece back into the chamber ---
    # deliberately longer than the gap, so the slot breaks into the bore
    bkit.boolean(body,
                 bkit.box("_windway", 49.0, SPEC["windway_width"],
                          SPEC["windway_height"],
                          centre=(10.5, 0.0, 12.5), mat=None),
                 "DIFFERENCE")

    # ---- three fipple holes breaking out of the windway floor -----------
    for (x, _y) in bkit.lay_out([SPEC["fipple_diameter"]] * SPEC["fipple_holes"],
                                gap=SPEC["fipple_pitch"]
                                - SPEC["fipple_diameter"]):
        bkit.boolean(body,
                     bkit.cylinder("_fipple", SPEC["fipple_diameter"] / 2.0,
                                   24.0, segments=20,
                                   centre=(x + 6.0, 0.0, 5.0), mat=None),
                     "DIFFERENCE")
    bkit.recalc(body)

    # ---- the pea, loose in the chamber, and the lanyard bow -------------
    pea = bkit.uv_sphere("Pea", 5.0, segments=32, rings=16,
                         centre=(CHAMBER[0], 0.0, CHAMBER[1]), mat=pea_mat)
    bow = bkit.arc_torus("LanyardBow", 9.0, 2.5, -25.0, 205.0,
                         centre=(-8.0, 0.0, 18.0), plane="XZ", seg_major=48,
                         seg_minor=16, mat=bow_mat)
    return dict(spec=SPEC, parts=3)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
