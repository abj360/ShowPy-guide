#!/usr/bin/env python3

"""
ch04_ex4.py --- reference answer to exercise 4.4: center form of an SVG arc

Contains:
    solve(): returns (center, theta1, dtheta) of the arc in `M0 0 a3 2 0 1 0 4 0`
"""

from showpy.geo.svg import ArcPiece, parse_path


def solve() -> tuple[tuple[float, float], float, float]:
    """Returns (center, theta1, dtheta) of the arc in `M0 0 a3 2 0 1 0 4 0`."""
    piece = parse_path("M0 0 a3 2 0 1 0 4 0")[0].pieces[0]
    if not isinstance(piece, ArcPiece):
        raise TypeError(f"expected an ArcPiece, got {type(piece).__name__}")
    center = (round(piece.center[0], 6), round(piece.center[1], 6))
    return center, round(piece.theta1_deg, 6), round(piece.dtheta_deg, 6)
