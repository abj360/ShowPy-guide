#!/usr/bin/env python3

"""
check_ch14_ex1.py --- checks exercise 14.1: behavior text of a delayed move

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 14.1."""
    got = list(solution.solve())
    expect(got == ["start", "delay 2, move 6"], f"got {got}")


if __name__ == "__main__":
    run("ch14_ex1", check)
