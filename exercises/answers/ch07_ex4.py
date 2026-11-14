#!/usr/bin/env python3

"""
ch07_ex4.py --- reference answer to exercise 7.4: recover a similarity

Contains:
    solve(): returns (scale, rotation degrees, translation) mapping the old points onto the new
"""

import math

import numpy as np
from showpy.sheet.replace import similarity_fit


def solve() -> tuple[float, float, tuple[float, float]]:
    """Returns (scale, rotation degrees, translation) mapping the old points onto the new."""
    src = np.array([[0.0, 0.0], [4.0, 0.0], [0.0, 3.0]])
    dst = np.array([[10.0, 10.0], [10.0, 14.0], [7.0, 10.0]])
    m = similarity_fit(src, dst)
    scale = math.sqrt(abs(np.linalg.det(m[:2, :2])))
    angle = math.degrees(math.atan2(m[1, 0], m[0, 0]))
    return scale, angle, (float(m[0, 2]), float(m[1, 2]))
