#!/usr/bin/env python3
"""
catalog.py -- query the object catalog without loading the whole thing.

The catalog is large enough that an agent should never read it end to end; it
should ask for the slice it needs. This is the progressive-loading entry point.

    python3 scripts/catalog.py stats
    python3 scripts/catalog.py domains
    python3 scripts/catalog.py list --domain kitchen --status todo --limit 20
    python3 scripts/catalog.py search "thread" --limit 15
    python3 scripts/catalog.py show coffee_mug
    python3 scripts/catalog.py recipes --recipe lathe
    python3 scripts/catalog.py next --limit 12      # highest-value unbuilt items
    python3 scripts/catalog.py mark coffee_mug --status scored --score 92

`list`/`search` emit a compact one-line-per-item table by default so an agent can
pick work without burning context, and full JSON only with --json.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "catalog", "catalog.json")
STATUSES = ("todo", "building", "built", "scored", "failed")
STATUS_DIR = os.path.join(HERE, "..", "catalog", ".status")
MODEL_DIR = os.path.join(HERE, "..", "catalog")


def _model_exists(item_id):
    for root, _dirs, files in os.walk(MODEL_DIR):
        if item_id + ".py" in files:
            return True
    return False


def _read_status(item_id):
    """Status is filesystem-derived, never read-modify-written into a shared file.

    A previous implementation rewrote catalog.json on every `mark`; with several
    agents marking at once the last writer silently reverted everyone else's
    work, and 69 finished models reported as 0 built. The existence of
    catalog/<domain>/<id>.py is the durable fact, so that is what we report.
    """
    path = os.path.join(STATUS_DIR, item_id + ".txt")
    if os.path.exists(path):
        try:
            with open(path) as fh:
                return fh.read().strip() or "built"
        except OSError:
            pass
    return "built" if _model_exists(item_id) else "todo"


def load():
    with open(CATALOG) as fh:
        cat = json.load(fh)
    for it in cat["items"]:
        it["status"] = _read_status(it["id"])
    return cat


def save(cat):
    """Retained for compatibility; `mark` no longer rewrites catalog.json."""
    with open(CATALOG, "w") as fh:
        json.dump(cat, fh, indent=1)


def fmt_row(it):
    return "%-26s %-22s %-8s %-9s %s" % (
        it["id"], it["name"][:22], it["size_class"], it.get("status", "todo"),
        ",".join(it["recipes"][:4]))


def cmd_stats(cat, args):
    items = cat["items"]
    by_status = {}
    for it in items:
        by_status[it.get("status", "todo")] = by_status.get(it.get("status", "todo"), 0) + 1
    print("catalog: %d items in %d domains" % (len(items), len(cat["domains"])))
    print("status:  " + "  ".join("%s=%d" % (k, by_status.get(k, 0)) for k in STATUSES))
    print("\n%-24s %5s %s" % ("DOMAIN", "COUNT", "BUILT"))
    for d in cat["domains"]:
        sub = [i for i in items if i["domain"] == d["id"]]
        built = sum(1 for i in sub if i.get("status") in ("scored",))
        print("%-24s %5d %d/%d" % (d["id"], d["count"], built, len(sub)))
    return 0


def cmd_domains(cat, args):
    for d in cat["domains"]:
        print("%-20s %-26s %3d  %s" % (d["id"], d["name"], d["count"], d["notes"]))
    return 0


def cmd_list(cat, args):
    rows = cat["items"]
    if args.domain:
        rows = [i for i in rows if i["domain"] in args.domain.split(",")]
    if args.status:
        rows = [i for i in rows if i.get("status", "todo") in args.status.split(",")]
    if args.size:
        rows = [i for i in rows if i["size_class"] in args.size.split(",")]
    rows = rows[: args.limit] if args.limit else rows
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    print("%-26s %-22s %-8s %-9s %s" % ("ID", "NAME", "SIZE", "STATUS", "RECIPES"))
    for it in rows:
        print(fmt_row(it))
    print("(%d rows)" % len(rows))
    return 0


def cmd_search(cat, args):
    q = args.query.lower()
    rows = [i for i in cat["items"]
            if q in i["id"].lower() or q in i["name"].lower()
            or q in i["domain"].lower() or q in i["domain_title"].lower()]
    if args.limit:
        rows = rows[: args.limit]
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    print("%-26s %-22s %-8s %s" % ("ID", "NAME", "SIZE", "DOMAIN"))
    for it in rows:
        print("%-26s %-22s %-8s %s" % (it["id"], it["name"][:22], it["size_class"],
                                       it["domain"]))
    print("(%d matches)" % len(rows))
    return 0


def cmd_show(cat, args):
    rows = [i for i in cat["items"] if i["id"] == args.item_id]
    if not rows:
        print("no such item: %s" % args.item_id, file=sys.stderr)
        return 2
    print(json.dumps(rows[0], indent=1))
    return 0


def cmd_recipes(cat, args):
    rows = [i for i in cat["items"] if args.recipe in i["recipes"]]
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    print("%-26s %-22s %s" % ("ID", "NAME", "RECIPES"))
    for it in rows[: args.limit or len(rows)]:
        print("%-26s %-22s %s" % (it["id"], it["name"][:22], ",".join(it["recipes"])))
    print("(%d items use %r)" % (len(rows), args.recipe))
    return 0


def cmd_next(cat, args):
    """Unbuilt items, simplest first: small size_class and few recipes is the
    cheapest way for a new agent to learn the toolkit."""
    order = {"small": 0, "medium": 1, "tiny": 2, "large": 3, "micro": 4,
             "huge": 5}
    rows = [i for i in cat["items"]
            if i.get("status", "todo") in ("todo", "failed")]
    rows.sort(key=lambda i: (order.get(i["size_class"], 9), len(i["recipes"])))
    rows = rows[: args.limit or 20]
    print("%-26s %-22s %-8s %-8s %s" % ("ID", "NAME", "SIZE", "DOMAIN", "RECIPES"))
    for it in rows:
        print("%-26s %-22s %-8s %-8s %s"
              % (it["id"], it["name"][:22], it["size_class"], it["domain"],
                 ",".join(it["recipes"][:5])))
    return 0


def cmd_mark(cat, args):
    if not any(i["id"] == args.item_id for i in cat["items"]):
        print("no such item: %s" % args.item_id, file=sys.stderr)
        return 2
    os.makedirs(STATUS_DIR, exist_ok=True)
    line = args.status
    if args.score is not None:
        line += " score=%d" % args.score
    if args.note:
        line += " " + args.note
    # One small file per item: concurrent marks cannot overwrite each other.
    with open(os.path.join(STATUS_DIR, args.item_id + ".txt"), "w") as fh:
        fh.write(line + "\n")
    print("marked %s -> %s%s" % (args.item_id, args.status,
                                (" score=%s" % args.score) if args.score is not None else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    sub.add_parser("domains")
    p = sub.add_parser("list")
    p.add_argument("--domain", default="")
    p.add_argument("--status", default="")
    p.add_argument("--size", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("show")
    p.add_argument("item_id")
    p = sub.add_parser("recipes")
    p.add_argument("recipe")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("next")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("mark")
    p.add_argument("item_id")
    p.add_argument("--status", required=True, choices=STATUSES)
    p.add_argument("--score", type=int)
    p.add_argument("--note", default="")

    args = ap.parse_args()
    cat = load()
    return {
        "stats": cmd_stats, "domains": cmd_domains, "list": cmd_list,
        "search": cmd_search, "show": cmd_show, "recipes": cmd_recipes,
        "next": cmd_next, "mark": cmd_mark,
    }[args.cmd](cat, args)


if __name__ == "__main__":
    sys.exit(main())