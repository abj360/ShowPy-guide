#!/usr/bin/env python3

"""
check_ch04_ex5.py --- checks exercise 4.5: scatter and keep the farthest

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

import numpy as np
from showpy.geo.measure import distance_matrix
from showpy.geo.regions import region
from showpy.geo.spacing import scatter

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 4.5."""
    got = np.asarray(solution.solve(), dtype=float)
    expect(got.shape == (15, 2), "return fifteen points")
    gaps = distance_matrix(got, got) + np.eye(15) * 1e9
    expect(gaps.min() >= 2.0 - 1e-9, f"closest pair {gaps.min():.3f} m is under 2 m")
    square = region([(0, 0), (10, 0), (10, 10), (0, 10)])
    expect(close(got, scatter(square, 15, 2.0, seed=0)), "scatter() is Bridson then farthest-point")


if __name__ == "__main__":
    run("ch04_ex5", check)
