#!/usr/bin/env python3

"""
ch09_ex3.py --- reference answer to exercise 9.3: place a set from an arc with open slots

Contains:
    solve(): returns the members of the placed arc in slot order
"""

from showpy.choreo.form_place import place
from showpy.choreo.forms import arc_form
from showpy.examples import two_set_show


def solve() -> tuple[str, ...]:
    """Returns the members of the placed arc in slot order."""
    form = arc_form("arc", [], (3.0, 3.0), 6.0, 150.0, -120.0, n=4)
    _, (filled,) = place(two_set_show(), "2", [form])
    return filled.members
