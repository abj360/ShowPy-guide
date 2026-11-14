#!/usr/bin/env python3

"""
ch07_ex2.py --- reference answer to exercise 7.2: word a point and read it back

Contains:
    solve(): returns the short wording of (-2.25, 7.0) and the point read back
"""

from showpy.examples import two_set_show
from showpy.sheet.coords import from_coords, to_coords


def solve() -> tuple[str, tuple[float, float]]:
    """Returns the short wording of (-2.25, 7.0) and the point read back."""
    show = two_set_show()
    text = to_coords(show, (-2.25, 7.0), "short")
    return text, from_coords(show, text)
