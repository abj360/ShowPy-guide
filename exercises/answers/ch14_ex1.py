#!/usr/bin/env python3

"""
ch14_ex1.py --- reference answer to exercise 14.1: behavior text of a delayed move

Contains:
    solve(): returns the behavior texts of T1's coordinate sheet with a 2-count delay
"""

from showpy.choreo.paths import delay
from showpy.examples import two_set_show
from showpy.export.print_sheets import coordinate_sheet


def solve() -> list[str]:
    """Returns the behavior texts of T1's coordinate sheet with a 2-count delay."""
    show = two_set_show()
    spec = delay(show.transition(("1", "2")), ["T1"], 2.0)
    sheet = coordinate_sheet(show.model_copy(update={"transitions": (spec,)}), "T1")
    return [row.behavior for row in sheet.rows]
