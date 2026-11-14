#!/usr/bin/env python3

"""
ch16_ex2.py --- reference answer to exercise 16.2: a round-trip property for the clock

Contains:
    solve(): returns a Hypothesis test that the clock round-trips through a ramp
"""

from collections.abc import Callable

from hypothesis import given, settings
from hypothesis import strategies as st
from showpy.time.clock import count_to_seconds, seconds_to_count
from showpy.time.models import TempoSection, Timeline, TimelineMode


def solve() -> Callable[[], None]:
    """Returns a Hypothesis test that the clock round-trips through a ramp."""
    ramp = TempoSection(at_count=0.0, counts_per_minute=120.0, ramp_to=180.0, ramp_counts=32.0)
    tl = Timeline(mode=TimelineMode.COUNTS, tempos=(ramp,))

    @settings(max_examples=200, database=None)
    @given(st.floats(0.0, 64.0))
    def test_round_trip(c: float) -> None:
        """States that seconds_to_count inverts count_to_seconds."""
        assert abs(seconds_to_count(tl, count_to_seconds(tl, c)) - c) <= 1e-9

    return test_round_trip
