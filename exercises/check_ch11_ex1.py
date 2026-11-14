#!/usr/bin/env python3

"""
check_ch11_ex1.py --- checks exercise 11.1: stagger from the end

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 11.1."""
    expect(close(solution.solve(), [4.5, 3.0, 1.5, 0.0]), "the last spot leaves first")


if __name__ == "__main__":
    run("ch11_ex1", check)
