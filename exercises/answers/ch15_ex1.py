#!/usr/bin/env python3

"""
ch15_ex1.py --- reference answer to exercise 15.1: when T8 moves

Contains:
    solve(): returns the global counts where T8 starts moving and arrives
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))

from t05_paths import build_tutorial_show


def solve() -> tuple[float, float]:
    """Returns the global counts where T8 starts moving and arrives."""
    show = build_tutorial_show()
    start, end = show.transition(("1", "2")).row("T8").window(16.0)
    return start, end
