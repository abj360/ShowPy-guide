# showpy.choreo (1): sets, forms and placement

`showpy.choreo` is the heart of the library. It is large, so four chapters cover it:

1. this one: sets and placements, forms, and building sets from forms;
2. matching spots to slots (chapter 10);
3. paths, routes, facing and custom motion (chapter 11);
4. the `PathEngine`, measures over time and collision help (chapter 12).

## Placements and sets: models.py

A `Placement` is one spot's state at one set:

| Field           | Meaning                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| `entity`        | the spot ID                                                                 |
| `x`, `y`        | meters, as in chapter 2                                                     |
| `facing`        | degrees, 0 toward the audience                                              |
| `form`, `order` | the form the spot belongs to in this set, and its index along it            |
| `pinned`        | the designer's lock                                                         |
| `note`          | text printed on coordinate sheets                                           |
| `on_field`      | false before an entrance or after an exit: not drawn, not collision-checked |

A `Set` is a snapshot: `id` (such as `12` or `12A`), `counts` (the length of the move into
it; 0 for the first set), `placements` (one per spot), `forms` (IDs present), `label`, `cue`,
`source_hash` (the hash of the script that built it) and `state` (`draft`, `proposed`,
`approved`).

| Method                                      | Returns                                                                               |
| ------------------------------------------- | ------------------------------------------------------------------------------------- |
| `set.get(entity)`                           | one placement; `UnknownRefError` with close matches                                   |
| `set.entity_ids()`                          | spot IDs in placement order                                                           |
| `set.positions(sel="all")`                  | an `(N, 2)` array in selection order                                                  |
| `set.table()`                               | a pandas DataFrame, one row per spot                                                  |
| `set.with_placements(updates, force=False)` | a new set; each update is a `Placement` or a dict of fields; pinned rows need `force` |

`SpotCount` (`set_id`, `on_field`, `off_field`, `changed`) is what
`showpy.show.counts.spot_counts(show)` returns for the set strip: how many spots are on and off
the field in each set and whether the on-field count changed from the previous set.

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.show.counts import spot_counts
>>> show = two_set_show()
>>> s2 = show.set("2")
>>> s2.get("T3"), s2.positions(["T4", "T1"]).tolist()
(Placement(entity='T3', x=4.0, y=9.0, facing=0.0, form=None, order=None, pinned=False, note=None, on_field=True), [[6.0, 9.0], [0.0, 9.0]])
>>> s2.table()[["entity", "x", "y", "on_field"]].head(2).to_string(index=False)
'entity   x   y  on_field\n    T1 0.0 9.0      True\n    T2 2.0 9.0      True'
>>> exit_t4 = s2.with_placements({"T4": {"on_field": False}})
>>> [
...     (c.set_id, c.on_field, c.off_field, c.changed)
...     for c in spot_counts(show.model_copy(update={"sets": (show.sets[0], exit_t4)}))
... ]
[('1', 4, 0, False), ('2', 3, 1, True)]
>>> s2.with_placements({"T9": {"x": 1.0}})
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: spot 'T9' is not in set 2 (hint: check the spot id or add the spot first)
```

## Forms: a stored shape plus ordered members

### The idea

Drawing dots one by one is how mistakes creep in. A **form** stores how to build a shape
(for example "an arc of radius 14 m centered at (0, 6), from 135° sweeping -90°") and an
ordered list of members. The dots are **generated** from it. To change the picture, edit the
form and regenerate; never move the dots by hand.

A `Form` has `id`, `set`, `kind`, `geometry` (the JSON recipe), `members`, `spacing` (a
`SpacingSpec`), `facing` (a `FacingSpec`), `locked` and `meta`.

The recipe depends on `kind`:

| `kind`                                                       | `geometry` keys                                            |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| `line`, `arc`, `curve`, `circle`, `wedge`, `polyline`, `svg` | `curve`: a curve's `construction()`                        |
| `block`                                                      | `origin`, `rows`, `cols`, `interval`, `facing`, `anchor`   |
| `fill`                                                       | `outline` (a `Region`), `interval`, `pattern`, `angle_deg` |
| `scatter`                                                    | `region`, `min_gap`, `seed`                                |
| `custom`                                                     | `points`, `facings` (or null)                              |
| `generated`                                                  | `fn` (a registered generator name), `params`               |

Every recipe may also hold `n`, the number of **slots**. Without `n` there is one slot per
member. Slots past the last member are **open**: `place` fills them by matching. Non-curve
recipes may hold `transform`, a 3 × 3 affine matrix applied to the generated points, which is
how a rotated block or a mirrored scatter stays editable.

### Spacing and facing specs

`SpacingSpec(mode, interval, start, end, align, gaps)` says how curve forms space their
slots: `count` (evenly over `start..end`, the default), `interval` (fixed gap) or
`proportional` (shared across SVG subpaths by length). `gaps` adds extra meters after given
slot indexes.

`FacingSpec(mode, value)` says how members face:

| `mode`         | Facing of each slot                                                            |
| -------------- | ------------------------------------------------------------------------------ |
| `audience`     | 0° (default for most kinds)                                                    |
| `fixed`        | `value` degrees                                                                |
| `toward_point` | toward the point `value`                                                       |
| `along`        | along the curve's travel direction, plus an optional offset                    |
| `normal`       | to the right of travel (outward on a counter-clockwise circle), plus an offset |
| `outward`      | away from the center (circles and arcs) or the slot centroid                   |

Curve kinds know the exact tangent at every slot. Other kinds use the chord through the
neighboring slots as their direction.

### The constructors

`line_form`, `arc_form`, `curve_form`, `circle_form` (faces outward by default),
`block_form` (faces `direction_deg`), `wedge_form` (faces the apex direction),
`polyline_form`, `svg_form`, `fill_form`, `scatter_form`, `custom_form` (stored facings win)
and `generated_form`. Each takes `form_id`, `members`, the shape arguments, optional spacing
and facing, and keyword-only `set_id` and `n`.

`slots(form)` returns slot positions. `slot_poses(form)` returns positions and facings.
`placements(form)` regenerates one `Placement` per member with `form` and `order` set.

Under the hood, all three call `form_layout.layout(form)`, which reads the recipe:

1. For curve kinds: rebuild the curve with `curve_from_construction`, compute arc-length
   stations with `curve_stations(curve, spacing, n)`, and evaluate points and exact tangents.
2. For other kinds: call the raw generator (`block`, `fill`, `scatter`, custom points, or the
   registered function), then apply the optional `transform`.
3. `member_facings(spec, layout)` turns directions into facings.

![Slots and facings of five form kinds: an arc facing normal, a circle facing outward, a 90° wedge, and two generated forms (rose and spiral).](figures/fig_forms.png)

```pycon
>>> from showpy.choreo.forms import (
...     arc_form,
...     block_form,
...     circle_form,
...     line_form,
...     placements,
...     slot_poses,
...     slots,
... )
>>> from showpy.choreo.models import FacingSpec, SpacingSpec
>>> arc = arc_form(
...     "a",
...     ["T1", "T2", "T3"],
...     (0, 0),
...     6.0,
...     150.0,
...     -120.0,
...     facing=FacingSpec(mode="toward_point", value=(0.0, 0.0)),
... )
>>> pts, facings = slot_poses(arc)
>>> pts.round(3).tolist(), [round(f, 3) for f in facings]
([[-5.196, 3.0], [0.0, 6.0], [5.196, 3.0]], [60.0, 0.0, 300.0])
>>> from guide_draw import sketch
>>> sketch.points(
...     pts,
...     facings=(facings,),
...     numbered=True,
...     caption="arc_form facing toward_point (0, 0): every member looks at the center.",
... )
>>> [
...     (p.entity, p.order, round(p.facing, 1))
...     for p in placements(circle_form("c", ["A", "B", "C", "D"], (0, 0), 2.0))
... ]
[('A', 0, 90.0), ('B', 1, 180.0), ('C', 2, 270.0), ('D', 3, 0.0)]
>>> slots(
...     line_form(
...         "l",
...         ["A", "B"],
...         (0, 0),
...         (10, 0),
...         spacing=SpacingSpec(mode="interval", interval=3.0, align="center"),
...     )
... ).tolist()
[[3.5, 0.0], [6.5, 0.0]]
>>> slots(line_form("l", ["A", "B", "C"], (0, 0), (10, 0), n=2)).tolist()
[[0.0, 0.0], [10.0, 0.0]]
>>> placements(line_form("l", ["A", "B", "C"], (0, 0), (10, 0), n=2))
Traceback (most recent call last):
  ...
showpy.core.errors.SpacingError: SPACING: form l has 3 members but 2 slots (hint: use at most 2 members or enlarge the shape)
```

The arc members face the center: the left one at `(-5.196, 3)` looks toward `(5.196, -3)`,
which is `atan2(5.196, 3) = 60°`, front-right. The circle form faces outward by default: the member at angle 0° (the point `(2, 0)`) faces
`+x`, which is facing 90°.

### Generated forms and the form-function registry

A **form function** is a pure `fn(params, n) -> Points` returning `n` points in slot order.
Every parameter has a default, so `fn({}, n)` always works. `register_form_fn(registry, name,
fn)` returns a new registry after probing `fn({}, 4)`; `DEFAULT_FORM_FNS` holds `rose`,
`sine_wave` and `spiral`. `generated_form(form_id, members, fn, ..., **params)` stores
`{"fn": name, "params": params}`; `edit_params(form, **params)` changes them.

- `spiral_points`: evenly by arc length along an Archimedean spiral.
- `sine_wave_points`: evenly by arc length along a sine wave toward `+x`.
- `rose_points`: around `r(θ) = radius·(inner + (1 - inner)·|cos(petals·θ/2)|)`. With
  `inner > 0` the petals never reach the center, so the outline is a simple closed curve and
  no two spots coincide.

The generators sample the shape densely (`CURVE_SAMPLES = 721`), wrap the samples in a
`Polyline` and call `space_along`, so spots are evenly spaced by arc length.

```pycon
>>> import numpy as np
>>> from showpy.choreo.form_fns import DEFAULT_FORM_FNS, form_fns, register_form_fn
>>> from showpy.choreo.forms import edit_params, generated_form
>>> [info.name for info in form_fns()]
['rose', 'sine_wave', 'spiral']
>>> wave = generated_form("w", [], "sine_wave", n=7, amplitude=1.0)
>>> slots(wave).round(3).tolist()[:3]
[[-8.0, 10.0], [-5.263, 10.837], [-2.737, 9.163]]
>>> slots(edit_params(wave, amplitude=0.0))[:, 1].tolist()
[10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
>>> def bad(params, n):
...     return np.zeros((n + 1, 2))
>>> register_form_fn(DEFAULT_FORM_FNS, "bad", bad)
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: form generator 'bad' returned shape (5, 2) for n=4 (hint: return n finite (x, y) rows)
```

## Editing forms: form_ops.py

Every function returns new forms and refuses a locked form unless `force=True`.

| Function                         | Does                                                                                                                                                        |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `edit(form, **changes)`          | changes recipe fields (for example `radius`) or form fields, then regenerates slots to validate                                                             |
| `reorder(form, order, prev_set)` | new member order: a list, `"reverse"`, `"by_x"`, `"by_y"` or `"nearest_prev"` (optimal match from `prev_set`)                                               |
| `split_form(form, at)`           | splits before an index or member; evenly spaced curve forms become trimmed pieces of the same curve, others custom forms; nobody moves                      |
| `merge_forms(a, b, form_id)`     | joins two forms of one set into a custom form; nobody moves                                                                                                 |
| `morph_targets(a, b)`            | where each member of `a` stands in `b`                                                                                                                      |
| `transform_form(form, matrix)`   | maps a form exactly: curve recipes through `transform_curve`, blocks under rotation and uniform scale keep their recipe, others gain a composed `transform` |
| `gate(form, hinge, deg)`         | rotates about the first slot, the last slot or a slot index, like a gate on a hinge                                                                         |
| `pinwheel(forms, center, deg)`   | rotates several forms together about one center                                                                                                             |
| `form_templates()`               | lists the constructors by kind                                                                                                                              |

```pycon
>>> from showpy.choreo.form_ops import edit, gate, reorder, split_form, transform_form
>>> from showpy.geo.affine import mirror_matrix
>>> row = line_form("row", ["A", "B", "C", "D"], (0, 0), (6, 0))
>>> slots(gate(row, "start", 90.0)).round(6).tolist()
[[0.0, 0.0], [0.0, 2.0], [0.0, 4.0], [0.0, 6.0]]
>>> (
...     reorder(row, "reverse").members,
...     edit(circle_form("c", ["A"], (0, 0), 2.0), radius=3.0).geometry["curve"]["radius"],
... )
(('D', 'C', 'B', 'A'), 3.0)
>>> left, right = split_form(row, "C")
>>> left.kind, right.geometry["curve"]["kind"], slots(right).tolist()
('line', 'trimmed', [[4.0, 0.0], [6.0, 0.0]])
>>> blk = block_form("b", ["A", "B"], (0, 10), 1, 2, 2.0)
>>> flipped = transform_form(blk, mirror_matrix((0, 0), (0, 1)))
>>> slots(flipped).tolist(), sorted(flipped.geometry)
([[1.0000000000000013, 10.0], [-0.9999999999999988, 10.0]], ['anchor', 'cols', 'facing', 'interval', 'n', 'origin', 'rows', 'transform'])
>>> sketch.points(
...     slots(row),
...     slots(gate(row, "start", 90.0)),
...     slots(gate(row, "end", -45.0)),
...     labels=("row", "gate start 90°", "gate end -45°"),
...     caption="gate(): the row swings about its first or last slot.",
... )
>>> edit(row.model_copy(update={"locked": True}), n=6)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: form row is locked (hint: unlock it first, or pass force=True as the designer)
```

The mirrored block kept its block recipe (the `1.0000000000000013` is rounding noise from the
matrix product) and gained a `transform` matrix, so it is still a
block you can edit; its slots swapped sides.

## Recognizing forms: form_fit.py

Imported or hand-placed spots can be turned back into a form. `detect_form(points, tol,
form_id, members)` tries a line, then an arc or circle, and falls back to a custom form.

**Line: total least squares.** Center the points and take the singular value decomposition
of the centered matrix. The first right singular vector is the direction that keeps the most
variance: the best line through the centroid, measured perpendicular to itself (not
vertically, as ordinary least squares would). The residual is the largest perpendicular
distance. `fit_line` returns the extreme points along that line.

**Circle: Kåsa, then Gauss–Newton.** A circle satisfies `x² + y² + D·x + E·y + F = 0`. That is
linear in `D, E, F`, so one linear least-squares solve gives a first guess: center
`(-D/2, -E/2)`, radius `√(cx² + cy² - F)` (Kåsa 1976). Kåsa's fit minimizes an algebraic
error that is biased on short arcs, so Gauss–Newton then refines the true geometric residuals
`|p_i - c| - r` for up to 50 steps.

**Arc or circle?** Sort the points by angle around the center and look at the angular gaps.
If the widest gap is more than 1.5 times the median gap, there is a hole: it is an arc that
starts after the hole and sweeps `360° - widest gap`. Otherwise it is a full circle.

Fitted forms space their slots evenly, so unevenly spaced imports come back evened out.

```pycon
>>> from showpy.choreo.form_fit import detect_form, fit_circle, fit_line
>>> fit_line([(0, 0), (1, 0.05), (3, 0)])
((7.65618608629115e-05, 0.021429938384877466), (3.0000382706739943, 0.010712098379067312), 0.03214224189203111)
>>> c, r, res = fit_circle([(5, 0), (0, 5), (-5, 0), (3, 4)])
>>> np.round(c, 9).tolist(), round(r, 9), round(res, 9)
([-0.0, 0.0], 5.0, 0.0)
>>> angles = np.radians([10, 40, 70, 100])
>>> found = detect_form(np.stack([4 * np.cos(angles), 4 * np.sin(angles)], axis=1))
>>> found.kind, round(found.geometry["curve"]["sweep_deg"], 6)
('arc', 90.0)
>>> detect_form([(0, 0), (3, 0), (1, 2), (4, 3)]).kind
'custom'
```

`slots()` happily returns 2 slots for a 3-member form with `n=2`: slots exist before
members. Only `placements()` (and `place()`) refuse a form with more members than slots. The
total-least-squares line through `(0, 0)`, `(1, 0.05)`, `(3, 0)` tilts slightly toward the
middle point; its largest perpendicular residual is 0.032 m.

## Building sets from forms: form_place.py

`place(show, set_id, forms, match_options=None)` builds a set's placements from forms:

1. Stamp each form with the set ID and check no spot is in two forms.
2. Members stand on their own slots: member `i` on slot `i`.
3. Spots of the set that belong to **no** given form are matched into the open slots (slots
   past each form's last member), from where they stand in the **previous** set, with
   `match()` and `match_options` (chapter 10). In the first set there is no previous set, so
   every slot needs a member.
4. Pinned placements stay where they are.
5. Each placement records `form` and `order`; the set lists the form IDs.
6. It returns `(placed, forms)`: the set, and the forms in the order given with their members
   filled in slot order. The show is not changed; store both, the set with `with_set` and the
   forms with a `FormOp`, so forms and placements agree.

`filled_forms(placed, forms)` reads the members back from any placed set in slot order; `place`
already returns them. `rebuild(show, form_id)` regenerates one stored form's placements in its
set and drops its members' stored path rows into and out of that set, so they walk straight.

```pycon
>>> from showpy.choreo.form_place import filled_forms, place, rebuild
>>> open_row = line_form("row", [], (6, 12), (0, 12), n=4)
>>> placed, (filled,) = place(show, "2", [open_row])
>>> [(p.entity, p.x, p.order) for p in placed.placements]
[('T1', 0.0, 3), ('T2', 2.0, 2), ('T3', 4.0, 1), ('T4', 6.0, 0)]
>>> filled.members, filled.set, filled_forms(placed, [open_row]) == [filled]
(('T4', 'T3', 'T2', 'T1'), '2', True)
>>> sketch.moves(
...     show.set("1").positions(),
...     placed.positions(),
...     caption="place() matched T1-T4 from set 1 into the four open slots of a row at y = 12: no crossings.",
... )
>>> place(show, "2", [line_form("short", [], (0, 12), (2, 12), n=2)])
Traceback (most recent call last):
  ...
showpy.core.errors.MatchError: MATCH: 4 spots without a form but only 2 open slots (hint: add members to forms, add slots with n=, or place those spots elsewhere)
```

The row's slots run from `(6, 12)` to `(0, 12)`, so slot 0 is on the right. Matching gave the
right-most spot, T4, slot 0: everyone walks straight up.

> **Check your understanding 9.a.** Why does the library store a form's recipe rather than its
> dots?
>
> **Check your understanding 9.b.** When does `detect_form` call a set of points on a circle an
> arc?

## Exercises

**Exercise 9.1 (warm-up).** Build a circle form of 8 open slots, radius 5, center `(0, 10)`,
and return each slot's facing.

**Exercise 9.2.** Build a 3 × 4 block form of 12 open slots at `(0, 20)`, interval 2 m,
facing 180°. Return the slot index of the front-left slot in stage coordinates (smallest y,
then smallest x).

**Exercise 9.3.** In `two_set_show()`, place set 2 from an arc form with 4 open slots
(center `(3, 3)`, radius 6, start 150°, sweep -120°). Return the members of the filled form
that `place` returns.

**Exercise 9.4 (harder).** Points on a circle of radius 7 around `(1, 2)` at angles 0°, 50°,
95°, 160° and 200° (uneven). Return `detect_form(...)`'s kind, center, radius and sweep.
Explain why it is an arc.
