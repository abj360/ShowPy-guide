# showpy.core: the foundation

`showpy.core` holds what every other package needs: errors, ID formats, shared types, units,
small utilities, the `Selection` model and validation reports. It imports nothing else from
`showpy`. Its seven modules are short; read them once and the rest of the library uses them
without comment.

## errors.py: the ShowPyError family

**What it is for.** One base class, `ShowPyError`, and one subclass per kind of failure. Every
error carries `code`, `message`, `context` and `hint` (section 2.7).

**Inputs.** `ShowPyError(message, *, hint, context=None, code=None)`. `hint` is required, so a
raise site cannot forget it. `code` defaults to the class's `default_code`.

| Class               | `default_code` | Raised when                                                |
| ------------------- | -------------- | ---------------------------------------------------------- |
| `UnknownRefError`   | `UNKNOWN_REF`  | an ID, name or unit does not resolve                       |
| `VersionError`      | `VERSION`      | a pinned version is missing or incompatible                |
| `SchemaError`       | `SCHEMA`       | data fails its schema or text format                       |
| `GeometryError`     | `GEOMETRY`     | a shape is degenerate (zero radius, collinear arc points)  |
| `ZeroLengthError`   | `ZERO_LENGTH`  | someone asks for the direction of a zero vector            |
| `SpacingError`      | `SPACING`      | items do not fit; `context["max_fit"]` says how many would |
| `TimeRangeError`    | `TIME_RANGE`   | a time is out of range, or start ≥ end                     |
| `TimelineError`     | `TIMELINE`     | tempo, measure or hold data are inconsistent               |
| `SurfaceError`      | `SURFACE`      | a point is off the sheet                                   |
| `MatchError`        | `MATCH`        | an assignment problem has no feasible solution             |
| `PathError`         | `PATH`         | a path instruction is invalid                              |
| `ContinuityError`   | `CONTINUITY`   | a path does not end on its target placement                |
| `LockedError`       | `LOCKED`       | an edit touches a pinned or locked item                    |
| `StorageError`      | `STORAGE`      | persistence fails                                          |
| `ConflictError`     | `CONFLICT`     | a concurrent edit landed first                             |
| `ValidationError`   | `VALIDATION`   | a structural integrity check fails                         |
| `DeprecatedWarning` | (a warning)    | a deprecated API was used                                  |

```pycon
>>> from showpy.core.errors import ContinuityError, PathError, ShowPyError, SpacingError
>>> error = SpacingError("only 7 spots fit", hint="lower n", context={"max_fit": 7})
>>> str(error)
'SPACING: only 7 spots fit (hint: lower n)'
>>> issubclass(ContinuityError, PathError), issubclass(PathError, ShowPyError)
(True, True)
>>> ShowPyError("no hint given")
Traceback (most recent call last):
  ...
TypeError: ShowPyError.__init__() missing 1 required keyword-only argument: 'hint'
```

**Pitfall.** Catch the narrowest class that fits. `except PathError` also catches
`ContinuityError`; `except ShowPyError` catches everything from the library.

## ids.py: references and transition IDs

IDs are plain strings with type aliases (`SpotId`, `SetId`, `FormId`, `RouteId`, `ZoneId`,
`LandmarkId`, `SheetRef`). A transition ID is a pair `(from_set, to_set)`.

- `parse_ref(text)` reads `kind:id@version` into `(kind, id, version or None)`.
- `format_ref(kind, ref_id, version=None)` writes it back.
- `parse_tid(text)` reads `12→13` or `12->13`; `format_tid(tid)` writes `12→13`.

```pycon
>>> from showpy.core.ids import format_ref, format_tid, parse_ref, parse_tid
>>> parse_ref("sheet:hs-football@1"), parse_ref("sheet:hs-football")
(('sheet', 'hs-football', '1'), ('sheet', 'hs-football', None))
>>> format_ref("sheet", "gym", "2"), parse_tid("12->12A"), format_tid(("12", "12A"))
('sheet:gym@2', ('12', '12A'), '12→12A')
>>> parse_ref("hs-football")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: bad reference 'hs-football' (hint: write references as kind:id or kind:id@version)
```

Under the hood: `parse_ref` matches the regular expression `REF_PATTERN`,
`^kind:id(@version)?$`, where `kind` starts with a letter. Storage writes transition folders
as `12-12A` (see `paths_doc` in chapter 13) because `→` is awkward in file names.

## types.py: aliases, FrozenModel, Box2, Box3 and Region

The aliases document units in signatures: `Meters`, `Seconds`, `Count`, `Degrees` and
`CountsPerMinute` are all `float`. `Point` is `tuple[float, float]`, `Ring` is a tuple of
points, and `Points` is a NumPy `(N, 2)` float array.

The split between `Point` and `Points` is deliberate (ADR 0001 decision 7). **Stored** data
uses tuples, which are immutable, hashable and JSON-safe. **Computation** uses arrays, which
are fast. A NumPy array inside a frozen model would still be mutable, so models never hold
one.

- `FrozenModel`: the base of every data class: `frozen=True`, `extra="forbid"`.
- `Box2(min, max)`: a bounding box, with `size` and `center` properties.
- `Box3`: the same in 3D, kept for later.
- `Region(exterior, holes=())`: an area as rings, which survives JSON. `to_shapely()` and
  `Region.from_shapely(polygon)` convert to and from Shapely polygons.

```pycon
>>> from showpy.core.types import Box2, Region
>>> box = Box2(min=(-2.0, 0.0), max=(4.0, 3.0))
>>> box.size, box.center
((6.0, 3.0), (1.0, 1.5))
>>> donut = Region(exterior=((0, 0), (6, 0), (6, 6), (0, 6)), holes=(((2, 2), (4, 2), (4, 4), (2, 4)),))
>>> donut.to_shapely().area
32.0
>>> Region.from_shapely(donut.to_shapely()) == donut
True
>>> Box2(min=(0, 0), max=(1, 1), color="red")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: Box2 rejects 1 field(s): color: Extra inputs are not permitted (hint: fix the fields named in context)
>>> Box2(min=(0, 0), max=(float("nan"), 1))
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: Box2 rejects 1 field(s): max.0: Input should be a finite number (hint: fix the fields named in context)
```

The donut is a 6 × 6 square (36 m²) with a 2 × 2 hole (4 m²): 32 m². `extra="forbid"`
rejected the unknown field `color` instead of silently storing it, and NaN is refused in every
float field, as is infinity. Constructors and `model_validate` raise `SchemaError`, the
library's own error, not Pydantic's `ValidationError`; `SchemaError` is not a `ValueError`, so
catch it by name or as `ShowPyError`.

## units.py: the only conversion point

| Function                                       | Does                                              | Example                                |
| ---------------------------------------------- | ------------------------------------------------- | -------------------------------------- |
| `UnitRegistry(meters_per_unit)`                | maps unit name to meters per unit; `factor(name)` | `DEFAULT_UNITS.factor("ft")` is 0.3048 |
| `convert(value, from_unit, to_unit, registry)` | `value · f_from / f_to`                           | 3 ft → 1 yd                            |
| `register_unit(registry, name, m)`             | returns a new registry with one more unit         | an 8-to-5 step                         |
| `units()`                                      | the default units as a dict                       |                                        |
| `normalize_angle(a)`                           | wraps into `[0, 360)`                             | -90 → 270                              |
| `angle_diff(a, b)`                             | signed shortest turn, in `(-180, 180]`            | 350 → 10 is +20                        |
| `facing_vector(θ)`                             | `(sin θ, -cos θ)`                                 | 0° → `(0, -1)`                         |
| `vector_facing(v)`                             | inverse; raises on a zero vector                  | `(1, 0)` → 90°                         |
| `round_to(value, precision)`                   | rounds half away from zero, for display           | 2.345 → 2.35                           |

```pycon
>>> from showpy.core.units import round_to, units, vector_facing
>>> sorted(units())
['cm', 'ft', 'in', 'm', 'mm', 'yd']
>>> round(2.345, 2), round_to(2.345), round_to(-2.345), round_to(7.3, 0.5)
(2.35, 2.35, -2.35, 7.5)
>>> round(0.125, 2), round_to(0.125)
(0.12, 0.13)
>>> vector_facing((0.0, 0.0))
Traceback (most recent call last):
  ...
showpy.core.errors.ZeroLengthError: ZERO_LENGTH: facing of a zero vector is undefined (hint: pass a non-zero direction or keep the previous facing)
```

Python's `round` uses banker's rounding on the binary value, so `round(0.125, 2)` gives
`0.12`. Printed coordinates must round the way people expect, so `round_to` rounds half away
from zero and gives `0.13`. Use `round_to` only for display; never round stored positions.

## util.py: small shared helpers

**`natural_sort(ids)`** sorts so `T2` comes before `T10`: digit runs compare as numbers.

**`parse_range(text)`** expands `T1-T8` into eight IDs; a single ID returns itself.
**`format_ranges(ids)`** compacts IDs into runs such as `T1–T3, T7`, using an en dash.

**`approx_equal(a, b, tol=1e-6)`** compares numbers or arrays with an absolute tolerance; a
shape mismatch is unequal. Tests use it for every float comparison.

**`seeded_rng(seed)`** returns the only random generator allowed in the library.

**`as_points(obj)`** turns a point, a list of points, an array, Shapely geometry or objects
with `x`/`y` into an `(N, 2)` float array. Functions that accept "anything point-like" call it
first.

**`content_hash(obj, *, domain="showpy.content")`** returns a SHA-256 hex digest of canonical
content: models are dumped, sets sorted and `-0.0` made `0.0`, then the value is hashed as RFC
8785 canonical JSON under its domain tag. Equal content hashes the same on every machine and
under every hash seed, and equal content in two domains (a revision and an asset, say) never
collides. Revisions, set scripts (`source_hash`) and assets use it.

**`chunk_counts(total, parts)`** splits counts into equal parts whose sum is exactly `total`.

**`close_matches(name, candidates)`** suggests up to three known names for error hints.

**`log(msg, **fields)`** writes `msg key=value ...`to the`showpy` logger.
**`timer()`** is a context manager yielding a `Timer`whose`elapsed_ms` is set on exit. It
reads the clock, so it is only for build reports; it never feeds library logic.

```pycon
>>> from showpy.core.util import (
...     approx_equal,
...     as_points,
...     chunk_counts,
...     close_matches,
...     content_hash,
...     format_ranges,
...     natural_sort,
...     parse_range,
... )
>>> parse_range("T8-T11"), format_ranges(["T1", "T2", "T3", "T7", "F1"])
(['T8', 'T9', 'T10', 'T11'], 'F1, T1–T3, T7')
>>> natural_sort(["T10", "B2", "T9"])
['B2', 'T9', 'T10']
>>> chunk_counts(10.0, 3), sum(chunk_counts(10.0, 3))
([3.3333333333333335, 3.3333333333333335, 3.333333333333333], 10.0)
>>> approx_equal(0.1 + 0.2, 0.3), 0.1 + 0.2 == 0.3, approx_equal([1, 2], [1, 2, 3])
(True, False, False)
>>> as_points((1, 2)).tolist(), as_points([(0, 0), (3, 4)]).shape
([[1.0, 2.0]], (2, 2))
>>> content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})
True
>>> close_matches("tpt", ["trumpets", "tubas", "flags"])
['trumpets']
>>> parse_range("T8-F2")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: bad range 'T8-F2' (hint: use one prefix and an ascending range, e.g. T1-T8)
```

Look at `chunk_counts(10, 3)`. Three times `3.3333333333333335` would sum to
`10.000000000000002`. The function makes the last part absorb the rounding, so the sum is
exactly 10. That matters when parts are added back up into a transition's counts.

## selection.py: Selection

A `Selection` is an ordered, duplicate-free tuple of spot IDs plus a `description`. A repeated
ID is dropped when the model is built, keeping its first position. It supports `|` (union, keeping the left order then new IDs), `&` (intersection), `-`
(difference), `len`, iteration and `in`. The `Selector` type alias names anything that picks
spots: an expression string, a list of IDs, or a `Selection`. Expressions are parsed by
`showpy.cast.select.select` (chapter 6).

```pycon
>>> from showpy.core.selection import Selection
>>> a, b = Selection(ids=("T1", "T2", "T3")), Selection(ids=("T3", "T4"))
>>> (a | b).ids, (a & b).ids, (a - b).ids, len(a), "T2" in a
(('T1', 'T2', 'T3', 'T4'), ('T3',), ('T1', 'T2'), 3, True)
>>> Selection(ids=("T1", "T2", "T1"))
Selection(ids=('T1', 'T2'), description='')
```

## validation.py: ValidationIssue and ValidationReport

Validators never raise on bad data. They return a `ValidationReport` holding
`ValidationIssue`s, each with `level` (`error` or `warning`), `code`, `where`, `message` and
`hint`. `report.ok` is true when no issue is an error, so warnings never block.
`ValidationReport.merge(*reports)` concatenates in order, and `str(report)` prints one terse
line per issue with an `E:` or `W:` prefix.

```pycon
>>> from showpy.core.validation import ValidationIssue, ValidationReport
>>> warn = ValidationIssue(
...     level="warning",
...     code="FACING_RANGE",
...     where="set 2 T1",
...     message="facing 400 outside [0, 360)",
...     hint="normalize the facing",
... )
>>> report = ValidationReport.merge(ValidationReport(), ValidationReport(issues=(warn,)))
>>> report.ok
True
>>> print(report)
W: FACING_RANGE set 2 T1: facing 400 outside [0, 360) (hint: normalize the facing)
```

Why return reports instead of raising? A designer wants to see every problem in a set at
once, not fix them one exception at a time. The `ValidationReport` class lives in `core`
(ADR 0001 fix 9) because both `time` and `show` produce reports, and `time` may not import
`show`.

> **Check your understanding 3.a.** Why does a `Placement` store `x` and `y` as floats in a
> tuple-friendly model and never a NumPy array?
>
> **Check your understanding 3.b.** You print `round(2.675, 2)` and get `2.67`. Which function
> should printed coordinates use, and what does it return?

## Exercises

**Exercise 3.1 (warm-up).** Return `format_ranges` of the IDs `T1`–`T6` without `T4`, plus
`B1` and `B2`, all given in a shuffled order.

**Exercise 3.2.** Split 13 counts into 4 parts with `chunk_counts` and return the parts. The
check verifies the sum is exactly 13.0 with `==`.

**Exercise 3.3.** Build a `Region` for a 10 m × 8 m rectangle at the origin with a 2 m × 2 m
hole whose lower-left corner is `(3, 3)`. Return its area in square meters.

**Exercise 3.4 (harder).** Write `solve(placement)` that returns a placement with
`facing` turned 90° counter-clockwise and wrapped into `[0, 360)`, without mutating the
input. A placement facing 300° must come back facing 30°.
