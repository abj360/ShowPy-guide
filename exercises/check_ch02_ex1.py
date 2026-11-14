#!/usr/bin/env python3

"""
check_ch02_ex1.py --- checks exercise 2.1: face a spot to the left

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 2.1."""
    got = solution.solve()
    expect(close(got, 270.0), f"got {got}; the direction is (-3, 0), toward audience left")


if __name__ == "__main__":
    run("ch02_ex1", check)
