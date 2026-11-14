#!/usr/bin/env python3

"""
check_ch04_ex1.py --- checks exercise 4.1: space 9 spots on a 20 m arc

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

import math
from types import ModuleType

import numpy as np

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 4.1."""
    pts = np.asarray(solution.solve(), dtype=float)
    expect(pts.shape == (9, 2), "return nine (x, y) rows")
    expect(
        close(np.linalg.norm(pts, axis=1), np.full(9, 20.0)),
        "spots must be 20 m from (0, 0)",
    )
    angles = np.degrees(np.arctan2(pts[:, 1], pts[:, 0]))
    expect(close(angles, np.linspace(60.0, 120.0, 9), 1e-6), "spots should run from 60° to 120°")
    expect(
        close(20.0 * np.radians(np.diff(angles)), np.full(8, 20.0 * (math.pi / 3) / 8)),
        "arc gaps differ",
    )


if __name__ == "__main__":
    run("ch04_ex1", check)
