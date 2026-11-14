#!/usr/bin/env python3

"""
check_ch02_ex3.py --- checks exercise 2.3: edit a show without mutating it

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.examples import two_set_show

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 2.3."""
    show = two_set_show()
    before = show.model_dump()
    got = solution.solve(show)
    expect(show.model_dump() == before, "the input show changed; build new objects instead")
    expect(close(got.set("2").get("T1").point, (0.0, 10.0)), "T1 should be at (0, 10) in set 2")
    expect(got.set("1") == show.set("1"), "set 1 should be untouched")


if __name__ == "__main__":
    run("ch02_ex3", check)
