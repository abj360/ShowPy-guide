#!/usr/bin/env python3

"""
ch13_ex1.py --- reference answer to exercise 13.1: insert a sub-set and renumber

Contains:
    solve(): returns (set ID, counts) pairs after inserting a sub-set and renumbering
"""

from showpy.examples import two_set_show
from showpy.show.manage import insert_subset, renumber


def solve() -> list[tuple[str, float]]:
    """Returns (set ID, counts) pairs after inserting a sub-set and renumbering."""
    show, _ = insert_subset(two_set_show(), "1", 3.0)
    show, _ = renumber(show)
    return [(s.id, s.counts) for s in show.sets]
