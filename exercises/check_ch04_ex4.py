#!/usr/bin/env python3

"""
check_ch04_ex4.py --- checks exercise 4.4: center form of an SVG arc

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.geo.svg import ArcPiece, parse_path

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 4.4."""
    center, theta1, dtheta = solution.solve()
    expect(
        close(center, (2.0, 1.490712), 1e-5),
        f"center {center} is wrong",
    )
    expect(dtheta < -180.0, "sweep=0 with large-arc=1 means a negative sweep beyond -180°")
    piece = parse_path("M0 0 a3 2 0 1 0 4 0")[0].pieces[0]
    expect(isinstance(piece, ArcPiece), "the path's first piece should be an arc")
    assert isinstance(piece, ArcPiece)
    expect(close((theta1, dtheta), (piece.theta1_deg, piece.dtheta_deg), 1e-5), "angles differ")


if __name__ == "__main__":
    run("ch04_ex4", check)
