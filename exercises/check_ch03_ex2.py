#!/usr/bin/env python3

"""
check_ch03_ex2.py --- checks exercise 3.2: split counts exactly

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 3.2."""
    got = solution.solve()
    expect(len(got) == 4, "split into exactly 4 parts")
    expect(sum(got) == 13.0, f"parts sum to {sum(got)!r}, not exactly 13.0")
    expect(max(got) - min(got) < 1e-9, "parts should be equal")


if __name__ == "__main__":
    run("ch03_ex2", check)
