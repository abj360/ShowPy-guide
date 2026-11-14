#!/usr/bin/env python3

"""
ch14_ex2.py --- reference answer to exercise 14.2: one frame row from the CSV

Contains:
    solve(): returns the CSV row of T4 at count 4 sampled at 2 per count
"""

from showpy.examples import two_set_show
from showpy.export.data import export_frames_csv


def solve() -> list[str]:
    """Returns the CSV row of T4 at count 4 sampled at 2 per count."""
    for line in export_frames_csv(two_set_show(), per_count=2).splitlines():
        cells = line.split(",")
        if cells[0] == "4" and cells[2] == "T4":
            return cells
    return []
