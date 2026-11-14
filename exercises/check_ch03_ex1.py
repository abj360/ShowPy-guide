#!/usr/bin/env python3

"""
check_ch03_ex1.py --- checks exercise 3.1: compact IDs into ranges

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 3.1."""
    got = solution.solve()
    expect(
        got == "B1–B2, T1–T3, T5–T6",
        f"got {got!r}; it sorts naturally, uses an en dash",
    )


if __name__ == "__main__":
    run("ch03_ex1", check)
