#!/usr/bin/env python3

"""
check_ch01_ex3.py --- checks exercise 1.3: measure which packages a package imports

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 1.3."""
    expect(solution.solve("time") == {"core"}, "time should import only core")
    got = solution.solve("geo")
    expect(got == {"core", "choreo", "sheet"}, f"geo imports core plus models; you found {got}")


if __name__ == "__main__":
    run("ch01_ex3", check)
