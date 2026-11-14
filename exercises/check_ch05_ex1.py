#!/usr/bin/env python3

"""
check_ch05_ex1.py --- checks exercise 5.1: seconds with a hold

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 5.1."""
    got = solution.solve()
    expect(close(got, 64 * 60 / 144 + 2), f"got {got}; 64 counts at 144 cpm plus the hold")


if __name__ == "__main__":
    run("ch05_ex1", check)
