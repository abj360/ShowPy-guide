#!/usr/bin/env python3

"""
check_ch09_ex1.py --- checks exercise 9.1: facings of a circle form

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 9.1."""
    got = solution.solve()
    want = [(90.0 + 45.0 * k) % 360.0 for k in range(8)]
    expect(close(got, want), "outward from the center: 90°, 135°, ... starting at angle 0")


if __name__ == "__main__":
    run("ch09_ex1", check)
