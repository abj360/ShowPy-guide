#!/usr/bin/env python3

"""
ch15_ex2.py --- reference answer to exercise 15.2: where the flags end

Contains:
    solve(): returns F1-F4 in set 3, rounded to 3 decimals
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))

from t05_paths import build_tutorial_show


def solve() -> list[tuple[float, float]]:
    """Returns F1-F4 in set 3, rounded to 3 decimals."""
    third = build_tutorial_show().set("3")
    return [(round(third.get(f).x, 3), round(third.get(f).y, 3)) for f in ("F1", "F2", "F3", "F4")]
