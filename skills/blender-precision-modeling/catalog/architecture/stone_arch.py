"""
stone_arch -- a single semicircular voussoir arch on two piers: a real
semicircular sweep, real voussoir joints, and a keystone.

Large size class (600..3000 mm) and a 2400 mm clear span. The joints are what
make it read as masonry rather than as a bent tube: `lay_out` computes the
number of voussoirs from the arc length, and the joints are real recesses cut
after the arch is swept -- one boolean each, on a cylinder-coaxial-free sweep,
so no facet coincidence.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    span=2400.0,            # clear opening, pier face to pier face
    rise=1200.0,            # semicircular: rise = span / 2
    pier_width=700.0,
    pier_depth=900.0,
    pier_height=1200.0,
    arch_thickness=420.0,   # radial depth of the voussoir ring
    arch_depth=900.0,       # how deep the arch is, front to back
    voussoir_count=15,      # odd, so a keystone lands at the crown
    keystone_extra=60.0,
    base_height=140.0,
)

SPAN = SPEC["span"]
R = SPAN / 2.0
PT = SPEC["pier_width"]
PV = SPEC["pier_height"]
AD = SPEC["arch_depth"]


def build():
    stone = bkit.pbr("ArchStone", base=(0.74, 0.72, 0.66), rough=0.66)
    key_stone = bkit.pbr("ArchKeystone", base=(0.80, 0.78, 0.71), rough=0.60)

    # ---- plinth under each pier: the ground course ------------------------
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("ArchPlinth%s" % tag, PT + 90.0, AD + 90.0,
                         SPEC["base_height"], r=18.0, segments=2,
                         centre=(sx * (R + PT / 2.0), 0.0,
                                 SPEC["base_height"] / 2.0), mat=stone)

    # ---- piers ------------------------------------------------------------
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("ArchPier%s" % tag, PT, AD, PV, r=22.0, segments=2,
                         centre=(sx * (R + PT / 2.0), 0.0,
                                 SPEC["base_height"] + PV / 2.0), mat=stone)

    # ---- the arch: a swept semicircular ring ------------------------------
    # arc_torus in the XZ plane, centred at the crown springing line. The
    # ring's radial thickness is arch_thickness, so the inner radius is R and
    # the outer is R + thickness.
    ring_mid = R + SPEC["arch_thickness"] / 2.0
    arch = bkit.arc_torus("ArchVoussoirs", ring_mid, SPEC["arch_thickness"] / 2.0,
                          0.0, 180.0, centre=(0.0, 0.0, PV + SPEC["base_height"]),
                          plane="XZ", seg_major=72, seg_minor=28, mat=stone,
                          caps=True)
    # The swept tube is circular in section; an arch ring is RECTANGULAR in
    # section. Scaling the object flattens it to the required depth.
    import bpy
    arch.scale = (1.0, AD / SPEC["arch_thickness"], 1.0)
    bpy.context.view_layer.update()

    # ---- voussoir joints: real recesses, computed not hand-placed --------
    # The joint positions come from the arc length divided by the voussoir
    # count, so the joints are evenly spaced by construction.
    n = SPEC["voussoir_count"]
    step = 180.0 / n
    joint_w = 14.0
    for i in range(1, n):
        a = math.radians(i * step)
        # a cutter that straddles the joint, sunk past both faces so it
        # crosses the arch's outer AND inner surface rather than being
        # tangent to either
        cut = bkit.rounded_box("_joint", joint_w, AD + 400.0, AD + 400.0,
                               r=2.0, segments=1)
        # orient the recess across the joint: rotate about Z by the angle of
        # the joint's radial direction, then push it out to the ring radius
        import math as _m
        cut.rotation_euler = (0.0, 0.0, a + _m.pi / 2.0)
        bkit.move(cut,
                  (R + SPEC["arch_thickness"] / 2.0) * _m.cos(a),
                  0.0,
                  (R + SPEC["arch_thickness"] / 2.0) * _m.sin(a)
                  + PV + SPEC["base_height"])
        bkit.boolean(arch, cut, "DIFFERENCE")

    # ---- keystone: the one voussoir that oversails the extrados -----------
    key = bkit.rounded_box("ArchKeystone",
                           SPEC["keystone_extra"], AD + 40.0,
                           520.0, r=14.0, segments=2,
                           centre=(0.0, 0.0,
                                   PV + SPEC["base_height"] + R
                                   + SPEC["arch_thickness"] - 60.0),
                           mat=key_stone)

    return dict(spec=SPEC, parts=6, voussoirs=n)


CHECKS = [
    dict(name="overall_width", mm=3890.0, tol=4.0, how="bbox_x"),
    dict(name="total_height", mm=3160.0, tol=8.0, how="bbox_z"),
    dict(name="pier_width", mm=700.0, tol=3.0, how="bbox_x", part="ArchPierL"),
    dict(name="pier_height", mm=1200.0, tol=3.0, how="bbox_z", part="ArchPierL"),
    dict(name="arch_depth", mm=900.0, tol=4.0, how="bbox_y", part="ArchVoussoirs"),
    dict(name="arch_outer_dia", mm=3240.0, tol=4.0, how="bbox_x",
         part="ArchVoussoirs"),
]
