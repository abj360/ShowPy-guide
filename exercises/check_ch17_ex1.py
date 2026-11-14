#!/usr/bin/env python3

"""
check_ch17_ex1.py --- checks exercise 17.1: find a module through the top-level API

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 17.1."""
    expect(solution.solve() == "showpy.choreo.match_ops", "suggest_swaps lives with apply_match")


if __name__ == "__main__":
    run("ch17_ex1", check)
