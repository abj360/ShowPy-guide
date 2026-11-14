#!/usr/bin/env python3

"""
check_ch13_ex2.py --- checks exercise 13.2: save twice and read back

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 13.2."""
    expect(tuple(solution.solve()) == (2, 12.0), "two revisions; the head has 12 counts")


if __name__ == "__main__":
    run("ch13_ex2", check)
