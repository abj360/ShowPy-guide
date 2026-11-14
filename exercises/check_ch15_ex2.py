#!/usr/bin/env python3

"""
check_ch15_ex2.py --- checks exercise 15.2: where the flags end

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 15.2."""
    got = [tuple(p) for p in solution.solve()]
    expect(close(got[0], (9.457, 26.305)), f"F1 should be at (9.457, 26.305), got {got[0]}")
    expect(close(got[3], (4.0, 32.0)), "the leader F4 ends on the last waypoint (4, 32)")


if __name__ == "__main__":
    run("ch15_ex2", check)
