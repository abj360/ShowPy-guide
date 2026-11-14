#!/usr/bin/env python3

"""
check_ch16_ex2.py --- checks exercise 16.2: a round-trip property for the clock

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 16.2."""
    test = solution.solve()
    expect(hasattr(test, "hypothesis"), "decorate the test with @given")
    test()


if __name__ == "__main__":
    run("ch16_ex2", check)
