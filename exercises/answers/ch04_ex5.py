#!/usr/bin/env python3

"""
ch04_ex5.py --- reference answer to exercise 4.5: scatter and keep the farthest

Contains:
    solve(): returns 15 spots at least 2 m apart in a 10 x 10 square
"""

from showpy.core.types import Points
from showpy.geo.regions import region
from showpy.geo.spacing import _bridson, distribute_on_points


def solve() -> Points:
    """Returns 15 spots at least 2 m apart in a 10 x 10 square."""
    square = region([(0, 0), (10, 0), (10, 10), (0, 10)])
    return distribute_on_points(_bridson(square, 2.0, 0), 15)
