#!/usr/bin/env python3

"""
ch10_ex2.py --- reference answer to exercise 10.2: more slots than spots

Contains:
    solve(): returns (assignment, unassigned slots) for five slots
"""

from showpy.choreo.match import match
from showpy.examples import two_set_show


def solve() -> tuple[dict[str, int], tuple[int, ...]]:
    """Returns (assignment, unassigned slots) for five slots."""
    slots = [(0.0, 9.0), (1.0, 9.0), (2.0, 9.0), (3.0, 9.0), (10.0, 9.0)]
    result = match(two_set_show().set("1"), slots)
    return result.assignment, result.unassigned_slots
