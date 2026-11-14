#!/usr/bin/env python3

"""
ch12_ex3.py --- reference answer to exercise 12.3: when is T2 fastest

Contains:
    solve(): returns (local count, peak speed) of T2 delayed 4 counts
"""

from showpy.choreo.engine import PathEngine
from showpy.choreo.paths import delay
from showpy.examples import two_set_show


def solve() -> tuple[float, float]:
    """Returns (local count, peak speed) of T2 delayed 4 counts."""
    show = two_set_show()
    spec = delay(show.transition(("1", "2")), ["T2"], 4.0)
    engine = PathEngine(show.model_copy(update={"transitions": (spec,)}))
    segments = engine.entity_segments("T2", ("1", "2"))
    fastest = max(segments, key=lambda g: abs(g.p1[1] - g.p0[1]) / (g.t1 - g.t0))
    speed = abs(fastest.p1[1] - fastest.p0[1]) / (fastest.t1 - fastest.t0)
    return (fastest.t0 + fastest.t1) / 2, speed
