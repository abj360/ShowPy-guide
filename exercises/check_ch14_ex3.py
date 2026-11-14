#!/usr/bin/env python3

"""
check_ch14_ex3.py --- checks exercise 14.3: claim, then swap as the designer

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 14.3."""
    expect(tuple(solution.solve()) == ("Bo", "Ada"), "after the swap Bo is on T1, Ada on T2")


if __name__ == "__main__":
    run("ch14_ex3", check)
