#!/usr/bin/env python3

"""
check_ch02_ex4.py --- checks exercise 2.4: reproducible scatter

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

import numpy as np
from showpy.geo.measure import distance_matrix

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 2.4."""
    a, b, c = solution.solve(3), solution.solve(3), solution.solve(4)
    expect(a.shape == (12, 2), "return a (12, 2) array")
    expect(bool((a == b).all()), "the same seed must give identical points")
    expect(not bool((a == c).all()), "another seed should give another picture")
    gaps = distance_matrix(a, a) + np.eye(12) * 1e9
    expect(gaps.min() >= 1.5 - 1e-9, f"closest pair is {gaps.min():.3f} m, below 1.5 m")


if __name__ == "__main__":
    run("ch02_ex4", check)
