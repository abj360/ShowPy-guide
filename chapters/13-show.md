# showpy.show: the show, its storage and its history

`showpy.show` holds the `Show` aggregate and everything that manages a whole show: adding and
retiming sets, splitting a show into movements, storing it as versioned documents, reverting to
earlier revisions, live collaboration, pins and validation. Who saved a revision, why, and who
may write at all are the host application's records and rules, not the library's.

## The Show and its index: models.py

A `Show` holds `id`, `title`, `pack`, `sheet`, `coordinates`, `notes`, `cast`, `timeline`,
`sets` (in show order), `forms` (form ID to form, across all sets), `transitions` (stored,
sparse), `facing_overrides`, `zones` (show-specific, on top of the sheet's), `dependencies`
(sheet reference to pinned version), `pins` and `revision` (the storage revision it was
loaded at).

| Method                                                 | Returns                                              |
| ------------------------------------------------------ | ---------------------------------------------------- |
| `show.set(id)`, `show.set_index(id)`, `show.set_ids()` | a set, its position, all IDs                         |
| `show.transition_ids()`                                | consecutive set pairs                                |
| `show.transition(tid)`                                 | the stored spec, or an empty one (everyone straight) |

`ShowIndex` answers "where are we at count `c`?". Count `c` is **at** set `s` when it equals
`s`'s start count, and **in** transition `(a, b)` when `start(a) < c < start(b)`. Exactly one
holds on `[0, total]`. `showpy.show.manage.index(show)` builds it, with each set's start
count, measure label and seconds.

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.show.manage import add_set, index, set_at_count, transition_at_count
>>> show = add_set(two_set_show(), "3", 4.0)
>>> [(e.set, e.start_count, e.seconds) for e in index(show).entries]
[('1', 0.0, 0.0), ('2', 8.0, 4.0), ('3', 12.0, 6.0)]
>>> set_at_count(show, 8.0), set_at_count(show, 9.0), transition_at_count(show, 9.0)
('2', None, (('2', '3'), 1.0))
>>> show.transition(("2", "3")).rows, show.transition(("1", "3"))
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: 1→3 is not a transition between consecutive sets (hint: use a pair from show.transition_ids())
```

## Managing sets: manage.py, sections.py, counts.py

| Function                                                        | Does                                                                                          |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `new_show(show_id, title, sheet, timeline, cast=None, pack="")` | one 0-count set `1` with every spot off the field at the front-center; pins the sheet version |
| `add_set(show, set_id, counts, after=None, placements=None)`    | inserts a set; spots without a given placement copy the previous one (not its form)           |
| `insert_subset(show, after, counts)`                            | inserts `12A` after `12`, taking its counts from the next set, so the total time stays        |
| `remove_set(show, set_id, merge_counts=True)`                   | deletes a set, its forms, pins and paths; merging keeps the total time                        |
| `set_counts(show, set_id, counts, rescale=False)`               | retimes a set and its incoming transition; `rescale` scales stored windows                    |
| `renumber(show)`                                                | renames sets 1..N, rewriting every reference; returns the mapping                             |
| `transitions(show)`                                             | consecutive pairs                                                                             |
| `index`, `set_at_count`, `transition_at_count`                  | the clock lookups above                                                                       |
| `upgrade_dependency(show, ref, version, sheet=None)`            | pins a newer sheet version                                                                    |
| `split_section(show, at)` / `join_sections(a, b)`               | split a show into movements and join them back                                                |
| `spot_counts(show)`                                             | on- and off-field counts per set, for the set strip                                           |

`set_counts` keeps ADR 0001 fix 16: the destination set's counts are the transition's
counts. With `rescale=True` stored windows, waypoint times and route windows scale in
proportion; without it, a stored window that no longer fits raises `PathError`.

`split_section(show, at)` gives two shows that both hold set `at`. The second one starts its
clock there: tempos, holds, markers, measures, audio sync, overrides and zone windows shift so
its count 0 is `at`. `join_sections` reverses it.

```pycon
>>> from showpy.show.manage import insert_subset, remove_set, renumber, set_counts
>>> from showpy.show.sections import join_sections, split_section
>>> sub, new_id = insert_subset(show, "1", 3.0)
>>> new_id, [(s.id, s.counts) for s in sub.sets]
('1A', [('1', 0.0), ('1A', 3.0), ('2', 5.0), ('3', 4.0)])
>>> renumber(sub)[1]
{'1': '1', '1A': '2', '2': '3', '3': '4'}
>>> [s.counts for s in remove_set(show, "2").sets]
[0.0, 12.0]
>>> first, second = split_section(show, "2")
>>> first.set_ids(), second.set_ids(), second.sets[0].counts
(['1', '2'], ['2', '3'], 0.0)
>>> joined = join_sections(first, second)
>>> joined.sets == show.sets, joined == show
(True, True)
>>> [(t.at_count, t.counts_per_minute) for t in joined.timeline.tempos]
[(0.0, 120.0)]
>>> set_counts(show, "1", 4.0)
Traceback (most recent call last):
  ...
showpy.core.errors.TimeRangeError: TIME_RANGE: the first set has counts 4.0 (hint: the first set starts the show; give it 0 counts)
```

## Change ops, pins and locks: changes.py, pinning.py, locks.py

Live editing works with small **ops**: `PlacementOp(set_id, placement)`, `FormOp(form)`,
`PathsOp(spec)` and `CountsOp(set_id, counts, rescale)`. `apply_change(show, ops,
force=False)` applies them in order, then refuses the result if it touches anything pinned.
`store_paths(show, PathsOp(spec))` stores a transition's paths in show order and drops a spec
that is all defaults.

`pin(show, target, pin_id, reason, by)` records a designer lock (`entity`, `form`, `set` or
`transition`) and sets the flags it covers: an entity pin pins that spot's placement in every
set; a set pin pins every placement and locks every form of the set; a form pin locks the
form; a transition pin locks a row for every spot. `unpin` removes the record and keeps flags
another pin still covers.

`locked_changes(before, after)` lists every pinned or locked item that differs between two
shows, by name; `require_unlocked(before, after, force)` raises if the list is not empty. This
**diff-based** guard is the safety net: whatever code made the edit, the comparison of
before and after catches it.

`join_sections` reverses `split_section`. When it glues the two timelines together it drops
any tempo section that only restates the tempo already in force (`_merge_tempos`), so
splitting and joining a constant-tempo show gives back an equal show. One case still differs
in data but not in timing: a split in the middle of a tempo ramp leaves that ramp written as
two sections.

```pycon
>>> from showpy.choreo.models import Placement
>>> from showpy.show.changes import apply_change
>>> from showpy.show.locks import locked_changes
>>> from showpy.show.models import CountsOp, PlacementOp
>>> from showpy.show.pinning import pin, unpin
>>> move = PlacementOp(set_id="2", placement=Placement(entity="T1", x=-2.0, y=9.0))
>>> apply_change(show, [move, CountsOp(set_id="3", counts=6.0)]).set("3").counts
6.0
>>> pinned = pin(show, "entity", "T1", "soloist")
>>> [s.get("T1").pinned for s in pinned.sets], pinned.pins[0].reason
([True, True, True], 'soloist')
>>> apply_change(pinned, [move])
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: edit touches pinned or locked items: placement T1 in set 2 (hint: leave pinned items as they are, unpin them first, or pass force=True)
>>> locked_changes(pinned, apply_change(pinned, [move], force=True))
['placement T1 in set 2']
>>> unpin(pinned, "entity", "T1") == show
True
```

## Validation: validate.py

Validators return `ValidationReport`s and never raise (chapter 3). Safety rules (collisions,
step size, bounds) belong to a separate checker, not here.

- `validate_set(show, candidate)`: every spot exactly once, known IDs, facings in range,
  forms consistent, pinned placements unchanged.
- `validate_paths(show, spec)`: known spots, counts equal to the destination set's, windows,
  style parameters, and continuity through the engine.
- `validate_dependencies(show, store)`: the sheet reference resolves and its version is
  pinned.
- `validate_show(show, store=None)`: all of the above plus the set sequence and the timeline.

```pycon
>>> from showpy.show.validate import validate_set, validate_show
>>> twin = show.set("2").model_copy(update={"placements": show.set("2").placements[:3]})
>>> print(validate_set(show, twin))
E: MISSING_SPOT set 2: T4 has no placement (hint: every spot is placed in every set)
>>> validate_show(show).ok
True
```

## Storage: documents, repositories and workspaces

### Documents

A show is stored as many small JSON documents rather than one big file, so two people editing
different sets touch different files and history shows what changed. `encode_show(show)`
splits it:

| Path                                   | Holds                                                                                   |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| `/show/show.json`                      | metadata, cast, set order, pins, dependencies                                           |
| `/show/sheet.json`, `/show/notes.json` | the sheet and notes                                                                     |
| `/time/timeline.json`                  | the timeline                                                                            |
| `/sets/<id>/set.json`                  | one set's placements (internal: a workspace lists the derived `placements.csv` instead) |
| `/sets/<id>/forms.json`                | that set's forms (only when it has any)                                                 |
| `/sets/<id>/set.py`                    | the set's build script, stored as text (written with `ws.write`, not by encode)         |
| `/transitions/<a>-<b>/paths.json`      | one transition's stored paths (only when not default)                                   |

`dump_json` writes canonically: sorted keys, two-space indent, sets sorted, `-0.0` written as
`0.0`. So equal content always gives equal bytes. `content_hash` hashes values as RFC 8785
canonical JSON under a domain tag (`showpy.content` by default), so equal content gives equal
hashes on every machine and under every hash seed. `decode_show(docs)` reassembles a
show; paths take the destination set's counts. `split_path` rejects `..`, `.`, `//` and `\`
so no path can escape the workspace.

```pycon
>>> from showpy.show.documents import decode_show, dump_json, encode_show, split_path
>>> sorted(encode_show(show))
['/sets/1/set.json', '/sets/2/set.json', '/sets/3/set.json', '/show/notes.json', '/show/sheet.json', '/show/show.json', '/time/timeline.json']
>>> decode_show(encode_show(show)) == show, dump_json({"b": 1, "a": [2]})
(True, b'{\n  "a": [\n    2\n  ],\n  "b": 1\n}\n')
>>> split_path("/sets/../config/limits.yaml")
Traceback (most recent call last):
  ...
showpy.core.errors.StorageError: BAD_PATH: path '/sets/../config/limits.yaml' is not a workspace path (hint: use an absolute path such as /sets/1/set.py, without '..', '.' or empty parts)
```

### Repositories and revisions

A `Repository` versions each show's documents in a **linear history**. Each revision is a
content-addressed tree: path → SHA-256 digest of the blob. Writing changes:

1. `transaction(show_id, changes, *, expected_revision, at)` takes the revision the caller
   read at. If the head has moved, it raises `ConflictError` listing every revision that
   landed since (short ID, time, paths). This is **optimistic concurrency**: compare-and-swap
   on the head, no locks held.
2. It merges the changes into the old tree (bytes write, `None` deletes).
3. If nothing differs, it returns the head unchanged: writes are idempotent.
4. The new tree must decode into a valid show, or the commit is refused.
5. The revision ID is `content_hash` of the parent, time and changed digests. Equal inputs
   give an equal ID: deterministic. A `Revision` holds only `id`, `parent`, `at` and
   `changed`.
6. The backend lands the revision only if its parent is still the head.

`InMemoryRepository` keeps everything in memory. `FileRepository(root)` keeps one folder per
show with JSON revisions, trees and content-addressed blob files; it writes atomically (temp
file plus `os.replace`), so two processes racing on one head cannot both land.
`InMemoryAssetStore` stores binary assets under `asset:sha256:<hex>` URIs.

### Workspaces

A `Workspace` exposes one show as files, like a working copy:

- It reads at its own revision. Writes expect that revision by default, so an edit made on a
  stale view raises `ConflictError` instead of overwriting someone else's. `refresh()` moves
  to the head; each successful write moves to the revision it created.
- `ls(path)`, `read(path)`, `write(path, data, at=...)`, `commit(changes, at=...)`.
- It does not know who is writing. The host decides who may write which file (an agent and
  the designer's limits, say) and refuses a write before it reaches ShowPy. Edit functions
  still refuse pinned items unless the caller passes `force=True`.
- Derived files are computed on read: `/show/index.csv`, `/sets/<id>/placements.csv`. A
  write to one is refused (`READ_ONLY`).

`files.py` holds the file view behind the workspace:

| Function or constant                                   | Does                                                                                                               |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `all_files(show, tree)` / `directories(show, tree)`    | every readable file path / every directory, each ending in `/`                                                     |
| `read_file(path, show, tree)`                          | text or bytes; derived tables are computed, missing designer files read as defaults                                |
| `show_changes(show, tree)`                             | the writes and deletes that store a show, including removed sets' files                                            |
| `staged_changes(path, raw, show, tree)`                | validates one file write and returns the document changes it makes (writing `[]` to `forms.json` clears the forms) |
| `require_writable(path)`                               | refuses a write to a derived table with `LockedError` `READ_ONLY`                                                  |
| `INDEX_DOC`, `LIMITS_DOC`, `WAIVERS_DOC`, `CLAIMS_DOC` | the fixed paths of the derived index and the designer's files                                                      |

`open_workspace(repo, show_id)`, `load_show(ws)` and `save_show(ws, show, at)` are the usual
entry points. `save_show` writes against `show.revision`, the revision the show was loaded at.

```pycon
>>> from datetime import UTC, datetime
>>> from showpy.core.errors import ConflictError
>>> from showpy.show.repositories import InMemoryRepository
>>> from showpy.show.storage import load_show, open_workspace, save_show
>>> at = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
>>> repo = InMemoryRepository()
>>> designer = open_workspace(repo, "demo")
>>> first = save_show(designer, show, at)
>>> first.parent, len(first.changed), first.id[:7]
('', 7, '0366592')
>>> agent = open_workspace(repo, "demo")
>>> retimed = save_show(designer, set_counts(load_show(designer), "3", 6.0), at)
>>> retimed.changed
('/sets/3/set.json',)
>>> try:
...     save_show(agent, load_show(agent), at)
... except ConflictError as error:
...     print(error.message)
1 revision(s) landed on demo since 0366592: 7976eeb 2026-11-11T09:00:00+00:00 (/sets/3/set.json)
>>> agent.ls("/"), agent.ls("/sets/1")
(['canvas/', 'config/', 'exports/', 'lib/', 'publish/', 'renders/', 'sets/', 'show/', 'time/', 'transitions/'], ['forms.json', 'placements.csv'])
>>> agent.write("/show/index.csv", "set,counts\n", at=at)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: READ_ONLY: /show/index.csv is derived and read-only (hint: edit forms.json, set.py or paths instead; the table follows)
```

## History: history.py

| Function                         | Does                                                                             |
| -------------------------------- | -------------------------------------------------------------------------------- |
| `diff_sets(a, b, tol)`           | spots moved, turned, added, removed; forms changed                               |
| `diff_paths(a, b)`               | spots and routes whose effective paths differ (a missing row equals the default) |
| `diff_show(a, b)`                | every difference between two shows as a JSON-safe dict                           |
| `revert(ws, revision_id, at)`    | saves an earlier revision's documents as a new head                              |
| `rename_entities(show, mapping)` | rewrites spot IDs everywhere, swaps allowed                                      |
| `changelog(ws, since)`           | terse lines, one per revision                                                    |

**Undo belongs to the host.** A revision records what changed and when, not who changed it, so
only the host knows which revisions its user made. The host keeps that record keyed by
revision ID and builds undo on `revert(ws, revision_id, at)`: it saves the documents of the
revision before the user's change as a new head. History is never rewritten, so every other
workspace sees the undo as an ordinary revision, and a stale one meets `ConflictError` as
usual.

```pycon
>>> from showpy.show.history import changelog, diff_sets, diff_show, revert
>>> diff_sets(show.set("1"), show.set("2")).moved
('T1', 'T2', 'T3', 'T4')
>>> diff_show(show, show.model_copy(update={"title": "Opener"}))
{'title': ['Test show', 'Opener']}
>>> designer.refresh() == designer.revision
True
>>> undone = revert(designer, first.id, at)
>>> undone.parent == retimed.id, load_show(designer).set("3").counts
(True, 4.0)
>>> print(changelog(designer, first.id))
7976eeb 2026-11-11 09:00 (/sets/3/set.json)
522a8b9 2026-11-11 09:00 (/sets/3/set.json)
```

## Collaboration: collab.py

The canvas is shared by the designer and the agent.

- `events_since(ws, revision)` derives `CanvasEvent`s (moves, form edits, path edits,
  retimes) from the revisions after `revision`, by comparing stored states. Replaying them
  with `apply_event` reproduces each edit. An unpin event, or a pin event that replaces a
  pin, needs `apply_event(..., force=True)`.
- `propose(show, ops, note, proposal_id)` wraps ops as a `Proposal` against the show's
  revision, after checking they apply. `preview_proposal` computes the ghost placements and
  paths for the canvas, and lists pinned items the proposal would touch.
- `accept(ws, proposal, at)` applies an open proposal. If the base moved, it still lands
  when nothing it touches changed since; otherwise `ConflictError` names the overlap.
  `reject(proposal, reason)` closes it.
- `highlight(target, ttl_s, at, event_id)` points the designer at something; it changes
  nothing. `selection(ws)` reads what the designer has selected. `pins(show)` lists locks.

```pycon
>>> from showpy.show.collab import accept, events_since, preview_proposal, propose
>>> proposal = propose(load_show(designer), [move], "open the left side", "p1")
>>> preview = preview_proposal(load_show(designer), proposal)
>>> [p.entity for p in preview.placements["2"]], preview.blocked
(['T1'], ())
>>> before = designer.revision
>>> accept(designer, proposal, at).changed
('/sets/2/set.json',)
>>> [(e.kind, e.payload["set_id"]) for e in events_since(designer, before)]
[('move', '2')]
```

> **Check your understanding 13.a.** Why does ShowPy offer `revert` but leave undo to the
> host?
>
> **Check your understanding 13.b.** An agent loads the show, the designer saves, then the
> agent saves. What happens, and what should the agent do?

## Exercises

**Exercise 13.1 (warm-up).** Insert a sub-set after set `1` of `two_set_show()` with 3 counts,
then renumber. Return the final set IDs and counts as a list of pairs.

**Exercise 13.2.** Save `two_set_show()` to an `InMemoryRepository`, retime set 2 to 12 counts
with a second save, and return the number of revisions and set 2's counts read back from the
head.

**Exercise 13.3.** Pin `T2` (entity pin) in `two_set_show()` and return the names
`locked_changes` reports after you force-move T2 in both sets.

**Exercise 13.4 (harder).** Save `two_set_show()` to an `InMemoryRepository` from the
designer's workspace. Then, from a second workspace for the agent, place T1–T4 of set 2 on a
`line_form` on `y = 12` from `x = 0` to `x = 6`, store the form, and save. Return set 2's
positions read back from the head and the paths the agent's revision changed.
