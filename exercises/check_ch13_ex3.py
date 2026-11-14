#!/usr/bin/env python3

"""
check_ch13_ex3.py --- checks exercise 13.3: what a pin protects

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 13.3."""
    got = list(solution.solve())
    expect(got == ["placement T2 in set 1", "placement T2 in set 2"], f"got {got}")


if __name__ == "__main__":
    run("ch13_ex3", check)
