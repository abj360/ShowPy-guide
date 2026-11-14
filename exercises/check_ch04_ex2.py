#!/usr/bin/env python3

"""
check_ch04_ex2.py --- checks exercise 4.2: facing after rotate then mirror

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 4.2."""
    got = solution.solve()
    expect(close(got, 195.0), f"got {got}; 30 + 135 = 165, mirrored 195")


if __name__ == "__main__":
    run("ch04_ex2", check)
