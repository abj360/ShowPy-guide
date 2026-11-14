#!/usr/bin/env python3

"""
check_ch15_ex3.py --- checks exercise 15.3: a center-out stagger

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 15.3."""
    got = solution.solve()
    expect(got > -0.467, f"tightest gap {got:.3f} m is not better than the original -0.467 m")


if __name__ == "__main__":
    run("ch15_ex3", check)
