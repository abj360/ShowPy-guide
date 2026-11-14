#!/usr/bin/env python3

"""
check_ch13_ex4.py --- checks exercise 13.4: an agent saves a form-built set

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import close, expect, run

LINE = [[0, 12], [2, 12], [4, 12], [6, 12]]
CHANGED = ["/sets/2/forms.json", "/sets/2/set.json"]


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 13.4."""
    positions, changed = solution.solve()
    expect(close(positions, LINE), f"set 2 at the head should be the line, got {positions}")
    expect(list(changed) == CHANGED, f"store the form too; the save should change {CHANGED}")


if __name__ == "__main__":
    run("ch13_ex4", check)
