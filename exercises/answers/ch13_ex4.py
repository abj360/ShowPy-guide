#!/usr/bin/env python3

"""
ch13_ex4.py --- reference answer to exercise 13.4: an agent saves a form-built set

Contains:
    solve(): returns set 2 positions at the head and the paths the agent's save changed
"""

from datetime import UTC, datetime

from showpy.choreo.form_place import place
from showpy.choreo.forms import line_form
from showpy.choreo.match_ops import with_set
from showpy.examples import two_set_show
from showpy.show.changes import apply_change
from showpy.show.models import FormOp
from showpy.show.repositories import InMemoryRepository
from showpy.show.storage import load_show, open_workspace, save_show


def solve() -> tuple[list[list[float]], list[str]]:
    """Returns set 2 positions at the head and the paths the agent's save changed."""
    at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    repo = InMemoryRepository()
    save_show(open_workspace(repo, "demo"), two_set_show(), at)
    agent = open_workspace(repo, "demo")
    show = load_show(agent)
    row = line_form("row", ["T1", "T2", "T3", "T4"], (0.0, 12.0), (6.0, 12.0))
    placed, filled = place(show, "2", [row])
    show = apply_change(with_set(show, placed), [FormOp(form=f) for f in filled])
    revision = save_show(agent, show, at)
    positions: list[list[float]] = repo.get_show("demo").set("2").positions().tolist()
    return positions, sorted(revision.changed)
