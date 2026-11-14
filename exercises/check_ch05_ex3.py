#!/usr/bin/env python3

"""
check_ch05_ex3.py --- checks exercise 5.3: label a count with its measure

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 5.3."""
    got = solution.solve()
    expect(tuple(got) == (15, 1.0), f"got {got}; 32 counts are measures 1-8, then 18 counts of 3")


if __name__ == "__main__":
    run("ch05_ex3", check)
