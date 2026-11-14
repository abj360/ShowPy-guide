#!/usr/bin/env python3

"""
ch06_ex2.py --- reference answer to exercise 6.2: add a group of flags entering at set 2

Contains:
    solve(): returns the example show with four flags entering in set 2
"""

from showpy.cast.models import Group
from showpy.cast.spots import add_group, add_spots_along
from showpy.examples import two_set_show
from showpy.geo.shapes import line
from showpy.show.models import Show


def solve() -> Show:
    """Returns the example show with four flags entering in set 2."""
    show = add_group(two_set_show(), Group(key="flags", label_prefix="F"))
    return add_spots_along(show, line((-3.0, 12.0), (3.0, 12.0)), 4, "flags", "2")
