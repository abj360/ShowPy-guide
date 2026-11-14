#!/usr/bin/env python3

"""
ch05_ex3.py --- reference answer to exercise 5.3: label a count with its measure

Contains:
    solve(): returns (measure, count in measure) of count 50
"""

from showpy.time.measures import count_to_measure
from showpy.time.models import MeasureSetting, TimelineMode
from showpy.time.timeline import new_timeline, set_measures


def solve() -> tuple[int, float]:
    """Returns (measure, count in measure) of count 50."""
    setting = MeasureSetting(counts_per_measure=4.0, changes=((32.0, 3.0),))
    label = count_to_measure(set_measures(new_timeline(TimelineMode.COUNTS, 120.0), setting), 50.0)
    assert label is not None
    return label.measure, label.count_in_measure
