#!/usr/bin/env python3

"""
check_ch12_ex1.py --- checks exercise 12.1: a position by hand

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.choreo.engine import PathEngine
from showpy.choreo.models import Easing, PathRow, PathStyle, Waypoint
from showpy.examples import with_rows

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 12.1."""
    row = PathRow(
        entity="T1",
        style=PathStyle.POLYLINE,
        start=1.0,
        end=7.0,
        waypoints=(Waypoint(x=3.0, y=5.0, at=3.0),),
        easing=Easing(kind="ease_in_out", strength=2.0),
    )
    want = PathEngine(with_rows({"T1": row})).position("T1", 4.0)
    expect(close(solution.solve(), want), f"the engine says {want.tolist()}")


if __name__ == "__main__":
    run("ch12_ex1", check)
