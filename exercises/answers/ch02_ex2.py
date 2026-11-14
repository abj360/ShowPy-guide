#!/usr/bin/env python3

"""
ch02_ex2.py --- reference answer to exercise 2.2: arc angle versus facing

Contains:
    solve(): returns (arc angle, facing) of the direction from (0, 10) to (0, 4)
"""

import math

from showpy.core.units import normalize_angle, vector_facing


def solve() -> tuple[float, float]:
    """Returns (arc angle, facing) of the direction from (0, 10) to (0, 4)."""
    dx, dy = 0.0 - 0.0, 4.0 - 10.0
    arc_deg = normalize_angle(math.degrees(math.atan2(dy, dx)))
    return arc_deg, vector_facing((dx, dy))
