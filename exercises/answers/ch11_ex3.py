#!/usr/bin/env python3

"""
ch11_ex3.py --- reference answer to exercise 11.3: a motion that bulges and ends on target

Contains:
    solve(): returns DEFAULT_MOTIONS extended with a `bulge` motion
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
from showpy.choreo.motion import DEFAULT_MOTIONS, MotionRegistry, register_motion
from showpy.core.types import Point, Points


def solve() -> MotionRegistry:
    """Returns DEFAULT_MOTIONS extended with a `bulge` motion."""

    # Any: motion parameters are JSON values chosen by each motion.
    def bulge(u: np.ndarray, start: Point, end: Point, params: Mapping[str, Any]) -> Points:
        """Moves along the chord with a sine bulge 1 m to the left at mid-move."""
        a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
        chord = b - a
        left = np.array([-chord[1], chord[0]]) / max(float(np.linalg.norm(chord)), 1e-12)
        result: Points = a + np.outer(u, chord) + np.outer(np.sin(np.pi * u), left)
        return result

    return register_motion(DEFAULT_MOTIONS, "bulge", bulge)
