#!/usr/bin/env python3

"""
check_ch07_ex2.py --- checks exercise 7.2: word a point and read it back

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 7.2."""
    text, point = solution.solve()
    expect(text == "L2.25 U7.00", f"got {text!r}")
    expect(close(point, (-2.25, 7.0)), "from_coords should invert to_coords")


if __name__ == "__main__":
    run("ch07_ex2", check)
