# showpy.choreo (4): the PathEngine

`PathEngine` is the only code that turns path instructions into positions over time
(CLAUDE.md rule 5). The canvas, the checker, exports, video and analysis all ask it, so they
can never disagree about where a performer is. This chapter explains how it works, from one
`position()` call down to the curve, and then the measures and collision helpers built on it.

## The big idea: a curve plus a time map

ADR 0002 decision 1. Each spot's move in a transition compiles to a `MotionPlan` holding two
separate things:

1. **A curve in space**: where the spot walks. A straight move is a `Segment`; waypoints give
   a `Polyline` or a `SplineCurve`; a rotation an `ArcCurve`; a follow-the-leader move a
   `TrimmedCurve` of the route; a custom motion a `Polyline` sampled at 257 points. A spot
   that does not move has no curve.
2. **A time map**: how far along the curve it is at each local count. It is piecewise linear
   between **knots**: the window start (distance 0), each timed waypoint (the arc length of
   that waypoint), and the window end (the full length).

Position at local count `τ`:

```text
u = clamp((τ - start) / (end - start), 0, 1)       share of the window passed
τ_e = start + ease(u) · (end - start)              eased time
s = interp(τ_e, knots_t, knots_s)                  meters along the curve
position = curve.point_at(s)
```

Why split space and time? With separate per-style formulas, every combination of style,
timed waypoints and easing would be a new case. One curve plus one time map covers all of
them. A new style only needs to build a curve. And since easing maps `[0, 1]` onto itself with
`e(0) = 0` and `e(1) = 1`, every style still ends exactly on its target.

![Arc length against local count for a move with window 1–7, a waypoint timed at count 3 and ease_in_out. The red knots are the time map; the blue curve is what positions use after easing.](figures/fig_engine_time.png)

## What one position() call does

```pycon
>>> import numpy as np
>>> from showpy.choreo.engine import PathEngine
>>> from showpy.choreo.models import Easing, PathRow, PathStyle, Waypoint
>>> from showpy.examples import two_set_show, with_rows
>>> row = PathRow(
...     entity="T1",
...     style=PathStyle.POLYLINE,
...     start=1.0,
...     end=7.0,
...     waypoints=(Waypoint(x=3.0, y=5.0, at=3.0),),
...     easing=Easing(kind="ease_in_out", strength=2.0),
... )
>>> show = with_rows({"T1": row})
>>> engine = PathEngine(show)
>>> engine.locate(4.0)
(('1', '2'), 4.0)
>>> plan = engine.compile(("1", "2")).plans["T1"]
>>> type(plan.curve).__name__, plan.curve.length(), plan.window, plan.knots_t, plan.knots_s
('Polyline', 8.0, (1.0, 7.0), (1.0, 3.0, 7.0), (0.0, 3.0, 8.0))
>>> [plan.pieces[i].kind for i in range(len(plan.pieces))]
['hold', 'line', 'line', 'hold']
>>> engine.position("T1", 4.0).round(4)
array([2.25, 6.  ])
```

Follow `engine.position("T1", 4.0)` through the code:

1. `position(entity, t)` calls `_resolve(t)`, which calls `locate(t)`. `locate` keeps the
   prefix sums of set counts (`_starts = [0, 8]`) and uses `bisect` to find that global count 4
   is inside transition `1→2` at local count `τ = 4`. Before count 0 or after the last set it
   returns `None`, and the spot stands at the first or last set.
2. `_plan(entity, tid)` calls `compile(tid)`, which returns the cached `CompiledTransition` or
   builds one: for every spot, `compile_entity` → `compile_plan(row, spec, a, b, motions)`.
3. `compile_plan` (in `engine_compile.py`) computes the window (`_window`), builds the curve
   (`_curve_for`: here `_waypoint_curve`, giving a `Polyline` through `(0, 5)`, `(3, 5)`,
   `(0, 9)`), checks continuity (`_require_end`), builds the knots (`_knots`) and the pieces
   (`_pieces`: a hold before the window, two line pieces, a hold after).
4. `validate_facing(plan)` checks the facing mode has the value it needs.
5. `plan_positions(plan, [4.0])` calls `plan_progress`: `u = (4 - 1)/6 = 0.5`,
   `ease(0.5) = 0.5` for `ease_in_out`, so `τ_e = 4`. Interpolating the knots
   `(1, 0), (3, 3), (7, 8)` at 4 gives `s = 3 + 5·(1/4) = 4.25`.
6. `plan.curve.point_at(4.25)`: the polyline's first leg is 3 m long, so the point is
   1.25 m into the second leg, which runs 5 m from `(3, 5)` toward `(0, 9)` with direction
   `(-0.6, 0.8)`. That is `(3 - 0.75, 5 + 1.0) = (2.25, 6.0)`, the Output above.

## Before, during and after the window

ADR 0002 decision 2: outside its window a spot stands still. Before `start` it is at the
previous set's placement, after `end` at the next set's. `on_field` follows the same rule:
the previous set's value before the window, the next set's after it, and **either** during
it, so an entrance is visible while the performer walks on.

## Facing in three phases

ADR 0002 decision 3, in `engine_facing.plan_facing`:

1. **Before the window**: the previous set's facing.
2. **During the window**: the row's `FacingMode` (chapter 11), blended in from the previous
   facing over `turn_counts`.
3. **After the window**: the next set's facing, blended in from the facing at the end of the
   window over `min(turn_counts, counts - end)`.

A blend over 0 counts snaps. Blending uses `turn(a, b, share, direction)`. Facing overrides
(`add_facing_override`) are applied last and win inside their global range, with the same
blend in and out.

![Facing over one transition: 0° before the window (counts 0–2), TRAVEL (135°) blended in over 1.5 counts, then the next set's 270° blended in after the window ends at 6.](figures/fig_facing_phases.png)

```pycon
>>> from showpy.choreo.models import FacingMode
>>> turning = PathRow(entity="T1", start=2.0, end=6.0, facing_mode=FacingMode.TRAVEL, turn_counts=1.5)
>>> base = two_set_show()
>>> moved = base.model_copy(
...     update={
...         "sets": (base.sets[0], base.sets[1].with_placements({"T1": {"x": 4.0, "facing": 270.0}}))
...     }
... )
>>> fe = PathEngine(with_rows({"T1": turning}, show=moved))
>>> [round(fe.facing_at("T1", t), 1) for t in (1.0, 2.75, 3.5, 5.0, 6.75, 8.0)]
[0.0, 67.5, 135.0, 135.0, 202.5, 270.0]
```

At count 2.75 the spot is halfway through its 1.5-count turn from 0° to the travel facing
135°: 67.5°. The window ends at 6. From there the spot blends from the facing at the end of
the window (135°) to the next set's 270° over `min(1.5, 8 - 6) = 1.5` counts; at 6.75 it is
halfway, 202.5°. At 8 it has arrived at 270°.

## Continuity checks

ADR 0002 decision 4. `hold`, `rotate`, `follow` and `custom` must end within `1e-6` m of the
target placement, or `compile` raises `ContinuityError`. `straight`, `polyline` and `curve`
end on the target by construction (the target is the curve's last vertex). The check happens
at compile time, so a bad path fails the first time anyone asks for any position in that
transition, not silently later.

```pycon
>>> from showpy.choreo.models import PathRow
>>> bad = with_rows({"T1": PathRow(entity="T1", style=PathStyle.HOLD)})
>>> PathEngine(bad).position("T1", 3.0)
Traceback (most recent call last):
  ...
showpy.core.errors.ContinuityError: CONTINUITY: hold path of T1 ends at (0.0, 5.0), not on its target (0.0, 9.0) (hint: change the path parameters or the target placement so they agree)
>>> late = with_rows({"T1": PathRow(entity="T1", start=6.0, end=9.0)})
>>> PathEngine(late).position("T1", 3.0)
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: window 6.0–9.0 of T1 does not fit 8.0 counts (hint: keep 0 <= start < end <= counts)
```

A `hold` row means "stay put", but set 2 moved T1 4 m upstage. The fix is to make the target
equal the start, or use a different style.

## Velocity and state

`velocity_at(entity, t)` is a central difference of the plan's own positions with
`h = 1e-4` counts (ADR 0002 decision 6), in meters per count. There is no second motion model
that could disagree with positions. `state_at` bundles position, facing, velocity, `moving`
and `on_field` into an `EntityState`; `sample(t)` returns a `Frame` of every spot's state;
`frames(t0, t1, per_count=8, fps=None)` yields frames per count, or per second of music
(through `count_to_seconds` and `seconds_to_count`, so holds and tempo changes are honored).

```pycon
>>> engine.velocity_at("T1", 2.0).round(4), engine.velocity_at("T1", 0.5)
(array([1., 0.]), array([0., 0.]))
>>> state = engine.state_at("T1", 5.0)
>>> state.moving, state.on_field, tuple(round(v, 3) for v in state.position)
(True, True, (1.0, 7.667))
>>> frames = list(PathEngine(two_set_show()).frames(0.0, 8.0, per_count=1))
>>> len(frames), frames[4].t, frames[4].tid, frames[4].states[0].position
(9, 4.0, ('1', '2'), (0.0, 7.0))
>>> PathEngine(two_set_show()).positions(4.0, "T1-T2")
array([[0., 7.],
       [2., 7.]])
```

`positions(t, sel)` accepts `"all"`, a selection expression, a list of IDs or a `Selection`;
strings are resolved with `showpy.cast.select.select`, so `"T1-T2"` is the range T1 to T2.

## Segments for exact collision checks

The checker must find the closest moment between every pair of spots, including crossings
that happen **between** counts. Sampling 8 times per count is not enough: two spots moving
at 3 m per count toward each other pass in about 0.06 counts (ADR 0002 alternatives). Instead,
`segments(tid, tol)` returns, per spot, a chain of `MotionSegment`s that are **linear in both
space and time**, each within `tol` meters (default 0.02) of the true motion. Between two
such segments the closest approach is a quadratic with an exact minimum (see `avoid` below),
so checks are exact to within `tol`.

How `entity_segments` builds them:

1. Start from the **edges**: 0, the counts, and every place the motion may kink, mapped into
   the window: time-map knots, curve breaks (polyline corners, spline knots, joins), easing
   breaks, and for `steps` the middle of each step, where its smoothstep turns from convex to
   concave.
2. For each interval `[lo, hi]`, measure how far the motion strays from the straight line
   between the end positions:
   - On a curve whose curvature has a closed-form bound (lines, polylines, arcs, circles, and
     trims or chains of them), the error is **bounded, not sampled**: the easing's largest
     gap from its chord, scaled by the distance travelled, plus `κ·L²/8` for the bend of an
     arc and the exact corner gap of a polyline. Accept within `tol`.
   - On any other curve (spline, ellipse, Bézier, SVG, spiral, custom motion), probe nine
     points at **jittered** shares, one in each ninth of the interval. The jitter is seeded
     per spot and transition from a stable digest, so every run probes the same points.
     Accept within `tol / 2`.
3. Otherwise split the interval in half and recurse. Past depth 20 it raises `PathError`
   `SEGMENT_BOUND` instead of returning a segment that breaks the bound.

Why a bound and jitter? Probes at fixed shares can line up with a periodic motion exactly. An
audit of the probe-only engine found a 4-cycle `weave` custom motion compiled to one segment
1.0 m off its path. A closed-form bound cannot be fooled by any spacing, and jittered probes
have no fixed spacing to line up with. A Hypothesis property test still checks every segment
at nine points, not only where the engine probed.

### The aliasing bug, and why easing breaks exist

Remember from chapter 11 that a `steps` easing equals linear time at the middle of each step.
Take `steps` with 4 steps over an 8-count window. The steps' middles are at counts 1, 3, 5
and 7. An earlier engine started from the time knots only and probed every eighth of an
interval, so the probes of `[0, 8]` were at counts 1, 2, ..., 7. At counts 1, 3, 5, 7 the eased
position equals the linear one exactly; at 2, 4, 6 (the step edges) it also does. **Every
probe sat exactly on the straight line**, so the whole stepped move was accepted as one
segment and the march-and-stop vanished. This is aliasing: the probe spacing
matched the period of the signal.

The fix has two parts. Subdivision starts from the easing's breaks: `easing_breaks(steps 4)` is
`[0.25, 0.5, 0.75]`, and the engine adds the middle of each step, so inside each piece the
smoothstep is purely convex or purely concave. And on a straight line the error is bounded in
closed form, with no probes to alias. Figure 12.3 replays the old probe-only subdivision next
to the current engine.

![The y position of a 4-step move (grey) and its time-linear segments (red). Left: the old probe-only subdivision without easing breaks; every probe lands on the line and one segment hides all four steps. Right: the current engine; 24 segments follow the motion within 2 cm.](figures/fig_segments.png)

```pycon
>>> steps = with_rows({"T1": PathRow(entity="T1", easing=Easing(kind="steps", strength=4.0))})
>>> segs = PathEngine(steps).entity_segments("T1", ("1", "2"))
>>> len(segs), segs[0].t0, segs[0].p0, round(segs[-1].t1, 6), segs[-1].p1
(24, 0.0, (0.0, 5.0), 8.0, (0.0, 9.0))
>>> worst = 0.0
>>> pe = PathEngine(steps)
>>> for seg in segs:
...     for share in np.linspace(0.05, 0.95, 19):
...         t = seg.t0 + share * (seg.t1 - seg.t0)
...         line_y = seg.p0[1] + share * (seg.p1[1] - seg.p0[1])
...         worst = max(worst, abs(pe.position("T1", t, local=("1", "2"))[1] - line_y))
>>> bool(worst <= 0.02)
True
```

## Speed

`speed(entity, tid, window=None)` sums the time-linear segments, so it uses exactly the
motion the checker sees. It returns `SpeedStats`: `distance`, moving `counts`, `m_per_count`,
`m_per_s` (through the clock, so tempo matters) and `max_instant` (the fastest segment).

```pycon
>>> from showpy.choreo.motion_stats import direction_of_travel, energy_curve, motion_contrast, speeds
>>> engine.speed("T1", ("1", "2"))
SpeedStats(distance=7.999999999999998, counts=6.0, m_per_count=1.333333333333333, m_per_s=2.666666666666666, max_instant=2.385310363079827)
>>> speeds(two_set_show(), ("1", "2"))[["entity", "distance", "m_per_count"]].head(2).to_string(
...     index=False
... )
'entity  distance  m_per_count\n    T1       4.0          0.5\n    T2       4.0          0.5'
```

The distance is the 8 m of the polyline, to rounding: the waypoint is a curve break, so a
segment ends exactly on the corner instead of cutting it. The fastest segment, 2.39 m per
count, is in the middle of the second leg, where `ease_in_out` is fastest.

## Measures over time: motion_stats.py

These live in `showpy.choreo`, not `showpy.geo`, because they need the engine (ADR 0002
addendum).

| Function                                      | Returns                                                                                                     |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `position_at(show, entity, t)`                | a position at a global count                                                                                |
| `speed(show, entity, tid, window)`            | `SpeedStats`                                                                                                |
| `speeds(show, tid)`                           | every spot ranked by peak then mean speed                                                                   |
| `direction_of_travel(show, entity, tid, tau)` | the facing of travel, or `None` when still                                                                  |
| `motion_contrast(show, tid)`                  | `MotionStats`: moving share, speed spread (coefficient of variation), direction variety (circular variance) |
| `energy_curve(show, per_count=1)`             | mean on-field speed through the show, as a pandas Series                                                    |
| `phrase_profile(show, t0, t1)`                | change, energy and density per phrase between markers                                                       |

**Circular variance** measures how spread directions are: average the unit vectors of every
moving spot's net travel direction; the variance is `1 - |mean vector|`. All alike gives 0;
evenly spread gives 1.

```pycon
>>> (
...     direction_of_travel(two_set_show(), "T1", ("1", "2"), 4.0),
...     motion_contrast(two_set_show(), ("1", "2")),
... )
(180.0, MotionStats(moving_share=1.0, speed_spread=0.0, direction_variety=0.0))
>>> curve = energy_curve(show, per_count=2)
>>> from guide_draw import sketch
>>> sketch.plot(
...     curve.index,
...     curve.values,
...     xlabel="global count",
...     ylabel="mean speed (m/count)",
...     caption="energy_curve() of the waypoint example: T1 is still until count 1, eases in and out, and arrives at 7.",
... )
```

## Collision help: avoid.py

Everything here is advice. The locked checker decides.

### Closest approach between two moving spots

Take two tracks that are linear in time on a shared interval: spot A from `a0` to `a1`, spot
B from `b0` to `b1`, as the share `s` goes from 0 to 1. Their difference is also linear:

```text
d(s) = (a0 - b0) + s·((a1 - a0) - (b1 - b0)) = d0 + s·w
|d(s)|² = |d0|² + 2s·(d0·w) + s²·(w·w)
```

That is a parabola in `s`. Its minimum is where the derivative `2(d0·w) + 2s(w·w)` is zero:
`s* = -(d0·w)/(w·w)`. The minimum on the interval is at `s*` clamped to `[0, 1]`. If
`w·w = 0` the spots move in parallel and the distance is constant.

`closest_approach(times_a, points_a, times_b, points_b)` merges both tracks' station times,
so between consecutive merged times both tracks are linear, then applies the formula on every
interval and keeps the minimum. With the engine's segments as tracks, the answer is exact to
within the segment tolerance.

![T1 and T2 swap places through the same point; the closest approach is at count 4, at 0 m.](figures/fig_closest.png)

```pycon
>>> from showpy.choreo.avoid import (
...     apply_fix,
...     closest_approach,
...     min_gaps,
...     suggest_delays,
...     suggest_waypoint,
... )
>>> closest_approach([0, 2], [(0, 0), (2, 0)], [0, 2], [(2, 1), (0, 1)])
(1.0, 1.0)
>>> from showpy.examples import crossing_show
>>> crossing = crossing_show()
>>> [(g.a, g.b, round(g.gap, 3), round(g.tau, 3)) for g in min_gaps(crossing, ("1", "2"), top=2)]
[('T1', 'T2', -0.6, 4.0), ('T2', 'T3', 3.4, 0.0)]
>>> fixes = suggest_delays(crossing, ("1", "2"), ("T1", "T2"))
>>> [(f.params["entity"], f.params["counts"], round(f.new_gap, 3)) for f in fixes[:2]]
[('T1', 4.0, 0.665), ('T2', 4.0, 0.665)]
>>> sketch.frames(crossing, (2.0, 4.0, 6.0), caption="crossing_show(): T1 and T2 meet at count 4.")
>>> fixed = crossing.model_copy(
...     update={"transitions": (apply_fix(crossing.transition(("1", "2")), fixes[0]),)}
... )
>>> sketch.frames(fixed, (2.0, 4.0, 6.0), caption="After apply_fix(delay T1 by 4): T2 passes first.")
```

`min_gaps` reports `-0.6`: the two 0.3 m footprints overlap by 0.6 m at count 4. Gaps are the
centre distance minus both footprints' `extent_m`.

| Function                                                 | Does                                                                                                                       |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `min_gaps(show, tid, sel, top)`                          | the `top` tightest on-field pairs, tightest first; a bounding-box broadphase skips pairs that cannot beat the current list |
| `suggest_delays(show, tid, pair, max_delay)`             | delays either spot in 0.5-count steps up to `max_delay`, keeping those that widen the gap; best first                      |
| `suggest_waypoint(show, tid, entity, around, clearance)` | two timed bends that take `entity` around `around` at their closest moment, one each side                                  |
| `suggest_reassignment(show, tid, sel, crossing_weight)`  | re-matches the spots to their own targets with a crossing penalty; apply with `match_ops.apply_match`                      |
| `separate_in_time(spec, ordered_sel, gap_counts)`        | staggers starts                                                                                                            |
| `apply_fix(spec, fix)`                                   | applies a delay, waypoint or stagger `Fix`                                                                                 |

Each `Fix` carries `new_gap` and `max_speed_after`, measured by re-running the engine on a
trial show, so you see the cost of a fix (a delayed spot must move faster) before you take
it.

```pycon
>>> from showpy.choreo.avoid import suggest_reassignment
>>> best = suggest_reassignment(crossing, ("1", "2"), ["T1", "T2"])
>>> best.crossings, best.assignment
(0, {'T1': 1, 'T2': 0})
>>> from showpy.choreo.engine_models import Fix
>>> apply_fix(
...     crossing.transition(("1", "2")),
...     Fix(kind="reassign", params={}, new_gap=1.0, max_speed_after=1.0),
... )
Traceback (most recent call last):
  ...
showpy.core.errors.PathError: PATH: a reassignment changes the next set, not the paths (hint: apply it with showpy.choreo.match_ops.apply_match(show, tid, result))
```

The hint names where to go next: a reassignment changes the next set, so apply it with
`showpy.choreo.match_ops.apply_match`, not with `apply_fix`.

## Caching and invalidate

`PathEngine(show, curve_tol=0.01, cache=True, motions=DEFAULT_MOTIONS)` caches compiled
transitions per instance. Shows are frozen, so a cache can only go stale if you keep using an
engine after building a new show; make a new engine for a new show. `invalidate(sets,
transitions)` clears this engine's memo for the transitions touching those sets.
`path_geometry(entity, tid)` returns the drawn path, `curve.to_polyline(curve_tol)`.

> **Check your understanding 12.a.** Why does `velocity_at` use a finite difference of
> positions instead of a formula per style?
>
> **Check your understanding 12.b.** Two spots move in parallel at the same speed. What does
> `closest_approach` return, and why is `w·w = 0` handled separately?
>
> **Check your understanding 12.c.** Why could probes at every eighth of an interval miss a
> 4-step `steps` easing?

## Exercises

**Exercise 12.1 (warm-up).** For the waypoint example at the start of the chapter, return
T1's position at global count 4 computed **by hand** from the knots and the polyline (no
engine). The check compares it with the engine.

**Exercise 12.2.** In the facing example, return T1's facing at local count 6.75. Then read
`plan_facing` and explain the value.

**Exercise 12.3.** For the tutorial-like show `two_set_show()` with T2 delayed by 4 counts
(keeping the end), return the local count where T2 is fastest and its peak speed in m/count.

**Exercise 12.4 (harder).** Return the closest approach `(tau, distance)` between T1 and T2
in `crossing_show()` computed with your own implementation of the formula over the engine's
`entity_segments`. The check compares with `min_gaps`.
