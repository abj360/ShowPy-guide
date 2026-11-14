#!/usr/bin/env python3

"""
check_ch07_ex1.py --- checks exercise 7.1: read the college hash distance

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 7.1."""
    expect(close(solution.solve(), 60 * 0.3048), "NCAA hashes are 60 ft from the sideline")


if __name__ == "__main__":
    run("ch07_ex1", check)
