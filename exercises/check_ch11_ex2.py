#!/usr/bin/env python3

"""
check_ch11_ex2.py --- checks exercise 11.2: an ease_out ripple

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 11.2."""
    want = [4.0 * (1 - (1 - u) ** 2) for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
    expect(close(solution.solve(), want), "starts are 4·(1 - (1 - u)²): 0, 1.75, 3, 3.75, 4")


if __name__ == "__main__":
    run("ch11_ex2", check)
