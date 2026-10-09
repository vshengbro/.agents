"""
power_bank -- 20 000 mAh USB power bank, 148 x 72 x 27 mm.

A power bank is a slab: the silhouette carries the recognition, so the job here
is to get the aspect ratio right (roughly 5 : 2.4 : 0.9) and to stop it looking
like a featureless rounded brick. The detail that does that work is the port
end -- two USB-A and one USB-C, recessed into one narrow face and positioned
with bkit.lay_out so the pitch is computed.

All the port cutters are blind pockets that straddle the shell surface by more
than 1 mm. Ending a cutter exactly flush with the wall is the tangency case that
produces non-manifold edges, so every one of them crosses rather than touches.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    body_length=148.0,
    body_width=72.0,
    body_height=27.0,
    corner_radius=6.5,
    port_face_clearance=6.0,
    usb_a_width=13.5,
    usb_a_height=6.0,
    usb_a_count=2,
    usb_c_width=9.0,
    usb_c_height=3.4,
    port_pitch=5.0,
    port_recess_depth=5.0,
    button_diameter=9.0,
    led_count=4,
    led_pitch=5.0,
    led_diameter=2.4,
)


def build():
    shell = bkit.preset("black_plastic")
    dark = bkit.pbr("PortCavity", base=(0.03, 0.03, 0.035), rough=0.55)
    alu = bkit.pbr("PortFlesh", base=(0.55, 0.57, 0.60), metal=0.85, rough=0.35)
    led = bkit.pbr("ChargeLed", base=(0.2, 0.9, 0.3), rough=0.3,
                   emission=(0.15, 1.0, 0.25), emission_strength=3.0)

    bl = SPEC["body_length"]
    bw = SPEC["body_width"]
    bh = SPEC["body_height"]

    body = bkit.rounded_box("PowerBankBody", bl, bw, bh,
                            r=SPEC["corner_radius"], segments=6,
                            centre=(0.0, 0.0, bh / 2.0), mat=shell)

    # ---- ports on one narrow end face, laid out by measurement -----------
    widths = [SPEC["usb_a_width"]] * SPEC["usb_a_count"] + [SPEC["usb_c_width"]]
    heights = [SPEC["usb_a_height"]] * SPEC["usb_a_count"] + [SPEC["usb_c_height"]]
    depths = [SPEC["port_recess_depth"]] * len(widths)
    x_face = bl / 2.0

    for (y, w), hh, d in zip(bkit.lay_out(widths, gap=SPEC["port_pitch"]),
                             heights, depths):
        cut = bkit.rounded_box("_port_cut", d + 3.0, w, hh, r=1.0, segments=3,
                               centre=(x_face - d / 2.0 + 1.5, y, bh / 2.0))
        bkit.boolean(body, cut, "DIFFERENCE")

    bkit.recalc(body)
    bkit.assign_faces_by(
        body, dark,
        lambda c, n: c.x / bkit.MM > x_face - SPEC["port_recess_depth"] - 0.4
        and c.z / bkit.MM > bh / 2.0 - 8.0 and c.z / bkit.MM < bh / 2.0 + 8.0)

    # ---- power button on the top face -----------------------------------
    button = bkit.cylinder("PowerBankButton", SPEC["button_diameter"] / 2.0, 2.2,
                           segments=32,
                           centre=(-bl / 2.0 + 22.0, -12.0, bh + 0.6), mat=alu)
    bkit.move(button, 0.0, 0.0, 0.0)

    # ---- four charge LEDs, evenly pitched by bkit.lay_out ----------------
    leds = []
    for (x, w) in bkit.lay_out([SPEC["led_diameter"]] * SPEC["led_count"],
                               gap=SPEC["led_pitch"] - SPEC["led_diameter"]):
        d = bkit.cylinder("_led", SPEC["led_diameter"] / 2.0, 1.4, segments=16,
                          centre=(x + bl / 2.0 - 26.0, 16.0, bh - 0.4), mat=led)
        bkit.move(d, 0.0, 0.0, 0.0)
        leds.append(d)
    bkit.join(leds, name="PowerBankLeds")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="body_length", mm=148.0, tol=0.4, how="bbox_x", part="PowerBankBody"),
    dict(name="body_width", mm=72.0, tol=0.4, how="bbox_y", part="PowerBankBody"),
    dict(name="body_height", mm=27.0, tol=0.4, how="bbox_z", part="PowerBankBody"),
    dict(name="button_diameter", mm=9.0, tol=0.3, how="diameter", part="PowerBankButton"),
    dict(name="led_row_width", mm=17.4, tol=0.4, how="bbox_x", part="PowerBankLeds"),
]