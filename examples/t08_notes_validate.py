#!/usr/bin/env python3

"""
t08_notes_validate.py --- tutorial step 8: adds design notes and validates the whole show

Contains:
    add_notes(): attaches a goal to set 2 and a warning to two trumpets
    main(): prints the notes found by set and by place, then the validation report
"""

from datetime import UTC, datetime

from showpy.notes.models import Anchor
from showpy.notes.notes import add_note, notes_for, notes_near
from showpy.show.models import Show
from showpy.show.validate import validate_show

from t05_paths import build_tutorial_show

WRITTEN_AT = datetime(2026, 11, 11, 9, 30, tzinfo=UTC)


def add_notes(show: Show) -> Show:
    """Adds a goal on set 2 and a warning anchored to T4 and T5."""
    show = add_note(
        show,
        "Block locks in on count 16",
        Anchor.on_set("2"),
        "n1",
        WRITTEN_AT,
        "designer",
        kind="goal",
    )
    return add_note(
        show,
        "T4 and T5 cross during the stagger",
        Anchor.on_spots(["T4", "T5"]),
        "n2",
        WRITTEN_AT,
        "agent",
        kind="warning",
    )


def main() -> None:
    """Looks notes up by set and by position, then validates the show."""
    show = add_notes(build_tutorial_show())
    print("notes on set 2:", [n.text for n in notes_for(show, "2")])
    near = notes_near(show, (0.0, 12.0), radius=2.0, set_id="1")
    print("notes near (0, 12) in set 1:", [(n.id, n.kind, n.author) for n in near])
    report = validate_show(show)
    print("valid:", report.ok, "issues:", len(report.issues))
    for issue in report.issues:
        print(f"  {issue.level} {issue.code} at {issue.where}: {issue.message}")


if __name__ == "__main__":
    main()
