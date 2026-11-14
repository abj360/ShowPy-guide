#!/usr/bin/env python3

"""
ch10_ex3.py --- reference answer to exercise 10.3: a pinned match

Contains:
    solve(): returns (max distance, crossings) with T1 pinned to slot 0
"""

from showpy.choreo.match import match
from showpy.choreo.models import MatchOptions
from showpy.examples import two_set_show


def solve() -> tuple[float, int]:
    """Returns (max distance, crossings) with T1 pinned to slot 0."""
    slots = [(6.0, 3.0), (4.0, 3.0), (2.0, 3.0), (0.0, 3.0)]
    result = match(two_set_show().set("1"), slots, options=MatchOptions(pinned={"T1": 0}))
    return result.max_distance, result.crossings
