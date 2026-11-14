#!/usr/bin/env python3

"""
ch02_ex3.py --- reference answer to exercise 2.3: edit a show without mutating it

Contains:
    solve(): returns a new show where T1 in set 2 stands 1 m further upstage
"""

from showpy.choreo.match_ops import with_set
from showpy.show.models import Show


def solve(show: Show) -> Show:
    """Returns a new show where T1 in set 2 stands 1 m further upstage."""
    second = show.set("2")
    y = second.get("T1").y
    return with_set(show, second.with_placements({"T1": {"y": y + 1.0}}))
