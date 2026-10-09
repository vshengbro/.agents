"""
viaduct_helpers_note -- (not a catalog item)

This module holds no geometry. It exists only to document the pitch arithmetic
the viaduct and bridge models share, so the numbers are written down once.
"""
ARCH_NOTE = ("Arch pitch = clear span + pier width, repeated SPANS times. "
             "Arch centres therefore sit at x0 + i*PITCH with "
             "x0 = -(SPANS-1)*PITCH/2, which makes the end arches symmetric "
             "about the origin by construction rather than by hand.")
