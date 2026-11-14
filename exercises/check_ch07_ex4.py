#!/usr/bin/env python3

"""
check_ch07_ex4.py --- checks exercise 7.4: recover a similarity

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 7.4."""
    scale, angle, shift = solution.solve()
    expect(close(scale, 1.0), "the triangle keeps its size")
    expect(close(angle, 90.0), "(4, 0) became (0, 4) relative to the first point: +90°")
    expect(close(shift, (10.0, 10.0)), "the origin went to (10, 10)")


if __name__ == "__main__":
    run("ch07_ex4", check)
