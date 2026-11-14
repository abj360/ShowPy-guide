#!/usr/bin/env python3

"""
ch07_ex1.py --- reference answer to exercise 7.1: read the college hash distance

Contains:
    solve(): returns the college front hash distance from the front sideline, in meters
"""

from showpy.sheet.bounds import landmark
from showpy.sheet.templates import get_sheet


def solve() -> float:
    """Returns the college front hash distance from the front sideline, in meters."""
    return float(landmark(get_sheet("sheet:college-football"), "front hash").geometry[0][1])
