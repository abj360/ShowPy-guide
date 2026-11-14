#!/usr/bin/env python3

"""
check_ch10_ex2.py --- checks exercise 10.2: more slots than spots

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 10.2."""
    assignment, free = solution.solve()
    expect(tuple(free) == (4,), f"got {free}; slot 4 at x = 10 is too far for anyone")
    expect(assignment == {"T1": 0, "T2": 1, "T3": 2, "T4": 3}, f"got {assignment}")


if __name__ == "__main__":
    run("ch10_ex2", check)
