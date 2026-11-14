#!/usr/bin/env python3

"""
ch06_ex3.py --- reference answer to exercise 6.3: near a point, right to left

Contains:
    solve(): returns set 1 spots within 2.5 m of (3, 5), ordered right to left
"""

from showpy.cast.select import near, ordered_along
from showpy.examples import two_set_show
from showpy.geo.shapes import line


def solve() -> tuple[str, ...]:
    """Returns set 1 spots within 2.5 m of (3, 5), ordered right to left."""
    first = two_set_show().set("1")
    picked = near(first, (3.0, 5.0), 2.5)
    return ordered_along(first, picked, by=line((10.0, 5.0), (-10.0, 5.0))).ids
