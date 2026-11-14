#!/usr/bin/env python3

"""
ch05_ex2.py --- reference answer to exercise 5.2: which count plays at 10 seconds

Contains:
    solve(): returns the count playing at 10 s in the 120 to 180 cpm ramp over 32 counts
"""

from showpy.time.clock import seconds_to_count
from showpy.time.models import TempoSection, Timeline, TimelineMode


def solve() -> float:
    """Returns the count playing at 10 s in the 120 to 180 cpm ramp over 32 counts."""
    ramp = TempoSection(at_count=0.0, counts_per_minute=120.0, ramp_to=180.0, ramp_counts=32.0)
    return seconds_to_count(Timeline(mode=TimelineMode.COUNTS, tempos=(ramp,)), 10.0)
