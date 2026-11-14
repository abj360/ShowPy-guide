#!/usr/bin/env python3

"""
ch16_ex1.py --- reference answer to exercise 16.1: a property for normalize_angle

Contains:
    solve(): returns a Hypothesis test that normalize_angle lands in [0, 360)
"""

from collections.abc import Callable

from hypothesis import given, settings
from hypothesis import strategies as st
from showpy.core.units import normalize_angle


def solve() -> Callable[[], None]:
    """Returns a Hypothesis test that normalize_angle lands in [0, 360)."""

    @settings(max_examples=200, database=None)
    @given(st.floats(-1e6, 1e6))
    def test_range(a: float) -> None:
        """States that normalize_angle lands in [0, 360)."""
        assert 0.0 <= normalize_angle(a) < 360.0

    return test_range
