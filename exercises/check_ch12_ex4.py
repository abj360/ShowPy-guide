#!/usr/bin/env python3

"""
check_ch12_ex4.py --- checks exercise 12.4: closest approach from segments

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.choreo.avoid import min_gaps
from showpy.examples import crossing_show

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 12.4."""
    tau, dist = solution.solve()
    gap = min_gaps(crossing_show(), ("1", "2"), sel=["T1", "T2"], top=1)[0]
    expect(close(tau, gap.tau, 1e-6), f"min_gaps finds tau {gap.tau}")
    expect(close(dist, gap.gap + 0.6, 1e-6), "gap = distance - 0.3 - 0.3")


if __name__ == "__main__":
    run("ch12_ex4", check)
