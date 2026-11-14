#!/usr/bin/env python3

"""
ch16_ex3.py --- reference answer to exercise 16.3: a falsifying curve

Contains:
    solve(): returns a curve and n for which space_along gives unequal straight gaps
"""

from showpy.geo.curves import AnyCurve
from showpy.geo.shapes import bezier


def solve() -> tuple[AnyCurve, int]:
    """Returns a curve and n for which space_along gives unequal straight gaps."""
    return bezier((0, 0), (0, 5), (1, 5), (7, 0)), 6
