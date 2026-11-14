#!/usr/bin/env python3

"""
ch06_ex1.py --- reference answer to exercise 6.1: select with a group and a difference

Contains:
    solve(): returns every trumpet except T2 and T3, from one expression
"""

from showpy.cast.select import select
from showpy.examples import two_set_show


def solve() -> tuple[str, ...]:
    """Returns every trumpet except T2 and T3, from one expression."""
    return select(two_set_show(), "group:trumpets - (T2 + T3)").ids
