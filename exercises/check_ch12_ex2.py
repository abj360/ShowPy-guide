#!/usr/bin/env python3

"""
check_ch12_ex2.py --- checks exercise 12.2: facing after the window

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 12.2."""
    expect(close(solution.solve(), 202.5), "halfway from the travel facing 135° to 270°")


if __name__ == "__main__":
    run("ch12_ex2", check)
