#!/usr/bin/env python3

"""
check_ch14_ex4.py --- checks exercise 14.4: the audio seek with a hold

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 14.4."""
    expect(close(solution.solve(), 1.25 + 4.0 + 2.0), "1.25 + 4 + the 2 s hold")


if __name__ == "__main__":
    run("ch14_ex4", check)
