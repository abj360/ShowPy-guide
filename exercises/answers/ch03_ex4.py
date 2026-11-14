#!/usr/bin/env python3

"""
ch03_ex4.py --- reference answer to exercise 3.4: turn a placement without mutating it

Contains:
    solve(): returns the placement turned 90 degrees counter-clockwise, wrapped into [0, 360)
"""

from showpy.choreo.models import Placement
from showpy.core.units import normalize_angle


def solve(placement: Placement) -> Placement:
    """Returns the placement turned 90 degrees counter-clockwise, wrapped into [0, 360)."""
    return placement.model_copy(update={"facing": normalize_angle(placement.facing + 90.0)})
