#!/usr/bin/env python3

"""
ch12_ex2.py --- reference answer to exercise 12.2: facing after the window

Contains:
    solve(): returns T1's facing at local count 6.75 in the facing example
"""

from showpy.choreo.engine import PathEngine
from showpy.choreo.models import FacingMode, PathRow
from showpy.examples import two_set_show, with_rows


def solve() -> float:
    """Returns T1's facing at local count 6.75 in the facing example."""
    row = PathRow(entity="T1", start=2.0, end=6.0, facing_mode=FacingMode.TRAVEL, turn_counts=1.5)
    base = two_set_show()
    target = base.sets[1].with_placements({"T1": {"x": 4.0, "facing": 270.0}})
    show = with_rows({"T1": row}, show=base.model_copy(update={"sets": (base.sets[0], target)}))
    return PathEngine(show).facing_at("T1", 6.75, local=("1", "2"))
