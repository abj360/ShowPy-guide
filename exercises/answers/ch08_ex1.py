#!/usr/bin/env python3

"""
ch08_ex1.py --- reference answer to exercise 8.1: a todo note on a transition

Contains:
    solve(): returns the example show with a todo note on transition 1 to 2
"""

from datetime import UTC, datetime

from showpy.examples import two_set_show
from showpy.notes.models import Anchor
from showpy.notes.notes import add_note
from showpy.show.models import Show


def solve() -> Show:
    """Returns the example show with a todo note on transition 1 to 2."""
    at = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
    return add_note(
        two_set_show(),
        "fix spacing",
        Anchor.on_transition(("1", "2")),
        "t1",
        at,
        "pat",
        kind="todo",
    )
