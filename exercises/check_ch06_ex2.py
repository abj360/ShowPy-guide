#!/usr/bin/env python3

"""
check_ch06_ex2.py --- checks exercise 6.2: add a group of flags entering at set 2

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.cast.select import select

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 6.2."""
    show = solution.solve()
    flags = select(show, "group:flags").ids
    expect(flags == ("F1", "F2", "F3", "F4"), f"expected F1-F4, got {flags}")
    expect(close(show.set("2").positions(list(flags))[:, 0], [-3, -1, 1, 3]), "space them evenly")
    expect(not any(show.set("1").get(f).on_field for f in flags), "off field in set 1")


if __name__ == "__main__":
    run("ch06_ex2", check)
