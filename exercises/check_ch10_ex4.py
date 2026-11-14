#!/usr/bin/env python3

"""
check_ch10_ex4.py --- checks exercise 10.4: the order-preserving DP by hand

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

import numpy as np
from showpy.choreo.match_solve import solve_ordered

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 10.4."""
    rng = np.random.default_rng(5)
    for _ in range(30):
        cost = rng.uniform(0, 10, (4, 7))
        got = list(solution.solve(cost))
        want = solve_ordered(cost).tolist()
        expect(got == want, f"got {got}, solve_ordered gives {want}")


if __name__ == "__main__":
    run("ch10_ex4", check)
