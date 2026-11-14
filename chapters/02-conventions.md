# Conventions from first principles

Every module follows the same few rules. Learn them once and the rest of the library reads
easily. Each rule here has a reason, and most of them have a test that fails if the rule is
broken.

## Meters, and where the origin sits

The library has one internal unit system:

- lengths in **meters**,
- angles in **degrees**,
- time in **counts**.

Nothing else is stored. Feet, yards and 8-to-5 steps exist only for display, and conversion
happens in exactly three places: `core/units.py`, `sheet/coords.py` and (later) the pack
language modules. If two parts of the code each converted units, they could round
differently and disagree by a centimeter. One conversion point rules that out.

The stage plane is the flat sheet seen from above.

- The origin `(0, 0)` is the **front-center** of the sheet: the middle of the edge nearest the
  audience. On a football field it is the 50-yard line on the front (home) sideline.
- `x` runs from `-width/2` (audience left) to `+width/2` (audience right).
- `y` runs from `0` at the front edge to `depth` at the back. Larger `y` is farther from the
  audience, which drill writers call upstage.

![The stage plane. The origin is the front-center. A facing of 0° points at the audience; facings grow counter-clockwise seen from above.](figures/fig_coordinates.png)

Why front-center? The center line `x = 0` is the mirror axis of almost every show, so mirror
images are just `x → -x`. Every point on the field has `y ≥ 0`, so "how far upstage" is a
plain number (ADR 0001 decision 4).

```pycon
>>> from showpy.sheet.templates import get_sheet
>>> field = get_sheet("sheet:hs-football")
>>> field.size_m
(109.728, 48.767999999999994)
>>> [lm.name for lm in field.landmarks[:2]], field.landmarks[0].geometry
(['center', 'back center'], ((0.0, 0.0),))
```

The field is 120 yards (109.728 m) wide including end zones and 160 feet (48.768 m) deep.
The landmark called `center` sits at `(0, 0)`. The odd `48.767999999999994` is how Python
prints the nearest binary float to 48.768; the library compares floats with a tolerance, never
with `==`.

### Converting units

`convert(value, from_unit, to_unit)` is the only conversion function. Units are looked up in
an immutable `UnitRegistry`, which maps a unit name to meters per unit.

```pycon
>>> from showpy.core.units import DEFAULT_UNITS, convert, register_unit
>>> convert(5.0, "yd", "m")
4.572
>>> steps = register_unit(DEFAULT_UNITS, "step85", 0.5715)
>>> round(convert(4.572, "m", "step85", steps), 6)
8.0
>>> "step85" in DEFAULT_UNITS.meters_per_unit
False
```

Five yards is 4.572 m, which is eight 8-to-5 steps of 0.5715 m. `register_unit` returned a
new registry. The default registry did not change.

Under the hood: `convert` calls `registry.factor(from_unit)` and `registry.factor(to_unit)`,
then returns `value * from_factor / to_factor`. `factor` raises `UnknownRefError` with close
matches when the name is unknown.

What if you get it wrong?

```pycon
>>> convert(1.0, "yrd", "m")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown unit 'yrd' (hint: use one of cm, ft, in, m, mm, yd)
```

Read every library error the same way: the class (`UnknownRefError`), the stable code
(`UNKNOWN_REF`), the message (`unknown unit 'yrd'`) and the hint after `hint:`, which says
what is allowed instead. Section 2.7 explains the error model.

## Facing degrees, and why the facing vector is (sin θ, −cos θ)

A facing says which way a performer looks. The rule:

- 0° faces the audience, which is the `-y` direction.
- Angles grow counter-clockwise seen from above. So 90° faces `+x` (audience right), 180°
  faces upstage (`+y`) and 270° faces `-x` (audience left).

To turn a facing into a direction we need a unit vector `v(θ)` with `v(0) = (0, -1)` that
turns counter-clockwise as θ grows. Start from the usual math direction `(cos φ, sin φ)`,
which points along `+x` at φ = 0. The audience direction `(0, -1)` is φ = -90°. Turning
counter-clockwise by θ from there gives φ = θ - 90°, so

```text
v(θ) = (cos(θ - 90°), sin(θ - 90°)) = (sin θ, -cos θ)
```

using `cos(θ - 90°) = sin θ` and `sin(θ - 90°) = -cos θ`. Check four cases:

| θ    | sin θ | -cos θ | direction            |
| ---- | ----- | ------ | -------------------- |
| 0°   | 0     | -1     | toward the audience  |
| 90°  | 1     | 0      | audience right, `+x` |
| 180° | 0     | 1      | upstage, `+y`        |
| 270° | -1    | 0      | audience left, `-x`  |

The inverse, `vector_facing(v)`, uses `atan2(vx, -vy)`, then wraps the result into
`[0, 360)`.

```pycon
>>> from showpy.core.units import angle_diff, facing_vector, normalize_angle, vector_facing
>>> facing_vector(90.0)
(1.0, -6.123233995736766e-17)
>>> vector_facing((-1.0, 0.0))
270.0
>>> vector_facing((1.0, 1.0))
135.0
>>> normalize_angle(-90.0), angle_diff(350.0, 10.0), angle_diff(10.0, 350.0)
(270.0, 20.0, -20.0)
```

Worked example. A performer at `(2, 5)` must face a drum major at `(-2, 9)`. The direction is
`(-4, 4)`. Then `atan2(vx, -vy) = atan2(-4, -4) = -135°`, which wraps to 225°. Check:
`v(225°) = (sin 225°, -cos 225°) = (-0.707, 0.707)`, which points left and upstage, as
expected.

`-6.12e-17` is floating-point noise: `cos 90°` is not exactly 0 in binary. It is why the
library compares with `approx_equal` and a tolerance.

`angle_diff(a, b)` returns the signed shortest turn from `a` to `b`, in `(-180, 180]`. From
350° to 10° is +20° (counter-clockwise through 0), not -340°.

## Arc angles use the math convention

Arcs, circles, spirals, rotations and grid rotations use the ordinary math convention: 0° is
`+x` and positive angles turn counter-clockwise. Facings use 0° = `-y`. Figure 2.2 puts them
side by side.

![Facing degrees (left) and arc angles (right). Both turn counter-clockwise; they differ by where 0° points: facing 0° is the audience (−y), arc 0° is +x.](figures/fig_angles.png)

Why two conventions? Each is natural for its job. Designers say "face the audience" far more
often than "face east", so facing 0° is the audience. Geometry formulas such as
`center + r·(cos a, sin a)` are standard with math angles, and rotation matrices use them too.
Mixing them up is the most common mistake, so remember the rule: **a facing is never an arc
angle**. They convert by `facing = arc_angle + 90°`.

```pycon
>>> import math
>>> from showpy.geo.shapes import arc
>>> quarter = arc((0.0, 0.0), 2.0, 0.0, 90.0)
>>> quarter.point_at(0.0), quarter.point_at(quarter.length()).round(9)
(array([2., 0.]), array([0., 2.]))
>>> quarter.tangent_at(0.0).round(9), vector_facing((0.0, 1.0))
(array([-0.,  1.]), 180.0)
```

The arc starts at math angle 0° (the point `(2, 0)`), sweeps +90° counter-clockwise and ends
at `(0, 2)`. At the start it travels along `+y`, and a spot walking that way has facing
180°: upstage.

## Counts as the unit of time

Time in a show is measured in **counts**: musical beats. A transition of 16 counts lasts 16
beats however fast the music is. Counts are stored, seconds are derived.

- Global count 0 is the show start and maps to 0 seconds (ADR 0001 decision 5).
- Set `1` has `counts = 0`. Every later set's `counts` is the length of the move into it.
- The global count where a set is reached is the sum of the counts of the sets up to it.
- Measure and count labels for display are 1-based, like musicians say them. Stored counts
  are 0-based.

Why count 0 at the start? It makes "the global count of set k" a plain prefix sum. It makes
the clock function start at the origin: 0 counts is 0 seconds. And audio needs only one
number to line up: `sync_offset_s` is the audio time that plays at count 0.

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.show.manage import index
>>> from showpy.time.clock import count_to_seconds
>>> show = two_set_show()
>>> [(e.set, e.counts, e.start_count, e.seconds) for e in index(show).entries]
[('1', 0.0, 0.0, 0.0), ('2', 8.0, 8.0, 4.0)]
>>> count_to_seconds(show.timeline, 8.0)
4.0
```

At 120 counts per minute one count is 0.5 s, so set 2 at count 8 is reached at 4.0 s.

## Immutability: pure functions return new objects

Every data class inherits `FrozenModel`, a Pydantic v2 model with `frozen=True` and
`extra="forbid"`. You cannot assign to a field, and you cannot add a field by accident.
"Edit" functions return a new object and leave the input alone.

```pycon
>>> s1 = show.set("1")
>>> s1.get("T1").x
0.0
>>> s1.get("T1").x = 3.0
Traceback (most recent call last):
  ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for Placement
x
  Instance is frozen [type=frozen_instance, input_value=3.0, input_type=float]
    For further information visit https://errors.pydantic.dev/2.14/v/frozen_instance
>>> moved = s1.with_placements({"T1": {"x": 3.0}})
>>> s1.get("T1").x, moved.get("T1").x
(0.0, 3.0)
>>> moved is s1, moved.get("T2") is s1.get("T2")
(False, True)
```

`with_placements` patched one placement and returned a new set. The old set still says
`x = 0`. Unchanged placements are shared, not copied, so a new show costs little memory.

Why bother?

- **Undo is free.** Keep the old object and you have the old state.
- **Caches are safe.** `PathEngine` caches compiled motion per show. Since a show cannot
  change, a cache can never go stale while you hold it.
- **No hidden coupling.** A function cannot change your data behind your back.

The pitfall: forgetting to keep the result. `with_placements(...)` on its own line does
nothing useful. Always write `show = f(show, ...)`.

## Determinism and seeded randomness

Same inputs, same outputs, every time (CLAUDE.md rule 3). Three habits make this true:

1. The only random generator is `core.util.seeded_rng(seed)`, which wraps
   `numpy.random.default_rng(seed)`. Functions that need randomness, like `scatter`, take a
   `seed` argument with a default.
2. No library function reads the clock. Every time stamp is an explicit `at: datetime`
   argument (ADR 0001 decision 8): note times, revision times, claim times.
3. Ties are broken on purpose, usually by natural ID order, so dict or input order cannot
   change a result. `match` sorts spots naturally before solving.

```pycon
>>> from showpy.geo.regions import region
>>> from showpy.geo.spacing import scatter
>>> area = region([(0, 0), (10, 0), (10, 6), (0, 6)])
>>> a, b = scatter(area, 6, 1.5, seed=7), scatter(area, 6, 1.5, seed=7)
>>> bool((a == b).all()), bool((a == scatter(area, 6, 1.5, seed=8)).all())
(True, False)
>>> from showpy.core.util import natural_sort
>>> natural_sort(["T10", "T2", "T1"])
['T1', 'T2', 'T10']
>>> from guide_draw import sketch
>>> sketch.points(
...     a,
...     scatter(area, 6, 1.5, seed=8),
...     labels=("seed 7", "seed 8"),
...     caption="scatter() with seed 7 and seed 8: same rules, different picture.",
... )
```

The same seed gives bit-identical points; another seed gives another picture.

Why it matters: a show is built by scripts. If a script gave a different set each run, a
rebuild would move performers for no reason, golden tests would flicker, and two people
could not reproduce each other's results.

## Errors that carry a code, a message, context and a hint

Every library error is a `ShowPyError` subclass with four parts:

| Part      | Meaning                                  | Example                           |
| --------- | ---------------------------------------- | --------------------------------- |
| `code`    | Stable machine-readable code             | `LOCKED`                          |
| `message` | What went wrong                          | `T1 is pinned in set 2`           |
| `context` | Values for debugging without reproducing | `{"entity": "T1"}`                |
| `hint`    | What the caller is allowed to do instead | `pass force=True as the designer` |

`str(error)` prints `CODE: message (hint: hint)`. The hierarchy is in `core/errors.py`:
`UnknownRefError`, `SchemaError`, `GeometryError` (with `ZeroLengthError`), `SpacingError`,
`TimeRangeError`, `TimelineError`, `SurfaceError`, `MatchError`, `PathError` (with
`ContinuityError`), `LockedError`, `StorageError` (with `ConflictError`) and
`ValidationError`.

```pycon
>>> from showpy.core.errors import ShowPyError
>>> try:
...     show.set("3")
... except ShowPyError as error:
...     print(type(error).__name__, error.code)
...     print("message:", error.message)
...     print("hint:", error.hint)
...     print("context:", error.context)
UnknownRefError UNKNOWN_REF
message: unknown set '3'
hint: known sets: 1, 2
context: {'set': '3'}
```

Why errors teach: the main caller is often an agent writing a script. A hint like "known sets:
1, 2" lets it fix the call on the next try, and a stable `code` lets a program react
without parsing English. There is no bare `ValueError` in the public API.

## Pins, locks and force=True

The designer owns the show. A **pin** is the designer's lock on something:

- `Placement.pinned`: this spot's placement in this set is locked.
- `Form.locked`: this form is locked.
- `PathRow.locked`: this spot's path in this transition is locked.
- `Show.pins`: the records behind the flags, each with who pinned it and why
  (`showpy.show.pinning.pin` sets both).

Every function that edits sets, forms or paths checks the flags. It raises `LockedError`
unless the caller passes `force=True`. Agents never pass `force`; the designer may.

```pycon
>>> pinned = s1.with_placements({"T1": {"pinned": True}})
>>> pinned.with_placements({"T1": {"x": 9.0}})
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: T1 is pinned in set 1 (hint: unpin it first, or pass force=True as the designer)
>>> pinned.with_placements({"T1": {"x": 9.0}}, force=True).get("T1").x
9.0
```

Under the hood: `Set.with_placements` looks at every placement it would replace. If the old
placement is pinned and `force` is false, it raises before building anything. Storage adds a
second guard: when an agent's workspace saves a show, `show.locks.require_unlocked` compares
the stored show with the new one and refuses any change to a pinned or locked item, however
it was made.

> **Check your understanding 2.a.** A spot at `(0, 10)` must face a point at `(0, 4)`. What
> is its facing, and why is it not 270°?
>
> **Check your understanding 2.b.** `arc((0, 0), 3, 90, 90)` starts at which point?
>
> **Check your understanding 2.c.** Why does `with_placements` on its own line have no effect
> on your show?

## Exercises

**Exercise 2.1 (warm-up).** Return the facing, in degrees, of a spot at `(4, 6)` that looks at
a spot at `(1, 6)`. Then explain in one sentence why it is 270°.

**Exercise 2.2.** Return the arc angle (math convention) and the facing of the direction
from the center `(0, 10)` to the point `(0, 4)`, as a tuple `(arc_deg, facing_deg)`, both in
`[0, 360)`.

**Exercise 2.3.** Write `solve(show)` that returns a new show where `T1` in set `2` stands
1 m further upstage. The input show must not change. Use `showpy.choreo.match_ops.with_set`.

**Exercise 2.4 (harder).** Write `solve(seed)` that returns 12 points scattered in the
rectangle `(0, 0)–(12, 8)` with a 1.5 m minimum gap. The check calls it twice with the same
seed (results must be identical) and with another seed (results must differ), and checks the
gap.
