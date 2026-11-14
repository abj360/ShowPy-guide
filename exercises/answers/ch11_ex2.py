#!/usr/bin/env python3

"""
ch11_ex2.py --- reference answer to exercise 11.2: an ease_out ripple

Contains:
    solve(): returns the starts of five spots rippled over 4 counts with ease_out
"""

from showpy.choreo.models import TransitionSpec
from showpy.choreo.paths import ripple


def solve() -> list[float]:
    """Returns the starts of five spots rippled over 4 counts with ease_out."""
    spec = ripple(TransitionSpec(id=("1", "2"), counts=8.0), list("ABCDE"), 4.0, "ease_out")
    return [spec.row(e).start for e in "ABCDE"]
