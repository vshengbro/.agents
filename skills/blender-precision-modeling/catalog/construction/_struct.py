"""SUPERSEDED -- see _sections.py.

This module was originally named `_struct.py`, which cannot be imported inside
Blender: CPython's stdlib already has a `_struct` accelerator module in
sys.modules, so `import _struct` binds that instead of this file. The live
helper is `_sections.py`. This stub exists only because the file could not be
removed from the host filesystem; nothing imports it.
"""
raise ImportError("_struct is a stdlib module name; use _sections instead")