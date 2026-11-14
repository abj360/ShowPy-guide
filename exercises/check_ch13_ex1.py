#!/usr/bin/env python3

"""
check_ch13_ex1.py --- checks exercise 13.1: insert a sub-set and renumber

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 13.1."""
    got = [tuple(p) for p in solution.solve()]
    expect(got == [("1", 0.0), ("2", 3.0), ("3", 5.0)], f"got {got}; total time must stay 8 counts")


if __name__ == "__main__":
    run("ch13_ex1", check)
