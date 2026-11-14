#!/usr/bin/env python3

"""
check_ch05_ex4.py --- checks exercise 5.4: where the ramp reaches 150 cpm

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.time.clock import count_to_seconds
from showpy.time.models import TempoSection, Timeline, TimelineMode

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 5.4."""
    count, seconds = solution.solve()
    ramp = TempoSection(at_count=0.0, counts_per_minute=120.0, ramp_to=180.0, ramp_counts=32.0)
    tl = Timeline(mode=TimelineMode.COUNTS, tempos=(ramp,))
    expect(close(count, 16.0), "tempo is linear in counts: halfway through the ramp")
    expect(close(seconds, count_to_seconds(tl, 16.0)), "seconds = (60/k)·ln(150/120)")


if __name__ == "__main__":
    run("ch05_ex4", check)
