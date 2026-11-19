#!/usr/bin/env python3

"""
ch13_ex2.py --- reference answer to exercise 13.2: save twice and read back

Contains:
    solve(): returns (number of revisions, set 2 counts at the head)
"""

from datetime import UTC, datetime

from showpy.examples import two_set_show
from showpy.show.manage import set_counts
from showpy.show.repositories import InMemoryRepository
from showpy.show.storage import load_show, open_workspace, save_show


def solve() -> tuple[int, float]:
    """Returns (number of revisions, set 2 counts at the head)."""
    at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
    repo = InMemoryRepository()
    ws = open_workspace(repo, "demo")
    save_show(ws, two_set_show(), at)
    save_show(ws, set_counts(load_show(ws), "2", 12.0), at)
    return len(repo.revisions("demo")), repo.get_show("demo").set("2").counts
