#!/usr/bin/env python3

"""
check_ch08_ex2.py --- checks exercise 8.2: notes near a point

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 8.2."""
    near, far = solution.solve()
    expect(list(near) == ["p1"], "0.707 m is within 1 m")
    expect(list(far) == [], "0.707 m is not within 0.5 m")


if __name__ == "__main__":
    run("ch08_ex2", check)
