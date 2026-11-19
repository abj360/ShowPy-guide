# An end-to-end tutorial

This chapter builds a small show from nothing: eight trumpets and four flags on a high-school
football field, three sets, staggered and curved paths and a follow-the-leader route. Then it
inspects the show with the engine, hunts tight gaps, adds notes, stores the show, saves an edit
from a second workspace, exports it and publishes it.

Every step is a real file in `examples/`. Each file imports the previous steps, so
you can run any step on its own from the repository root, for example
`uv run python examples/t04_arc_set.py`. The build runs every file and pastes its
real output here. The pictures under the outputs are drawn from the same functions.

## Step 1: create a show on a field template

{{code: examples/t01_new_show.py}}

{{output: t01_new_show}}

What happened inside `new_show`:

1. `parse_ref(sheet.ref)` split `sheet:hs-football@1`; a sheet without a version would raise
   `VersionError`, because a show must pin the exact sheet it was drawn on.
2. It built set `1` with `counts=0` and one off-field placement per spot of the cast (none
   yet).
3. It recorded `dependencies = {"sheet:hs-football": "1"}`.

`new_timeline(TimelineMode.COUNTS, 144.0)` made one tempo section at count 0: 144 counts per
minute, so one count lasts `60/144 = 0.4167` s.

```pycon
>>> from t01_new_show import create_show
>>> from guide_draw import sketch
>>> sketch.sheet(
...     create_show().sheet,
...     px_per_m=6.0,
...     caption="The empty show's sheet: the NFHS field, rendered by render_sheet().",
... )
```

## Step 2: add groups and draw spots

{{code: examples/t02_spots.py}}

{{output: t02_spots}}

`add_group` stored two groups. `add_spots_along` called `space_along(line, 8)` and then
`add_spot`-like logic for each point: the lowest free label under the prefix (`T1`...`T8`), a
circle footprint of the group's default radius, and a placement in **every** set (here only
set 1). `set_shape("group:flags", ...)` resolved the expression with `select` and gave the
flags a 1.2 × 0.5 m rectangle, whose `extent_m` is 0.65 m. `define_selection` stored `ends`,
usable later as `sel:ends`.

```pycon
>>> from t02_spots import add_performers
>>> from showpy.sheet.render import SheetCanvas
>>> crop = SheetCanvas(min_x=-16.0, min_y=8.0, max_x=16.0, max_y=36.0, px_per_m=14.0)
>>> sketch.frames(
...     add_performers(create_show()),
...     (0.0,),
...     crop=crop,
...     caption="Set 1: trumpets (red) on y = 12, flags (blue) on y = 24. Ticks show facing 0°, toward the audience.",
... )
```

## Step 3: build set 2 from a block form

{{code: examples/t03_block_set.py}}

{{output: t03_block_set}}

`add_set("2", 16)` copied every placement from set 1 (positions, facings, on-field state,
but not form membership). `block_form` stored a recipe, not dots: origin `(0, 18)`, 2 rows,
4 columns, 2.286 m apart (four 8-to-5 steps). `place` generated the 8 slots front row first,
left to right, stood member `i` on slot `i`, and recorded `form="block"` and `order` on each
placement. `place` returned the placed set together with the forms, members filled, so
`with_set` stored the set and `apply_change([FormOp(...)])` stored the form on the show and
listed it in set 2's `forms`.

```pycon
>>> from t03_block_set import add_block_set
>>> blocked = add_block_set(add_performers(create_show()))
>>> sketch.frames(
...     blocked,
...     (0.0, 16.0),
...     crop=crop,
...     caption="Set 1 (count 0) and set 2 (count 16): the trumpets form the block; the flags hold.",
... )
```

## Step 4: build set 3 from an arc, matching performers to slots

{{code: examples/t04_arc_set.py}}

{{output: t04_arc_set}}

Three ways to fill the same 8 slots:

- **By order** sends T1 to slot 0, T2 to slot 1 and so on, ignoring where people stand: the
  longest move is 7.24 m and three pairs of paths cross.
- **sum** minimizes total travel: 30 m, with a 6.54 m longest move.
- **bottleneck_then_sum** (the default) first finds the smallest possible longest move, then
  the shortest total among assignments with that longest move. Here it gives the same answer
  as `sum`, with no crossings.

The block's front row (T1–T4) did not take the four middle slots: T1 and T2 go to the left end
of the arc, T3 and T4 to the right end, and the back row (T5–T8) fills the middle. The arc
form was then built with members in slot order and placed.

```pycon
>>> from t04_arc_set import add_arc_set, compare_objectives
>>> from showpy.show.manage import add_set
>>> results = compare_objectives(add_set(blocked, "3", 16.0))
>>> start = blocked.set("2").positions([f"T{i}" for i in range(1, 9)])
>>> sketch.moves(
...     start,
...     results["by order"].target_points(),
...     caption="By order: three crossings and a 7.24 m longest move.",
... )
>>> sketch.moves(
...     start,
...     results["bottleneck_then_sum"].target_points(),
...     caption="Default matching: no crossings, longest move 6.54 m.",
... )
```

## Step 5: add paths: a stagger, curves and follow-the-leader

{{code: examples/t05_paths.py}}

{{output: t05_paths}}

Three kinds of path instructions:

1. **Stagger**: `ordered_along(..., by="x")` ordered the trumpets left to right, and
   `stagger(step=1)` delayed the `i`-th by `i` counts, keeping the end: T8 starts at count 7
   and must cover its move in 9 counts instead of 16. `set_easing("ease_in_out")` makes every
   trumpet start and stop gently.
2. **Curves**: `curve_path` gave T1 and T4 a smooth `curve` row through one control point
   each, so they swing wide into the arc.
3. **Follow-the-leader**: `make_route` built a route back through the flag file (F1 ... F4)
   and on through two waypoints. Offsets `12, 8, 4, 0` are each flag's position along it;
   every flag travels 16.155 m, so the spacing along the route is kept.
   `follow_and_set_targets` wrote the flags' end points into set 3. `set_facing(TRAVEL,
turn_counts=2)` makes them look where they walk, turning over 2 counts.

`store_paths` stored each spec in show order.

```pycon
>>> from t05_paths import build_tutorial_show
>>> show = build_tutorial_show()
>>> sketch.frames(
...     show,
...     (16.0, 20.0, 24.0, 28.0, 32.0),
...     crop=crop,
...     caption="Transition 2→3: the flags follow F4 along the route; T1 and T4 curve wide into the arc.",
... )
```

## Step 6: ask the engine

{{code: examples/t06_engine.py}}

{{output: t06_engine}}

Read the output with chapter 12 in mind:

- At 144 cpm, set 2 (count 16) is reached at `16·60/144 = 6.667` s.
- T8 is still at count 4: its stagger delay is 7 counts. At count 8 it has barely started,
  because `ease_in_out` starts slowly.
- F1 at count 24 faces 90° (audience right) because its route runs along `+x` there and its
  facing mode is `TRAVEL`.
- `speeds` ranks T8 first: it covers 8.48 m in 9 counts, a mean of 0.942 m per count, and its
  peak is 1.767 m per count in the middle of its eased move.
- T1's curved path needed 21 time-linear segments to stay within 2 cm.

```pycon
>>> import numpy as np
>>> from showpy.choreo.engine import PathEngine
>>> engine = PathEngine(show)
>>> counts = np.linspace(0.0, 16.0, 161)
>>> sketch.plot(
...     counts,
...     [float(np.linalg.norm(engine.velocity_at("T8", c))) for c in counts],
...     [float(np.linalg.norm(engine.velocity_at("T1", c))) for c in counts],
...     labels=("T8 (delay 7)", "T1 (delay 0)"),
...     xlabel="global count",
...     ylabel="speed (m/count)",
...     caption="Speeds in transition 1→2: the stagger squeezes T8's move into 9 counts.",
... )
```

## Step 7: find tight gaps with avoid

{{code: examples/t07_avoid.py}}

{{output: t07_avoid}}

The stagger has a cost: in transition 1→2 the trumpets' paths cross while some are still
waiting, and footprints overlap (negative gaps). `min_gaps` used exact closest approach on the
engine's segments. `suggest_delays` tried delaying either spot in 0.5-count steps and
re-measured each trial with a fresh engine: delaying T4 by 4 more counts opens the pair to
1.262 m, at the price of a faster peak (1.390 m per count).

The last line is the lesson: fixing one pair moved the problem. T3 and T5 still overlap. The
helpers are advice; the designer decides, and a safety checker has the final word. A better fix
here is a different stagger order, or matching the block so paths do not cross.

```pycon
>>> from showpy.choreo.avoid import min_gaps
>>> worst = min_gaps(show, ("1", "2"), top=1)[0]
>>> sketch.frames(
...     show,
...     (7.0, round(worst.tau, 2), 9.0),
...     crop=crop,
...     caption="Around the tightest moment of 1→2: T4 and T5 overlap near count 7.9.",
... )
```

## Step 8: add notes and validate

{{code: examples/t08_notes_validate.py}}

{{output: t08_notes_validate}}

`notes_near` found the warning anchored to T4 and T5 because T4 stands 1.143 m from
`(0, 12)` in set 1. `validate_show` checked structure only (every spot in every set, paths
compile and end on target, the timeline is sound): it is `ok`. Note that it passes even with
the overlaps of step 7: collisions are the checker's job, not validation's.

## Step 9: save, meet a conflict, save a wider arc

{{code: examples/t09_storage_build.py}}

{{output: t09_storage_build}}

What happened, in order:

1. The designer saved the show: 11 documents in one revision, `d7284d4`.
2. The agent opened a workspace at that revision. The designer then retimed set 3 to 24
   counts (with `rescale=True`, so the stored path windows stretched too).
3. The agent tried to save its stale view. The repository saw that the head had moved and
   raised `ConflictError`, listing what landed: the retime's short ID, its time and the two
   paths it changed. The agent refreshed instead of overwriting.
4. The agent edited the form, not the dots: `edit` set the stored arc's radius to 16, `place()`
   stood the arc members on the new slots, and `FormOp` stored the edited form.
   `validate_show` confirmed the structure before saving.
5. `save_show` wrote only the documents that differ from the head: set 3's placements and its
   forms, 2 paths. The agent's revision landed on top of the designer's retime, so set 3
   keeps its 24 counts.
6. `changelog(agent, first.id)` lists the two revisions after the first, oldest first, with
   their times and paths. A revision holds only its ID, parent, time and changed paths: who
   saved it and why is the host's record, here the `authors` dictionary keyed by revision ID.
   The host also decides who may write, and builds undo on `revert(ws, revision_id, at)`,
   which saves an earlier revision's documents as a new head.

## Step 10: export frames, video, data and printouts

{{code: examples/t10_export.py}}

{{output: t10_export}}

![The tutorial show rendered by showpy.export.video.render_frame at counts 0, 8, 16, 24 and 32: the line, the stagger, the block, the curve and the follow-the-leader, and the arc.](figures/tutorial_frames.png)

- `export_video` rendered counts 0 to 4 at 6 frames per **second of music**, and returned MP4
  bytes (the `ftyp` box marks an MP4 file).
- `export_json` tagged the document `showpy.show.v1`, and `import_json` read back an equal
  show.
- `export_frames_csv` sampled every spot once per count.
- T4's coordinate sheet words each position, describes each move (`delay 3, move 13`,
  `curve 16`) and lists the yard lines and hashes it crosses, in walking order.
- The cue sheet lists the rehearsal marker added in this step.

## Step 11: publish and claim spots

{{code: examples/t11_publish.py}}

{{output: t11_publish}}

The publication is a value. `publish` took a join token and kept only its SHA-256, so
`pub.link` carries no token: `join_link(pub, token)` builds the link performers open, and a
guessed token does not verify. The host keeps the token, and its own roster keeps performers'
contacts; claims never hold them. Each claim returned a new publication with the claim locked. A
crew member could not claim a performer spot (`ValidationError`). The designer swapped Ada and
Bo. Republishing after a retime carried both claims over, because their spots still exist and
are still claimable by their roles, and `notify_changes` listed whose part changed.

```pycon
>>> from pathlib import Path
>>> sketch.image(
...     (Path("figures") / "tutorial_qr.png").read_bytes(),
...     caption="The QR code of the join link, written by qr_code(pub, token) in step 11.",
... )
```

> **Check your understanding 15.a.** In step 9, why did the agent's save fail even though
> the agent changed nothing?
>
> **Check your understanding 15.b.** In step 7, why does `validate_show` in step 8 still pass?

## Exercises

**Exercise 15.1 (warm-up).** Using `build_tutorial_show()` from `t05_paths.py`, return the
global count at which T8 starts moving and the count at which it arrives.

**Exercise 15.2.** Return the tutorial show's flag positions in set 3 (F1–F4), rounded to
3 decimals.

**Exercise 15.3 (harder).** Change the opening stagger of the tutorial so it runs from the
**center outward** (T4 and T5 first, then T3 and T6, ...; one count per pair) and return the
new tightest gap in transition 1→2. The check requires it to be larger than the original
-0.463 m.
