#!/usr/bin/env python3

"""
ch03_ex3.py --- reference answer to exercise 3.3: area of a region with a hole

Contains:
    solve(): returns the area of a 10 x 8 rectangle minus a 2 x 2 hole at (3, 3)
"""

from showpy.core.types import Region


def solve() -> float:
    """Returns the area of a 10 x 8 rectangle minus a 2 x 2 hole at (3, 3)."""
    outer = ((0.0, 0.0), (10.0, 0.0), (10.0, 8.0), (0.0, 8.0))
    hole = ((3.0, 3.0), (5.0, 3.0), (5.0, 5.0), (3.0, 5.0))
    return float(Region(exterior=outer, holes=(hole,)).to_shapely().area)
