#!/usr/bin/env python3

"""
check_ch02_ex2.py --- checks exercise 2.2: arc angle versus facing

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 2.2."""
    arc_deg, facing = solution.solve()
    expect(close(arc_deg, 270.0), "math angle of (0, -6) is -90°, wrapped to 270°")
    expect(close(facing, 0.0), "pointing at -y is facing the audience: 0°")


if __name__ == "__main__":
    run("ch02_ex2", check)
