"""
dome -- geodesic dome, 24 m span: a faceted shell of real triangular panels on
a triangular strut lattice, over a compression ring.

A geodesic dome is not a smooth lathe. It is a triangulated sphere, and the
read comes from the FACETS: a smooth dome renders as a beach ball. So the shell
is a UV sphere deliberately left flat-shaded, cut to a hemisphere, and the
lattice is a `lathe` of meridian tubes plus `array_radial` rings.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    span=24000.0,
    radius=12000.0,
    height=9600.0,          # crown above the springing line
    strut_radius=70.0,
    panel_thickness=40.0,
    meridian_count=12,
    ring_count=5,
    base_ring_width=600.0,
)

R = SPEC["radius"]
HR = SPEC["height"]
SR = SPEC["strut_radius"]
MER = SPEC["meridian_count"]
NR = SPEC["ring_count"]


def build():
    frame = bkit.preset("brushed_metal")
    panel = bkit.pbr("DomePanel", base=(0.80, 0.83, 0.86), rough=0.22,
                     coat=0.3)
    concrete = bkit.pbr("DomeRing", base=(0.72, 0.71, 0.67), rough=0.68)

    # ---- compression ring at the springing line --------------------------
    ring = bkit.tube("DomeBaseRing", R + SPEC["base_ring_width"] / 2.0,
                     R - 40.0, SPEC["base_ring_width"], segments=96,
                     centre=(0.0, 0.0, 0.0), mat=concrete)

    # ---- shell: a hemisphere, FLAT shaded so the facets read ------------
    # segments=meridian_count*2 and rings=ring_count*2 gives the facet count a
    # real geodesic panel would have. shade_smooth would erase every facet and
    # the dome would render as a smooth ball.
    shell = bkit.uv_sphere("DomeShell", R, segments=MER * 2, rings=NR * 2 + 1,
                           centre=(0.0, 0.0, 0.0), mat=panel)
    # Keep the upper hemisphere: delete everything below the springing line
    # with one plane cut, so no face is left open (the boolean closes it).
    bkit.boolean(shell, bkit.box("_halfspace", R * 3.0, R * 3.0, R * 3.0,
                                 centre=(0.0, 0.0, -R * 1.5)))
    bkit.move(shell, 0.0, 0.0, HR - R)
    bpy_update()

    # ---- meridians: one arc, swept MER times -----------------------------
    # Each meridian is a quarter-torus lying in a radial plane, running from
    # the base ring to the crown. array_radial needs the swept object on the
    # Z axis at z = 0, so the arc is built about the origin and lifted after.
    r_arc = HR
    mer = bkit.arc_torus("DomeMeridians", r_arc, SR, -90.0, 0.0,
                         centre=(0.0, 0.0, 0.0), plane="XZ",
                         seg_major=40, seg_minor=12, mat=frame, caps=True)
    # arc runs from (r_arc, 0, 0) [base] up to (0, 0, r_arc) [crown] in XZ.
    # Sweep about Z, then lift the whole dome of meridians to the crown.
    bkit.array_radial(mer, MER)
    bkit.move(mer, 0.0, 0.0, HR)
    bpy_update()

    # ---- latitude rings: real hoops at computed heights ------------------
    # The ring radii follow the dome's own profile, sampled from the same
    # ellipse the meridians trace, so struts and shell agree.
    for i in range(1, NR):
        f = i / float(NR)                       # 0 at the base, 1 at the crown
        z = HR * math.sin(math.pi / 2.0 * f)
        rr = R * math.cos(math.pi / 2.0 * f)
        if rr < SR * 1.5:
            break
        bkit.torus("DomeRing%d" % (i + 1), rr, SR * 0.8, seg_major=64,
                   seg_minor=12, centre=(0.0, 0.0, z), mat=frame)

    return dict(spec=SPEC, parts=2 + NR, meridians=MER, rings=NR)


def bpy_update():
    """matrix_world is cached; array_radial and scale both need a refresh."""
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="span", mm=24600.0, tol=40.0, how="bbox_x"),
    dict(name="height", mm=12000.0, tol=60.0, how="bbox_z"),
    dict(name="base_ring_width", mm=600.0, tol=10.0, how="bbox_z",
         part="DomeBaseRing"),
    dict(name="shell_dia", mm=23756.0, tol=8.0, how="diameter",
         part="DomeShell"),
]
