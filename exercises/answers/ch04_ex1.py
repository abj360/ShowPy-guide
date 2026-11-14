#!/usr/bin/env python3

"""
ch04_ex1.py --- reference answer to exercise 4.1: space 9 spots on a 20 m arc

Contains:
    solve(): returns 9 spots evenly spaced on the arc
"""

from showpy.core.types import Points
from showpy.geo.shapes import arc
from showpy.geo.spacing import space_along


def solve() -> Points:
    """Returns 9 spots evenly spaced on the arc."""
    return space_along(arc((0.0, 0.0), 20.0, 60.0, 60.0), 9)
