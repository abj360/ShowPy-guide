#!/usr/bin/env python3

"""
check_ch06_ex1.py --- checks exercise 6.1: select with a group and a difference

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 6.1."""
    expect(tuple(solution.solve()) == ("T1", "T4"), "expected ('T1', 'T4') in cast order")


if __name__ == "__main__":
    run("ch06_ex1", check)
