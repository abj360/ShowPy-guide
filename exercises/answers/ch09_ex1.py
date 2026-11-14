#!/usr/bin/env python3

"""
ch09_ex1.py --- reference answer to exercise 9.1: facings of a circle form

Contains:
    solve(): returns the facing of each of the 8 slots of the circle form
"""

from showpy.choreo.forms import circle_form, slot_poses


def solve() -> list[float]:
    """Returns the facing of each of the 8 slots of the circle form."""
    _, facings = slot_poses(circle_form("c", [], (0.0, 10.0), 5.0, n=8))
    return [float(f) for f in facings]
