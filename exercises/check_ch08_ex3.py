#!/usr/bin/env python3

"""
check_ch08_ex3.py --- checks exercise 8.3: hidden drafts, one accepted

Contains:
    check(): tests the solution and raises WrongAnswerError with a hint
"""

from types import ModuleType

from checklib import expect, run


def check(solution: ModuleType) -> None:
    """Tests the solution to exercise 8.3."""
    show = solution.solve()
    expect(len(show.set_ids()) == 3, "add set 3 first, so the show has two transitions")
    expect(len(show.notes) == 1, "only the accepted draft belongs on the show")
    note = show.notes[0]
    expect(note.id == "draft-2", f"the draft on 2→3 is the second one, draft-2; got {note.id}")
    expect(note.anchor.tid == ("2", "3"), "accept the draft anchored on transition 2→3")
    expect(note.kind == "warning" and note.author == "agent", "drafts are agent warnings")
    expect(note.visible, "accept_draft makes the note visible")


if __name__ == "__main__":
    run("ch08_ex3", check)
