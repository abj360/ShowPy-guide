#!/usr/bin/env python3

"""
ch17_ex3.py --- reference answer to exercise 17.3: docstring summaries

Contains:
    solve(): returns the first docstring line of five avoid functions
"""

import showpy


def solve() -> dict[str, str]:
    """Returns the first docstring line of five avoid functions."""
    names = ("min_gaps", "closest_approach", "suggest_delays", "suggest_waypoint", "apply_fix")
    return {name: (getattr(showpy, name).__doc__ or "").strip().splitlines()[0] for name in names}
