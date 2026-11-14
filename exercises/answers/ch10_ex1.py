#!/usr/bin/env python3

"""
ch10_ex1.py --- reference answer to exercise 10.1: a bottleneck by hand

Contains:
    solve(): returns the bottleneck value of the 3 x 3 matrix
"""

from showpy.choreo.match import bottleneck_value


def solve() -> float:
    """Returns the bottleneck value of the 3 x 3 matrix."""
    return bottleneck_value([[4.0, 1.0, 3.0], [2.0, 0.0, 5.0], [3.0, 2.0, 2.0]])
