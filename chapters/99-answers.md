# Appendix: answer key

Answers to every "Check your understanding" question, then a worked solution to every exercise. Each solution is the real file in `exercises/answers/`, followed by the real output of its check script run with `--answers`.

## Check your understanding

**1.a** `showpy.geo.measure` imports only `showpy.choreo.models`, a data-class module that itself imports only `core`. It never imports choreo logic, so the logic layers stay intact.

**1.b** It walks straight from its placement in the previous set to its placement in the next set, over the full counts of the transition, with linear easing.

**2.a** 0°. The direction is `(0, -6)`, toward the audience. 270° would be the direction `(-1, 0)`, audience left. Do not confuse the facing with the arc angle of `(0, -1)`, which is 270°.

**2.b** Arc angles are math angles: 90° is `+y`, so the arc starts at `(0, 3)`.

**2.c** `with_placements` returns a new set and never changes the old one. Unless you keep the result (for example with `with_set(show, new_set)`), the show still holds the old set.

**3.a** A NumPy array inside a frozen model would still be mutable, it is not hashable, and it does not round-trip through JSON. Tuples are all three.

**3.b** `round_to(2.675)`, which rounds half away from zero on the decimal value and returns `2.68`.

**4.a** An arc has constant curvature, so equal arc lengths cut equal chords. A Bézier curve bends more in some places than others, so equal arcs have chords of different lengths.

**4.b** 270°. A mirror across `x = 0` has `L = diag(-1, 1)`, which maps the facing vector `(sin θ, -cos θ)` to `(-sin θ, -cos θ)`: the facing `360° - θ`.

**4.c** Every pair of Bridson samples is already at least the minimum gap apart, so any subset keeps that property.

**5.a** On a gentle ramp `k·Δ/r0` is tiny. `log(1 + x)` loses most of its digits to rounding when `x` is tiny, while `log1p(x)` and `expm1(x)` stay accurate.

**5.b** At 120 cpm a count is 0.5 s. Count 16 is at 8.0 s (the hold starts there). Count 17 is at `8 + 2 + 0.5 = 10.5` s.

**5.c** None. The sync offset only changes which part of the audio plays at each count.

**6.a** Operators apply left to right, so it is `((T1-T8 - group:flags) & tag:lead)`: trumpets T1 to T8 that are not flags and are tagged `lead`.

**6.b** A spot exists in every set. Before it enters, it needs a placement to walk from; `on_field=False` keeps it hidden and out of collision checks.

**7.a** Stage left. Stage directions are the performer's, facing the audience, so audience right is the performer's left.

**7.b** No rotation undoes a mirror, so the best rotation would fit mirrored points badly and pass the error on silently. Mirrored landmarks usually mean a wrong pairing; refusing makes the caller check it, and the hint names `mirror` for a deliberate flip.

**8.a** Determinism: the same inputs must give the same note, so tests and replays match. The library never reads the clock.

**9.a** The recipe is the designer's intent. Editing it (a radius, a member order) regenerates every dot consistently, and it stays small, editable JSON.

**9.b** When the widest angular gap between neighbouring points is more than 1.5 times the median gap: the points leave a hole, so they lie on an arc.

**10.a** The optimal largest cost is one of the matrix's costs, and feasibility is monotone in the threshold: if a threshold works, every larger one works. Binary search over the sorted costs finds the smallest feasible one exactly.

**10.b** Its objective is a sum of independent (spot, slot) costs. A crossing depends on two assignments at once, which such a sum cannot express.

**11.a** The side offset is `sin(2π·cycles·u)`. It must be 0 at `u = 1`, which needs `2·cycles` to be a whole number.

**11.b** The 4 m move now happens between counts 2 and 8, so 4/6 = 0.667 m per count.

**12.a** Positions already exist for every style, including custom motions. A finite difference of them can never disagree with positions, and no style needs its own derivative.

**12.b** The distance is constant. With `w·w = 0` the formula would divide by zero, so the code takes `s = 0` and returns the constant distance.

**12.c** Inside each step the smoothstep is exactly half done at the step's middle, and probes at every eighth of an 8-count window land on step edges and middles, where the eased position equals the linear one. Every probe sat on the line.

**13.a** A revision holds no author, so ShowPy cannot tell which change was the user's; the host can. `revert` is deterministic and lands as an ordinary new head, so history is never rewritten and every workspace sees the undo.

**13.b** The agent's save raises `ConflictError`, listing what landed. The agent should refresh, reload, reapply its edit and save again.

**14.a** Purity and determinism: a value can be passed around, tested and stored, and no hidden registry can depend on call order or on which process ran first.

**14.b** 3 s × 30 frames per second = 90 frames, all showing the held positions.

**15.a** `save_show` writes against the revision the show was loaded at. The designer had saved since, so the head moved and the transaction refused the stale base.

**15.b** Validation is structural. Collisions and spacing are safety rules that belong to a separate checker.

**16.a** Warnings announce future breakage, such as deprecations. Failing on them keeps the zero-warnings rule and catches problems before they become errors.

**16.b** Read the diff. If the change is intended, regenerate the fixture with `SHOWPY_UPDATE_GOLDEN=1` and have a human review it. If not, fix the code. Never regenerate just to turn the run green.

## Exercise solutions

### Exercise 1.1

Every class knows its module in `__module__`; `showpy.PathEngine` loads it lazily.

{{code: exercises/answers/ch01_ex1.py}}

{{check: ch01_ex1}}

### Exercise 1.2

`two_set_show()` has four spots and two sets. It stores no transition: rows are sparse, so an empty transition is not stored at all.

{{code: exercises/answers/ch01_ex2.py}}

{{check: ch01_ex2}}

### Exercise 1.3

Walk the AST of each file, skip nodes inside `if TYPE_CHECKING:` blocks, and collect the second part of every `showpy.<package>` import. `geo` imports `choreo` and `sheet` only for their data classes.

{{code: exercises/answers/ch01_ex3.py}}

{{check: ch01_ex3}}

### Exercise 2.1

The direction is `(-3, 0)`. `atan2(vx, -vy) = atan2(-3, 0) = -90°`, wrapped to 270°: audience left.

{{code: exercises/answers/ch02_ex1.py}}

{{check: ch02_ex1}}

### Exercise 2.2

The direction is `(0, -6)`. Its math angle is -90°, or 270°; its facing is 0°, toward the audience.

{{code: exercises/answers/ch02_ex2.py}}

{{check: ch02_ex2}}

### Exercise 2.3

Patch one placement with `with_placements` and swap the set in with `with_set`. Nothing is mutated.

{{code: exercises/answers/ch02_ex3.py}}

{{check: ch02_ex3}}

### Exercise 2.4

`scatter` draws all randomness from `seeded_rng(seed)`, so the same seed repeats exactly.

{{code: exercises/answers/ch02_ex4.py}}

{{check: ch02_ex4}}

### Exercise 3.1

`format_ranges` sorts naturally, then joins runs with an en dash.

{{code: exercises/answers/ch03_ex1.py}}

{{check: ch03_ex1}}

### Exercise 3.2

`chunk_counts` lets the last part absorb rounding, so the sum is exact.

{{code: exercises/answers/ch03_ex2.py}}

{{check: ch03_ex2}}

### Exercise 3.3

80 m² minus the 4 m² hole.

{{code: exercises/answers/ch03_ex3.py}}

{{check: ch03_ex3}}

### Exercise 3.4

`model_copy(update=...)` returns a new placement; `normalize_angle(390) = 30`.

{{code: exercises/answers/ch03_ex4.py}}

{{check: ch03_ex4}}

### Exercise 4.1

The arc is 20·π/3 = 20.944 m long; eight gaps of 2.618 m.

{{code: exercises/answers/ch04_ex1.py}}

{{check: ch04_ex1}}

### Exercise 4.2

Rotation adds 135°: 165°. The mirror maps θ to 360° - θ: 195°.

{{code: exercises/answers/ch04_ex2.py}}

{{check: ch04_ex2}}

### Exercise 4.3

A closed spline has one segment per point: 4 segments of 256 samples plus one row.

{{code: exercises/answers/ch04_ex3.py}}

{{check: ch04_ex3}}

### Exercise 4.4

`large-arc = 1` with `sweep = 0` picks the far center and a negative sweep beyond -180°.

{{code: exercises/answers/ch04_ex4.py}}

{{check: ch04_ex4}}

### Exercise 4.5

This is exactly what `scatter` does: Bridson samples, then farthest-point selection.

{{code: exercises/answers/ch04_ex5.py}}

{{check: ch04_ex5}}

### Exercise 5.1

64 counts at 144 cpm take 26.667 s, plus the 2 s hold.

{{code: exercises/answers/ch05_ex1.py}}

{{check: ch05_ex1}}

### Exercise 5.2

Invert `s = (60/k)·ln(r/r0)`: `c = r0·expm1(k·s/60)/k` with `k = 1.875`.

{{code: exercises/answers/ch05_ex2.py}}

{{check: ch05_ex2}}

### Exercise 5.3

Counts 0–31 are measures 1–8. Count 50 is 18 counts into 3/4: six full measures (9–14) and count 1 of measure 15.

{{code: exercises/answers/ch05_ex3.py}}

{{check: ch05_ex3}}

### Exercise 5.4

Tempo is linear in counts, so 150 cpm is halfway: count 16. Seconds `(60/1.875)·ln(150/120) = 7.141`.

{{code: exercises/answers/ch05_ex4.py}}

{{check: ch05_ex4}}

### Exercise 6.1

Parentheses group the two exclusions; `group:trumpets` keeps cast order.

{{code: exercises/answers/ch06_ex1.py}}

{{check: ch06_ex1}}

### Exercise 6.2

`add_spots_along` with set `2` places the flags on the field from set 2 and off it in set 1.

{{code: exercises/answers/ch06_ex2.py}}

{{check: ch06_ex2}}

### Exercise 6.3

`near` picks T2 and T3; ordering along a line that runs right to left reverses them.

{{code: exercises/answers/ch06_ex3.py}}

{{check: ch06_ex3}}

### Exercise 6.4

Every library error carries the position of the bad token in `context`.

{{code: exercises/answers/ch06_ex4.py}}

{{check: ch06_ex4}}

### Exercise 7.1

NCAA hashes are 60 ft = 18.288 m from each sideline.

{{code: exercises/answers/ch07_ex1.py}}

{{check: ch07_ex1}}

### Exercise 7.2

Short style writes `L2.25 U7.00`; `from_coords` reads it back.

{{code: exercises/answers/ch07_ex2.py}}

{{check: ch07_ex2}}

### Exercise 7.3

The canvas spans x from -12 to 12 and y from -2 to 12. `px = (5 + 12)·5 = 85`, `py = (12 - 5)·5 = 35`.

{{code: exercises/answers/ch07_ex3.py}}

{{check: ch07_ex3}}

### Exercise 7.4

The fit is a pure 90° rotation with scale 1 that maps the origin to `(10, 10)`.

{{code: exercises/answers/ch07_ex4.py}}

{{check: ch07_ex4}}

### Exercise 8.1

`Anchor.on_transition` attaches the note to `1→2`; `notes_for` finds it by the pair.

{{code: exercises/answers/ch08_ex1.py}}

{{check: ch08_ex1}}

### Exercise 8.2

The point note is 0.707 m away: inside 1 m, outside 0.5 m.

{{code: exercises/answers/ch08_ex2.py}}

{{check: ch08_ex2}}

### Exercise 8.3

A draft is a plain hidden `Note` by the agent; `accept_draft` adds only the chosen one, visible.

{{code: exercises/answers/ch08_ex3.py}}

{{check: ch08_ex3}}

### Exercise 9.1

Outward facings on a counter-clockwise circle start at 90° and grow by 360°/8.

{{code: exercises/answers/ch09_ex1.py}}

{{check: ch09_ex1}}

### Exercise 9.2

A block facing 180° has its own front row upstage and its own left on the audience's right, so its last slot is the audience's front-left.

{{code: exercises/answers/ch09_ex2.py}}

{{check: ch09_ex2}}

### Exercise 9.3

The arc runs left to right, so matching gives the leftmost spot the first slot.

{{code: exercises/answers/ch09_ex3.py}}

{{check: ch09_ex3}}

### Exercise 9.4

The gap from 200° back to 360° is 160°, more than 1.5 times the median gap, so it is an arc of 200°.

{{code: exercises/answers/ch09_ex4.py}}

{{check: ch09_ex4}}

### Exercise 10.1

Threshold 1 leaves row 2 without a slot; threshold 2 allows `0→1, 1→0, 2→2`.

{{code: exercises/answers/ch10_ex1.py}}

{{check: ch10_ex1}}

### Exercise 10.2

Slot 4 at `x = 10` would cost T4 5.66 m; the cap is 5 m, so slot 4 stays open.

{{code: exercises/answers/ch10_ex2.py}}

{{check: ch10_ex2}}

### Exercise 10.3

T1 must walk to the far right slot, crossing the other three moves.

{{code: exercises/answers/ch10_ex3.py}}

{{check: ch10_ex3}}

### Exercise 10.4

Keep a running minimum of the previous row while scanning columns left to right, and remember where it came from.

{{code: exercises/answers/ch10_ex4.py}}

{{check: ch10_ex4}}

### Exercise 11.1

With `direction="end"` the last spot gets delay 0 and the first `3·1.5 = 4.5`.

{{code: exercises/answers/ch11_ex1.py}}

{{check: ch11_ex1}}

### Exercise 11.2

`4·(1 - (1 - u)²)` for `u = 0, ¼, ½, ¾, 1`.

{{code: exercises/answers/ch11_ex2.py}}

{{check: ch11_ex2}}

### Exercise 11.3

`sin(πu)` is 0 at both ends, so the motion starts and ends on target; registration probes this.

{{code: exercises/answers/ch11_ex3.py}}

{{check: ch11_ex3}}

### Exercise 11.4

T1 at `(0, 5)` turns -90° about `(4, 5)`: from angle 180° to 90°, ending at `(4, 9)`.

{{code: exercises/answers/ch11_ex4.py}}

{{check: ch11_ex4}}

### Exercise 12.1

Ease the window share, interpolate the knots, then walk the polyline: `(2.25, 6.0)`.

{{code: exercises/answers/ch12_ex1.py}}

{{check: ch12_ex1}}

### Exercise 12.2

After the window the facing blends from 135° to 270° over 1.5 counts; 0.75 counts in it is 202.5°.

{{code: exercises/answers/ch12_ex2.py}}

{{check: ch12_ex2}}

### Exercise 12.3

A delayed straight move with `keep_end` walks 4 m in 4 counts: 1 m per count throughout.

{{code: exercises/answers/ch12_ex3.py}}

{{check: ch12_ex3}}

### Exercise 12.4

Merge the station times of both tracks, then minimize the parabola on each interval.

{{code: exercises/answers/ch12_ex4.py}}

{{check: ch12_ex4}}

### Exercise 13.1

The sub-set takes 3 of set 2's 8 counts, so set 2 keeps 5; `renumber` then names them 1–3.

{{code: exercises/answers/ch13_ex1.py}}

{{check: ch13_ex1}}

### Exercise 13.2

Two saves, two revisions; `get_show` reads the head.

{{code: exercises/answers/ch13_ex2.py}}

{{check: ch13_ex2}}

### Exercise 13.3

An entity pin covers the spot's placement in every set; both moves are reported.

{{code: exercises/answers/ch13_ex3.py}}

{{check: ch13_ex3}}

### Exercise 13.4

The agent's workspace starts at the designer's revision, so the save lands; it writes only set 2's placements and its new form.

{{code: exercises/answers/ch13_ex4.py}}

{{check: ch13_ex4}}

### Exercise 14.1

The coordinate sheet describes the move from the path row: delay 2, then 6 counts of movement.

{{code: exercises/answers/ch14_ex1.py}}

{{check: ch14_ex1}}

### Exercise 14.2

At count 4 (2 s at 120 cpm) T4 is halfway: `(6, 7)`.

{{code: exercises/answers/ch14_ex2.py}}

{{check: ch14_ex2}}

### Exercise 14.3

`swap_claims` swaps the performers of two claimed spots.

{{code: exercises/answers/ch14_ex3.py}}

{{check: ch14_ex3}}

### Exercise 14.4

Lead-in 1.25 s, plus count 8 at 4 s, plus the 2 s hold before it.

{{code: exercises/answers/ch14_ex4.py}}

{{check: ch14_ex4}}

### Exercise 15.1

The stagger delays T8 by 7 counts and keeps the end at 16.

{{code: exercises/answers/ch15_ex1.py}}

{{check: ch15_ex1}}

### Exercise 15.2

`follow_and_set_targets` wrote the flags' ends along the route.

{{code: exercises/answers/ch15_ex2.py}}

{{check: ch15_ex2}}

### Exercise 15.3

Starting the inside pair first keeps the inner paths from crossing waiting spots.

{{code: exercises/answers/ch15_ex3.py}}

{{check: ch15_ex3}}

### Exercise 16.1

`normalize_angle` wraps any float into `[0, 360)`.

{{code: exercises/answers/ch16_ex1.py}}

{{check: ch16_ex1}}

### Exercise 16.2

The clock's inverse is analytic, so the round trip is exact to rounding.

{{code: exercises/answers/ch16_ex2.py}}

{{check: ch16_ex2}}

### Exercise 16.3

On a Bézier curve equal arc lengths give unequal chords.

{{code: exercises/answers/ch16_ex3.py}}

{{check: ch16_ex3}}

### Exercise 17.1

`showpy.suggest_swaps` resolves lazily to `showpy.choreo.match_ops`.

{{code: exercises/answers/ch17_ex1.py}}

{{check: ch17_ex1}}

### Exercise 17.2

`showpy.__all__` lists every public name.

{{code: exercises/answers/ch17_ex2.py}}

{{check: ch17_ex2}}

### Exercise 17.3

Each public function's docstring starts with a verb-first summary line.

{{code: exercises/answers/ch17_ex3.py}}

{{check: ch17_ex3}}

### Capstone

See chapter 18 for the reference solution and its measurements.
