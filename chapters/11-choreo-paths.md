# showpy.choreo (3): paths, routes, facing and motion

Between two sets every spot moves. This chapter covers how that movement is **described**.
The next chapter covers how the engine turns descriptions into positions.

## The data: TransitionSpec, PathRow and friends

A `TransitionSpec` holds every instruction for one transition: `id` (the pair of set IDs),
`counts` (always the destination set's counts; ADR 0001 fix 16), `rows` (spot ID to
`PathRow`), `routes` (route ID to `Route`), `notes` and `source_hash`.

Rows are **sparse**: a spot without a row walks straight from its old placement to its new
one over the full counts. `spec.row(entity)` returns the stored row or that default.
`show.transition(tid)` returns the stored spec or an empty one.

A `PathRow` describes one spot's move:

| Field                           | Meaning                                                                                       |
| ------------------------------- | --------------------------------------------------------------------------------------------- |
| `style`                         | `straight`, `hold`, `curve`, `polyline`, `follow`, `rotate`, `custom`                         |
| `start`, `end`                  | the move's window in **local** counts (0 = start of the transition); `end=None` means the end |
| `waypoints`                     | points passed on the way, each optionally timed with `at` (a local count)                     |
| `route`                         | the route followed, for `follow`                                                              |
| `pivot`, `sweep_deg`            | the rotation center and signed angle, for `rotate`                                            |
| `facing_mode`, `facing_value`   | how the spot faces while moving                                                               |
| `turn_counts`, `turn_direction` | counts spent turning into and out of the facing; which way                                    |
| `pace`                          | step-pace multiplier for step-size reporting; positions ignore it                             |
| `easing`                        | how progress maps to time across the window                                                   |
| `motion_fn`, `motion_params`    | a registered custom motion, for `custom`                                                      |
| `locked`, `note`                | the designer's lock; free text                                                                |

`row.window(counts)` returns `(start, end)` with `end` filled in.

## Editing paths: paths.py

Every function takes a `TransitionSpec` and returns a new one, and raises `LockedError` on a
locked row unless `force=True`. `sel` is a list of IDs or a `Selection`; resolve expressions
first with `select`.

| Function                                                     | Does                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `default_paths(show, tid)`                                   | an empty spec: everyone straight                                                                  |
| `set_style(spec, sel, style, **params)`                      | changes style; `rotate` needs `pivot` and `sweep_deg`, `follow` a `route`, `custom` a `motion_fn` |
| `delay(spec, sel, counts, keep_end=True)`                    | starts later; `keep_end` keeps the end (the move gets faster), otherwise the window shifts        |
| `hold(spec, sel, until=None, from_=None)`                    | holds until a count, from a count, or the whole transition                                        |
| `arrive_early(spec, sel, counts)`                            | ends `counts` before the window's end                                                             |
| `window(spec, sel, start, end)`                              | sets both ends                                                                                    |
| `add_waypoint(spec, entity, point, at=None, index=None)`     | bends the path; a straight row becomes `polyline`                                                 |
| `remove_waypoint` / `clear_waypoints`                        | removes one or all bends; `clear` returns rows to straight                                        |
| `curve_path(spec, entity, *control)`                         | a smooth spline through control points                                                            |
| `stagger(spec, ordered_sel, step, direction, keep_end)`      | delays the `i`-th spot by `i·step`                                                                |
| `ripple(spec, ordered_sel, total, curve)`                    | spreads starts from 0 to `total`, shaped by an easing                                             |
| `set_facing(spec, sel, mode, value, turn_counts, direction)` | facing while moving                                                                               |
| `set_pace(spec, sel, pace)`                                  | step-pace multiplier                                                                              |
| `custom_path(spec, sel, motion, registry, **params)`         | a registered custom motion                                                                        |
| `set_easing(spec, sel, easing)`                              | an `Easing` or a kind name                                                                        |
| `lock(spec, sel)` / `unlock(spec, sel)`                      | the designer's locks                                                                              |
| `paths_table(spec)`                                          | rows that differ from the default, as a DataFrame                                                 |

```pycon
>>> from showpy.choreo.models import Easing, FacingMode, PathStyle, TransitionSpec
>>> from showpy.choreo.paths import (
...     add_waypoint,
...     delay,
...     lock,
...     paths_table,
...     ripple,
...     set_easing,
...     set_style,
...     stagger,
...     window,
... )
>>> spec = TransitionSpec(id=("1", "2"), counts=8.0)
>>> spec = stagger(spec, ["T1", "T2", "T3", "T4"], step=1.0)
>>> [spec.row(e).window(8.0) for e in ("T1", "T2", "T3", "T4")]
[(0.0, 8.0), (1.0, 8.0), (2.0, 8.0), (3.0, 8.0)]
>>> [spec.row(e).start for e in ("T1", "T2", "T3")] == [0.0, 1.0, 2.0]
True
>>> rippled = ripple(
...     TransitionSpec(id=("1", "2"), counts=8.0), ["A", "B", "C", "D", "E"], 4.0, "ease_in"
... )
>>> [rippled.row(e).start for e in "ABCDE"]
[0.0, 0.25, 1.0, 2.25, 4.0]
>>> paths_table(spec)[["entity", "style", "start", "end"]].to_string(index=False)
'entity    style  start  end\n    T2 straight    1.0 None\n    T3 straight    2.0 None\n    T4 straight    3.0 None'
>>> add_waypoint(spec, "T1", (1.0, 7.0), at=4.0).row("T1").style.value
'polyline'
>>> window(spec, ["T1"], 2.0, 10.0)
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: window 2.0–10.0 of T1 does not fit 8.0 counts (hint: keep 0 <= start < end <= counts)
>>> delay(lock(spec, ["T1"]), ["T1"], 1.0)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: path of T1 in 1→2 is locked (hint: unlock it first, or pass force=True as the designer)
>>> set_style(spec, ["T1"], PathStyle.ROTATE)
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: rotate paths need pivot, sweep_deg (hint: pass pivot, sweep_deg)
```

`paths_table` lists only T2 to T4: `stagger` gave T1 a delay of 0, which is the default
row, so T1 has no stored row at all. The `ease_in` ripple starts five spots at `4·u²` for `u = 0, ¼, ½, ¾, 1`: 0, 0.25, 1, 2.25, 4.
The first spots leave close together, the last ones far apart.

`showpy.show.paths_store.save_paths(ws, spec, at)` and `load_paths(ws, tid)` read and write
one transition's paths as `/transitions/<a>-<b>/paths.json` in a workspace (chapter 13).

## Easing: motion.py

An **easing** reshapes time inside a move's window. Let `u` be the share of the window that
has passed (0 at the start, 1 at the end). The easing returns the share of the **distance**
covered. Every easing is a monotone map from `[0, 1]` onto itself with `e(0) = 0` and
`e(1) = 1`, so an eased move still starts and ends on its placements, whatever the kind.

| `kind`              | `e(u)` with strength `k`                                     |
| ------------------- | ------------------------------------------------------------ |
| `linear`            | `u`                                                          |
| `ease_in`           | `u^k`: slow start                                            |
| `ease_out`          | `1 - (1 - u)^k`: slow finish                                 |
| `ease_in_out`       | `½(2u)^k` for `u < ½`, else `1 - ½(2 - 2u)^k`                |
| `hold_then_burst`   | 0 until `u = 1 - 1/k`, then linear to 1: wait, then go       |
| `burst_then_settle` | linear to 1 by `u = 1/k`, then 1: go, then wait              |
| `steps`             | `round(k)` smooth steps: march-and-stop                      |
| `custom`            | piecewise-linear through `points`, from `(0, 0)` to `(1, 1)` |

`steps` uses a **smoothstep** inside each step, `s(x) = x²(3 - 2x)`, so each step starts and
stops with zero speed instead of jerking. `easing_breaks(easing)` lists the time shares where
an easing has a kink or a pause; the engine uses them (chapter 12).

![Every easing kind as distance share (vertical) against time share (horizontal). The dashed line is linear.](figures/fig_easing.png)

```pycon
>>> import numpy as np
>>> from showpy.choreo.motion import ease, easing_breaks, turn
>>> u = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
>>> ease(Easing(kind="ease_in_out", strength=2.0), u).tolist()
[0.0, 0.125, 0.5, 0.875, 1.0]
>>> ease(Easing(kind="hold_then_burst", strength=4.0), u).tolist()
[0.0, 0.0, 0.0, 0.0, 1.0]
>>> ease(Easing(kind="steps", strength=2.0), np.array([0.25, 0.5, 0.75])).tolist()
[0.25, 0.5, 0.75]
>>> (
...     easing_breaks(Easing(kind="steps", strength=4.0)),
...     easing_breaks(Easing(kind="hold_then_burst", strength=4.0)),
... )
([0.25, 0.5, 0.75], [0.75])
>>> from guide_draw import sketch
>>> t = np.linspace(0.0, 1.0, 201)
>>> sketch.plot(
...     t,
...     ease(Easing(kind="steps", strength=4.0), t),
...     t,
...     labels=("steps (4)", "linear"),
...     xlabel="time share u",
...     ylabel="distance share",
...     caption="steps easing: four smoothstep moves. At u = 1/8, 3/8, 5/8, 7/8 it equals the linear line.",
... )
```

Look at the `steps` output. At `u = ¼, ½, ¾` the stepped easing equals plain linear time:
each step's smoothstep is exactly half done at its middle. Remember this; chapter 12 shows
how it once fooled the engine.

`turn(start, end, u, direction)` interpolates a facing: the `shortest` way (by `angle_diff`),
always `counterclockwise`, or always `clockwise`.

```pycon
>>> from showpy.choreo.models import TurnDirection
>>> turn(350.0, 10.0, 0.5), turn(350.0, 10.0, 0.5, TurnDirection.CLOCKWISE)
(0.0, 180.0)
```

From 350° to 10° the short way is +20° through 0°; clockwise it is -340°, so halfway is
`350 - 170 = 180°`.

## Custom motions

A **custom motion** is a pure function `fn(u, start, end, params) -> Points` returning
positions at progress shares `u`. It must return `start` at `u = 0` and `end` at `u = 1`.
Motions live in an immutable `MotionRegistry`; `register_motion(registry, name, fn)` probes the
function on a test move from `(0, 0)` to `(4, 3)` and refuses it if it misses either end.

Built-ins in `DEFAULT_MOTIONS`:

- `weave`: a sine offset to the side, `amplitude·sin(2π·cycles·u)` along the left normal.
  `cycles` must be a multiple of 0.5, or the offset would not return to 0 at the end.
- `zigzag`: the same with a triangle wave (sharp corners).
- `figure_eight`: a side offset `sin(2πu)` plus an along-track offset `½·sin(4πu)`.
- `spiral`: circles the move's midpoint, half a turn plus `turns` extra full turns.

![The four built-in custom motions from (0, 0) to (8, 0).](figures/fig_motions.png)

```pycon
>>> from showpy.choreo.motion import DEFAULT_MOTIONS, motions, register_motion, weave
>>> [m.name for m in motions(DEFAULT_MOTIONS)]
['figure_eight', 'spiral', 'weave', 'zigzag']
>>> weave(np.array([0.0, 0.125, 1.0]), (0.0, 0.0), (8.0, 0.0), {"cycles": 1, "amplitude": 0.5}).round(
...     9
... ).tolist()
[[0.0, 0.0], [1.0, 0.353553391], [8.0, -0.0]]
>>> def drift(u, start, end, params):
...     return np.outer(u, np.subtract(end, start)) + np.asarray(start) + [0.0, 1.0]
>>> register_motion(DEFAULT_MOTIONS, "drift", drift)
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: motion 'drift' does not start at start and end at end (hint: return start at u=0 and end at u=1, shape (len(u), 2))
>>> weave(np.array([1.0]), (0.0, 0.0), (8.0, 0.0), {"cycles": 0.3})
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: cycles must be a multiple of 0.5 so the move ends on target (hint: use cycles like 1, 1.5 or 2)
```

`drift` adds 1 m sideways everywhere, so it misses both ends and registration refuses it.
Fix it by fading the offset with `sin(πu)`, which is 0 at both ends (exercise 11.3).

## Show-aware builders: routes.py

Some paths need the placements, so these take the show.

**Follow the leader.** A file of performers walks one behind the other along the leader's
path. `make_route(show, tid, leader, waypoints, members)` builds a `Route`:

1. The route curve runs **back through the file** (last member first, up to the leader) and
   then on through the leader's waypoints (or to the leader's next placement).
2. Each member's `offset` is the arc length of its current spot on that curve.
3. Every member travels the same distance, `travel` = the leader's remaining length. So the
   spacing along the route is kept.

`follow(spec, route, start, end)` stores the route and gives every member a `follow` row.
`follow_and_set_targets(show, tid, route)` also writes each member's end point into the next
set, because those ends are decided by the route, not by a form.

Pitfall: a route must have length. If the file and the leader's waypoints collapse to a single
point (for example, a one-spot file whose leader stays put), `make_route` raises `PathError`
with the hint "give a waypoint away from the leader's start".

**Counter-march.** `counter_march(show, tid, sel, turn_at, counts_per_turn)` turns a file
back on itself, passing 1 m to the leader's left: each member walks to `turn_at`, turns left
through a half circle and comes back alongside the file. A selection with no members raises
`PathError`: a counter-march needs at least one spot, leader first.

**L-shaped moves.** `two_part(show, spec, sel, corner, split)` goes x first or y first (or
through a given corner point), optionally reaching the corner at local count `split`.

**Rotation.** `rotate_path(show, spec, sel, pivot, deg)` rotates spots about a pivot point or
the centroid of their starting spots. Each spot's destination must be its start rotated by
`deg`, or the engine raises `ContinuityError`.

![Left: follow the leader; T4 leads to (10, 9) then (10, 14), and the file keeps its spacing along the route. Right: a counter-march turning at (10, 5); the file ends reversed, alongside its own path.](figures/fig_routes.png)

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.choreo.routes import follow_and_set_targets, make_route, rotate_path, two_part
>>> show = two_set_show()
>>> route = make_route(show, ("1", "2"), "T4", [(10.0, 9.0), (10.0, 14.0)], ["T4", "T3", "T2", "T1"])
>>> route.offsets, round(route.travel, 3)
((6.0, 4.0, 2.0, 0.0), 10.657)
>>> led = follow_and_set_targets(show, ("1", "2"), route)
>>> [tuple(round(v, 3) for v in led.set("2").get(e).point) for e in ("T4", "T1")]
[(10.0, 14.0), (9.293, 8.293)]
>>> sketch.frames(
...     led,
...     (0.0, 4.0, 8.0),
...     caption="follow_and_set_targets: the file follows T4 at counts 0, 4 and 8.",
... )
>>> two_part(show, show.transition(("1", "2")), ["T2"], "x_first").row("T2").waypoints
(Waypoint(x=2.0, y=5.0, at=None),)
>>> from showpy.choreo.engine import PathEngine
>>> spun = rotate_path(show, show.transition(("1", "2")), ["T1"], (0.0, 0.0), 90.0)
>>> PathEngine(show.model_copy(update={"transitions": (spun,)})).compile(("1", "2"))
Traceback (most recent call last):
  ...
showpy.core.errors.ContinuityError: CONTINUITY: rotate path of T1 ends at (-5.0, 6.123233995736766e-16), not on its target (0.0, 9.0) (hint: change the path parameters or the target placement so they agree)
```

T4 starts 6 m along the route (behind it are T3, T2 and T1, 2 m apart) and walks 10.657 m:
`√(4² + 4²) = 5.657` m to `(10, 9)` plus 5 m up to `(10, 14)`. T1 walks the same distance and
ends 6 m behind T4 along the route, partway up the diagonal at `(9.293, 8.293)`.

`two_part` with `x_first` put the corner at `(2, 5)`: T2's move is purely in y (from
`(2, 5)` to `(2, 9)`), so "x first" is a zero-length leg and the corner equals the start.
The waypoint is stored anyway; the engine drops points closer than 1 µm to the previous one
when it compiles the path, so T2 still walks straight.

The rotation failed on purpose. Rotating T1 at `(0, 5)` by 90° about the origin ends at
`(-5, 0)`, but set 2 says `(0, 9)`. The engine checks every non-straight style at compile time
(ADR 0002 decision 4). The message gives both points; the hint says to change the path or the
target. Here, put T1's set 2 placement at `(-5, 0)`, or change the pivot.

## Facing tools: facing.py

The `face_*` functions edit the placements of **one set** (ADR 0001 fix 14):

| Function                                      | Faces                                                |
| --------------------------------------------- | ---------------------------------------------------- |
| `face_audience(set, sel)`                     | 0°                                                   |
| `face_direction(set, sel, deg)`               | a fixed facing                                       |
| `face_point(set, sel, point)`                 | toward a point; a spot on the point keeps its facing |
| `face_entity(set, sel, entity)`               | toward another spot's placement in the same set      |
| `face_along(show, set_id, form_id, reverse)`  | along the form's curve                               |
| `face_normal(show, set_id, form_id, outward)` | perpendicular; outward is the right of travel        |

Facing over **time** is different. During a move, a `PathRow`'s `facing_mode` decides:

| `FacingMode`                | During the window the spot faces                                     |
| --------------------------- | -------------------------------------------------------------------- |
| `to_target` (default)       | its facing in the next set                                           |
| `fixed`                     | `facing_value` degrees                                               |
| `travel` / `against_travel` | the direction it walks / the opposite                                |
| `toward_point`              | a point                                                              |
| `toward_entity`             | another spot, wherever that spot is at that moment                   |
| `audience`                  | 0°                                                                   |
| `interpolate`               | turns from the old facing to the new one as the eased progress grows |

`add_facing_override(show, override)` forces a facing on spots over a **global** count range,
on top of any path. Overrides win inside their range, with the same blending in and out.

```pycon
>>> from showpy.choreo.facing import add_facing_override, face_entity, face_point
>>> from showpy.choreo.models import FacingOverride
>>> s1 = show.set("1")
>>> [p.facing for p in face_point(s1, ["T1", "T4"], (3.0, 9.0)).placements]
[143.13010235415598, 0.0, 0.0, 216.86989764584402]
>>> face_entity(s1, ["T1"], "T4").get("T1").facing
90.0
>>> o = FacingOverride(entities="T1-T2", mode=FacingMode.AUDIENCE, start=2.0, end=6.0, turn_counts=1.0)
>>> len(add_facing_override(show, o).facing_overrides)
1
>>> add_facing_override(show, o.model_copy(update={"end": 20.0}))
Traceback (most recent call last):
  ...
showpy.core.errors.TimeRangeError: TIME_RANGE: override 2.0–20.0 is outside the show (0–8.0) (hint: keep the range within 0–8.0 counts)
```

T1 at `(0, 5)` looking at `(3, 9)` sees the direction `(3, 4)`, which is
`atan2(3, -4) = 143.13°`: right and upstage. The 3-4-5 triangle makes it easy to check.

> **Check your understanding 11.a.** Why must `weave`'s `cycles` be a multiple of 0.5?
>
> **Check your understanding 11.b.** `delay(spec, ["T1"], 2.0)` with `keep_end=True` on an
> 8-count straight move of 4 m: what is T1's speed during the move?

## Exercises

**Exercise 11.1 (warm-up).** Stagger `T1`–`T4` from the **end** with a step of 1.5 counts in
an 8-count transition and return the starts in ID order.

**Exercise 11.2.** Ripple 5 spots over 4 counts with `ease_out` and return the starts. Derive
them by hand from `1 - (1 - u)²` first.

**Exercise 11.3.** Write a custom motion `solve()` that returns a function bulging 1 m to the
left of travel at mid-move, `start + u·(end - start) + sin(πu)·left`, and register it as
`bulge`. Return the new registry. The check moves `T1` with it.

**Exercise 11.4 (harder).** In `two_set_show()`, make `T1` rotate 90° clockwise about
`(4, 5)` in transition `1→2`, and set its set 2 placement so the engine compiles. Return the
show. Explain why the target must be `(4, 9)`.
