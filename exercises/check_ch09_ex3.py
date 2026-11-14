#!/usr/bin/env python3

"""
check_ch09_ex3.py --- checks exercise 9.3: place a set from an arc with open slots

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 9.3."""
    got = tuple(solution.solve())
    expect(got == ("T1", "T2", "T3", "T4"), f"got {got}; left slot to the leftmost spot")


if __name__ == "__main__":
    run("ch09_ex3", check)
