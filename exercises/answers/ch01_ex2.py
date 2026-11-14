#!/usr/bin/env python3

"""
ch01_ex2.py --- reference answer to exercise 1.2: count spots, sets and stored transitions

Contains:
    solve(): returns (spots, sets, stored transitions) of the example show
"""

from showpy.examples import two_set_show


def solve() -> tuple[int, int, int]:
    """Returns (spots, sets, stored transitions) of the example show."""
    show = two_set_show()
    return len(show.cast.spots), len(show.sets), len(show.transitions)
