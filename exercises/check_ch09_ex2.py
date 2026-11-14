#!/usr/bin/env python3

"""
check_ch09_ex2.py --- checks exercise 9.2: the front-left slot of a turned block

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 9.2."""
    got = solution.solve()
    expect(got == 11, f"got {got}; facing upstage, the block's back-right slot is stage front-left")


if __name__ == "__main__":
    run("ch09_ex2", check)
