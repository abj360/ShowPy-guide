#!/usr/bin/env python3

"""
check_ch17_ex2.py --- checks exercise 17.2: search the public API

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

import showpy

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 17.2."""
    got = list(solution.solve())
    want = sorted(name for name in showpy.__all__ if "note" in name)
    expect(got == want and "add_note" in got, f"got {got}")


if __name__ == "__main__":
    run("ch17_ex2", check)
