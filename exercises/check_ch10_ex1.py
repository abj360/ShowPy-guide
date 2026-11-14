#!/usr/bin/env python3

"""
check_ch10_ex1.py --- checks exercise 10.1: a bottleneck by hand

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 10.1."""
    expect(close(solution.solve(), 2.0), "rows can take 1, 2 and 2 (0→1, 1→0, 2→2): largest 2")


if __name__ == "__main__":
    run("ch10_ex1", check)
