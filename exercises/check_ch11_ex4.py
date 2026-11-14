#!/usr/bin/env python3

"""
check_ch11_ex4.py --- checks exercise 11.4: a rotation that compiles

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.choreo.engine import PathEngine

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 11.4."""
    show = solution.solve()
    row = show.transition(("1", "2")).row("T1")
    expect(row.style.value == "rotate" and close(row.sweep_deg, -90.0), "a -90° rotate row")
    engine = PathEngine(show)
    engine.compile(("1", "2"))
    expect(
        close(engine.position("T1", 4.0), (4 - 4 * 0.5**0.5, 5 + 4 * 0.5**0.5)), "midway on the arc"
    )


if __name__ == "__main__":
    run("ch11_ex4", check)
