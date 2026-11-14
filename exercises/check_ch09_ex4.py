#!/usr/bin/env python3

"""
check_ch09_ex4.py --- checks exercise 9.4: recognize an uneven arc

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 9.4."""
    kind, center, radius, sweep = solution.solve()
    expect(kind == "arc", "the gap from 200° back to 0° (160°) is over 1.5x the median gap")
    expect(close(center, (1.0, 2.0)) and close(radius, 7.0), "center (1, 2), radius 7")
    expect(close(sweep, 200.0), "the arc sweeps 360 - 160 = 200 degrees")


if __name__ == "__main__":
    run("ch09_ex4", check)
