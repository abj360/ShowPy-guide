#!/usr/bin/env python3

"""
ch13_ex3.py --- reference answer to exercise 13.3: what a pin protects

Contains:
    solve(): returns locked_changes after force-moving pinned T2 in both sets
"""

from showpy.choreo.match_ops import with_set
from showpy.examples import two_set_show
from showpy.show.locks import locked_changes
from showpy.show.pinning import pin


def solve() -> list[str]:
    """Returns locked_changes after force-moving pinned T2 in both sets."""
    pinned = pin(two_set_show(), "entity", "T2", "soloist")
    moved = pinned
    for set_id in ("1", "2"):
        s = moved.set(set_id)
        moved = with_set(moved, s.with_placements({"T2": {"x": 9.0}}, force=True))
    return locked_changes(pinned, moved)
