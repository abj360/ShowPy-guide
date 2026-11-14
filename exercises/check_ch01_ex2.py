#!/usr/bin/env python3

"""
check_ch01_ex2.py --- checks exercise 1.2: count spots, sets and stored transitions

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 1.2."""
    got = solution.solve()
    expect(got == (4, 2, 0), "use show.cast.spots, show.sets and show.transitions; rows are sparse")


if __name__ == "__main__":
    run("ch01_ex2", check)
