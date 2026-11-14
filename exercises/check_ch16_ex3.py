#!/usr/bin/env python3

"""
check_ch16_ex3.py --- checks exercise 16.3: a falsifying curve

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

import numpy as np
from showpy.geo.spacing import space_along

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 16.3."""
    curve, n = solution.solve()
    pts = space_along(curve, n)
    chords = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    expect(float(chords.max() - chords.min()) > 0.01, "chords are equal; pick a curvier curve")


if __name__ == "__main__":
    run("ch16_ex3", check)
