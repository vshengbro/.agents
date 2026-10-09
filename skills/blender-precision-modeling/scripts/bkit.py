"""
bkit -- the Blender-side toolkit for precise, good-looking procedural models.

This module is imported by every model generator. It is deliberately small,
deterministic and scale-aware; everything here exists because leaving it to
per-model ad-hoc code produced measurable quality loss.

RULES THIS FILE ENFORCES
  1. UNITS. Author every dimension in millimetres. Convert to metres exactly
     once, inside `v()` / `mesh_from()`. Mixing mm and m is the single most
     common way a "197 mm" model becomes 197 m.
  2. SCALE-AWARE STAGING. Light power must scale with r^2 and camera distance
     with r, or a 3 mm screw and a 30 m crane are both black or both blown out
     from the same rig. `studio()` and `frame()` derive everything from the
     model's own bounding radius.
  3. COMPUTED LAYOUT. Repeated features (ports, holes, slats, teeth) are laid
     out from real feature widths plus an explicit gap. Hand-placed constants
     silently produce coincident faces that destroy EXACT booleans.
  4. NO LEFTOVER GEOMETRY. `finish()` reports the mesh health that a render
     cannot show: non-manifold edges, flipped normals, loose verts, bbox drift.
  5. DETERMINISM. Fixed RNG seed so two runs of the same spec are byte-comparable,
     which is what makes score-vs-score regression checks meaningful.

Import from a model script with:

    import bpy, bkit
    bkit.reset()
    ...
    bkit.report()          # prints + returns the dict the harness scores
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

# --------------------------------------------------------------------------
# 0. units
# --------------------------------------------------------------------------

MM = 0.001          # one millimetre in Blender units (metres)
CM = 0.01
M = 1.0
SEED = 20260101     # fixed: reproducible models


def v(*args):
    """Millimetres -> Blender Vector in metres. The ONLY conversion point.

    Accepts both v(x, y, z) and v((x, y, z)) so generator scripts can pass
    vertex tuples straight through without unpacking them.
    """
    if len(args) == 1 and hasattr(args[0], "__len__"):
        x, y, z = args[0]
    elif len(args) == 3:
        x, y, z = args
    else:
        raise TypeError("v() takes (x, y, z) or a 3-sequence, got %r" % (args,))
    return Vector((x * MM, y * MM, z * MM))


def u(mm_value):
    """Scalar millimetres -> metres."""
    return mm_value * MM


def rnd(seed=SEED):
    return random.Random(seed)


# --------------------------------------------------------------------------
# 1. scene lifecycle
# --------------------------------------------------------------------------

def reset():
    """Wipe the file to an empty scene with sane units and CPU-only Cycles."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = "MILLIMETERS"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"          # never rely on a GPU being present
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    # Adaptive sampling is the difference between a 20-hour catalog sweep and a
    # 2-hour one. `samples` is a CEILING, and a flat studio surface converges in
    # a fraction of it: without this every pixel pays the full budget even where
    # the answer stopped changing two hundred samples ago. The denoiser is
    # already smoothing what is left, so the threshold can sit loose.
    # Measured on acoustic_guitar (6-shot set, 8 threads): threshold 0.02 ->
    # 19.8 s, 0.05 -> 15.6 s, 0.10 -> 13.6 s. Bounces were measured too and made
    # no difference (8/6 vs 3/2 within 1%), so they are left alone.
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.adaptive_min_samples = 8
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 6
    # Caustics cost real time and put fireflies in the specular highlights of
    # every metal part; nothing in this catalog is a caustic showcase.
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = 1100
    sc.render.resolution_y = 850
    sc.render.film_transparent = False
    # Standard keeps material colour honest; Filmic/AgX desaturate saturated paint.
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    return sc


# --------------------------------------------------------------------------
# 2. materials
# --------------------------------------------------------------------------

_PRESETS = {
    # Metal BASE TONE is the single strongest lever on whether a metal reads as
    # metal. Under this key, a base near 0.82 renders a near-white sheet with no
    # tonal range -- it reads as paper, not steel. Measured on a knife blade
    # with the lighting held fixed: base 0.82 washed out to white, base 0.48
    # with metal 0.90 read as steel with a visible gradient.
    #
    # Metalness stays deliberately below 1.0. A perfectly metallic surface has
    # NO diffuse term, so in this dark studio it mirrors the backdrop and reads
    # black -- every wave-2 metal model needed a local override to be visible at
    # all. 0.85 keeps the metallic read while letting enough diffuse through to
    # hold its form. Use bkit.pbr(..., metal=1.0) deliberately for mirrors only.
    "polished_metal": dict(base=(0.62, 0.63, 0.65), metal=0.85, rough=0.14),
    "brushed_metal": dict(base=(0.54, 0.55, 0.57), bump=0.0003, rough_var=0.06,  metal=0.85, rough=0.32),
    "anodized":      dict(base=(0.45, 0.46, 0.49), metal=0.85, rough=0.42),
    "dark_metal":    dict(base=(0.24, 0.25, 0.27), metal=0.85, rough=0.38),
    "gold":          dict(base=(0.86, 0.64, 0.26), metal=0.85, rough=0.18),
    "copper":        dict(base=(0.78, 0.44, 0.30), metal=0.85, rough=0.22),
    "steel":         dict(base=(0.50, 0.51, 0.53), metal=0.85, rough=0.25),
    "white_plastic": dict(base=(0.88, 0.88, 0.87), metal=0.0, rough=0.35),
    "black_plastic": dict(base=(0.045, 0.045, 0.050), metal=0.0, rough=0.30),
    "red_paint":     dict(base=(0.62, 0.055, 0.045), metal=0.0, rough=0.22),
    "blue_paint":    dict(base=(0.045, 0.14, 0.52), metal=0.0, rough=0.22),
    "yellow_paint":  dict(base=(0.80, 0.62, 0.05), metal=0.0, rough=0.25),
    "wood":          dict(base=(0.35, 0.20, 0.09), bump=0.0012, rough_var=0.1,  metal=0.0, rough=0.48),
    "rubber":        dict(base=(0.055, 0.055, 0.058), bump=0.0005, rough_var=0.1,  metal=0.0, rough=0.72),
    "ceramic":       dict(base=(0.92, 0.91, 0.88), bump=0.0002, rough_var=0.05,  metal=0.0, rough=0.18),
    # Full transmission renders near-black against a dark studio, because the
    # glass has nothing bright behind it to show. A partial transmission with a
    # tinted base reads as glass and still holds its silhouette.
    "glass":         dict(base=(0.82, 0.88, 0.92), metal=0.0, rough=0.05,
                          transmission=0.82, ior=1.45),
    "fabric":        dict(base=(0.34, 0.33, 0.36), bump=0.0008, rough_var=0.12,  metal=0.0, rough=0.88),
    "soil":          dict(base=(0.16, 0.11, 0.07), bump=0.0018, rough_var=0.14,  metal=0.0, rough=0.92),
    "leaf":          dict(base=(0.13, 0.34, 0.09), bump=0.0006, rough_var=0.1,  metal=0.0, rough=0.55),
}


def _set(bsdf, names, value):
    """Set the first socket that exists -- socket names move between versions."""
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return True
    return False


def _auto_detail(rough, metal, base, bump, rough_var):
    """Derive micro-detail for any material, from its own parameters.

    Measured across the catalog: 2,185 direct `pbr()` calls versus 527
    `preset()` calls, and ZERO passing `bump`. Tuning the preset table therefore
    left ~81% of the catalog's materials untouched -- adding detail to seven
    named presets changed almost nothing, because most models build their own
    material inline. So the default has to live in `pbr()` itself, derived from
    the material that is actually being made.

    A perfectly uniform roughness is the strongest "synthetic plastic" signal
    there is, so every material gets some variation unless the caller asks for
    a specific amount by passing bump/rough_var explicitly.
    """
    if bump is not None or rough_var is not None:
        return (bump or 0.0), (rough_var or 0.0)
    lum = 0.2126 * base[0] + 0.7152 * base[1] + 0.0722 * base[2]
    # Swing widened ~2.5x: at +-0.11 a large flat face still read as one
    # uniform plate. Round 4 called this out explicitly.
    if metal >= 0.5:
        # A metal gets its surface variation from REFLECTION, not from
        # roughness jitter. Widening this swing was tried and reverted: at
        # rough_var 0.13 a polished blade grew visible dark speckle across its
        # whole face, which reads as dirt rather than as brushing. Metals keep a
        # whisper of tooth so a perfectly flat face is not perfectly featureless.
        return 0.00016, 0.04
    if rough >= 0.65:
        return 0.0011, 0.26          # rubber, fabric, soil
    if rough >= 0.35:
        return 0.0008, 0.20          # wood, stone, plastic
    if lum < 0.10:
        return 0.0004, 0.12          # dark glossy
    return 0.00022, 0.10             # ceramic, paint, gloss


def pbr(name, base=(0.8, 0.8, 0.8), rough=0.4, metal=0.0, transmission=0.0,
        ior=1.45, emission=None, emission_strength=0.0, coat=0.0, alpha=1.0,
        bump=None, bump_scale=None, bump_detail=2.0, rough_var=None):
    """Create (or fetch) a Principled material. Socket names are version-proofed.

    `bump` (metres of displacement) and `rough_var` add procedural micro-detail
    driven by a noise texture, and DEFAULT to a value derived from this
    material's own roughness, metalness and brightness. Pass explicit values to
    override, or `bump=0, rough_var=0` to ask for a perfectly smooth surface.

    `bump_scale` is **cycles per metre** -- the noise is driven from world
    position -- and defaults to `1 / bump`, i.e. the surface undulates over
    roughly the distance it is displaced. Tying the two together is what keeps
    the detail reading as tooth: a noise feature far larger than the bump reads
    as slow waves, one far smaller reads as dirt.
    """
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    bump, rough_var = _auto_detail(rough, metal, base, bump, rough_var)
    if bump_scale is None:
        bump_scale = (1.0 / bump) if bump else 90.0
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if (bump or rough_var) and b is not None:
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexNoise")
        # Feature size is a physical quantity: a 0.5 mm tooth on a screwdriver
        # and a 0.5 mm tooth on a van. The vector has to be chosen for that.
        #
        #   TexCoord.Object  -- scaled by the object's own transform, so a
        #     non-uniformly scaled primitive smears the detail into bands.
        #   TexCoord.Generated -- normalised to the bounding box, so the feature
        #     size scales WITH the object: bump_scale 90 on a 5 mm part is
        #     0.05 mm of tooth, and on a 5 m van it is 55 mm. Large panels came
        #     out looking sandblasted.
        #   Geometry.Position -- world space. Neither problem: it is not affected
        #     by an object's transform, and one unit is one metre always.
        #
        # The cost is that the texture is not attached to the surface, so a part
        # that moves after the material is created slides through its own tooth.
        # Nothing in this catalog moves after build(), and "wrong scale" is a
        # defect on every render while "the tool is a repeat transformer" is a
        # defect on none.
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nt.links.new(geo.outputs["Position"], tex.inputs["Vector"])
        tex.inputs["Scale"].default_value = bump_scale
        if "Detail" in tex.inputs:
            tex.inputs["Detail"].default_value = bump_detail
        if bump:
            bn = nt.nodes.new("ShaderNodeBump")
            bn.inputs["Strength"].default_value = 1.0
            bn.inputs["Distance"].default_value = u(bump)
            nt.links.new(tex.outputs["Fac"], bn.inputs["Height"])
            nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
        if rough_var:
            rr = nt.nodes.new("ShaderNodeMapRange")
            rr.inputs["To Min"].default_value = max(0.02, rough - rough_var)
            rr.inputs["To Max"].default_value = min(1.0, rough + rough_var)
            nt.links.new(tex.outputs["Fac"], rr.inputs["Value"])
            nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    _set(b, ["Base Color"], (base[0], base[1], base[2], 1.0))
    _set(b, ["Roughness"], rough)
    _set(b, ["Metallic"], metal)
    _set(b, ["IOR"], ior)
    _set(b, ["Alpha"], alpha)
    if transmission:
        _set(b, ["Transmission Weight", "Transmission"], transmission)
    if coat:
        _set(b, ["Coat Weight", "Clearcoat"], coat)
        _set(b, ["Coat Roughness", "Clearcoat Roughness"], 0.06)
    if emission is not None:
        _set(b, ["Emission Color", "Emission"], (emission[0], emission[1], emission[2], 1.0))
        _set(b, ["Emission Strength"], emission_strength)
    if alpha < 1.0 or transmission:
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else mat.blend_method
    return mat


def preset(name):
    """Fetch a named material preset, e.g. preset('brushed_metal')."""
    if name not in _PRESETS:
        raise KeyError("unknown material preset %r (have: %s)"
                       % (name, ", ".join(sorted(_PRESETS))))
    return pbr(name, **_PRESETS[name])


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


# --------------------------------------------------------------------------
# 3. mesh construction
# --------------------------------------------------------------------------

def mesh_from(name, verts_mm, faces, mat=None, smooth=False):
    """verts_mm in millimetres, faces as index tuples -> object in the scene."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v(p)) for p in verts_mm], [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat is not None:
        assign(ob, mat)
    if smooth:
        shade_smooth(ob)
    return ob


def shade_smooth(obj, angle_deg=32.0):
    """Smooth shading with an angle threshold that does not depend on an asset.

    This used to call `bpy.ops.object.shade_auto_smooth()`, which in Blender 4.x
    links a "Smooth by Angle" geometry-nodes asset out of the install's
    datafiles. On a patched or trimmed Blender that asset is absent, the
    operator still returns without raising, and the mesh comes back with every
    polygon still flat -- so the `except` fallback never fired and nothing
    reported a problem. Every curved surface in the catalog was faceted, and a
    vision round independently reported "stair-stepped silhouettes on cylinders"
    without knowing why.

    An EdgeSplit modifier gives the same result with no asset at all: every face
    smooth, and edges whose adjacent faces diverge by more than the threshold
    split apart so the hard edge stays hard. Verified by `scripts/shadecheck.py`,
    which counts flat polygons rather than trusting the call to have worked.
    """
    for poly in obj.data.polygons:
        poly.use_smooth = True
    for mod in list(obj.modifiers):
        if mod.type == "EDGE_SPLIT":
            obj.modifiers.remove(mod)
    m = obj.modifiers.new("AutoSmooth", "EDGE_SPLIT")
    m.use_edge_angle = True
    m.use_edge_sharp = True
    m.split_angle = math.radians(angle_deg)
    return obj


def box(name, sx, sy, sz, centre=(0, 0, 0), mat=None):
    """Axis-aligned box given full sizes in mm."""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    cx, cy, cz = centre
    verts = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
             (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
             (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
             (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_from(name, verts, faces, mat)


def rounded_box(name, sx, sy, sz, r=2.0, segments=4, centre=(0, 0, 0), mat=None):
    """Box with filleted edges. `r` is the corner radius in mm, clamped to fit."""
    r = max(0.01, min(r, sx / 2.05, sy / 2.05, sz / 2.05))
    ob = box(name, sx, sy, sz, centre, mat)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = u(r)
    bev.segments = segments
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(30)
    bev.harden_normals = False
    apply_mods(ob)
    return ob


def cylinder(name, radius, height, segments=48, centre=(0, 0, 0), axis="Z",
             cap=True, mat=None, smooth=True, r2=None):
    """Cylinder / truncated cone in mm. r2 gives a cone (None = same as radius)."""
    r2 = radius if r2 is None else r2
    verts, faces = [], []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        verts.append((math.cos(a) * radius, math.sin(a) * radius, -height / 2.0))
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        verts.append((math.cos(a) * r2, math.sin(a) * r2, height / 2.0))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))
    if cap:
        faces.append(tuple(range(segments - 1, -1, -1)))
        faces.append(tuple(range(segments, 2 * segments)))
    ob = mesh_from(name, verts, faces, mat)
    place(ob, centre, axis)
    if smooth:
        shade_smooth(ob, 40)
    return ob


def tube(name, r_out, r_in, height, segments=48, centre=(0, 0, 0), axis="Z", mat=None):
    """Hollow cylinder (pipe / ring / washer) with a real wall thickness."""
    h = height / 2.0
    verts, faces = [], []
    for z in (-h, h):
        for r in (r_out, r_in):
            for i in range(segments):
                a = 2.0 * math.pi * i / segments
                verts.append((math.cos(a) * r, math.sin(a) * r, z))
    O0, I0, O1, I1 = 0, segments, 2 * segments, 3 * segments
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((O0 + i, O0 + j, O1 + j, O1 + i))     # outer wall
        faces.append((I1 + i, I1 + j, I0 + j, I0 + i))     # inner wall
        faces.append((O0 + j, O0 + i, I0 + i, I0 + j))     # bottom ring
        faces.append((O1 + i, O1 + j, I1 + j, I1 + i))     # top ring
    ob = mesh_from(name, verts, faces, mat)
    place(ob, centre, axis)
    shade_smooth(ob, 40)
    return ob


def uv_sphere(name, radius, segments=48, rings=24, centre=(0, 0, 0), mat=None):
    verts, faces = [], []
    verts.append((0, 0, radius))
    for j in range(1, rings):
        phi = math.pi * j / rings
        z = radius * math.cos(phi)
        r = radius * math.sin(phi)
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    verts.append((0, 0, -radius))
    top, bottom = 0, len(verts) - 1
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((top, 1 + j, 1 + i))
    for ring in range(rings - 2):
        b0 = 1 + ring * segments
        b1 = b0 + segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((b0 + i, b0 + j, b1 + j, b1 + i))
    base = 1 + (rings - 2) * segments
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((bottom, base + i, base + j))
    ob = mesh_from(name, verts, faces, mat)
    weld(ob)          # collapse the pole fans, which float within 1e-6 of each other
    recalc(ob)
    place(ob, centre, "Z")
    shade_smooth(ob, 60)
    return ob


# recipes.md lists `sphere()`; bkit's real name is uv_sphere (it follows the
# bpy operator it mirrors). Alias it so models written from the documented API
# work instead of dying with AttributeError.
sphere = uv_sphere


def torus(name, r_major, r_minor, seg_major=64, seg_minor=24, centre=(0, 0, 0),
          axis="Z", mat=None):
    """Torus built from explicit loops.

    bmesh.ops.create_torus does not exist in the 4.x bmesh.ops namespace, and
    a naive use of a mis-signed operator silently returns None. Parametric loops
    are also better behaved under subdivision.
    """
    verts, faces = [], []
    for i in range(seg_major):
        a = 2.0 * math.pi * i / seg_major
        ca, sa = math.cos(a), math.sin(a)
        for j in range(seg_minor):
            b = 2.0 * math.pi * j / seg_minor
            rr = r_major + r_minor * math.cos(b)
            verts.append((ca * rr, sa * rr, r_minor * math.sin(b)))
    for i in range(seg_major):
        i2 = (i + 1) % seg_major
        for j in range(seg_minor):
            j2 = (j + 1) % seg_minor
            faces.append((i * seg_minor + j, i2 * seg_minor + j,
                          i2 * seg_minor + j2, i * seg_minor + j2))
    ob = mesh_from(name, verts, faces, mat)
    recalc(ob)
    place(ob, centre, axis)
    shade_smooth(ob, 60)
    return ob


def recalc(obj):
    """Make face normals consistently outward on a closed solid.

    Hand-built parametric surfaces (tori, arcs, lofts) get their winding subtly
    wrong depending on the sweep direction, and an inward-facing shell renders
    as a black hole while still passing a non-manifold check. Recomputing is
    cheap and makes the mesh-health volume test trustworthy.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def weld(obj, dist_mm=0.01):
    """Merge coincident vertices.

    Necessary wherever a revolve or sweep reaches its axis: a lathe profile that
    starts at radius 0 emits `segments` vertices that all sit at exactly the
    same point, which reads as a non-manifold tangle and poisons the volume
    check. Welding collapses them into a proper pole fan.

    The default is 0.01 mm, NOT something smaller. Blender 4.5 hashes weld
    candidates at float32 precision, so a 5e-7 m threshold sits below the hash's
    resolution and stops merging entirely: lathe poles then fail to collapse
    above roughly 12 m and every large model silently carries 40-90 non-manifold
    edges. Nothing warned -- the models simply stopped being watertight once
    the catalog reached architecture scale.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=u(dist_mm))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def lathe(name, profile, segments=48, centre=(0, 0, 0), mat=None, cap_ends=True,
          smooth=True):
    """Revolve a (radius_mm, z_mm) profile around Z. The workhorse for vessels,
    bottles, lamp shades, wheels, knobs -- anything with a circular silhouette."""
    verts, faces = [], []
    n = len(profile)
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        for (r, z) in profile:
            verts.append((ca * r, sa * r, z))
    for i in range(segments):
        i2 = (i + 1) % segments
        for k in range(n - 1):
            faces.append((i * n + k, i2 * n + k, i2 * n + k + 1, i * n + k + 1))
    if cap_ends and n >= 2:
        if abs(profile[0][0]) > 1e-6:
            faces.append(tuple(i * n for i in range(segments))[::-1])
        if abs(profile[-1][0]) > 1e-6:
            faces.append(tuple(i * n + (n - 1) for i in range(segments)))
    ob = mesh_from(name, verts, faces, mat)
    place(ob, centre, "Z")
    weld(ob)                      # collapse axis vertices into a pole
    if smooth:
        shade_smooth(ob, 40)
    return ob


def loft(name, sections, closed_loop=True, cap_start=True, cap_end=True,
         mat=None, smooth=False):
    """Bridge a list of equal-length vertex rings (mm) into a surface.

    Sections must all have the same vertex count. This is how car bodies, chairs,
    hulls and anything with a changing cross-section are built.
    """
    if len(sections) < 2:
        raise ValueError("loft needs >= 2 sections")
    n = len(sections[0])
    if any(len(s) != n for s in sections):
        raise ValueError("all loft sections must have %d points" % n)
    # Accept either (x, y) or (x, y, z) points. The section helpers return 3D,
    # but a 2D ring bridged by loft() is the natural thing to write by hand, and
    # silently rejecting it is a trap worth more than a strict signature.
    verts, faces = [], []
    for s in sections:
        for p in s:
            verts.append((p[0], p[1], p[2]) if len(p) >= 3 else (p[0], p[1], 0.0))
    for k in range(len(sections) - 1):
        a, b = k * n, (k + 1) * n
        rng = range(n) if closed_loop else range(n - 1)
        for i in rng:
            j = (i + 1) % n
            faces.append((a + i, a + j, b + j, b + i))
    if cap_start:
        faces.append(tuple(range(n - 1, -1, -1)))
    if cap_end:
        base = (len(sections) - 1) * n
        faces.append(tuple(range(base, base + n)))
    ob = mesh_from(name, verts, faces, mat)
    if smooth:
        shade_smooth(ob, 45)
    return ob


def rounded_rect_section(sx, sy, r, per_corner=6, centre=(0, 0, 0)):
    """One closed CCW ring of a rounded rectangle -- the standard loft section."""
    hx, hy = sx / 2.0 - r, sy / 2.0 - r
    pts = []
    for cx, cy, a0 in ((hx, hy, 0.0), (-hx, hy, math.pi / 2),
                       (-hx, -hy, math.pi), (hx, -hy, 3 * math.pi / 2)):
        for i in range(per_corner + 1):
            a = a0 + (math.pi / 2) * i / per_corner
            pts.append((centre[0] + cx + math.cos(a) * r,
                        centre[1] + cy + math.sin(a) * r))
    # drop duplicated seam points. These return 2D rings; loft() accepts 2D or
    # 3D, so both a hand-written ring and a 3D section compose with it.
    out = []
    for p in pts:
        if not out or (abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9):
            out.append((p[0], p[1]))
    return out


def superellipse_section(sx, sy, n=3.0, steps=64, centre=(0, 0, 0)):
    """|x/a|^n + |y/b|^n = 1 ring. n=2 ellipse, n=4 squircle, n>8 boxy.

    Lets one loft cover cars (n~4), eggs (n~2.2) and tablets (n~8) without
    hand-built per-corner lists.
    """
    pts = []
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        x = math.copysign(abs(ct) ** (2.0 / n), ct) * sx / 2.0
        y = math.copysign(abs(st) ** (2.0 / n), st) * sy / 2.0
        pts.append((centre[0] + x, centre[1] + y))
    return pts


def extrude_profile(name, poly, height, centre=(0, 0, 0), axis="Z", mat=None,
                    cap=True):
    """Extrude a closed 2D polygon (mm) along an axis. Sharp-edged."""
    n = len(poly)
    verts = [(p[0], p[1], -height / 2.0) for p in poly] + \
            [(p[0], p[1], height / 2.0) for p in poly]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    if cap:
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range(n, 2 * n)))
    ob = mesh_from(name, verts, faces, mat)
    place(ob, centre, axis)
    return ob


# --------------------------------------------------------------------------
# 4. transforms / operators
# --------------------------------------------------------------------------

def arc_torus(name, r_major, r_minor, a0_deg, a1_deg, centre=(0, 0, 0),
              plane="XZ", seg_major=None, seg_minor=24, mat=None, caps=True):
    """A partial torus -- mug/kettle handles, hooks, arches, horseshoes, brackets.

    The arc runs from a0 to a1 degrees inside `plane` ("XZ", "XY" or "YZ").
    `caps` closes the two ends; leave it off when the arc ends should be buried
    inside another solid (a handle whose tips disappear into a mug wall).
    """
    span = abs(a1_deg - a0_deg)
    seg_major = seg_major or max(6, int(span / 4.0))
    verts, faces = [], []
    for i in range(seg_major + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / seg_major)
        ca, sa = math.cos(a), math.sin(a)
        for j in range(seg_minor):
            b = 2.0 * math.pi * j / seg_minor
            rr = r_major + r_minor * math.cos(b)
            off = r_minor * math.sin(b)
            if plane == "XZ":
                p = (ca * rr, off, sa * rr)
            elif plane == "XY":
                p = (ca * rr, sa * rr, off)
            else:                                    # "YZ"
                p = (off, ca * rr, sa * rr)
            verts.append(p)
    for i in range(seg_major):
        for j in range(seg_minor):
            j2 = (j + 1) % seg_minor
            a0i = i * seg_minor
            a1i = (i + 1) * seg_minor
            faces.append((a0i + j, a1i + j, a1i + j2, a0i + j2))
    if caps:
        faces.append(tuple(range(seg_minor - 1, -1, -1)))
        base = seg_major * seg_minor
        faces.append(tuple(range(base, base + seg_minor)))
    ob = mesh_from(name, verts, faces, mat)
    recalc(ob)
    # Build around the origin and move it with place(), like every other
    # primitive. Baking `centre` into the vertices instead meant that composing
    # this with bkit.duplicate() -- which SETS location -- double-counted the
    # offset and pushed parts twice as far as intended.
    place(ob, centre)
    shade_smooth(ob, 60)
    return ob


def move(obj, x_mm, y_mm, z_mm):
    """Translate by MILLIMETRES.

    Blender's `Object.location` is in METRES, like every other raw bpy numeric.
    Assigning `obj.location = (5, 0, 8)` therefore puts the part at 5000 mm and
    silently blows the scene bounding box up by three orders of magnitude.
    Everything else in a model script is millimetres, so use this.
    """
    obj.location = Vector((obj.location.x + u(x_mm),
                           obj.location.y + u(y_mm),
                           obj.location.z + u(z_mm)))
    # matrix_world is cached; without this the next bbox()/measure() call reads
    # pre-move coordinates and the move silently appears to do nothing.
    bpy.context.view_layer.update()
    return obj


def place(obj, centre, axis="Z"):
    """Move an origin-centred primitive to `centre` (mm) and orient its axis.

    The refresh at the end is not decoration. `matrix_world` is cached and is
    only recomputed on a depsgraph update, so an object placed without one
    reports its PRE-PLACE coordinates to the next bbox()/measure()/render call.
    That was being masked here by `shade_auto_smooth()`, which happened to force
    an update as a side effect; when smooth shading stopped going through that
    operator, a cylinder built at centre=(0,0,20) started measuring -20..20 and
    every detached-geometry self-test moved by exactly the amount it was off.
    `move()` has always refreshed for this reason; `place()` now does too.
    """
    obj.location = v(*centre)
    if axis == "X":
        obj.rotation_euler = (0.0, math.radians(90), 0.0)
    elif axis == "Y":
        obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    bpy.context.view_layer.update()
    return obj


def rotate_about(obj, deg_x=0.0, deg_y=0.0, deg_z=0.0):
    """Rotate a part about its OWN centre, baking the rotation into the mesh.

    Assigning `obj.rotation_euler` does NOT do this. It rotates about the
    object's origin, and this toolkit deliberately leaves that origin at the
    WORLD origin for the recipes that bake `centre` into mesh data -- which is
    most of them. So a one-line `rotation_euler` assignment on a part authored
    24 m up a tower swings that part around the scene origin rather than around
    itself. A lint across the catalog found 120 models visibly disfigured this
    way, the worst displacing a knife blade by 127% of the whole model's size.

    Two details make this correct where a naive version is not:

    * It rotates about the mesh's own centroid, not about `obj.location`. The
      recipes are inconsistent about where the centre lives -- `box()` bakes it
      into vertex data while `cylinder()` puts it in `obj.location` -- so the
      object's origin is the one thing that cannot be trusted as the pivot.
    * It bakes into the mesh and leaves `rotation_euler` at zero. A leftover
      rotation keeps composing with every later `move()`, which is how a part
      ends up somewhere nobody authored.

    `rotation_euler` is still correct for a part authored AT the world origin,
    which is why this is a helper rather than a change to the recipes.
    """
    if not obj.data.vertices:
        return obj
    c = Vector((0.0, 0.0, 0.0))
    for v in obj.data.vertices:
        c += v.co
    c /= len(obj.data.vertices)
    rx = math.radians(deg_x)
    ry = math.radians(deg_y)
    rz = math.radians(deg_z)
    rot = (Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
           @ Matrix.Rotation(rx, 4, "X"))
    # rotate ABOUT c is T(c) . R . T(-c): shift the pivot to the origin, turn,
    # shift back. Writing it the other way round (T(-c) . R . T(c)) maps the
    # pivot c to R(2c) - c, which throws the part further from where it was
    # instead of turning it in place -- and it still returns an object, so
    # nothing complains.
    obj.data.transform(Matrix.Translation(c) @ rot @ Matrix.Translation(-c))
    obj.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    return obj


def apply_mods(obj):
    """Bake every modifier so later booleans and bbox maths see real geometry."""
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError:
            obj.modifiers.remove(m)
    return obj


def bevel(obj, width_mm, segments=3, angle_deg=30, apply=True, clamp=True):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = u(width_mm)
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle_deg)
    if clamp:
        # Without this, bevelling a 5+-gon (a dodecahedron face, a pentagonal
        # prism) splits the n-gon into a fan and leaves the mesh non-manifold.
        m.use_clamp_overlap = True
    if apply:
        apply_mods(obj)
    return obj


def mirror(obj, axis="X", apply=True, merge=None):
    """Reflect the object across an axis plane.

    Neither merge setting is right in general, and getting it wrong is silent:

    * Blender's default (merge ON) welds the two halves' seam vertices. If the
      source geometry TOUCHES the mirror plane, that weld collapses two
      boundaries into one and leaves a ring of single-face edges -- 38
      non-manifold edges for a typical panel.
    * merge OFF keeps each half a separate closed shell, which is right for
      that panel -- but if the source is ALREADY symmetric about the plane the
      mirrored copy lands exactly on top of it, giving coincident duplicate
      geometry and dozens of four-face edges. That is how an airliner lost 76
      non-manifold edges.

    So `merge=None` (the default) picks per object: weld when the source crosses
    or sits on the plane, keep the halves separate when it does not. Pass
    `merge=True` or `False` to force one behaviour.
    """
    bpy.context.view_layer.update()
    bb = bbox(obj)
    lo = {"X": bb["x_min"], "Y": bb["y_min"], "Z": bb["z_min"]}[axis]
    hi = {"X": bb["x_max"], "Y": bb["y_max"], "Z": bb["z_max"]}[axis]
    span = abs(hi - lo) or 1.0
    tol = max(0.05, span * 1e-3)

    # ALREADY symmetric about the plane: reflecting it lays a second copy
    # exactly on top of the first, and the coincident geometry reads as dozens
    # of four-face edges. Four aircraft did this and reported 76-152
    # non-manifold edges each. A body that already spans both sides does not
    # need mirroring, so skip it.
    if abs(lo + hi) < tol and (lo < 0 < hi or (lo > 0 and hi > 0)):
        return obj

    # Weld ONLY when the source genuinely CROSSES the plane. A body that
    # straddles it needs its halves joined; a panel that merely SITS on it
    # would have its boundary welded shut, and a part entirely to one side
    # gains nothing from merging. Forcing merge on the latter two is what
    # produces stray single-face edges.
    if merge is None:
        merge = (lo < -tol) and (hi > tol)
    m = obj.modifiers.new("Mirror", "MIRROR")
    m.use_axis = (axis == "X", axis == "Y", axis == "Z")
    m.use_mirror_merge = merge
    if apply:
        apply_mods(obj)
        recalc(obj)
    return obj


def array_linear(obj, count, offset_mm, apply=True, world=False):
    """Repeat `obj` in a straight line, `count` times, `offset_mm` apart.

    The Array modifier's constant offset is in the object's LOCAL space, so
    arraying a rotated member steps along that member's own axis rather than the
    direction you asked for -- a ledger that was rotated about Y swept sideways.
    A scaffold built that way looks like it came apart.

    Pass `world=True` to have the offset rotated into the object's local frame
    first, so `offset_mm` is the world-space step you actually intend. Arrayed
    members with no rotation of their own are unaffected either way.
    """
    off = v(*offset_mm)
    if world:
        bpy.context.view_layer.update()
        try:
            off = obj.matrix_world.to_3x3().inverted() @ off
        except Exception:
            off = v(*offset_mm)
    m = obj.modifiers.new("Array", "ARRAY")
    m.count = count
    m.use_relative_offset = False
    m.use_constant_offset = True
    m.constant_offset_displace = off
    if apply:
        apply_mods(obj)
    return obj


def array_radial(obj, count, radius_mm=None, axis="Z", apply=True, centre=None):
    """Sweep `obj` around the Z axis (or X/Y) in equal angular steps.

    The offset empty must carry the ANGULAR STEP, not identity rotation.
    Blender's object offset is `empty.matrix_world.inverted() @ obj.matrix_world`,
    so an identity-rotated empty at the origin yields a pure translation and
    every copy lands on top of the last. Giving the empty one step of rotation
    turns the offset into a real orbit.

    `radius_mm` is optional and only documentary -- place `obj` at the radius you
    want yourself, so the sweep centres on the real axis.

    `centre` (mm) is the hub the copies orbit about, defaulting to the world
    origin. Pass it whenever the hub is anywhere else -- a wheel whose hub sits
    at (900, 300, 0) otherwise throws every spoke outside its own footprint.
    """
    step = 2.0 * math.pi / max(1, count)
    m = obj.modifiers.new("ArrayRadial", "ARRAY")
    m.count = count
    m.use_relative_offset = False
    m.use_object_offset = True
    m.use_merge_vertices = False
    empty = bpy.data.objects.new("ArrayPivot", None)
    bpy.context.collection.objects.link(empty)
    empty.location = v(0, 0, 0)
    # The modifier's object offset is `empty.matrix_world.inverted() @
    # obj.matrix_world`. Putting the empty at the ORIGIN with a positive
    # rotation therefore yields R(-T) @ T(c), and copy k lands at c*(1+k):
    # a spiral, not an orbit -- observed as the 8th copy at 2.4x the radius.
    #
    # A pure rotation still orbits the WORLD ORIGIN, which is only right when
    # the hub is at the origin. For a hub anywhere else, the relative transform
    # must be a rotation ABOUT THAT HUB:
    #     offset_to = T(C) R(T) T(-C)
    #     empty.matrix_world = M_obj @ T(C) R(-T) T(-C)
    # otherwise every copy swings outside the feature's own footprint -- which
    # reads as braces and spokes "spraying away" from the structure.
    bpy.context.view_layer.update()
    if centre is None:
        centre = (0.0, 0.0, 0.0)
    cvec = v(*centre)
    rot_axis = {"X": Vector((1.0, 0.0, 0.0)),
                "Y": Vector((0.0, 1.0, 0.0))}.get(axis, Vector((0.0, 0.0, 1.0)))
    Tc = Matrix.Translation(cvec)
    Rm = Matrix.Rotation(-step, 4, rot_axis)
    empty.matrix_world = Tc @ Rm @ Tc.inverted()
    m.offset_object = empty
    # Blender takes the offset object's matrix_world AS the local offset -- it is
    # NOT empty^-1 @ object. Multiplying by the object's own matrix (which an
    # earlier version did) re-introduces the object's translation and stacks
    # every copy coincident. Measured: with the Mo factor the span is 0.010 m;
    # without it, a correct orbit. So the pivot is the rotation ALONE.
    bpy.context.view_layer.update()
    if apply:
        apply_mods(obj)
    return obj


def boolean(obj, cutter, op="DIFFERENCE", apply=True, solver="EXACT"):
    m = obj.modifiers.new("Bool", "BOOLEAN")
    m.operation = op
    m.object = cutter
    m.solver = solver
    if apply:
        apply_mods(obj)
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obj


def bore_segments(host_segments):
    """Segment count for a cutter coaxial with a host surface.

    A boolean cutter that shares the host's exact segment count puts coincident
    facet edges on both surfaces, and the EXACT solver answers that with a
    handful of non-manifold edges. Off by a few segments and the same cut comes
    back clean.
    """
    return max(16, int(host_segments) + 7)


def bore(obj, radius, depth=None, centre=(0, 0, 0), axis="Z", host_segments=64,
         mat=None, apply=True):
    """Drill a coaxial bore with a deliberately different segment count."""
    cutter = cylinder("_bore_cut", radius, depth, segments=bore_segments(host_segments),
                      centre=centre, axis=axis, mat=mat)
    return boolean(obj, cutter, "DIFFERENCE", apply=apply)


def join(objs, name=None):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    if name:
        ob.name = name
    return ob


def duplicate(obj, name, offset_mm=(0, 0, 0), rot_deg=(0, 0, 0)):
    new = obj.copy()
    new.data = obj.data.copy()
    new.name = name
    bpy.context.collection.objects.link(new)
    new.location = v(*offset_mm)
    new.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    return new


def set_origin_bottom(obj):
    """Drop the object origin to the lowest point; keeps models sitting on z=0."""
    bb = bbox(obj)
    dz = -(bb["z_min"])
    for vert in obj.data.vertices:
        vert.co.z += u(dz)
    return obj


def centre_origin(obj):
    bb = bbox(obj)
    cx = (bb["x_min"] + bb["x_max"]) / 2.0
    cy = (bb["y_min"] + bb["y_max"]) / 2.0
    cz = (bb["z_min"] + bb["z_max"]) / 2.0
    for vert in obj.data.vertices:
        vert.co.x -= u(cx)
        vert.co.y -= u(cy)
        vert.co.z -= u(cz)
    return obj


# --------------------------------------------------------------------------
# 5. measured layout (the anti-hand-placing rule)
# --------------------------------------------------------------------------

def lay_out(widths, gap, centre=True):
    """X positions (mm) for a row of features given their widths and one gap.

    Returns a list of (x_centre, width) in mm. Compute every repeated feature
    through this, never with hand-placed constants: two hand-placed features
    that land on the same coordinate produce coincident boolean faces, and the
    EXACT solver answers that by deleting the whole body.
    """
    total = sum(widths) + gap * (len(widths) - 1)
    x = -total / 2.0 if centre else 0.0
    out = []
    for w in widths:
        out.append((x + w / 2.0, w))
        x += w + gap
    return out


def grid_positions(cols, rows, pitch_x, pitch_y, centre=True):
    """Row-major (x, y) positions in mm for a perforated panel / key grid."""
    out = []
    x0 = -(cols - 1) * pitch_x / 2.0 if centre else 0.0
    y0 = -(rows - 1) * pitch_y / 2.0 if centre else 0.0
    for r in range(rows):
        for c in range(cols):
            out.append((x0 + c * pitch_x, y0 + r * pitch_y))
    return out


def perforated_panel(name, cols, rows, pitch_x, pitch_y, hole_r, panel_sx, panel_sy,
                     thickness, mat=None):
    """A real perforated sheet: circular holes cut through a thin plate.

    Built as a single mesh (ring around every hole) rather than N booleans --
    orders of magnitude faster and immune to boolean solver failures.
    """
    verts, faces = [], []
    hx, hy = panel_sx / 2.0, panel_sy / 2.0
    z0, z1 = -thickness / 2.0, thickness / 2.0
    seg = 16
    for (px, py) in grid_positions(cols, rows, pitch_x, pitch_y):
        for z in (z0, z1):
            for i in range(seg):
                a = 2.0 * math.pi * i / seg
                verts.append((px + math.cos(a) * hole_r, py + math.sin(a) * hole_r, z))
    base = 0
    for k in range(cols * rows):
        for i in range(seg):
            j = (i + 1) % seg
            a0 = base + i
            b0 = base + seg + i
            faces.append((a0, base + j, base + seg + j, b0))      # hole wall
        base += 2 * seg
    # NB: do not append a separate border ring here. Those vertices were never
    # referenced by a face, so they showed up as permanent loose verts and the
    # panel could never report mesh_ok. SOLIDIFY closes the sheet from the
    # perforated surface instead.
    ob = mesh_from(name, verts, faces, mat)
    solid = ob.modifiers.new("Skin", "SOLIDIFY")
    solid.thickness = u(0.01)
    apply_mods(ob)
    recalc(ob)
    return ob


def gear(name, teeth, module_mm, thickness, bore_r, mat=None, pressure_angle=20.0):
    """Spur gear with real involute-ish flanks. teeth*module = pitch diameter."""
    r_pitch = teeth * module_mm / 2.0
    r_out = r_pitch + module_mm
    r_root = r_pitch - 1.25 * module_mm
    r_bore = bore_r
    step = 2.0 * math.pi / teeth
    poly = []
    for t in range(teeth):
        a = t * step
        # root -> flank -> tip -> flank -> root, with the tip narrower than the
        # root (that taper is what reads as a gear rather than a cog)
        poly.append((r_root, a + step * 0.02))
        poly.append((r_out, a + step * 0.28))
        poly.append((r_out, a + step * 0.52))
        poly.append((r_root, a + step * 0.78))
    ring = [(math.cos(a) * r, math.sin(a) * r) for (r, a) in poly]
    body = extrude_profile(name + "_body", ring, thickness, mat=mat)
    if r_bore > 0:
        cutter = cylinder(name + "_bore", r_bore, thickness * 4, segments=48, mat=None)
        boolean(body, cutter, "DIFFERENCE")
    return body


def thread(name, radius, pitch, length, turns=None, thread_h=0.35, mat=None,
           segments_per_turn=24):
    """A real helical thread: triangular profile swept along a helix.

    Used for bolts, screws, bottle caps and threaded rods. Radius is the
    *outer* thread radius; the core is at radius - thread_h.
    """
    turns = turns if turns is not None else max(1.0, length / pitch)
    steps = int(turns * segments_per_turn)
    core = radius - thread_h
    prof = [(core, -0.5 * pitch * 0.75), (radius, 0.0), (core, 0.5 * pitch * 0.75)]
    # A thread cross-section is a CLOSED loop (core -> crest -> core -> back to
    # the start), not a polyline. Bridging only consecutive profile points left
    # the core line open, putting one boundary edge on every helix step.
    prof = list(prof) + [prof[0]]
    verts, faces = [], []
    for s in range(steps + 1):
        t = s / steps
        ang = 2.0 * math.pi * turns * t
        z = -length / 2.0 + length * t
        for (pr, pz) in prof:
            verts.append((math.cos(ang) * pr, math.sin(ang) * pr, z + pz))
    n = len(prof)
    for s in range(steps):
        for k in range(n - 1):
            a = s * n + k
            faces.append((a, a + 1, a + n + 1, a + n))
    faces.append(tuple(range(n - 1, -1, -1)))
    base = steps * n
    faces.append(tuple(range(base, base + n)))
    ob = mesh_from(name, verts, faces, mat)
    recalc(ob)
    weld(ob, 0.002)
    shade_smooth(ob, 50)
    return ob


# --------------------------------------------------------------------------
# 6. measurement / health
# --------------------------------------------------------------------------

def bbox(obj, world=True):
    """Bounding box of one object, returned in MILLIMETRES."""
    mw = obj.matrix_world if world else Matrix.Identity(4)
    pts = [mw @ vert.co for vert in obj.data.vertices]
    if not pts:
        return dict(x_min=0, x_max=0, y_min=0, y_max=0, z_min=0, z_max=0,
                    sx=0, sy=0, sz=0)
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return dict(x_min=min(xs) / MM, x_max=max(xs) / MM,
                y_min=min(ys) / MM, y_max=max(ys) / MM,
                z_min=min(zs) / MM, z_max=max(zs) / MM,
                sx=(max(xs) - min(xs)) / MM, sy=(max(ys) - min(ys)) / MM,
                sz=(max(zs) - min(zs)) / MM)


def scene_bbox(exclude=("Backdrop", "Ground", "Floor")):
    xs, ys, zs = [], [], []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in exclude:
            continue
        bb = bbox(ob)
        xs += [bb["x_min"], bb["x_max"]]
        ys += [bb["y_min"], bb["y_max"]]
        zs += [bb["z_min"], bb["z_max"]]
    if not xs:
        return dict(x_min=0, x_max=0, y_min=0, y_max=0, z_min=0, z_max=0,
                    sx=0, sy=0, sz=0)
    return dict(x_min=min(xs), x_max=max(xs), y_min=min(ys), y_max=max(ys),
                z_min=min(zs), z_max=max(zs),
                sx=max(xs) - min(xs), sy=max(ys) - min(ys), sz=max(zs) - min(zs))


def scene_radius(target=None):
    """Bounding-sphere radius (metres) about `target` (mm, default scene centre)."""
    if target is None:
        bb = scene_bbox()
        target = ((bb["x_min"] + bb["x_max"]) / 2.0,
                  (bb["y_min"] + bb["y_max"]) / 2.0,
                  (bb["z_min"] + bb["z_max"]) / 2.0)
    tv = v(*target)
    best = 0.0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        mw = ob.matrix_world
        for vert in ob.data.vertices:
            d = (mw @ vert.co - tv).length
            if d > best:
                best = d
    return best if best > 0 else 0.01


def health(obj=None):
    """Mesh health a render cannot show. Returns a dict; `ok` is the gate.

    `by_object` names the culprit for every failure: with a 20-part model a
    single aggregate number sends you hunting through the wrong part.
    """
    objs = [obj] if obj else [o for o in bpy.data.objects
                              if o.type == "MESH" and o.name not in ("Backdrop", "Ground")]
    total = dict(verts=0, faces=0, nonmanifold=0, loose_verts=0,
                 negative_volume=0, tiny_faces=0, by_object=[])
    for ob in objs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        verts = len(bm.verts)
        faces = len(bm.faces)
        nm = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        loose = sum(1 for v in bm.verts if not v.link_faces)
        tiny = sum(1 for f in bm.faces if f.calc_area() < (u(0.02)) ** 2)
        try:
            vol = bm.calc_volume(signed=True)
        except Exception:
            vol = 0.0
        total["verts"] += verts
        total["faces"] += faces
        total["nonmanifold"] += nm
        total["loose_verts"] += loose
        total["tiny_faces"] += tiny
        if vol < 0:
            total["negative_volume"] += 1
        problems = []
        if nm:
            problems.append("nonmanifold=%d" % nm)
        if loose:
            problems.append("loose=%d" % loose)
        if tiny:
            problems.append("tiny_faces=%d" % tiny)
        if vol < 0:
            problems.append("inverted_normals(volume=%.4g mm^3)" % (vol / MM ** 3))
        total["by_object"].append(dict(name=ob.name, verts=verts, faces=faces,
                                       problems=problems))
        bm.free()
    total["empty"] = 1 if (total["verts"] == 0 or total["faces"] == 0) else 0
    # An empty object satisfies every other condition trivially -- zero
    # non-manifold edges, zero loose verts -- so without this it reads as
    # PERFECT. A boolean that deleted the mesh entirely was scoring clean.
    total["ok"] = (total["nonmanifold"] == 0 and total["loose_verts"] == 0
                   and total["negative_volume"] == 0 and not total["empty"])
    return total


def material_coverage():
    """Meshes with no material render as grey clay -- almost always a bug."""
    missing = [ob.name for ob in bpy.data.objects
               if ob.type == "MESH"
               and ob.name not in ("Backdrop", "Ground")
               and not ob.data.materials]
    return missing


# --------------------------------------------------------------------------
# 7. staging: lights, camera, world
# --------------------------------------------------------------------------

def _area(name, loc_m, target_m, size_m, power_w, color=(1, 1, 1), size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE" if size_y else "SQUARE"
    ld.size = size_m
    if size_y:
        ld.size_y = size_y
    ld.energy = power_w
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = Vector(loc_m)
    ob.rotation_euler = (Vector(target_m) - Vector(loc_m)).normalized() \
        .to_track_quat("-Z", "Y").to_euler()
    return ob


def assign_faces_by(obj, mat, predicate, keep=()):
    """Give a subset of faces a second material.

    `predicate(centre_world_vec, normal) -> bool`. `keep` lists material names
    already in slot 0 that must be preserved when the object already has slots.

    Use instead of a second overlapping shell object: a duplicate interior mesh
    z-fights with the real wall and leaves both objects non-manifold.
    """
    if mat.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(mat)
    index = [m.name for m in obj.data.materials].index(mat.name)
    mw = obj.matrix_world
    hit = 0
    for poly in obj.data.polygons:
        c = mw @ poly.center
        n = (mw.to_3x3() @ poly.normal).normalized()
        if predicate(c, n):
            poly.material_index = index
            hit += 1
    return hit


def srgb_to_linear(c):
    """sRGB-encoded value -> scene-linear (Blender's own transfer curve)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _median_luma(path, alpha_only=True):
    """Median SCENE-LINEAR luminance of a rendered RGBA PNG, or None.

    `image.pixels` returns DISPLAY-REFERRED sRGB, not radiance. Verified: a
    surface emitting exactly 0.5 linear radiance reads back as 0.73464 -- the
    sRGB encoding of 0.5 -- and reading it back as "Non-Color" does not change
    it. Since sRGB values are always higher than linear, solving exposure
    against the raw number made every render underexposed. The conversion
    happens here, once, at the boundary.

    With `alpha_only`, pixels with alpha < 0.5 are ignored so the statistic
    describes the subject and not the backdrop. Returns None rather than a bogus
    number: `image.pixels` is empty until materialised, and an empty buffer
    yields NaN which would sail through a `<= 0` guard.
    """
    if not os.path.exists(path):
        return None
    img = bpy.data.images.load(path)
    try:
        px = list(img.pixels)          # forces the buffer to load
        if not px:
            return None
        vals = []
        for i in range(0, len(px), 4):
            if alpha_only and px[i + 3] < 0.5:
                continue
            vals.append((px[i] + px[i + 1] + px[i + 2]) / 3.0)
        if not vals:
            return None
        vals.sort()
        return srgb_to_linear(vals[len(vals) // 2])
    except Exception:
        return None
    finally:
        bpy.data.images.remove(img)


def _probe_exposure(scene, render_kw):
    """Measure the grey ball while deliberately UNDerexposed.

    Probing at the working exposure is only valid when the scene is not
    clipped: a ball that reads 1.0000 tells you nothing except that it clipped,
    and the solve then lands on a guess. Probing several stops down puts the
    measurement in the linear range where luminance actually scales, so the
    solved exposure is correct whether the rig is 4 stops hot or 4 stops dim.
    """
    for offset in (-9.0, -5.0, 0.0):
        scene.view_settings.exposure = render_kw["base"] + offset
        scene.render.filepath = render_kw["name"]
        scene.render.resolution_x = render_kw["res"]
        scene.render.resolution_y = max(8, int(render_kw["res"] * 0.75))
        scene.cycles.samples = render_kw["samples"]
        bpy.ops.render.render(write_still=True)
        value = _median_luma(render_kw["name"], alpha_only=True)
        if value is None or value != value:
            continue
        if 1e-5 <= value <= 0.85:
            # back out the probe's own offset to get the true scene value
            return value / (2.0 ** offset), offset
    return None, 0.0


def auto_exposure(target_point=None, target=0.18, probe_samples=6, probe_res=160,
                  limit=6.0, probe_name="_exposure_probe.png", ball_radius_m=None):
    """Solve exposure by rendering an 18 % grey calibration ball.

    Why a ball and not the subject: a subject-median target forces a black
    rubber tyre to render mid-grey, destroying the albedo the model is supposed
    to communicate. A fixed exposure is the opposite failure -- it works for one
    material and blows out or crushes every other. Exposing on a known 18 % grey
    card fixes the *lighting*, so a black object stays black, a white one stays
    white, and the whole catalog shares one consistent tonality.

    The ball is placed at the camera's aim point (anywhere else it falls outside
    the framed view and the probe comes back empty), rendered alone against a
    transparent film, and sampled by median, then removed.
    Returns the exposure applied (0.0 if the probe failed).
    """
    sc = bpy.context.scene
    rad_m = scene_radius() if ball_radius_m is None else ball_radius_m
    # NOTE: uv_sphere() takes millimetres; scene_radius()/camera distances are
    # metres. Mixing the two here silently yields a 30 um ball that covers zero
    # pixels, and the probe then reads as "unreadable" instead of "too small".
    ball_r_mm = (rad_m / MM) * 0.45
    if target_point is None:
        bb = scene_bbox()
        target_point = ((bb["x_min"] + bb["x_max"]) / 2.0,
                        (bb["y_min"] + bb["y_max"]) / 2.0,
                        (bb["z_min"] + bb["z_max"]) / 2.0)
    keep = (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples,
            sc.render.filepath, sc.view_settings.exposure, sc.render.film_transparent)
    hidden = []
    ball = None
    try:
        for ob in bpy.data.objects:
            if ob.type == "MESH" and not ob.hide_render:
                ob.hide_render = True
                hidden.append(ob)
        ball = uv_sphere("_calibration_ball", ball_r_mm, segments=32, rings=16,
                         centre=target_point,
                         mat=pbr("_CalibrationGrey", base=(0.18, 0.18, 0.18),
                                 rough=1.0))
        ball.hide_render = False

        sc.cycles.use_denoising = False
        sc.render.film_transparent = True
        measured, offset = _probe_exposure(sc, dict(
            name=probe_name, base=keep[4], res=probe_res, samples=probe_samples))
    except Exception as exc:
        measured = None
        print("[bkit] auto_exposure probe failed: %s" % exc)
    finally:
        if ball is not None:
            bpy.data.objects.remove(ball, do_unlink=True)
        for ob in hidden:
            ob.hide_render = False
        (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples,
         sc.render.filepath, sc.view_settings.exposure,
         sc.render.film_transparent) = keep
        sc.cycles.use_denoising = True

    if measured is None or measured != measured or measured <= 1e-7:
        print("[bkit] auto_exposure: probe unreadable, keeping exposure %s" % keep[4])
        return 0.0
    ev = max(-limit, min(limit, math.log2(target / measured)))
    sc.view_settings.exposure = keep[4] + ev
    print("[bkit] auto_exposure: ball %.5f (probe %+.0f EV) -> exposure %+.2f EV"
          % (measured, offset, sc.view_settings.exposure))
    return round(sc.view_settings.exposure, 3)


def studio(subject_radius_m, floor=True, exposure=None):
    """Build a scale-aware studio around a subject of the given radius (metres).

    Light power follows the inverse-square law (power ~ r^2) and the key light
    size scales with r, so a 2 mm watch gear and a 30 m crane are both correctly
    exposed from the same three-light recipe. Exposure is derived, never guessed.
    """
    r = max(1e-4, subject_radius_m)
    sc = bpy.context.scene
    centre = Vector((0.0, 0.0, r * 0.85))

    if floor:
        # The floor must be large enough that its far edge is never in frame.
        # With per-view framing the camera can sit close, and a finite plane
        # then shows up as a hard horizon line across the render.
        bpy.ops.mesh.primitive_plane_add(size=max(4.0, r * 400.0), location=(0, 0, 0))
        g = bpy.context.active_object
        g.name = "Backdrop"
        # mid-grey, not near-black: a 0.05 backdrop renders as a black void and
        # the subject floats, which reads as a modelling mistake rather than a
        # lighting choice. This also gives white objects something to separate from.
        assign(g, pbr("StudioFloor", base=(0.19, 0.195, 0.205), rough=0.45))

    # Powers in Watts scale with r^2 so irradiance at the subject is constant.
    # The key is deliberately dominant: with a strong fill the shadow side fills
    # in and every object reads as a flat white cutout. Constants are calibrated
    # so an 18% grey ball placed at the aim point reads ~0.18 at exposure 0 with
    # the Standard view transform, leaving auto_exposure() almost nothing to do.
    p = r * r
    _area("Key", (r * 1.9, -r * 2.0, r * 2.4), centre,
          r * 1.9, 0.80 * p, color=(1.0, 0.98, 0.95), size_y=r * 1.4)
    _area("Fill", (-r * 2.6, -r * 1.4, r * 1.1), centre,
          r * 2.4, 0.21 * p, color=(0.88, 0.93, 1.0), size_y=r * 1.8)
    _area("Rim", (-r * 1.0, r * 2.6, r * 2.0), centre,
          r * 1.7, 0.46 * p, color=(0.94, 0.96, 1.0), size_y=r * 1.2)
    # raking strip: reads engraved/raised detail as shape instead of glare
    _area("TopStrip", (0.0, r * 0.4, r * 3.2), centre, r * 3.0, 0.21 * p,
          size_y=r * 0.35)

    w = bpy.data.worlds.new("Studio")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mapn = nt.nodes.new("ShaderNodeMapping")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    mapn.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.012, 0.014, 0.018, 1)
    ramp.color_ramp.elements[1].position = 0.85
    # Metals are pure reflection: with metallic=1 there is NO diffuse term, so a
    # near-black world renders chrome and steel as black holes. The bright end of
    # this gradient is the bounce card a product photographer would put opposite
    # the key, and it is what makes metal read as metal.
    ramp.color_ramp.elements[1].color = (0.85, 0.88, 0.95, 1)
    nt.links.new(tex.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.55
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    if exposure is not None:
        sc.view_settings.exposure = exposure
    return sc


def camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    """Camera on a spherical orbit (degrees) around `target` (mm).

    Spherical beats hand-rolled Euler: it cannot gimbal at the poles and stays
    readable when you are iterating on angles.
    """
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = v(*target)
    loc = t + Vector((dist_m * math.cos(el) * math.cos(az),
                      dist_m * math.cos(el) * math.sin(az),
                      dist_m * math.sin(el)))
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    ob = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (t - loc).normalized().to_track_quat("-Z", "Y").to_euler()
    return ob


def projected_extent(cam, target):
    """Half-extent along the camera's right, up AND forward axes, in metres.

    The forward extent is the one that keeps the camera OUTSIDE the subject.
    Fitting the silhouette alone is not enough: look straight down the length of
    a 300 mm rail and its silhouette is only 55 mm wide, so the fit puts the
    camera 128 mm from the centre -- which is inside the rail. Every such shot
    renders flat grey planes with the camera embedded in the model.

    Returns `(half_r, half_u, depth)`. Collapsing the first two into one scalar
    (the older behaviour) loses which axis was wide, and the caller then fits
    that width against the wrong field of view -- see frame().
    """
    t = v(*target)
    quat = cam.matrix_world.to_quaternion()
    right = quat @ Vector((1.0, 0.0, 0.0))
    up = quat @ Vector((0.0, 1.0, 0.0))
    fwd = quat @ Vector((0.0, 0.0, -1.0))       # the direction the camera looks
    half_r = half_u = 0.0
    depth = 0.0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        mw = ob.matrix_world
        for vert in ob.data.vertices:
            d = (mw @ vert.co) - t
            hr = abs(d.dot(right))
            hu = abs(d.dot(up))
            if hr > half_r:
                half_r = hr
            if hu > half_u:
                half_u = hu
            hd = abs(d.dot(fwd))
            if hd > depth:
                depth = hd
    return half_r, half_u, depth


def projected_radius(cam, target, fallback_m):
    """Largest projected half-extent of the subject, in metres.

    Kept as a single number for callers that only need a "how big is this"
    answer (light sizing, clip planes). Camera fitting must use
    projected_extent() instead, because it needs the three axes apart.
    """
    half_r, half_u, _depth = projected_extent(cam, target)
    extent = max(half_r, half_u)
    return extent if extent > 1e-6 else fallback_m


def frame(cam, target, radius_m, margin=1.18, per_view=True, depth_margin=1.25):
    """Dolly the camera back along its own axis until the subject fits.

    Uses BOTH the horizontal and vertical FOV, so a tall narrow subject and a
    wide flat subject both fit without hand-tuned distances. Without this, any
    change of aspect ratio or lens silently clips the model.

    The two screen axes are fitted SEPARATELY against their own FOV, then the
    larger requirement wins. Fitting one combined extent against the narrower
    FOV -- which is what this used to do -- pushes any wide subject away until
    the narrow FOV swallows it: a 60 m airliner filled ~15% of frame in its
    front view, because its 60 m width was fitted into the VERTICAL field.

    And the camera must also stay OUTSIDE the subject. Fitting the silhouette
    alone is not enough when the camera looks down the long axis: a 55 x 300 x
    44 mm rail seen end-on has a 55 mm silhouette, so the fit lands the camera
    128 mm from the centre -- inside the rail, rendering flat grey planes. The
    distance is therefore also floored by the subject's extent along the view
    direction, which is what actually keeps the lens clear of the geometry.
    """
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / max(1, sc.render.resolution_y)
    sensor = cam.data.sensor_width / 1000.0
    f = cam.data.lens / 1000.0
    half_h = math.atan(sensor / (2.0 * f))
    half_v = math.atan((sensor / aspect) / (2.0 * f))
    depth = 0.0
    if per_view:
        bpy.context.view_layer.update()
        half_r, half_u, depth = projected_extent(cam, target)
        if half_r < 1e-6 and half_u < 1e-6:      # empty scene: fall back to sphere
            half_r = half_u = radius_m
            depth = radius_m
        need = max(half_r * margin / math.tan(half_h),
                   half_u * margin / math.tan(half_v))
    else:
        need = radius_m * margin / math.tan(min(half_h, half_v))
        depth = radius_m
    # Never stand inside the thing being photographed.
    need = max(need, depth * depth_margin)
    # ...and when the subject is much longer ALONG the view axis than across it,
    # backing off to clear the near face is still not enough. A 55 x 300 x 44 mm
    # rail seen end-on has its near face 37 mm from the lens, and a 55 mm face at
    # 37 mm fills the frame with one flat grey rectangle -- the camera is legally
    # outside the object and the image is still worthless. So for a slender
    # subject the distance is also driven by the DEPTH extent: far enough that
    # the length recedes into the frame instead of presenting a wall.
    across = max(half_r, half_u, 1e-9)
    if depth > 2.0 * across:
        need = max(need, depth / math.tan(min(half_h, half_v)) * 0.85)
    t = v(*target)
    cur = (cam.location - t).length
    # Blender's default near plane is 0.1 m. A small subject framed closer than
    # that sits entirely INSIDE the near plane and every shot renders empty --
    # a 19 mm ball joint at 89 mm vanished. Scale both planes to the shot.
    cam.data.clip_start = max(need * 0.01, 1e-4)
    cam.data.clip_end = max(need * 40.0, 10.0)
    if abs(cur - need) > 1e-6:
        cam.location = t + (cam.location - t).normalized() * need
    cam.rotation_euler = (t - cam.location).normalized() \
        .to_track_quat("-Z", "Y").to_euler()
    return cam


# Standard three-quarter product angles; enough to expose every modelling error
# (silhouette, symmetry, proportion, and top-surface detail).
SHOTS = [
    ("hero", -35.0, 22.0, 85.0),
    ("three_quarter", 40.0, 26.0, 85.0),
    ("side", 2.0, 4.0, 95.0),
    ("top", -90.0, 78.0, 85.0),
    ("rear", 145.0, 18.0, 85.0),
    ("front", -90.0, 3.0, 95.0),
]


def shots_for(target=None):
    """The six shot angles, oriented to the subject's own long axis.

    SHOTS is written for a subject whose long axis runs along Y: `side` sits at
    azimuth 2 (looking down X) and `front` at -90 (looking across Y). That is
    right for a mug and wrong for anything elongated in X -- every vehicle. The
    file called `side.png` shows the vehicle's nose, and `front.png` shows its
    flank, which silently inverts the one view the rubric uses to judge
    silhouette and proportion.

    The named views therefore follow the geometry: when the subject is longer in
    X than in Y, the side and front azimuths trade places. Which end of the
    object faces "front" is a modelling decision the bounding box cannot know,
    but the SIDE view -- the one that carries most of the score -- is now always
    correct.
    """
    bb = scene_bbox()
    if bb["sx"] > bb["sy"] * 1.15:
        # Swap the two AZIMUTHS, leaving the names alone. Swapping the names as
        # well looks equivalent and is not: it reassigns each shot to the other
        # camera and reproduces the original table exactly.
        out = []
        for name, az, el, lens in SHOTS:
            if name == "side":
                az = -90.0            # look across Y: that is the long face
            elif name == "front":
                az = 2.0              # look down X: that is the end of it
            out.append((name, az, el, lens))
        return out
    return list(SHOTS)


def render_shots(outdir, target, radius_m, shots=None, samples=None, res=(1100, 850),
                 exposure_target=0.22):
    """Render the standard shot list. Returns the list of written paths.

    Auto-exposure is solved once, from the first shot's camera, before any final
    render: probing with one shot's framing keeps every angle in a set at the
    same tonality, which is what makes scores comparable across the catalog.
    """
    import os as _os
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.image_settings.file_format = "PNG"
    _os.makedirs(outdir, exist_ok=True)
    written = []
    cam = None
    for i, (name, az, el, lens) in enumerate(shots or shots_for(target)):
        cam = camera(az, el, radius_m * 2.6, lens, target)
        frame(cam, target, radius_m)
        sc.camera = cam
        if i == 0 and exposure_target:
            auto_exposure(target_point=target, target=exposure_target,
                          ball_radius_m=radius_m)
        print("[bkit] render %s exposure=%.2f EV samples=%d res=%dx%d"
              % (name, sc.view_settings.exposure, sc.cycles.samples,
                 sc.render.resolution_x, sc.render.resolution_y), flush=True)
        path = _os.path.join(outdir, "%s.png" % name)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        written.append(path)
    return written


# --------------------------------------------------------------------------
# 8. reporting
# --------------------------------------------------------------------------

def sit_on_floor(gap_mm=0.0):
    """Raise the whole assembly so its lowest point rests exactly on z=0.

    Non-negotiable before rendering. The studio backdrop is an opaque plane at
    z=0, so any model authored hanging below the origin (a bolt built downward
    from its head, a table with legs at negative z) is silently buried: it still
    reports a correct bounding box and a clean mesh while the camera sees only
    whatever pokes above the floor.
    """
    zs = []
    objs = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        bb = bbox(ob)
        zs.append((bb["z_min"], ob))
        objs.append(ob)
    if not zs:
        return 0.0
    lowest = min(z for z, _ in zs)
    delta = u(gap_mm - lowest)
    for ob in objs:
        ob.location.z += delta
    # matrix_world is cached; without this the very next bbox()/scene_radius()
    # call reads pre-move coordinates and the camera aims at the old centre.
    bpy.context.view_layer.update()
    return round(-lowest + gap_mm, 3)


def measure(part=None, how="bbox_z"):
    """Named measurement of one part, in MILLIMETRES.

    This is what makes dimensional claims checkable. A model does not assert
    "the body is 84 mm across"; it declares how to measure it and the harness
    measures the real geometry:

        CHECKS = [
            dict(name="body_diameter", mm=84.0, tol=0.5,
                 how="diameter", part="MugBody"),
            dict(name="body_height", mm=98.0, tol=0.5,
                 how="bbox_z", part="MugBody"),
        ]

    `part` defaults to the whole assembly. `how` is one of bbox_x, bbox_y,
    bbox_z, bbox_max, bbox_min, diameter (larger of bbox_x/bbox_y), longest
    (largest of all three).
    """
    if part:
        ob = bpy.data.objects.get(part)
        if ob is None:
            raise KeyError("no object named %r (have: %s)"
                           % (part, [o.name for o in bpy.data.objects]))
        bb = bbox(ob)
    else:
        ob = None
        bb = scene_bbox()
    sx, sy, sz = bb["sx"], bb["sy"], bb["sz"]

    # Swept diameters. A bounding box cannot express a rotor: three propeller
    # blades at 120 degrees span 1.5R x 1.73R, never 2R, and `diameter` reports
    # the axial chord instead. These measure the true distance from an axis
    # through the part's own centre, which is what a rotor diameter means.
    if how in ("swept_z", "swept_xy", "swept_x", "swept_y"):
        objs = [bpy.data.objects.get(part)] if part else [
            o for o in bpy.data.objects
            if o.type == "MESH" and o.name not in ("Backdrop", "Ground", "Floor")]
        objs = [o for o in objs if o is not None]
        # The axis belongs to the ASSEMBLY, not to each part: three propeller
        # blades are three objects, and measuring each about its own centre
        # returns R/2 instead of the rotor's 2R. Take one centre for the whole
        # parent (or the whole scene) and sweep every part about it.
        if part:
            axis_bb = bbox(bpy.data.objects[part])
        else:
            axis_bb = scene_bbox()
        cx = ((axis_bb["x_min"] + axis_bb["x_max"]) / 2.0) * MM
        cy = ((axis_bb["y_min"] + axis_bb["y_max"]) / 2.0) * MM
        cz = ((axis_bb["z_min"] + axis_bb["z_max"]) / 2.0) * MM
        best = 0.0
        for o in objs:
            mw = o.matrix_world
            for vert in o.data.vertices:
                p = mw @ vert.co             # METRES
                dx, dy, dz = p.x - cx, p.y - cy, p.z - cz
                if how == "swept_z":
                    d2 = dx * dx + dy * dy
                elif how == "swept_x":
                    d2 = dy * dy + dz * dz
                elif how == "swept_y":
                    d2 = dx * dx + dz * dz
                else:
                    d2 = dx * dx + dy * dy + dz * dz
                if d2 > best:
                    best = d2
        return math.sqrt(best) / MM        # back to millimetres, like every mode

    return {
        # sizes
        "bbox_x": sx, "bbox_y": sy, "bbox_z": sz,
        "bbox_max": max(sx, sy, sz), "bbox_min": min(sx, sy, sz),
        "diameter": max(sx, sy), "longest": max(sx, sy, sz),
        # coordinates -- needed for "how high is this part's top above the
        # floor", which no size can express
        "x_min": bb["x_min"], "x_max": bb["x_max"],
        "y_min": bb["y_min"], "y_max": bb["y_max"],
        "z_min": bb["z_min"], "z_max": bb["z_max"],
        # top/bottom above z=0: the commonest real dimension in this catalog
        "top_z": bb["z_max"], "bottom_z": bb["z_min"],
    }[how]


def report(spec=None):
    """Collect the machine-checkable facts a scorer needs. Never raises."""
    bb = scene_bbox()
    h = health()
    rad = scene_radius()
    data = dict(
        bbox=bb,
        radius_mm=rad / MM,
        verts=h["verts"], faces=h["faces"],
        nonmanifold=h["nonmanifold"], loose_verts=h["loose_verts"],
        tiny_faces=h["tiny_faces"], negative_volume=h["negative_volume"],
        mesh_ok=h["ok"],
        by_object=h["by_object"],
        objects=len([o for o in bpy.data.objects
                     if o.type == "MESH" and o.name not in ("Backdrop", "Ground")]),
        materials=len(bpy.data.materials),
        unmaterialed=material_coverage(),
    )
    if spec:
        data["spec"] = spec
    data["bkit_sha"] = toolkit_sha()
    return data


def toolkit_sha():
    """Short hash of THIS bkit source file, stamped into every report.

    A render is only evidence about the model if you know which toolkit made
    it. Four rounds of vision scoring were spent judging images that predated
    the fixes being scored -- every image was stale and nothing said so, because
    a directory of PNGs carries no version. Stamping the hash turns "are these
    renders current?" from an archaeology exercise into one comparison, and
    scripts/check_freshness.py turns it into a red/green answer.

    Returns None rather than raising if the source is unreadable: a missing
    stamp must never be the reason a model fails to render.
    """
    import hashlib
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "bkit.py"), "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:12]
    except Exception:
        return None


def dump(data, path):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, default=str)
    return path
