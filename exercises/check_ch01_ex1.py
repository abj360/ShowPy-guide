#!/usr/bin/env python3

"""
check_ch01_ex1.py --- checks exercise 1.1: find where PathEngine lives

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 1.1."""
    got = solution.solve()
    expect(got == "showpy.choreo.engine", "look at showpy.PathEngine.__module__")


if __name__ == "__main__":
    run("ch01_ex1", check)
