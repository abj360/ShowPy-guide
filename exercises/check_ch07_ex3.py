#!/usr/bin/env python3

"""
check_ch07_ex3.py --- checks exercise 7.3: meters to pixels

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 7.3."""
    expect(close(solution.solve(), (85.0, 35.0)), "px = (x - min_x)·5, py = (max_y - y)·5")


if __name__ == "__main__":
    run("ch07_ex3", check)
