#!/usr/bin/env python3

"""
check_ch11_ex3.py --- checks exercise 11.3: a motion that bulges and ends on target

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from showpy.choreo.engine import PathEngine
from showpy.choreo.paths import custom_path
from showpy.examples import two_set_show

from checklib import close, expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 11.3."""
    registry = solution.solve()
    expect("bulge" in registry.names(), "register the motion under the name bulge")
    spec = custom_path(two_set_show().transition(("1", "2")), ["T1"], "bulge", registry)
    show = two_set_show().model_copy(update={"transitions": (spec,)})
    engine = PathEngine(show, motions=registry)
    expect(close(engine.position("T1", 8.0), (0.0, 9.0)), "the move must end on target")
    expect(close(engine.position("T1", 4.0), (-1.0, 7.0), 0.02), "mid-move is 1 m left of (0, 7)")


if __name__ == "__main__":
    run("ch11_ex3", check)
