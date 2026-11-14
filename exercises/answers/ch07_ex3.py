#!/usr/bin/env python3

"""
ch07_ex3.py --- reference answer to exercise 7.3: meters to pixels

Contains:
    solve(): returns the pixel of stage point (5, 5) on the canvas
"""

from showpy.sheet.render import SheetCanvas
from showpy.sheet.templates import blank_sheet


def solve() -> tuple[float, float]:
    """Returns the pixel of stage point (5, 5) on the canvas."""
    canvas = SheetCanvas.for_sheet(blank_sheet(20, 10), px_per_m=5, margin_m=2)
    return canvas.to_px((5.0, 5.0))
