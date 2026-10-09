#!/usr/bin/env python3
"""detached.py -- find sub-geometry floating free of the body it belongs to.

    blender -b --factory-startup --python detached.py -- <model.py> [...]
    blender -b --factory-startup --python detached.py -- --batch <list.txt>

A model can be watertight, correctly dimensioned, fully materialled and still
score a perfect objective gate while carrying a chip of geometry floating in
mid-air beside it. Every objective check is per-object, so a stray part that is
itself clean is invisible to all of them; it only shows up as something that
reads as dirt on the render.

The test is CONNECTED COMPONENTS, not per-object health. Two objects that
touch are one component; a part that overlaps nothing and touches nothing is its
own island. An island is flagged when it is:

  * not the whole model (a one-component model has nothing to be detached from)
  * small relative to the body it floats beside -- a big island is a modelling
    error, not a stray
  * separated by a gap, rather than merely adjacent

Reported per island: its vertex/face count, its bounding box, the gap to the
nearest other component, and the object it came from -- because "there is
something floating" is not actionable and "this face group, 18 mm from Barrel,
0.4% of the faces" is.
"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, os.path.join(SCRIPTS, "scripts"))

# Every length in this file is METRES. Blender's world is metres and so is
# `v.co`; the model files are authored in millimetres and convert at the bkit
# boundary, not here. The first draft of these constants read "0.30" and "0.02"
# as if they were millimetres while comparing them against metre distances,
# which made a 300 mm gap count as touching and welded anything within 20 mm --
# so the detector reported "clean" on an astrolabe with a padlock visibly
# hanging in mid-air. The names now carry their unit.
WELD_M = 0.00002        # 0.02 mm: tighter than float32 noise at model scale
TOUCH_FLOOR_M = 0.00015  # 0.15 mm: below this, float noise alone explains a gap
TOUCH_REL = 0.004        # ...or 0.4% of the body's diagonal, whichever is larger
SMALL_FRAC = 0.06        # an island under 6% of total verts is "stray", not "body"


def components():
    """Union-find over mesh vertices, welded across objects by position."""
    verts = []
    owner = []          # (object_name, vertex_index)
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        mw = ob.matrix_world
        for v in ob.data.vertices:
            verts.append(mw @ v.co)
            owner.append((ob.name, v.index))

    parent = list(range(len(verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # weld by quantised position, so parts that meet exactly still connect
    buckets = {}
    for i, p in enumerate(verts):
        key = (round(p.x / WELD_M), round(p.y / WELD_M), round(p.z / WELD_M))
        buckets.setdefault(key, []).append(i)
    for idxs in buckets.values():
        for j in idxs[1:]:
            union(idxs[0], j)

    # edges within each object connect their endpoints
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        offset = None
        for i, (nm, _vi) in enumerate(owner):
            if nm == ob.name:
                offset = i
                break
        for e in ob.data.edges:
            union(offset + e.vertices[0], offset + e.vertices[1])

    groups = {}
    for i in range(len(verts)):
        groups.setdefault(find(i), []).append(i)
    return verts, owner, list(groups.values())


def _box_gap(a, b):
    """Separation between two axis-aligned boxes; 0.0 when they overlap."""
    d2 = 0.0
    for k in range(3):
        d = max(0.0, max(a["lo"][k] - b["hi"][k], b["lo"][k] - a["hi"][k]))
        d2 += d * d
    return d2 ** 0.5


def _merge_by_proximity(infos, touch):
    """Group components whose boxes are within `touch` of one another.

    Vertex connectivity alone is the wrong test for an ASSEMBLY. A padlock hangs
    from a rod: the two share no vertices, so union-find calls them two objects,
    and a keyboard's keys share nothing with the panel they sit on. Neither is a
    defect -- they are how real objects are put together.

    What actually marks a defect is a group of geometry separated from EVERY
    other group, not merely unconnected to some of them. So components are first
    gathered into assemblies by proximity (transitively, because a chain of
    touching parts is one assembly), and only whole assemblies are judged.
    """
    n = len(infos)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(n):
        for j in range(i + 1, n):
            if _box_gap(infos[i], infos[j]) <= touch:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(infos[i])
    return list(groups.values())


def analyse_scene():
    """Analyse whatever is currently in the scene. Returns the result dict."""
    verts, owner, groups = components()
    if not groups:
        return dict(error="no geometry")

    faces = sum(len(o.data.polygons) for o in bpy.data.objects
                if o.type == "MESH" and o.name not in ("Backdrop", "Ground"))
    infos = []
    for g in groups:
        lo = Vector((1e9, 1e9, 1e9))
        hi = Vector((-1e9, -1e9, -1e9))
        names = set()
        for i in g:
            p = verts[i]
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
            names.add(owner[i][0])
        infos.append(dict(verts=len(g), lo=lo, hi=hi, objs=sorted(names)))

    body = max(infos, key=lambda c: c["verts"])
    diag = sum((body["hi"][k] - body["lo"][k]) ** 2 for k in range(3)) ** 0.5
    touch = max(TOUCH_FLOOR_M, TOUCH_REL * diag)
    total_v = len(verts)

    # components -> assemblies, then judge the assemblies
    assemblies = _merge_by_proximity(infos, touch)
    main = max(assemblies, key=lambda a: sum(c["verts"] for c in a))

    def box_of(group):
        return dict(lo=Vector(tuple(min(c["lo"][k] for c in group)
                                    for k in range(3))),
                    hi=Vector(tuple(max(c["hi"][k] for c in group)
                                    for k in range(3))))

    islands = []
    for idx, asm in enumerate(assemblies):
        if asm is main:
            continue
        frac = sum(c["verts"] for c in asm) / float(total_v)
        if frac > SMALL_FRAC:
            continue
        mine = box_of(asm)
        # separation from the nearest OTHER assembly -- including the main one,
        # which is usually the nearest and is the reason this reads as floating
        others = [box_of(g) for j, g in enumerate(assemblies) if j != idx]
        gap = min(_box_gap(mine, o) for o in others)
        if gap <= touch:
            continue
        objs = sorted({o for c in asm for o in c["objs"]})
        islands.append(dict(objects=objs,
                            verts=sum(c["verts"] for c in asm),
                            parts=len(asm),
                            frac=round(frac, 5), gap_mm=round(gap * 1000.0, 3),
                            touch_mm=round(touch * 1000.0, 3),
                            bbox_mm=[round(mine["lo"].x * 1000, 2),
                                     round(mine["lo"].y * 1000, 2),
                                     round(mine["lo"].z * 1000, 2),
                                     round(mine["hi"].x * 1000, 2),
                                     round(mine["hi"].y * 1000, 2),
                                     round(mine["hi"].z * 1000, 2)]))

    return dict(components=len(infos), assemblies=len(assemblies),
                verts=total_v, faces=faces,
                touch_mm=round(touch * 1000.0, 3),
                islands=islands, clean=not islands)


def analyse(model_path):
    """Build one model file and analyse the scene it produces."""
    import importlib.util
    s = importlib.util.spec_from_file_location("det_model", model_path)
    mod = importlib.util.module_from_spec(s)
    sys.modules["det_model"] = mod
    try:
        s.loader.exec_module(mod)
        mod.build()
    except Exception as exc:
        return dict(model=os.path.basename(model_path)[:-3], error=str(exc)[:200])
    out = analyse_scene()
    out["model"] = os.path.basename(model_path)[:-3]
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    models = []
    if argv and argv[0] == "--batch":
        with open(argv[1]) as fh:
            models = [l.strip() for l in fh if l.strip()]
    else:
        models = argv

    out = []
    for m in models:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        r = analyse(m)
        out.append(r)
        if r.get("error"):
            print("DETAIL-ERR %-26s %s" % (r["model"], r["error"]), flush=True)
        elif r["islands"]:
            for isl in r["islands"]:
                print("DETACHED   %-26s %-22s verts=%-5d gap=%.1fmm frac=%.3f%%"
                      % (r["model"], "+".join(isl["objects"])[:22], isl["verts"],
                         isl["gap_mm"], isl["frac"] * 100), flush=True)
        else:
            print("clean      %-26s parts=%d" % (r["model"], r["components"]),
                  flush=True)

    import json
    dest = os.environ.get("DETACHED_OUT", "/tmp/detached.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    bad = [r for r in out if r.get("islands")]
    print("\n%d models analysed, %d with detached islands, %d errored -> %s"
          % (len(out), len(bad), sum(1 for r in out if r.get("error")), dest))


main()
