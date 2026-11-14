#!/usr/bin/env python3

"""
ch17_ex2.py --- reference answer to exercise 17.2: search the public API

Contains:
    solve(): returns the sorted public names that contain `note`
"""

import showpy


def solve() -> list[str]:
    """Returns the sorted public names that contain `note`."""
    return sorted(name for name in showpy.__all__ if "note" in name)
