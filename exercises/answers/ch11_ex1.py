#!/usr/bin/env python3

"""
ch11_ex1.py --- reference answer to exercise 11.1: stagger from the end

Contains:
    solve(): returns the starts of T1-T4 staggered from the end by 1.5 counts
"""

from showpy.choreo.models import TransitionSpec
from showpy.choreo.paths import stagger


def solve() -> list[float]:
    """Returns the starts of T1-T4 staggered from the end by 1.5 counts."""
    ids = ["T1", "T2", "T3", "T4"]
    spec = stagger(TransitionSpec(id=("1", "2"), counts=8.0), ids, step=1.5, direction="end")
    return [spec.row(e).start for e in ids]
