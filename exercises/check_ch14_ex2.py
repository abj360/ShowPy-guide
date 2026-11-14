#!/usr/bin/env python3

"""
check_ch14_ex2.py --- checks exercise 14.2: one frame row from the CSV

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 14.2."""
    got = list(solution.solve())
    expect(got == ["4", "2", "T4", "6", "7", "0", "true"], f"got {got}")


if __name__ == "__main__":
    run("ch14_ex2", check)
