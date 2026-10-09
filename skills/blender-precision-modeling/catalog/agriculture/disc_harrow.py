"""
Disc Harrow -- catalog entry `disc_harrow`.

The model itself lives in `harrow.py`; this wrapper exists because the catalog
indexes by id, and a model whose filename is not its id is never rendered,
scored or counted. It loads the sibling module and re-exports its contract, so
there is exactly one implementation.
"""
import importlib.util
import os

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harrow.py")
_spec = importlib.util.spec_from_file_location("_model_harrow", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

SPEC = dict(_mod.SPEC)
CHECKS = [dict(c) for c in getattr(_mod, "CHECKS", [])]


def build():
    return _mod.build()
