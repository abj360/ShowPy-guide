#!/usr/bin/env python3

"""
ch12_ex1.py --- reference answer to exercise 12.1: a position by hand

Contains:
    solve(): returns T1's position at count 4 in the waypoint example, computed by hand
"""

import numpy as np


def solve() -> tuple[float, float]:
    """Returns T1's position at count 4 in the waypoint example, computed by hand."""
    start, end, tau = 1.0, 7.0, 4.0
    u = (tau - start) / (end - start)
    eased_share = 2 * u**2 if u < 0.5 else 1 - 2 * (1 - u) ** 2
    eased = start + eased_share * (end - start)
    s = float(np.interp(eased, [1.0, 3.0, 7.0], [0.0, 3.0, 8.0]))
    if s <= 3.0:
        return s, 5.0
    along = (s - 3.0) / 5.0
    return 3.0 - 3.0 * along, 5.0 + 4.0 * along
