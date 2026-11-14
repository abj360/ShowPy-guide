#!/usr/bin/env python3

"""
check_ch17_ex3.py --- checks exercise 17.3: docstring summaries

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 17.3."""
    got = solution.solve()
    expect(
        set(got)
        == {"min_gaps", "closest_approach", "suggest_delays", "suggest_waypoint", "apply_fix"},
        "five names",
    )
    expect(
        got["closest_approach"].startswith("Returns (time, distance)"), "first docstring line only"
    )


if __name__ == "__main__":
    run("ch17_ex3", check)
