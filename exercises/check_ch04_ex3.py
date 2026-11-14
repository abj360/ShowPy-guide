#!/usr/bin/env python3

"""
check_ch04_ex3.py --- checks exercise 4.3: a closed centripetal spline

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.geo.shapes import curve_through

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 4.3."""
    length, start, rows = solution.solve()
    ref = curve_through((0, 0), (4, 0), (4, 3), (0, 3), closed=True)
    expect(close(length, ref.length()), "use closed=True, default alpha")
    expect(close(start, (0.0, 0.0)), "a closed spline starts at its first point")
    expect(rows == 4 * 256 + 1, "4 segments x 256 + 1 rows")


if __name__ == "__main__":
    run("ch04_ex3", check)
