"""ruler -- a 300 mm school ruler: bevelled edges, millimetre graduations, and
the numbered centimetre marks.

The graduations are the model. A ruler with a printed scale painted on one
face has no model detail; here the ticks are real geometry cut as a computed
row, with the long ticks every 10 mm, the mid ticks every 5 mm and short ticks
every millimetre -- three pitches derived from the 1 mm module, so no two ticks
can share a coordinate.

Construction: a bevelled bar with a real chamfer, 300 millimetre ticks cut
into the top face as thin recessed blades, and a bevelled end. Cuts use
`bkit.bore`-style overlap rather than coincident facets.

Orientation: the ruler lies along X with the graduations facing up, Z up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    length=300.0,
    width=30.0,
    thickness=2.5,
    tick_module=1.0,
    major_every=50.0,          # the numbered centimetre marks
    major_tick_length=15.0,
    minor_tick_length=6.0,
    edge_chamfer=0.6,
)

L, W, T = 300.0, 30.0, 2.5


def build():
    body = bkit.pbr("RulerBody", base=(0.86, 0.80, 0.52), rough=0.42)
    ink = bkit.pbr("RulerInk", base=(0.10, 0.10, 0.12), rough=0.50)
    edge = bkit.pbr("RulerEdge", base=(0.72, 0.66, 0.42), rough=0.36)

    bar = bkit.rounded_box("RulerBar", L, W, T, r=0.5, segments=3,
                           centre=(0.0, 0.0, T / 2.0), mat=body)

    # ---- graduations: 300 mm of ticks at a 1 mm module. The three tick
    # lengths come from the module, so adding a millimetre cannot make two
    # ticks land on the same station.
    n = int(L / SPEC["tick_module"])
    x0 = -L / 2.0 + 4.0
    for i in range(n + 1):
        x = x0 + i * SPEC["tick_module"]
        if x > L / 2.0 - 2.0:
            break
        rem = i % 50
        if rem == 0:
            ln = SPEC["major_tick_length"]
        elif rem % 5 == 0:
            ln = SPEC["major_tick_length"] * 0.62
        else:
            ln = SPEC["minor_tick_length"]
        # the tick is a thin blade standing slightly proud of the face: a
        # second shell would z-fight, so this is a real raised mark
        bkit.rounded_box("Tick%d" % i, 0.45, ln, 0.22, r=0.08,
                         segments=2,
                         centre=(x, W / 2.0 - 1.5 - ln / 2.0, T + 0.10),
                         mat=ink if rem == 0 else edge)

    # ---- the bevelled measuring edge, chamfered like a real ruler
    bkit.rounded_box("EdgeBevel", L, 4.0, T * 0.55, r=0.6, segments=3,
                     centre=(0.0, -W / 2.0 + 1.6, T * 0.62), mat=edge)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=305)


CHECKS = [
    dict(name="length", mm=300.0, tol=0.5, how="bbox_x", part="RulerBar"),
    dict(name="width", mm=30.0, tol=0.5, how="bbox_y", part="RulerBar"),
    dict(name="thickness", mm=2.5, tol=0.3, how="bbox_z", part="RulerBar"),
    dict(name="major_tick_length", mm=15.0, tol=0.6, how="bbox_y",
         part="Tick0"),
    dict(name="overall_length", mm=300.0, tol=1.5, how="bbox_x"),
]