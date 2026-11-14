# showpy.notes: design notes

Designers and the agent leave notes for rehearsal and for each other: "block locks in on
count 16", "watch T4 and T5 here". `showpy.notes` stores them on the show, finds them by set,
transition or place, and lets the designer accept notes the agent drafted.

## The data: models.py

An **anchor** says what a note is attached to. It is a tagged model, not an untagged union
of a string, a tuple or a polygon, because an untagged union cannot be read back from JSON
without guessing (ADR 0001 fix 19). An `Anchor` has a `kind` and exactly one payload field:

| `kind`       | Payload field       | Constructor                        |
| ------------ | ------------------- | ---------------------------------- |
| `set`        | `set_id`            | `Anchor.on_set("2")`               |
| `transition` | `tid`               | `Anchor.on_transition(("1", "2"))` |
| `point`      | `point`             | `Anchor.at_point((0.0, 12.0))`     |
| `area`       | `area` (a `Region`) | `Anchor.on_area(region)`           |
| `spots`      | `spots`             | `Anchor.on_spots(["T4", "T5"])`    |

A `Note` has `id`, `text`, `kind` (`goal`, `idea`, `todo`, `warning`), `anchor`, `author`,
`created_at` and `visible`. A hidden note (`visible=False`) is a draft: it waits for the
designer to accept it.

```pycon
>>> from showpy.notes.models import Anchor
>>> Anchor.on_spots(["T4", "T5"])
Anchor(kind='spots', set_id=None, tid=None, point=None, area=None, spots=('T4', 'T5'))
>>> Anchor(kind="set", set_id="2", point=(0.0, 0.0))
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: set anchor needs only set_id (hint: use the Anchor.on_* constructors)
```

## Working with notes: notes.py

| Function                                                         | Does                                                                  |
| ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| `add_note(show, text, anchor, note_id, at, author, kind="idea")` | adds a note; ID and time are explicit, so the result is deterministic |
| `edit_note(show, note_id, **changes)`                            | changes fields; the ID is fixed                                       |
| `remove_note(show, note_id)`                                     | removes a note                                                        |
| `notes_for(show, target, include_hidden=False)`                  | notes on a set (an ID) or a transition (a pair)                       |
| `notes_near(show, p, radius, set_id=None, include_hidden=False)` | notes at or around a point                                            |
| `accept_draft(show, draft)`                                      | adds a hidden draft note to the show, visible                         |

`notes_near` matches by geometry: point anchors by distance, area anchors by distance to the
area, and spot anchors when any anchored spot's on-field placement (in any set, or only in
`set_id`) is within the radius.

`add_note` checks that the anchor's set, transition or spots exist, so a note can never point
at nothing.

```pycon
>>> from datetime import UTC, datetime
>>> from showpy.examples import two_set_show
>>> from showpy.notes.notes import add_note, notes_for, notes_near
>>> at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
>>> show = add_note(two_set_show(), "go big", Anchor.on_set("2"), "n1", at, "pat", kind="goal")
>>> show = add_note(show, "lead here", Anchor.on_spots(["T1"]), "n2", at, "pat")
>>> [n.text for n in notes_for(show, "2")], [n.id for n in notes_near(show, (0.0, 9.0), 0.5)]
(['go big'], ['n2'])
>>> add_note(show, "x", Anchor.on_set("9"), "n3", at, "pat")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown set '9' (hint: known sets: 1, 2)
>>> add_note(show, "dup", Anchor.on_set("1"), "n1", at, "pat")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: note 'n1' already exists (hint: pick a new note id, or use edit_note)
```

`T1` stands at `(0, 9)` in set 2, so the note anchored to it is found near that point.

### Accepting drafted notes

The agent proposes notes as plain `Note`s with `author="agent"` and `visible=False`. They are
**not** on the show yet: the designer accepts them one by one with `accept_draft`, which adds
the note and makes it visible. The library never calls a model itself.

```pycon
>>> from showpy.notes.models import Note
>>> from showpy.notes.notes import accept_draft
>>> draft = Note(
...     id="draft-1",
...     text="calm opener",
...     kind="goal",
...     anchor=Anchor.on_set("1"),
...     author="agent",
...     created_at=at,
...     visible=False,
... )
>>> accepted = accept_draft(show, draft)
>>> [(n.id, n.author, n.visible) for n in accepted.notes], len(show.notes)
([('n1', 'pat', True), ('n2', 'pat', True), ('draft-1', 'agent', True)], 2)
```

> **Check your understanding 8.a.** Why must a note's `created_at` be passed in rather than
> read from the clock?

## Exercises

**Exercise 8.1 (warm-up).** Add a `todo` note "fix spacing" on transition `1→2` of
`two_set_show()` with ID `t1`, author `pat`, at 2026-11-11 10:00 UTC. Return the show.

**Exercise 8.2.** Add a point note at `(5, 7)` and return the IDs of notes within 1 m of
`(5.5, 7.5)` and within 0.5 m (as two lists).

**Exercise 8.3 (harder).** Add set `3` (8 counts) to `two_set_show()`. Draft one hidden
`warning` note per transition by hand, with IDs `draft-1`, `draft-2`, ..., text "check
spacing", author `agent` and time 2026-11-11 10:00 UTC. Accept only the draft on transition
`2→3` and return the show.
