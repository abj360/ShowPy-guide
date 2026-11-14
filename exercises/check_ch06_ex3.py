#!/usr/bin/env python3

"""
check_ch06_ex3.py --- checks exercise 6.3: near a point, right to left

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 6.3."""
    expect(tuple(solution.solve()) == ("T3", "T2"), "T2 (x=2) and T3 (x=4) are within 2.5 m")


if __name__ == "__main__":
    run("ch06_ex3", check)
