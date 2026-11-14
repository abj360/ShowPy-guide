#!/usr/bin/env python3

"""
ch04_ex3.py --- reference answer to exercise 4.3: a closed centripetal spline

Contains:
    solve(): returns (length, start point, table rows) of the closed spline
"""

from showpy.core.types import Point
from showpy.geo.shapes import curve_through


def solve() -> tuple[float, Point, int]:
    """Returns (length, start point, table rows) of the closed spline."""
    curve = curve_through((0, 0), (4, 0), (4, 3), (0, 3), closed=True)
    start = curve.point_at(0.0)
    return curve.length(), (float(start[0]), float(start[1])), len(curve._table[0])
