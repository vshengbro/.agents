#!/usr/bin/env python3
"""
score.py -- the objective half of the quality gate.

    python3 scripts/score.py /tmp/run/coffee_mug [more dirs ...] [--json out]

Scoring is split on purpose. Everything that can be measured from the model
itself is computed here, deterministically, so two runs of the same spec always
score the same and a regression cannot hide. Everything that needs judgement --
does this look like a coffee mug, are the proportions believable -- is left to a
vision scorer, and this script emits the skeleton that scorer fills in.

OBJECTIVE (55 points, computed here)
    mesh integrity    20  watertight, no loose verts, no inverted normals,
                         no degenerate faces, every part carries a material
    dimensional       25  measured size vs the item's real-world SPEC, and the
                         measured size vs the declared size class
    scene hygiene     10  named parts, no stray geometry, sane part count

SUBJECTIVE (45 points, filled in by a vision scorer)
    form plausibility 15  recognisably the named object
    proportion        15  silhouette and internal ratios read correctly
    surface           10  materials and shading are believable
    presentation       5  exposure, framing, nothing clipped

Exit status is 0 only when the objective half is perfect AND a vision score of
full marks has been supplied, so the loop cannot pass on numbers alone.
"""
import argparse
import json
import os
import sys

MM_BANDS = {"micro": (0.2, 5), "tiny": (5, 30), "small": (30, 150),
            "medium": (150, 600), "large": (600, 3000), "huge": (3000, 40000)}


def load_report(outdir):
    path = os.path.join(outdir, "report.json")
    if not os.path.exists(path):
        return None, path
    try:
        with open(path) as fh:
            return json.load(fh), path
    except ValueError:
        return None, path


def _pick(value, bbox, key=""):
    """Interpret a SPEC entry as a millimetre measurement."""
    sx, sy, sz = bbox["sx"], bbox["sy"], bbox["sz"]
    longest = max(sx, sy, sz)
    if "diameter" in key or "_dia" in key:
        return max(sx, sy), key
    if "height" in key:
        return sz, key
    if "length" in key or "long" in key:
        return longest, key
    if "width" in key:
        return min(sx, sy), key
    return None, key


def score_objective(rep):
    """Return (points_earned, points_possible, detail_list)."""
    detail = []
    pts = 0.0
    bbox = rep.get("bbox") or {}
    spec = rep.get("spec") or {}

    # ---- 1. mesh integrity (20) ----
    mesh_pts = 0.0
    if rep.get("status") == "ok":
        mesh_pts += 4
        detail.append(("build_status", 4, 4, rep.get("status")))
    else:
        detail.append(("build_status", 0, 4, rep.get("status", "error")))

    nm = rep.get("nonmanifold", 0)
    nm_pts = 6.0 if nm == 0 else max(0.0, 6.0 - min(6.0, nm / 50.0))
    mesh_pts += nm_pts
    detail.append(("watertight_nonmanifold", nm_pts, 6, "%d edges" % nm))

    loose = rep.get("loose_verts", 0)
    loose_pts = 3.0 if loose == 0 else 0.0
    mesh_pts += loose_pts
    detail.append(("no_loose_verts", loose_pts, 3, str(loose)))

    inv = rep.get("negative_volume", 0)
    inv_pts = 3.0 if inv == 0 else 0.0
    mesh_pts += inv_pts
    detail.append(("no_inverted_normals", inv_pts, 3, "%d objects" % inv))

    unm = rep.get("unmaterialed") or []
    mat_pts = 4.0 if not unm else max(0.0, 4.0 - len(unm))
    mesh_pts += mat_pts
    detail.append(("all_parts_materialised", mat_pts, 4,
                   "none missing" if not unm else str(unm[:3])))
    pts += mesh_pts

    # ---- 2. dimensional fidelity (25) ----
    # Only ENVELOPE keys can be checked against a whole-model bounding box.
    # Sub-part keys (wall thickness, handle tube radius, bore diameter) describe
    # features the bbox cannot see, so scoring them against the bbox punishes
    # correct models and rewards ones that happen to match size.
    dim_pts = 0.0
    checked = []
    declared = rep.get("checks") or []
    if declared:
        # The model declared HOW each dimension is measured; measure accordingly.
        for c in declared:
            checked.append((c["name"], c["want"], c.get("got"),
                            c.get("error"), bool(c.get("ok"))))
        dim_pts = 20.0 * sum(1 for c in checked if c[4]) / len(checked)
        detail.append(("spec_dimensions", dim_pts, 20,
                       "%d/%d declared checks within tolerance: %s"
                       % (sum(1 for c in checked if c[4]), len(checked),
                          ", ".join("%s want %s got %s%s"
                                    % (c[0], c[1], c[2], "" if c[4] else "!")
                                    for c in checked[:5]))))
    else:
        # No declared checks: fall back to comparing envelope keys, but never
        # award full credit, because a bbox cannot prove a sub-part dimension.
        for key, val in sorted(spec.items()):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                continue
            if key.startswith("_"):
                continue
            if not any(t in key for t in ("diameter", "height", "length", "width", "_dia")):
                continue
            got, k = _pick(val, bbox, key)
            if got is None:
                continue
            tol = max(0.5, 0.02 * max(val, 1.0))
            err = abs(got - val)
            checked.append((k, val, round(got, 2), round(err, 3), err <= tol))
        if len(checked) >= 2:
            dim_pts = 10.0 * sum(1 for c in checked if c[4]) / len(checked)
        else:
            dim_pts = 4.0
        detail.append(("spec_dimensions", dim_pts, 20,
                       "no CHECKS declared; envelope-key estimate only "
                       "(%d key(s), partial credit) -- declare CHECKS" % len(checked)))

    longest = max(bbox.get("sx", 0), bbox.get("sy", 0), bbox.get("sz", 0))
    cls = spec.get("_size_class")
    band = MM_BANDS.get(cls)
    if band:
        lo, hi = band
        if lo * 0.5 <= longest <= hi * 2.0:
            dim_pts += 5.0
            detail.append(("size_class", 5.0, 5,
                           "%s: longest %.1f mm in [%g, %g]" % (cls, longest, lo, hi)))
        else:
            detail.append(("size_class", 0.0, 5,
                           "%s: longest %.1f mm outside [%g, %g]" % (cls, longest, lo, hi)))
    else:
        dim_pts += 2.5
        detail.append(("size_class", 2.5, 5, "no size class declared"))
    dim_pts = min(25.0, dim_pts)
    pts += dim_pts

    # ---- 3. scene hygiene (10) ----
    hy_pts = 0.0
    objs = rep.get("objects", 0)
    if objs >= 1:
        hy_pts += 3.0
        detail.append(("has_geometry", 3.0, 3, "%d objects" % objs))
    if rep.get("faces", 0) > 0:
        hy_pts += 2.0
        detail.append(("has_faces", 2.0, 2, str(rep.get("faces"))))
    named = all(o.get("name") for o in rep.get("by_object") or [])
    if named and rep.get("by_object"):
        hy_pts += 3.0
        detail.append(("parts_named", 3.0, 3, "all %d" % len(rep["by_object"])))
    else:
        detail.append(("parts_named", 0.0, 3, "unnamed part present"))
    seated = rep.get("seated_offset_mm")
    if seated is not None:
        hy_pts += 2.0
        detail.append(("seated_on_floor", 2.0, 2, "%+.1f mm" % seated))
    else:
        detail.append(("seated_on_floor", 0.0, 2, "not reported"))
    pts += min(10.0, hy_pts)

    return pts, 55.0, detail


def score_one(outdir, vision=None):
    rep, path = load_report(outdir)
    if rep is None:
        # No report means the render has not produced one: the job failed, is
        # still running, or was never started. That is NOT a model scoring zero
        # -- it is the absence of a measurement. Reporting it as 0.0/55 puts a
        # bookkeeping gap into the same column as a real gate failure and makes
        # the pass rate mean two different things at once.
        return dict(name=os.path.basename(outdir.rstrip("/")),
                    error="no report.json -- never scored", status="no_report",
                    objective=None, objective_possible=55.0, total=None,
                    passed=False)
    obj_pts, obj_pos, detail = score_objective(rep)
    result = dict(name=os.path.basename(outdir.rstrip("/")),
                  status="scored",
                  objective=round(obj_pts, 2), objective_possible=obj_pos,
                  checks=[dict(name=n, got=g, want=w, note=note)
                          for (n, g, w, note) in detail])
    if vision:
        result["vision"] = vision
        result["vision_total"] = vision.get("total")
        result["total"] = round(obj_pts + float(vision.get("total", 0.0)), 2)
    else:
        result["vision"] = None
        result["total"] = round(obj_pts, 2)
    result["passed"] = (obj_pts >= obj_pos - 1e-6
                        and bool(vision) and float(vision.get("total", 0)) >= 45.0)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdirs", nargs="+")
    ap.add_argument("--vision", default="",
                    help="JSON file with the vision scorer's verdict")
    ap.add_argument("--json", default="", help="write the combined result here")
    args = ap.parse_args()

    vision_by_item = {}
    if args.vision and os.path.exists(args.vision):
        with open(args.vision) as fh:
            blob = json.load(fh)
        entries = blob if isinstance(blob, list) else [blob]
        for e in entries:
            key = e.get("item") or e.get("name")
            if key:
                vision_by_item[key] = e
        print("loaded %d vision verdict(s) from %s"
              % (len(vision_by_item), os.path.basename(args.vision)))

    targets = []
    for d in args.outdirs:
        if os.path.exists(os.path.join(d, "report.json")):
            targets.append(d)
            continue
        subs = [os.path.join(d, n) for n in sorted(os.listdir(d))
                if os.path.isdir(os.path.join(d, n)) and not n.startswith(".")]
        targets.extend(subs or [d])
    if len(targets) > len(args.outdirs):
        print("(expanded %d path(s) to %d model director%s)"
              % (len(args.outdirs), len(targets),
                 "y" if len(targets) == 1 else "ies"))

    results = [score_one(d, vision_by_item.get(os.path.basename(d.rstrip("/")),
                                               None))
               for d in targets]
    for r in results:
        if r.get("status") == "no_report":
            print("%-26s NOT SCORED           %s" % (r["name"], r["error"]))
            continue
        head = "%-26s objective %5.1f/%-4.0f" % (r["name"], r["objective"],
                                                 r["objective_possible"])
        if r.get("vision_total") is not None:
            head += "  vision %5.1f/45" % r["vision_total"]
        head += "  total %6.2f" % r["total"]
        head += "  %s" % ("PASS" if r["passed"] else "FAIL")
        print(head)
        for c in r.get("checks", []):
            if c["got"] < c["want"]:
                print("      - %-24s %5.2f/%-4.1f  %s"
                      % (c["name"], c["got"], c["want"], c["note"]))

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2, default=str)

    # Three different outcomes, never collapsed into one number: scored and
    # passed, scored and failed, and never scored at all. A pass rate that
    # divides by "everything I pointed at" mixes the last two and reads as a
    # modelling problem when it is a bookkeeping one.
    scored = [r for r in results if r.get("status") == "scored"]
    passed = [r for r in scored if r["passed"]]
    unscored = [r for r in results if r.get("status") != "scored"]
    obj_full = [r for r in scored if r["objective"] >= r["objective_possible"] - 1e-6]
    print("\nobjective 55/55 : %d/%d scored" % (len(obj_full), len(scored)))
    print("full gate 100   : %d/%d scored" % (len(passed), len(scored)))
    if unscored:
        print("not scored      : %d  (%s)"
              % (len(unscored), ", ".join(r["name"] for r in unscored[:8])
                 + ("..." if len(unscored) > 8 else "")))
    return 0 if (scored and len(passed) == len(scored) and not unscored) else 1


if __name__ == "__main__":
    sys.exit(main())