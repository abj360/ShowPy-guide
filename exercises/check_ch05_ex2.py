#!/usr/bin/env python3

"""
check_ch05_ex2.py --- checks exercise 5.2: which count plays at 10 seconds

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

import math
from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 5.2."""
    got = solution.solve()
    k = 60.0 / 32.0
    expect(close(got, 120.0 * math.expm1(k * 10.0 / 60.0) / k), f"got {got}")


if __name__ == "__main__":
    run("ch05_ex2", check)
