#!/usr/bin/env python3

"""
check_ch15_ex1.py --- checks exercise 15.1: when T8 moves

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 15.1."""
    expect(close(solution.solve(), (7.0, 16.0)), "transition 1→2 starts at global count 0")


if __name__ == "__main__":
    run("ch15_ex1", check)
