#!/usr/bin/env python3

"""
ch01_ex1.py --- reference answer to exercise 1.1: find where PathEngine lives

Contains:
    solve(): returns the dotted module name that defines PathEngine
"""

import showpy


def solve() -> str:
    """Returns the dotted module name that defines PathEngine."""
    return str(showpy.PathEngine.__module__)
