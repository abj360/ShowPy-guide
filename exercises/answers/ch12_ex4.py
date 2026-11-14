#!/usr/bin/env python3

"""
ch12_ex4.py --- reference answer to exercise 12.4: closest approach from segments

Contains:
    solve(): returns (tau, center distance) of the closest approach of T1 and T2
"""

import numpy as np
from showpy.choreo.engine import PathEngine
from showpy.examples import crossing_show


def solve() -> tuple[float, float]:
    """Returns (tau, center distance) of the closest approach of T1 and T2."""
    engine = PathEngine(crossing_show())
    tracks = []
    for entity in ("T1", "T2"):
        segs = engine.entity_segments(entity, ("1", "2"))
        times = [segs[0].t0, *(g.t1 for g in segs)]
        points = np.array([segs[0].p0, *(g.p1 for g in segs)])
        tracks.append((times, points))
    merged = np.unique(np.concatenate([tracks[0][0], tracks[1][0]]))
    a = np.stack([np.interp(merged, tracks[0][0], tracks[0][1][:, k]) for k in (0, 1)], axis=1)
    b = np.stack([np.interp(merged, tracks[1][0], tracks[1][1][:, k]) for k in (0, 1)], axis=1)
    best = (0.0, float("inf"))
    for i in range(len(merged) - 1):
        d0, w = a[i] - b[i], (a[i + 1] - b[i + 1]) - (a[i] - b[i])
        ww = float(w @ w)
        s = 0.0 if ww == 0 else min(max(-float(d0 @ w) / ww, 0.0), 1.0)
        dist = float(np.linalg.norm(d0 + s * w))
        if dist < best[1]:
            best = (float(merged[i] + s * (merged[i + 1] - merged[i])), dist)
    return best
