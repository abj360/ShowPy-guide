#!/usr/bin/env python3

"""
ch08_ex3.py --- reference answer to exercise 8.3: hidden drafts, one accepted

Contains:
    solve(): drafts one hidden warning per transition and accepts only the one on 2→3
"""

from datetime import UTC, datetime

from showpy.examples import two_set_show
from showpy.notes.models import Anchor, Note
from showpy.notes.notes import accept_draft
from showpy.show.manage import add_set
from showpy.show.models import Show


def solve() -> Show:
    """Drafts one hidden warning per transition and accepts only the one on 2→3."""
    at = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
    show = add_set(two_set_show(), "3", 8.0)
    drafts = [
        Note(
            id=f"draft-{n}",
            text="check spacing",
            kind="warning",
            anchor=Anchor.on_transition(tid),
            author="agent",
            created_at=at,
            visible=False,
        )
        for n, tid in enumerate(show.transition_ids(), start=1)
    ]
    chosen = next(d for d in drafts if d.anchor.tid == ("2", "3"))
    return accept_draft(show, chosen)
