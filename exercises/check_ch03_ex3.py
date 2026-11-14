#!/usr/bin/env python3

"""
check_ch03_ex3.py --- checks exercise 3.3: area of a region with a hole

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 3.3."""
    got = solution.solve()
    expect(close(got, 76.0), f"got {got}; 80 m² minus a 4 m² hole is 76 m²")


if __name__ == "__main__":
    run("ch03_ex3", check)
