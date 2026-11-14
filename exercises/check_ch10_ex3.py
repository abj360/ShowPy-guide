#!/usr/bin/env python3

"""
check_ch10_ex3.py --- checks exercise 10.3: a pinned match

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 10.3."""
    longest, crossings = solution.solve()
    expect(close(longest, (6.0**2 + 2.0**2) ** 0.5), "T1 must walk from (0, 5) to (6, 3)")
    expect(crossings == 3, f"got {crossings} crossings; T1 crosses the other three")


if __name__ == "__main__":
    run("ch10_ex3", check)
