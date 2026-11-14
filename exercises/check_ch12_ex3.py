#!/usr/bin/env python3

"""
check_ch12_ex3.py --- checks exercise 12.3: when is T2 fastest

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 12.3."""
    tau, peak = solution.solve()
    expect(close(peak, 1.0), "4 m in the last 4 counts at constant speed is 1 m per count")
    expect(4.0 <= tau <= 8.0, "T2 only moves from count 4 to 8")


if __name__ == "__main__":
    run("ch12_ex3", check)
