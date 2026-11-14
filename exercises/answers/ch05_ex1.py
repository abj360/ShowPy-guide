#!/usr/bin/env python3

"""
ch05_ex1.py --- reference answer to exercise 5.1: seconds with a hold

Contains:
    solve(): returns the seconds at count 64 at 144 cpm with a 2 s hold at count 32
"""

from showpy.time.clock import count_to_seconds
from showpy.time.models import Hold, TimelineMode
from showpy.time.timeline import add_hold, new_timeline


def solve() -> float:
    """Returns the seconds at count 64 at 144 cpm with a 2 s hold at count 32."""
    tl = add_hold(new_timeline(TimelineMode.COUNTS, 144.0), Hold(at_count=32.0, seconds=2.0))
    return count_to_seconds(tl, 64.0)
