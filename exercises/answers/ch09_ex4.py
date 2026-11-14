#!/usr/bin/env python3

"""
ch09_ex4.py --- reference answer to exercise 9.4: recognize an uneven arc

Contains:
    solve(): returns (kind, center, radius, sweep) of the detected form
"""

import numpy as np
from showpy.choreo.form_fit import detect_form


def solve() -> tuple[str, tuple[float, float], float, float]:
    """Returns (kind, center, radius, sweep) of the detected form."""
    a = np.radians([0.0, 50.0, 95.0, 160.0, 200.0])
    pts = np.stack([1.0 + 7.0 * np.cos(a), 2.0 + 7.0 * np.sin(a)], axis=1)
    form = detect_form(pts)
    curve = form.geometry["curve"]
    return form.kind, tuple(curve["center"]), curve["radius"], curve["sweep_deg"]
