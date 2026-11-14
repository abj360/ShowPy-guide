#!/usr/bin/env python3

"""
ch05_ex4.py --- reference answer to exercise 5.4: where the ramp reaches 150 cpm

Contains:
    solve(): returns (count, seconds) where the ramp first reaches 150 cpm
"""

import math


def solve() -> tuple[float, float]:
    """Returns (count, seconds) where the ramp first reaches 150 cpm."""
    r0, r1, span = 120.0, 180.0, 32.0
    k = (r1 - r0) / span
    count = (150.0 - r0) / k
    return count, 60.0 / k * math.log(150.0 / r0)
