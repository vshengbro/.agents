"""Render each face of the model with an orthographic camera, for measurement.

The counterpart to `face_diff.py`. A beauty render cannot be diffed against a
vendor diagram: perspective foreshortens a 19.7 x 19.7 x 9.5 cm block, and
bounding-box auto-framing picks the wrong extent and reported that chassis at
h/w 0.75 against a true 0.48. Every band and column taken from such a frame is
confidently wrong.

Ortho fixes both: no foreshortening, and a frame that maps linearly onto the
object, so a feature at 16.5% of the panel width renders at 16.5% on the
machine.

    blender --background --python blender_ortho_faces.py

Outputs renders/ortho/{front,rear,left,right,top,bottom}.png.

Two things this deliberately does differently from a beauty rig:

  * Flat, even lighting. Area lights aimed at 3/4 product shots from 30-80 cm
    leave a dead-on face almost unlit, and unlit perforations read as "missing"
    when they are merely in shadow. Measurement only needs even light.
  * A fixed half-extent, not an auto-fit. RADIUS must comfortably exceed
    W/2 or the block is cropped; it must not be much larger or band resolution
    drops. Keep it a constant and adjust if the part changes size.
"""
import math
import os

import bpy
import mathutils
from mathutils import Vector

#: half-extent of the ortho frame in scene units. For a 19.7 cm part, 10.6
#: leaves ~4% margin and fills the frame. Must be > W/2.
RADIUS = 10.6

#: set dressing that must not appear in a measurement render
HIDE = ("Floor", "BounceL", "BounceR", "Key", "Top", "Rim", "Fill", "RearBayFill")

#: azimuth(deg), elevation(deg) per face, in this model's convention where the
#: front panel is -Y. 270 = -Y = front, 90 = +Y = rear.
FACES = {
    "front": (270.0, 0.0),
    "rear": (90.0, 0.0),
    "right": (0.0, 0.0),
    "left": (180.0, 0.0),
    "top": (0.0, 90.0),
    "bottom": (0.0, -90.0),
}


def render_face(blend, name, az_deg, el_deg, out_path,
                res=(1200, 1200), samples=64, hide=HIDE):
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res

    for h in hide:
        o = bpy.data.objects.get(h)
        if o:
            o.hide_render = True

    # flat grey world: a constant, not a gradient, so panel luminance stays
    # uniform and a band profile measures geometry rather than lighting
    w = bpy.data.worlds.get("OrthoWorld") or bpy.data.worlds.new("OrthoWorld")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.56, 0.58, 1.0)
    bg.inputs[1].default_value = 1.0
    sc.world = w

    ld = bpy.data.lights.new("OrthoFill", "AREA")
    ld.energy, ld.size = 900.0, 40.0
    lo = bpy.data.objects.new("OrthoFill", ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (24.0, 34.0, 30.0)
    lo.rotation_euler = (math.radians(46), 0.0, math.radians(145))

    cd = bpy.data.cameras.new("OrthoCam")
    cd.type = "ORTHO"
    cd.ortho_scale = RADIUS * 2.0
    cam = bpy.data.objects.new("OrthoCam", cd)
    bpy.context.collection.objects.link(cam)

    # distance is arbitrary under ortho; keep it well clear of the geometry
    a, e = math.radians(az_deg), math.radians(el_deg)
    mid = 4.75
    cam.location = Vector((60 * math.cos(e) * math.cos(a),
                           60 * math.cos(e) * math.sin(a),
                           60 * math.sin(e) + mid))
    d = (Vector((0, 0, mid)) - cam.location).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print("ORTHO %-8s %s" % (name, out_path))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    blend = os.path.join(root, "mac_studio.blend")
    if not os.path.exists(blend):
        blend = os.path.join(os.getcwd(), "mac_studio.blend")
    if not os.path.exists(blend):
        raise SystemExit("mac_studio.blend not found")

    out = os.path.join(root, "renders", "ortho")
    os.makedirs(out, exist_ok=True)
    for name, (az, el) in FACES.items():
        render_face(blend, name, az, el, os.path.join(out, name + ".png"))
    print("done:", len(FACES), "faces ->", out)


if __name__ == "__main__":
    main()
