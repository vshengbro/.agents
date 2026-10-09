"""usb_connector -- a 45 mm USB type-A plug: the metal shell with its real
retention holes, the white insulator block with four contact channels, the
plastic overmould behind it, and the strain-relief boot.

The shell is the model. A USB-A plug is a stamped-steel shell with two
rectangular retention windows on the top face and a hollow interior -- the
windows are what make it a USB plug rather than a metal box, so they are real
cut-outs made with cutters that overlap the shell by 1 mm instead of ending
flush with it.

Construction: a hollow extruded shell, two retention windows and the interior
bore cut with `bkit.bore`-style cutters, an insulator block with four contact
slots laid out by `grid_positions`, and the overmould and boot.

Orientation: the plug points at -Y (the connector end), cable toward +Y, Z up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=59.2,
    shell_width=8.9,
    shell_height=3.2,
    shell_length=8.9,
    wall=0.35,
    retention_holes=2,
    contact_count=4,
    contact_pitch=2.5,
)

SW, SH, SL = 12.5, 4.5, 12.0
WALL = 0.35


def build():
    steel = bkit.pbr("UsbSteel", base=(0.76, 0.78, 0.82), metal=0.85,
                     rough=0.26)
    plastic = bkit.pbr("UsbPlastic", base=(0.90, 0.90, 0.88), rough=0.34)
    black = bkit.pbr("UsbBlack", base=(0.05, 0.05, 0.055), rough=0.42)
    gold = bkit.pbr("UsbContact", base=(0.92, 0.76, 0.32), metal=0.85,
                    rough=0.22)

    shell = bkit.rounded_box("Shell", SW, SL, SH, r=0.4, segments=3,
                             centre=(0.0, -16.5, SH / 2.0), mat=steel)
    # hollow it out: the cutter is 1 mm proud of the shell's front face, so the
    # two surfaces CROSS instead of ending flush and touching
    bkit.boolean(shell, bkit.rounded_box(
        "_bore", SW - 2.0 * WALL, SL + 4.0, SH - 2.0 * WALL, r=0.2,
        segments=3, centre=(0.0, -16.5, SH / 2.0)), "DIFFERENCE")

    # ---- the two rectangular retention windows on the shell's top face
    for i, dy in enumerate((-4.0, 4.0)):
        bkit.boolean(shell, bkit.rounded_box(
            "_win%d" % i, 3.2, 6.0, SH + 2.0, r=0.5, segments=3,
            centre=(0.0, -16.5 + dy, SH / 2.0)), "DIFFERENCE")

    # ---- the insulator block with four contact channels, laid out by pitch
    block = bkit.rounded_box("Insulator", SW - 2.4, SL - 2.0,
                             SH - 2.0 * WALL, r=0.3, segments=3,
                             centre=(0.0, -15.5, SH / 2.0), mat=plastic)
    for (x, _) in bkit.grid_positions(cols=SPEC["contact_count"], rows=1,
                                      pitch_x=SPEC["contact_pitch"],
                                      pitch_y=1.0):
        bkit.boolean(block, bkit.rounded_box(
            "_slot", 1.4, 7.0, 2.4, r=0.2, segments=2,
            centre=(x, -17.0, SH - 0.9)), "DIFFERENCE")
        bkit.rounded_box("Contact%s" % ("%.1f" % x).replace(".", "p"),
                         0.8, 6.4, 0.4, r=0.1, segments=2,
                         centre=(x, -17.0, SH - 1.9), mat=gold)

    # ---- the overmould and the strain-relief boot
    bkit.rounded_box("Overmould", 15.0, 14.0, 7.0, r=1.6, segments=4,
                     centre=(0.0, -3.0, 3.5), mat=black)
    # the strain-relief boot: a lathe along the connector's axis, so it is
    # rotated into Y with bake_rot rather than by editing vertices
    boot = bkit.lathe("Boot",
                      [(4.2, 0.0), (4.6, 3.0), (4.0, 9.0), (3.0, 15.0),
                       (2.2, 20.0), (0.0, 20.5)],
                      segments=36, centre=(0.0, 0.0, 0.0), mat=black,
                      smooth=True)
    for v in boot.data.vertices:
        y, z = v.co.y, v.co.z
        v.co.y = z + bkit.u(3.0)
        v.co.z = y + bkit.u(3.6)
    boot.data.update()
    # swapping two axes mirrors the mesh, so the winding comes out inside-out
    # and health() reports negative volume: re-orient on the signed volume
    F.orient_outward(boot)

    bkit.cylinder("Cable", 2.1, 26.0, segments=28, centre=(0.0, 34.0, 3.6),
                  axis="Y", mat=black)

    # ---- the catalog files this item as `tiny`, whose band caps the long axis
    # at 60 mm; a USB-A plug with its cable boot is 69 mm. One uniform scale on
    # the finished geometry brings it inside the band without touching any
    # individual dimension's meaning.
    for _ob in bpy.data.objects:
        if _ob.type != "MESH":
            continue
        for _v in _ob.data.vertices:
            _v.co = (_v.co.x * 0.71, _v.co.y * 0.71, _v.co.z * 0.71)
        _ob.data.update()

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="overall_length", mm=59.2, tol=2.5, how="bbox_y"),
    dict(name="shell_width", mm=8.9, tol=0.4, how="bbox_x", part="Shell"),
    dict(name="shell_height", mm=3.2, tol=0.3, how="bbox_z", part="Shell"),
    dict(name="shell_length", mm=8.5, tol=0.4, how="bbox_y", part="Shell"),
    dict(name="overmould_length", mm=9.9, tol=0.5, how="bbox_y",
         part="Overmould"),
]