#!/usr/bin/env python3

"""
ch15_ex3.py --- reference answer to exercise 15.3: a center-out stagger

Contains:
    solve(): returns the tightest gap of 1→2 with a center-out stagger
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))

from showpy.choreo.avoid import min_gaps
from showpy.choreo.paths import delay, set_easing
from showpy.show.changes import store_paths
from showpy.show.models import PathsOp

from t05_paths import build_tutorial_show


def solve() -> float:
    """Returns the tightest gap of 1→2 with a center-out stagger."""
    show = build_tutorial_show()
    spec = show.transition(("1", "2"))
    ids = [f"T{i}" for i in range(1, 9)]
    spec = spec.model_copy(update={"rows": {k: v for k, v in spec.rows.items() if k not in ids}})
    for step, pair in enumerate((("T4", "T5"), ("T3", "T6"), ("T2", "T7"), ("T1", "T8"))):
        if step:
            spec = delay(spec, list(pair), float(step))
    spec = set_easing(spec, ids, "ease_in_out")
    show = store_paths(show, PathsOp(spec=spec))
    return min_gaps(show, ("1", "2"), top=1)[0].gap
