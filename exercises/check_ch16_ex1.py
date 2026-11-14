#!/usr/bin/env python3

"""
check_ch16_ex1.py --- checks exercise 16.1: a property for normalize_angle

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 16.1."""
    test = solution.solve()
    expect(callable(test), "return the decorated test function")
    expect(hasattr(test, "hypothesis"), "decorate the test with @given")
    test()


if __name__ == "__main__":
    run("ch16_ex1", check)
