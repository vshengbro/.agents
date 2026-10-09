"""
graphics_card -- 304 x 118 x 45 mm dual-fan discrete GPU.

Lying the way it sits on a bench, the card's 300 mm axis is X, the 111 mm
card height is Y and the cooler thickness is Z. That orientation is what puts
the PCIe x16 fingers on the -Y long edge -- an 89 mm section of it, near the
bracket -- instead of underneath, where `sit_on_floor` would lift the whole
card off the bench to hide them.

Everything repeated here is computed, and the fan is the reason: nine blades
from one `array_radial` sweep, 24 heatsink fins from one `array_linear`,
22 gold fingers and three bracket ports from `bkit.lay_out`. Both fans are
assembled at the world origin and moved afterwards, because `array_radial`
orbits the world Z axis -- a fan built in place would throw its blades around
the middle of the card.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=304.0,
    width=118.0,
    height=45.0,
    fins=24,
    fan_blades=9,
    fan_diameter=66.0,
    ports=3,
    pcie_pins=22,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
PCB_L = 300.0                               # bare PCB length
BRACKET_X = -PCB_L / 2.0 - 2.0              # 4 mm plate off the PCB's -X end
PCIE_X0, PCIE_L = -60.0, 89.0              # 89 mm x16 edge, near the bracket
FIN_Z0, FIN_T = 2.0, 18.0                  # fin stack floor and height
FIN_X0, FIN_PITCH = -42.0, 6.0
FR = SPEC["fan_diameter"] / 2.0
FAN_Z = FIN_Z0 + FIN_T + 8.0               # fan mid-plane, 1.5 mm into fins


def _fan(alu, dark):
    """One axial fan, built at the world origin so array_radial orbits it."""
    shroud = bkit.tube("_shroud", FR, FR - 3.0, 19.0, segments=48,
                       centre=(0, 0, FAN_Z), mat=dark)
    hub = bkit.cylinder("_hub", 10.0, 19.0, segments=32, centre=(0, 0, FAN_Z),
                        mat=alu)
    # Blade placed at the radius FIRST: the sweep centres on the real axis.
    blade = bkit.box("_blade", 20.0, 9.0, 1.6, centre=(22.0, 0.0, FAN_Z),
                     mat=alu)
    bkit.array_radial(blade, count=SPEC["fan_blades"], axis="Z")
    return [shroud, hub, blade]


def build():
    pcb_mat = bkit.pbr("GpuPcbMat", base=(0.09, 0.24, 0.15), rough=0.46)
    alu = bkit.pbr("GpuAluminium", base=(0.62, 0.63, 0.66), metal=0.85,
                   rough=0.34)
    dark = bkit.pbr("GpuDark", base=(0.21, 0.21, 0.24), rough=0.46)
    gold = bkit.preset("gold")
    copper = bkit.preset("copper")

    # ---- PCB, with the x16 edge connector notched out of the -Y side ----
    pcb = bkit.rounded_box("GpuPcb", 300.0, 111.0, 1.6, r=1.0, segments=2,
                           centre=(0, 0, 0.8), mat=pcb_mat)
    edge = bkit.rounded_box("_edge", PCIE_L, 4.0, 1.6, r=0.4, segments=2,
                            centre=(PCIE_X0 + PCIE_L / 2.0, -55.5, 0.8))
    bkit.boolean(pcb, edge, "DIFFERENCE")
    fingers = []
    for i, (x, w) in enumerate(bkit.lay_out([1.0] * SPEC["pcie_pins"],
                                            gap=0.5)):
        fingers.append(bkit.box(
            "_f%d" % i, w, 3.4, 0.5,
            centre=(PCIE_X0 + 2.0 + x, -55.0, 0.9), mat=gold))
    bkit.join(fingers, name="GpuPcieFingers")

    # ---- I/O bracket: a thin plate standing on the -X end ---------------
    bracket = bkit.rounded_box("GpuBracket", 4.0, 111.0, H, r=1.0, segments=2,
                               centre=(BRACKET_X, 0.0, H / 2.0), mat=alu)
    ports = []
    for i, (y, w) in enumerate(bkit.lay_out([16.0] * SPEC["ports"], gap=7.0)):
        bkit.boolean(bracket, bkit.rounded_box(
            "_dp%d" % i, 8.0, w, 11.0, r=0.8, segments=2,
            centre=(BRACKET_X, y, 34.0)), "DIFFERENCE")
        ports.append(bkit.rounded_box(
            "_dpin%d" % i, 3.0, w - 2.0, 9.0, r=0.6, segments=2,
            centre=(BRACKET_X + 1.0, y, 34.0), mat=dark))
    bkit.join(ports, name="GpuPorts")

    # ---- fin stack on one pitch, over a copper base ----------------------
    fin = bkit.rounded_box("_fin", 1.6, 100.0, FIN_T, r=0.4, segments=2,
                           centre=(FIN_X0 + 3.0, 0.0, FIN_Z0 + FIN_T / 2.0),
                           mat=alu)
    bkit.array_linear(fin, count=SPEC["fins"], offset_mm=(FIN_PITCH, 0, 0))
    baseplate = bkit.rounded_box("_base", 150.0, 104.0, 2.0, r=1.0, segments=2,
                                 centre=(FIN_X0 + 75.0, 0.0, 3.0), mat=copper)
    bkit.join([fin, baseplate], name="GpuHeatsink")

    # ---- two fans, each assembled at the origin then positioned ---------
    fans = []
    for i, x in enumerate((-8.0, 62.0)):
        f = bkit.join(_fan(alu, dark), name="_fan%d" % i)
        bkit.move(f, x, 0.0, 0.0)
        fans.append(f)
    bkit.join(fans, name="GpuFans")

    # ---- backplate over the PCB tail, on its own standoff pillars -------
    bkit.rounded_box("GpuBackplate", 48.0, 104.0, 2.4, r=1.5, segments=3,
                     centre=(124.0, 0.0, 3.6), mat=alu)
    pillars = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=3,
                                                   pitch_x=36.0, pitch_y=40.0)):
        pillars.append(bkit.rounded_box(
            "_p%d" % i, 5.0, 5.0, 1.2, r=0.5, segments=2,
            centre=(124.0 + x, y, 1.8), mat=alu))
    bkit.join(pillars, name="GpuStandoffs")

    # ---- 8-pin PCIe power on the +Y edge, clear of the fin stack ---------
    bkit.rounded_box("GpuPower", 20.0, 10.0, 9.0, r=1.0, segments=2,
                     centre=(-108.0, 56.0, 6.0), mat=dark)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="length", mm=304.0, tol=1.0, how="bbox_x"),
    dict(name="width", mm=118.0, tol=1.0, how="bbox_y"),
    dict(name="height", mm=45.0, tol=1.0, how="bbox_z"),
]
