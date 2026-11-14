#!/usr/bin/env python3

"""
ch03_ex1.py --- reference answer to exercise 3.1: compact IDs into ranges

Contains:
    solve(): returns the compact range text of T1-T6 without T4, plus B1 and B2
"""

from showpy.core.util import format_ranges


def solve() -> str:
    """Returns the compact range text of T1-T6 without T4, plus B1 and B2."""
    ids = ["T6", "B2", "T1", "T3", "B1", "T2", "T5"]
    return format_ranges(ids)
