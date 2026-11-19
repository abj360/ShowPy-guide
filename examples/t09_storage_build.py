#!/usr/bin/env python3

"""
t09_storage_build.py --- tutorial step 9: saves the show, meets a conflict, saves a wider set 3

ShowPy records what changed and when. Who made a change and why is the host's record, kept here
in a plain dictionary keyed by revision ID.

Contains:
    widen_arc(): returns the show with set 3's arc form widened and its set placed again
    main(): saves, edits from two workspaces, saves the wider set 3 and lists the history
"""

import tempfile
from datetime import UTC, datetime, timedelta

from showpy.choreo.form_ops import edit
from showpy.choreo.form_place import place
from showpy.choreo.match_ops import with_set
from showpy.core.errors import ConflictError
from showpy.show.changes import apply_change
from showpy.show.file_repository import FileRepository
from showpy.show.history import changelog
from showpy.show.manage import set_counts
from showpy.show.models import FormOp, Show
from showpy.show.storage import load_show, open_workspace, save_show
from showpy.show.validate import validate_show

from t05_paths import build_tutorial_show
from t08_notes_validate import add_notes

SHOW_ID = "opener"
START = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)
WIDER_RADIUS = 16.0


def minutes(n: int) -> datetime:
    """Returns the tutorial start time plus n minutes."""
    return START + timedelta(minutes=n)


def widen_arc(show: Show) -> Show:
    """Returns the show with set 3's arc form widened and its set placed again from it."""
    wider = edit(show.forms["arc"], radius=WIDER_RADIUS)
    placed, stored = place(show, "3", [wider])
    return apply_change(with_set(show, placed), [FormOp(form=f) for f in stored])


def main() -> None:
    """Runs the storage workflow against a file repository in a temporary folder."""
    authors: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as folder:
        repo = FileRepository(folder)
        designer = open_workspace(repo, SHOW_ID)
        first = save_show(designer, add_notes(build_tutorial_show()), minutes(0))
        authors[first.id] = "designer: create opener"
        print("saved revision", first.id[:7], "with", len(first.changed), "documents")

        agent = open_workspace(repo, SHOW_ID)
        slower = set_counts(load_show(designer), "3", 24.0, rescale=True)
        retimed = save_show(designer, slower, minutes(1))
        authors[retimed.id] = "designer: slow the arc to 24 counts"
        try:
            save_show(agent, load_show(agent), minutes(2))
        except ConflictError as error:
            print("conflict:", error.message)
            print("hint:", error.hint)
        agent.refresh()
        print(
            "agent now reads", agent.revision[:7], "set 3 counts", load_show(agent).set("3").counts
        )

        wider = widen_arc(load_show(agent))
        print("valid before saving:", validate_show(wider).ok)
        revision = save_show(agent, wider, minutes(3))
        authors[revision.id] = "agent: widen the arc to 16 m"
        print("agent saved", revision.id[:7], "changing", list(revision.changed))
        saved = load_show(agent)
        t1 = saved.set("3").get("T1")
        print(
            f"T1 now at ({t1.x:.3f}, {t1.y:.3f}), form radius",
            saved.forms["arc"].geometry["curve"]["radius"],
        )
        print(changelog(agent, first.id))
        for stored in repo.revisions(SHOW_ID):
            print("host record:", stored.id[:7], authors[stored.id])


if __name__ == "__main__":
    main()
