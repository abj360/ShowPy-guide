#!/usr/bin/env python3

"""
check_ch03_ex4.py --- checks exercise 3.4: turn a placement without mutating it

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.choreo.models import Placement

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 3.4."""
    before = Placement(entity="T1", x=1.0, y=2.0, facing=300.0)
    got = solution.solve(before)
    expect(before.facing == 300.0, "the input placement changed")
    expect(close(got.facing, 30.0), f"300 + 90 wraps to 30, got {got.facing}")
    expect(got.point == (1.0, 2.0), "the position must not change")


if __name__ == "__main__":
    run("ch03_ex4", check)
