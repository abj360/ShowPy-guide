#!/usr/bin/env python3

"""
check_ch08_ex1.py --- checks exercise 8.1: a todo note on a transition

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from datetime import UTC, datetime
from types import ModuleType

from showpy.notes.notes import notes_for

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 8.1."""
    show = solution.solve()
    notes = notes_for(show, ("1", "2"))
    expect([n.id for n in notes] == ["t1"], "one note with id t1 on transition (1, 2)")
    expect(notes[0].kind == "todo" and notes[0].author == "pat", "kind todo, author pat")
    expect(notes[0].created_at == datetime(2026, 11, 11, 10, 0, tzinfo=UTC), "time 10:00 UTC")


if __name__ == "__main__":
    run("ch08_ex1", check)
