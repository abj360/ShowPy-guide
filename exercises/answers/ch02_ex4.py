#!/usr/bin/env python3

"""
ch02_ex4.py --- reference answer to exercise 2.4: reproducible scatter

Contains:
    solve(): returns 12 points scattered in (0, 0)-(12, 8) at least 1.5 m apart
"""

from showpy.core.types import Points
from showpy.geo.regions import region
from showpy.geo.spacing import scatter


def solve(seed: int) -> Points:
    """Returns 12 points scattered in (0, 0)-(12, 8) at least 1.5 m apart."""
    area = region([(0, 0), (12, 0), (12, 8), (0, 8)])
    return scatter(area, 12, 1.5, seed=seed)
