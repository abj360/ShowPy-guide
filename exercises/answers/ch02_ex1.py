#!/usr/bin/env python3

"""
ch02_ex1.py --- reference answer to exercise 2.1: face a spot to the left

Contains:
    solve(): returns the facing from (4, 6) toward (1, 6), in degrees
"""

from showpy.core.units import vector_facing


def solve() -> float:
    """Returns the facing from (4, 6) toward (1, 6), in degrees."""
    return vector_facing((1.0 - 4.0, 6.0 - 6.0))
