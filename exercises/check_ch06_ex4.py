#!/usr/bin/env python3

"""
check_ch06_ex4.py --- checks exercise 6.4: find the bad token

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.examples import two_set_show

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 6.4."""
    show = two_set_show()
    expect(solution.solve(show, "T1 + T2") == -1, "a valid expression returns -1")
    expect(solution.solve(show, "T1 + T9") == 5, "T9 starts at index 5")
    expect(solution.solve(show, "group:x - T1") == 0, "group:x starts at index 0")


if __name__ == "__main__":
    run("ch06_ex4", check)
