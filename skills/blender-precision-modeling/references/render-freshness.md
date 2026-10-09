# Render freshness — a render set has a version, and it is not the file dates

A directory of PNGs carries no version. The moment the toolkit changes, every
image already on disk silently becomes evidence about code that no longer
exists — and nothing about the images says so. They still look like renders,
they still have plausible mtimes, and a scoring round will happily grade them.

This is not hypothetical. Four rounds of vision scoring in this project graded
**698 of 716 stale renders**: every fix had landed in `bkit.py` *after* the
images were made, so each round re-litigated a toolkit state that was already
superseded, and the score never moved because the score had nothing to do with
the current code.

## The rule

**Never score renders you have not checked against the current toolkit.**
Checking is one command, and it is cheaper than one wasted round.

```bash
python3 scripts/check_freshness.py <render_root>
```

It exits `0` only when every `report.json` carries the `bkit_sha` of the live
`bkit.py`. Anything stale, unstamped, unparseable, or missing is a failure.

```
$ python3 scripts/check_freshness.py ~/.blenderlab/renders
  STALE      airliner                       made with 7f21c0ab9e44
  UNSTAMPED  bowl                          no bkit_sha in report
  ...
bkit sha c0b9433b3132 | 718 reports: 0 current, 0 stale, 718 unstamped
STALE SET -- these renders do not reflect the current toolkit.
```

An unstamped report counts as stale on purpose. A render whose provenance is
unknown is not evidence, and treating "no version" as "probably fine" is the
exact hole this closes.

## Where the stamp comes from

`bkit.report()` adds `bkit_sha` to every report it produces. It is a SHA-1 of
`bkit.py` itself, truncated to 12 hex characters — computed from the file on
disk, so it tracks edits to the toolkit without anyone having to remember to
bump a version constant.

```python
def toolkit_sha():
    """Short hash of THIS bkit source file, stamped into every report."""
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "bkit.py"), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:12]
```

It returns `None` instead of raising if the source is unreadable. A missing
stamp must never be the reason a model fails to render — it just means the
render is unstamped, and unstamped is already a failure downstream.

## Why not use mtimes

Comparing image mtime against `bkit.py`'s mtime looks equivalent and is not:

- **It only catches changes made to `bkit.py`.** A model file edited on its own
  leaves its renders stale in the only way that matters — the geometry changed
  and the images did not.
- **It is ambiguous under concurrency.** A sweep writes renders continuously, so
  "render is older than bkit" and "render is newer than bkit" are both true for
  parts of one batch, depending on when you looked.
- **It cannot be checked without the source tree.** The stamp travels with the
  render, so a handed-off render set is self-describing.

If you want model-file provenance too, compare `report.json["model_script"]`
and its content hash; the sweep driver (`scripts/all_models.py` pattern) is
where that belongs.

## Consequence for how you work

Fix the toolkit first, then re-render, then score. Scoring before re-rendering
is not a shortcut, it is measuring the wrong thing — and it is invisible, which
is what makes it expensive. Run `check_freshness.py` at the *start* of a scoring
round, not at the end when the round has already been spent.
