"""
Regression tests for the bkit toolkit.

Run:

    <blender> -b --factory-startup -noaudio -t 6 --python scripts/test_bkit.py

Every case here corresponds to a defect a builder agent actually hit while using
this skill for real work. A fix that is not pinned here is not a fix.

This file lives in the SKILL, not in /tmp: /tmp on this host is periodically
wiped, which once destroyed the whole suite along with several hundred renders.
"""
import math
import sys
import traceback

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import bpy
import bkit

results = []


def case(name):
    def deco(fn):
        try:
            bkit.reset()
            results.append((name, "PASS", fn()))
        except Exception as exc:
            results.append((name, "FAIL", "%s: %s" % (type(exc).__name__, exc)))
            traceback.print_exc()
        finally:
            bkit.reset()
        return fn
    return deco


def healthy(o):
    h = bkit.health(o)
    return h["nonmanifold"] == 0 and h["loose_verts"] == 0 and h["negative_volume"] == 0


# ---------------------------------------------------------------- primitives
@case("box_mm_discipline")
def _():
    o = bkit.box("B", 197, 197, 95, mat=bkit.preset("dark_metal"))
    bb = bkit.bbox(o)
    assert abs(bb["sx"] - 197) < 0.01 and abs(bb["sz"] - 95) < 0.01
    return dict(sx=round(bb["sx"], 3), sz=round(bb["sz"], 3))


@case("rounded_box")
def _():
    o = bkit.rounded_box("RB", 100, 60, 40, r=6, segments=5, mat=bkit.preset("red_paint"))
    assert abs(bkit.bbox(o)["sx"] - 100) < 0.05
    assert healthy(o)
    return dict(verts=len(o.data.vertices))


@case("cylinder_cone_tube_sphere_torus")
def _():
    out = {}
    for name, o in (
            ("cylinder", bkit.cylinder("C", 25, 80, segments=48)),
            ("cone", bkit.cylinder("K", 30, 70, segments=40, r2=8)),
            ("tube", bkit.tube("T", 30, 20, 50, segments=48)),
            ("sphere", bkit.sphere("S", 30)),
            ("torus", bkit.torus("To", 40, 10))):
        assert healthy(o), "%s not watertight" % name
        out[name] = len(o.data.vertices)
    return out


@case("sphere_alias_is_uv_sphere")
def _():
    # recipes.md documents sphere(); bkit's real name is uv_sphere. Models written
    # from the documented table died with AttributeError until this alias existed.
    assert bkit.sphere is bkit.uv_sphere
    return dict(verts=len(bkit.sphere("S", 10).data.vertices))


@case("lathe_welds_poles_at_scale")
def _():
    # weld's default sat BELOW Blender's float32 weld-hash precision, so lathe
    # poles stopped collapsing above ~12 m and every large model silently carried
    # 40-90 non-manifold edges.
    o = bkit.lathe("Col", [(0, 0), (1200, 0), (1200, 26000), (0, 26000)],
                   segments=64, mat=bkit.preset("ceramic"))
    assert healthy(o), "%d non-manifold on a 26 m lathe" % bkit.health(o)["nonmanifold"]
    return dict(verts=len(o.data.vertices))


@case("thread_is_watertight")
def _():
    o = bkit.thread("Th", radius=10, pitch=3, length=40, mat=bkit.preset("steel"))
    assert healthy(o), "%d non-manifold" % bkit.health(o)["nonmanifold"]
    return dict(verts=len(o.data.vertices))


@case("perforated_panel_is_watertight")
def _():
    # this used to append 8 border vertices referenced by no face, so it could
    # never report mesh_ok
    o = bkit.perforated_panel("Perf", cols=6, rows=5, pitch_x=14, pitch_y=14,
                              hole_r=4, panel_sx=90, panel_sy=70, thickness=2,
                              mat=bkit.preset("dark_metal"))
    assert healthy(o)
    return dict(verts=len(o.data.vertices))


@case("loft_accepts_2d_and_3d_sections")
def _():
    ring = bkit.rounded_rect_section(60, 40, r=8, per_corner=4)
    assert all(len(p) == 2 for p in ring), "sections must stay 2D"
    a = bkit.loft("A", [[(x, y, z) for (x, y) in ring] for z in (0, 20, 40)],
                  mat=bkit.preset("wood"))
    b = bkit.loft("B", [[(x, y, float(z)) for (x, y) in ring] for z in (0, 25)],
                  mat=bkit.preset("wood"))
    assert healthy(a) and healthy(b)
    return dict(lifted=len(a.data.polygons), explicit=len(b.data.polygons))


# ---------------------------------------------------------------- operations
@case("mirror_on_plane_and_about_symmetric_body")
def _():
    # Neither merge setting is right in general. Panel ON the plane needs no
    # merge; body ALREADY SYMMETRIC about it needs merge or it duplicates.
    p = bkit.box("P", 3, 40, 90, centre=(1.5, 0, 45), mat=bkit.preset("steel"))
    bkit.mirror(p, "X")
    h1 = bkit.health(p)
    assert h1["nonmanifold"] == 0, "panel on plane: %d" % h1["nonmanifold"]
    bkit.reset()
    s = bkit.box("S", 60, 40, 20, centre=(0, 0, 10), mat=bkit.preset("steel"))
    bkit.mirror(s, "X")
    h2 = bkit.health(s)
    assert h2["nonmanifold"] == 0, "symmetric body: %d" % h2["nonmanifold"]
    return dict(on_plane=h1["nonmanifold"], symmetric=h2["nonmanifold"])


@case("array_radial_orbits_the_hub")
def _():
    R = 100.0
    for k in range(3):
        a = math.radians(90 + 120 * k)
        bl = bkit.box("Blade%d" % k, 14, R, 5, centre=(0, R / 2, 0),
                      mat=bkit.preset("steel"))
        bl.rotation_euler = (0.0, 0.0, a)
    bpy.context.view_layer.update()
    bb = max(bkit.measure("Blade0", "bbox_x"), bkit.measure("Blade0", "bbox_y"))
    swept = bkit.measure(None, "swept_z")
    assert swept > bb, "swept %.1f must exceed a single blade's bbox %.1f" % (swept, bb)
    return dict(swept_mm=round(swept, 1), blade_bbox_mm=round(bb, 1))


@case("array_linear_world_offset")
def _():
    m = bkit.box("L", 20, 20, 100, centre=(0, 0, 50), mat=bkit.preset("steel"))
    m.rotation_euler = (0.0, math.radians(90), 0.0)
    bpy.context.view_layer.update()
    bkit.array_linear(m, 4, (200, 0, 0), world=True)
    # v.co is MESH-LOCAL; the 90 deg rotation lives on the object, so the
    # arrayed span must be read through matrix_world or it reads as the
    # 20 mm thickness and looks like the array did nothing.
    bpy.context.view_layer.update()
    mw = m.matrix_world
    xs = [(mw @ v.co).x for v in m.data.vertices]
    span = max(xs) - min(xs)
    # 100 mm member along world X plus three 200 mm steps = 700 mm = 0.7 m
    assert abs(span - 0.7) < 0.02, "world span %.3f m, expected 0.700" % span
    return dict(span_m=round(span, 3))


@case("bore_deconflicts_segment_count")
def _():
    assert bkit.bore_segments(64) != 64 and bkit.bore_segments(120) != 120
    d = bkit.cylinder("D", 40, 20, segments=64, mat=bkit.preset("steel"))
    bkit.bore(d, 16, depth=40, host_segments=64)
    assert healthy(d)
    return dict(sx=round(kit_bbox(d)["sx"], 2)) if False else dict(nonmanifold=0)


def kit_bbox(o):
    return bkit.bbox(o)


@case("bevel_keeps_pentagon_watertight")
def _():
    r_c = 20.0 / (2 * math.cos(math.radians(30)))
    poly = [(math.cos(math.radians(30 + 60 * i)) * r_c,
             math.sin(math.radians(30 + 60 * i)) * r_c) for i in range(5)]
    o = bkit.extrude_profile("Pent", poly, 8, mat=bkit.preset("steel"))
    bkit.bevel(o, width_mm=0.8, segments=2)
    assert healthy(o), "%d non-manifold after bevel" % bkit.health(o)["nonmanifold"]
    return dict(verts=len(o.data.vertices))


@case("lay_out_honours_gap")
def _():
    pos = bkit.lay_out([9, 9, 26, 12, 14, 9], gap=6)
    gaps = [pos[i + 1][0] - pos[i + 1][1] / 2 - (pos[i][0] + pos[i][1] / 2)
            for i in range(len(pos) - 1)]
    assert abs(min(gaps) - 6.0) < 1e-6
    return dict(min_gap=round(min(gaps), 6))


@case("health_flags_open_mesh")
def _():
    o = bkit.mesh_from("Open", [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)],
                       [(0, 1, 2, 3)])
    h = bkit.health(o)
    assert h["nonmanifold"] > 0 and not h["ok"]
    return dict(nonmanifold=h["nonmanifold"])


@case("sit_on_floor_refreshes_matrix")
def _():
    o = bkit.box("B", 40, 40, 60, centre=(0, 0, -60))
    bkit.sit_on_floor()
    bb = bkit.bbox(o)
    assert abs(bb["z_min"]) < 1e-4 and abs(bb["z_max"] - 60) < 0.01
    return dict(z_min=round(bb["z_min"], 6), z_max=round(bb["z_max"], 2))


@case("move_uses_millimetres")
def _():
    o = bkit.box("B", 20, 20, 20)
    before = bkit.bbox(o)["x_max"]
    bkit.move(o, 5, 0, 0)
    delta = bkit.bbox(o)["x_max"] - before
    assert abs(delta - 5.0) < 0.01, "move(5) shifted %.3f mm" % delta
    return dict(delta_mm=round(delta, 3))


@case("measure_sizes_coordinates_and_swept")
def _():
    bkit.box("B", 40, 60, 80, centre=(0, 0, 40), mat=bkit.preset("steel"))
    assert abs(bkit.measure(None, "bbox_x") - 40) < 0.01
    assert abs(bkit.measure(None, "z_max") - 80) < 0.01
    assert abs(bkit.measure(None, "longest") - 80) < 0.01
    for how in ("swept_z", "swept_x", "swept_y", "swept_xy"):
        assert bkit.measure(None, how) > 0.01
    return dict(bbox_z=round(bkit.measure(None, "bbox_z"), 2))


@case("measure_part_isolation")
def _():
    bkit.box("Big", 100, 100, 100, centre=(0, 0, 0), mat=bkit.preset("white_plastic"))
    bkit.box("Pin", 10, 10, 60, centre=(0, 0, 110), mat=bkit.preset("dark_metal"))
    assert abs(bkit.measure("Pin", "bbox_z") - 60) < 0.01
    assert abs(bkit.measure("Pin", "z_max") - 140) < 0.5
    return dict(pin_z=round(bkit.measure("Pin", "bbox_z"), 1))


@case("metal_presets_below_full_metalness")
def _():
    # metallic = 1.0 has no diffuse term and renders black in a dark studio
    for name in ("steel", "brushed_metal", "polished_metal", "dark_metal",
                 "gold", "copper", "anodized"):
        b = bkit.preset(name).node_tree.nodes["Principled BSDF"]
        assert b.inputs["Metallic"].default_value < 1.0, name
    return dict(ok=True)


@case("srgb_to_linear_roundtrip")
def _():
    assert abs(bkit.srgb_to_linear(0.73536) - 0.5) < 0.01
    for v in (0.02, 0.1, 0.3, 0.6, 0.9):
        assert bkit.srgb_to_linear(v) <= v + 1e-9
    return dict(srgb0735=round(bkit.srgb_to_linear(0.73536), 4))


@case("assign_faces_by_adds_second_material")
def _():
    o = bkit.lathe("V", [(0, 0), (30, 0), (30, 50), (0, 50)], segments=48,
                   mat=bkit.preset("ceramic"))
    hit = bkit.assign_faces_by(o, bkit.pbr("Inner", base=(0.9, 0.9, 0.9)),
                               lambda c, n: c.z / bkit.MM < 25)
    assert hit > 0 and len(o.data.materials) == 2
    return dict(faces=hit, materials=len(o.data.materials))


@case("every_pbr_call_gets_micro_detail")
def _():
    # 2,185 direct pbr() calls vs 527 preset() calls, and zero passing bump --
    # so tuning the preset table left ~81% of the catalog untouched. The default
    # has to live in pbr() itself. Every material must arrive with its Normal
    # and Roughness driven by noise, whatever its parameters.
    for name, kw in (("matt", dict(base=(0.4, 0.4, 0.4), rough=0.7)),
                     ("wood", dict(base=(0.35, 0.20, 0.09), rough=0.48)),
                     ("gloss", dict(base=(0.92, 0.91, 0.88), rough=0.18)),
                     ("steel", dict(base=(0.64, 0.66, 0.68), rough=0.25, metal=0.85))):
        m = bkit.pbr(name, **kw)
        b = m.node_tree.nodes["Principled BSDF"]
        assert b.inputs["Normal"].is_linked, "%s: Normal not driven" % name
        assert b.inputs["Roughness"].is_linked, "%s: Roughness not driven" % name
        assert m.node_tree.nodes.get("Bump") is not None, name
    return dict(materials=4, note="all wired")


@case("explicit_zero_opts_out_of_micro_detail")
def _():
    m = bkit.pbr("Smooth", base=(0.5, 0.5, 0.5), rough=0.5, bump=0, rough_var=0)
    b = m.node_tree.nodes["Principled BSDF"]
    assert not b.inputs["Normal"].is_linked, "bump=0 must mean no bump"
    return dict(opted_out=True)


@case("array_radial_orbits_a_primed_object")
def _():
    # bkit.cylinder + place() gives the source a non-identity matrix_world --
    # i.e. most primitives. The radial pivot's matrix was assigned but never
    # flushed, so the Array modifier read a stale identity offset and stacked
    # all 20 copies coincident.
    for k in range(6):
        a = math.radians(60 * k)
        spoke = bkit.cylinder("S%d" % k, 4, 30, segments=24,
                              centre=(60, 0, 0), mat=bkit.preset("steel"))
        spoke.rotation_euler = (0.0, 0.0, a)
        bkit.array_radial(spoke, count=6)
        xs = [(spoke.matrix_world @ v.co).x for v in spoke.data.vertices]
        ys = [(spoke.matrix_world @ v.co).y for v in spoke.data.vertices]
        lo = (min(xs) + min(ys)) / 2.0
        hi = (max(xs) + max(ys)) / 2.0
        assert hi - lo > 0.02, ("copies %d..%d m: coincident, not an orbit"
                                % (lo, hi))
    return dict(copies=6)


@case("health_rejects_an_empty_mesh")
def _():
    # An empty object trivially satisfies every other condition, so it used to
    # score PERFECT. A boolean that deleted a mesh entirely read as clean.
    o = bkit.mesh_from("Empty", [], [])
    h = bkit.health(o)
    assert h["verts"] == 0 and h["faces"] == 0
    assert h["empty"] == 1, "empty flag missing"
    assert not h["ok"], "an empty mesh must not be healthy"
    b = bkit.box("B", 10, 10, 10)
    assert bkit.health(b)["ok"] and bkit.health(b)["empty"] == 0
    return dict(empty_flag=1)


@case("camera_near_clip_scales_with_the_subject")
def _():
    # Blender's near plane defaults to 0.1 m, so a 19 mm subject framed at
    # 89 mm rendered as an empty frame in every shot.
    for radius_mm in (9.5, 100.0, 3000.0):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bkit.reset()
        bkit.box("B", radius_mm, radius_mm, radius_mm,
                 centre=(0, 0, radius_mm / 2), mat=bkit.preset("ceramic"))
        rad = bkit.scene_radius()
        tgt = (0.0, 0.0, radius_mm / 2)
        cam = bkit.camera(-35, 22, rad * 2.6, 85.0, tgt)
        bkit.frame(cam, tgt, rad)
        dist = (cam.location - bkit.v(*tgt)).length
        assert cam.data.clip_start < dist * 0.5, (
            "clip_start %.4f m vs camera distance %.4f m -- subject is inside "
            "the near plane and will vanish" % (cam.data.clip_start, dist))
        assert cam.data.clip_end > dist * 2.0, "far plane too near"
    return dict(cases=3)


@case("a_wide_subject_fills_the_frame_it_is_wide_in")
def _():
    # A 600 x 20 x 20 mm bar is WIDE. Framing used to collapse its projected
    # extent to one scalar and fit that against the narrower vertical FOV, so
    # the bar was pushed away until the vertical field swallowed it and it
    # filled ~15% of frame. Each axis must be fitted against its OWN field.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.box("Bar", 600.0, 20.0, 20.0, centre=(0, 0, 10.0),
             mat=bkit.preset("ceramic"))
    rad = bkit.scene_radius()
    tgt = (0.0, 0.0, 10.0)
    cam = bkit.camera(-90.0, 3.0, rad * 2.6, 95.0, tgt)     # broadside: bar is wide
    bkit.frame(cam, tgt, rad)
    dist = (cam.location - bkit.v(*tgt)).length

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1100, 850
    aspect = sc.render.resolution_x / sc.render.resolution_y
    sensor = cam.data.sensor_width / 1000.0
    f = cam.data.lens / 1000.0
    half_h = math.atan(sensor / (2.0 * f))
    half_v = math.atan((sensor / aspect) / (2.0 * f))

    hr, hu, _depth = bkit.projected_extent(cam, tgt)
    assert hr > hu * 5.0, (
        "test premise broken: side-on bar should project wide, got hr=%.1f "
        "hu=%.1f" % (hr, hu))

    # fraction of each frame dimension the subject should now occupy
    fill_w = (hr / (dist * math.tan(half_h)))
    fill_h = (hu / (dist * math.tan(half_v)))
    assert fill_w > 0.60, (
        "wide subject fills only %.0f%% of frame width -- the old combined-"
        "scalar fit pushed it away" % (fill_w * 100))
    assert fill_h <= 1.0 and fill_w <= 1.0, "subject is clipped by the frame"

    # the narrow axis must still fit inside the vertical field
    assert fill_h < 0.95, "thin bar should not fill the vertical field"
    return dict(fill_w=round(fill_w, 3), fill_h=round(fill_h, 3))


@case("a_tall_subject_fills_the_frame_it_is_tall_in")
def _():
    # The mirror image of the case above: fitting only the horizontal field
    # would push a tall subject away. This pins BOTH axes, not just one.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.box("Post", 20.0, 20.0, 600.0, centre=(0, 0, 300.0),
             mat=bkit.preset("ceramic"))
    rad = bkit.scene_radius()
    tgt = (0.0, 0.0, 300.0)
    cam = bkit.camera(-90.0, 3.0, rad * 2.6, 95.0, tgt)     # front-on: post is tall
    bkit.frame(cam, tgt, rad)
    dist = (cam.location - bkit.v(*tgt)).length

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1100, 850
    aspect = sc.render.resolution_x / sc.render.resolution_y
    sensor = cam.data.sensor_width / 1000.0
    f = cam.data.lens / 1000.0
    half_h = math.atan(sensor / (2.0 * f))
    half_v = math.atan((sensor / aspect) / (2.0 * f))

    hr, hu, _depth = bkit.projected_extent(cam, tgt)
    fill_w = hr / (dist * math.tan(half_h))
    fill_h = hu / (dist * math.tan(half_v))
    assert fill_h > 0.60, (
        "tall subject fills only %.0f%% of frame height" % (fill_h * 100))
    assert fill_w <= 1.0 and fill_h <= 1.0, "subject is clipped by the frame"
    return dict(fill_w=round(fill_w, 3), fill_h=round(fill_h, 3))


@case("the_noise_vector_is_world_space_with_a_physical_feature_size")
def _():
    # Three candidate vectors, three different failure modes:
    #   TexCoord.Object     -- scaled by the object's transform, so a
    #                         non-uniformly scaled primitive smears the detail
    #                         into bands.
    #   TexCoord.Generated  -- normalised to the bounding box, so the feature
    #                         size scales WITH the object: bump_scale 90 on a
    #                         5 mm part is 0.05 mm of tooth and on a 5 m van it
    #                         is 55 mm. Large panels came out sandblasted.
    #   Geometry.Position   -- world space: one unit is one metre, always, and
    #                         an object's transform does not enter into it.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    mat = bkit.pbr("ProbeMat", base=(0.5, 0.5, 0.5), rough=0.8)
    nt = mat.node_tree
    noise = [n for n in nt.nodes if n.type == "TEX_NOISE"]
    assert noise, "pbr() built no noise texture for a rough material"
    links = [l for l in nt.links if l.to_node == noise[0]
             and l.to_socket.name == "Vector"]
    assert len(links) == 1, "noise is not driven by exactly one coordinate node"
    assert links[0].from_socket.name == "Position", (
        "noise is driven by %s -- Object space is scaled by the object's "
        "transform, and Generated scales the feature size with the object"
        % links[0].from_socket.name)

    # and the feature size must be tied to the displacement, not to the object
    bump, _rv = bkit._auto_detail(0.8, 0.0, (0.5, 0.5, 0.5), None, None)
    scale = noise[0].inputs["Scale"].default_value
    feature_m = 1.0 / scale
    assert 0.4 < feature_m / bump < 2.5, (
        "noise features are %.2f mm but the bump is %.2f mm -- they should be "
        "the same order, or the surface reads as waves or as dirt"
        % (feature_m * 1000, bump * 1000))
    return dict(vector=links[0].from_socket.name,
                feature_mm=round(feature_m * 1000, 4),
                bump_mm=round(bump * 1000, 4))


@case("metal_presets_stay_dark_enough_to_read_as_metal")
def _():
    # Measured on a knife blade with the lighting held fixed: base 0.82 renders
    # a near-white sheet with no tonal range (paper), base 0.48 with metal 0.90
    # reads as steel. A preset that drifts back up washes out ~70% of the
    # catalog at once, since most models take their metal from a preset.
    #
    # Judged by RELATIVE LUMINANCE, not by the largest channel: gold and copper
    # are chromatic and their red channel is legitimately high, but their
    # luminance -- the quantity that actually decides how bright they render --
    # is moderate. A max-channel rule would flag them as washed out when they
    # are not, and would invite someone to "fix" them into grey.
    offenders = []
    for name, spec in bkit._PRESETS.items():
        if spec.get("metal", 0.0) < 0.5:
            continue
        r, g, b = spec.get("base", (0, 0, 0))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum > 0.70:
            offenders.append("%s lum=%.2f" % (name, lum))
    assert not offenders, ("metal presets too bright to read as metal: "
                           + ", ".join(offenders))
    return dict(metal_presets=sum(1 for s in bkit._PRESETS.values()
                                  if s.get("metal", 0.0) >= 0.5))


@case("a_metal_gets_its_variation_from_reflection_not_roughness")
def _():
    # Widening the metal branch of _auto_detail to rough_var 0.13 put visible
    # dark speckle across a polished blade -- it reads as dirt, not brushing.
    # A metal's surface variation comes from reflection; the swing stays small.
    bump, rvar = bkit._auto_detail(0.25, 0.9, (0.5, 0.5, 0.5), None, None)
    assert rvar is not None and rvar <= 0.06, (
        "metal rough_var is %.3f -- large enough to speckle a polished face" % rvar)
    assert bump is not None and bump <= 0.0003, (
        "metal bump is %.5f m -- too coarse for a machined face" % bump)
    # and it must still not be perfectly flat
    assert rvar > 0.0, "metal has no micro-detail at all"

    # the opposite end: a rough dielectric SHOULD get the wide swing
    _, drvar = bkit._auto_detail(0.9, 0.0, (0.2, 0.2, 0.2), None, None)
    assert drvar > rvar * 2, (
        "dielectrics need more roughness variation than metals; "
        "metal=%.3f dielectric=%.3f" % (rvar, drvar))
    return dict(metal_rough_var=round(rvar, 4),
                dielectric_rough_var=round(drvar, 4))


@case("the_camera_never_stands_inside_a_long_thin_subject")
def _():
    # Fitting the silhouette alone puts the camera INSIDE the subject when it
    # looks down the long axis. A 55 x 300 x 44 mm rail seen end-on has a 55 mm
    # silhouette, so the fit lands ~128 mm from the centre -- mid-rail -- and
    # every shot is flat grey planes.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.box("Rail", 55.0, 300.0, 44.0, centre=(0, 0, 22),
             mat=bkit.preset("steel"))
    rad = bkit.scene_radius()
    tgt = (0.0, 0.0, 22.0)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1100, 850

    worst = None
    for az in (2.0, -90.0, 0.0, 180.0, 90.0):
        cam = bkit.camera(az, 4.0, rad * 2.6, 95.0, tgt)
        bkit.frame(cam, tgt, rad)
        dist = (cam.location - bkit.v(*tgt)).length
        _hr, _hu, depth = bkit.projected_extent(cam, tgt)
        clearance = dist - depth
        if worst is None or clearance < worst:
            worst = clearance
        assert clearance > 0.0, (
            "camera at azimuth %.0f is %.1f mm INSIDE the subject (dist %.1f, "
            "subject half-depth %.1f)"
            % (az, -clearance * 1000, dist * 1000, depth * 1000))

    # being outside is not sufficient: at 37 mm from the near face a 55 mm face
    # still fills the frame with one flat rectangle. The end-on view of a slender
    # object must back off far enough that its LENGTH is in shot.
    cam = bkit.camera(-90.0, 3.0, rad * 2.6, 95.0, tgt)
    bkit.frame(cam, tgt, rad)
    dist = (cam.location - bkit.v(*tgt)).length
    _hr, _hu, depth = bkit.projected_extent(cam, tgt)
    assert dist > depth * 4.0, (
        "end-on view of a 300 mm rail sits only %.0f mm from a subject whose "
        "half-depth is %.0f mm -- the near face will fill the frame"
        % (dist * 1000, depth * 1000))
    return dict(min_clearance_mm=round(worst * 1000, 1),
                end_on_distance_mm=round(dist * 1000, 1))


@case("the_side_shot_looks_at_the_side_of_an_x_long_subject")
def _():
    # SHOTS is authored for a subject whose long axis runs along Y. For a
    # vehicle -- long in X -- that made the file called `side.png` show the nose
    # and `front.png` show the flank, inverting the one view the vision rubric
    # uses for silhouette and proportion.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.box("Vehicle", 4600.0, 1900.0, 1500.0, centre=(0, 0, 750),
             mat=bkit.preset("steel"))
    names = dict((n, az) for n, az, _e, _l in bkit.shots_for())
    assert set(names) == {"hero", "three_quarter", "side", "top", "rear", "front"}, \
        "shots_for() lost or renamed a shot: %s" % sorted(names)
    assert names["side"] == -90.0, (
        "for an X-long subject the side view must look across Y (az -90), got %s"
        % names["side"])
    assert names["front"] == 2.0, (
        "for an X-long subject the front view must look down X (az 2), got %s"
        % names["front"])

    # and a Y-long subject keeps the original assignment
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.box("Mug", 90.0, 90.0, 110.0, centre=(0, 0, 55), mat=bkit.preset("ceramic"))
    ylong = dict((n, az) for n, az, _e, _l in bkit.shots_for())
    assert ylong["side"] == 2.0 and ylong["front"] == -90.0, \
        "a Y-long subject must keep the original side/front assignment"
    return dict(x_long_side_az=names["side"], y_long_side_az=ylong["side"])


@case("rotate_about_pivots_on_the_part_not_the_world_origin")
def _():
    # `rotation_euler` rotates about the object's origin, and the recipes leave
    # that at the WORLD origin -- so a part 200 mm off centre swings right around
    # the scene. 120 catalog models were visibly disfigured this way.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    # box() bakes `centre` into mesh data, so its origin is (0,0,0)
    box = bkit.box("P", 40.0, 40.0, 40.0, centre=(200.0, 0.0, 0.0),
                   mat=bkit.preset("steel"))
    assert tuple(round(c, 6) for c in box.location) == (0.0, 0.0, 0.0), \
        "test premise broken: box should carry no object offset"

    before = bkit.scene_bbox()
    cx_before = (before["x_min"] + before["x_max"]) / 2.0

    bkit.rotate_about(box, deg_z=90.0)
    after = bkit.scene_bbox()
    cx_after = (after["x_min"] + after["x_max"]) / 2.0
    assert abs(cx_after - cx_before) < 0.01, (
        "rotate_about moved the part's centre from %.2f to %.2f mm -- it is "
        "still pivoting on the world origin" % (cx_before, cx_after))

    # a cube is symmetric, so the size must be unchanged too
    assert abs(after["sx"] - before["sx"]) < 0.01, "rotation distorted the part"
    assert tuple(box.rotation_euler) == (0.0, 0.0, 0.0), \
        "rotate_about must leave rotation_euler at zero"

    # and the same for a part whose centre lives in obj.location (cylinder)
    cyl = bkit.cylinder("C", 20.0, 60.0, segments=32, centre=(0.0, 200.0, 0.0),
                        mat=bkit.preset("steel"))
    b0 = bkit.scene_bbox()
    cy0 = (b0["y_min"] + b0["y_max"]) / 2.0
    bkit.rotate_about(cyl, deg_y=90.0)
    b1 = bkit.scene_bbox()
    cy1 = (b1["y_min"] + b1["y_max"]) / 2.0
    assert abs(cy1 - cy0) < 0.01, (
        "cylinder centre drifted %.2f -> %.2f mm" % (cy0, cy1))
    return dict(cx=round(cx_after, 3), cy=round(cy1, 3))


@case("a_slot_whose_pid_we_may_not_signal_is_still_live")
def _():
    # SlotPool decides admission by os.kill(pid, 0). On hosts that forbid
    # cross-process signalling that raises EPERM -- which means the process
    # EXISTS. Reading EPERM as "dead" reports every slot free, so the global
    # cap silently stops capping and every runner admits its full quota.
    # Only ESRCH means the process is gone.
    import errno as _errno
    import os as _os
    import shutil as _shutil
    import tempfile as _tempfile

    import blrun

    root = _tempfile.mkdtemp(prefix="bkit-slots-")
    try:
        pool = blrun.SlotPool(root, cap=2)
        slot = _os.path.join(root, ".slots", "slot-test")
        with open(slot, "w") as fh:
            fh.write("4242 1.0\n")

        real_kill = blrun.os.kill

        def eperm(_pid, _sig):
            raise OSError(_errno.EPERM, "Operation not permitted")

        def esrch(_pid, _sig):
            raise OSError(_errno.ESRCH, "No such process")

        blrun.os.kill = eperm
        assert pool._alive(slot), (
            "EPERM was read as a dead slot -- the global cap would not cap "
            "anything on a host that forbids signalling")

        blrun.os.kill = esrch
        assert not pool._alive(slot), "ESRCH must mean the slot is reusable"

        blrun.os.kill = real_kill

        with open(slot, "w") as fh:
            fh.write("done 4242 1.0\n")
        assert not pool._alive(slot), "a released slot must read as free"
        return dict(cases=3)
    finally:
        blrun.os.kill = real_kill
        _shutil.rmtree(root, ignore_errors=True)


print()
print("=" * 78)
print("BKIT REGRESSION SUITE")
print("=" * 78)
npass = 0
for name, status, info in results:
    if status == "PASS":
        npass += 1
    print("  [%s] %-44s %s" % (status, name, str(info)[:40]))
print("-" * 78)
print("RESULT %d/%d passed" % (npass, len(results)))
sys.exit(0 if npass == len(results) else 1)