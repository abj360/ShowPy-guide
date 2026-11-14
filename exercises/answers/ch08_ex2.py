#!/usr/bin/env python3

"""
ch08_ex2.py --- reference answer to exercise 8.2: notes near a point

Contains:
    solve(): returns note IDs within 1 m and within 0.5 m of (5.5, 7.5)
"""

from datetime import UTC, datetime

from showpy.examples import two_set_show
from showpy.notes.models import Anchor
from showpy.notes.notes import add_note, notes_near


def solve() -> tuple[list[str], list[str]]:
    """Returns note IDs within 1 m and within 0.5 m of (5.5, 7.5)."""
    at = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
    show = add_note(two_set_show(), "look", Anchor.at_point((5.0, 7.0)), "p1", at, "pat")
    near = [n.id for n in notes_near(show, (5.5, 7.5), 1.0)]
    return near, [n.id for n in notes_near(show, (5.5, 7.5), 0.5)]
