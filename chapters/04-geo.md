# showpy.geo: static geometry

`showpy.geo` is pure geometry on the stage plane: curves, shapes built from them, areas,
spacing spots along curves and inside areas, affine transforms, snapping, measures and design
analysis. It never reads time. Anything about motion lives in `showpy.choreo`.

The chapter has eight parts: the curve machinery, the concrete curves, SVG paths, the shape
constructors, regions, spacing, transforms, and measures with analysis.

## The curve machinery: curve_base.py

### What a curve is here

A **curve** is a path on the plane. The library needs to ask a curve four kinds of question:

1. Where is the point that is `s` meters along you? (`point_at`)
2. Which way do you run there? (`tangent_at`, `normal_at`)
3. Which point of you is closest to `p`? (`project`)
4. Give me a polyline close to you, for drawing and for Shapely. (`to_polyline`)

All four use **arc length** `s`, the distance travelled along the curve, in meters. A curve
of length `L` has `s` from 0 to `L`. This is the parameter performers feel: "8 meters along
the arc" means the same thing on a line, an arc or a spline.

`Curve` is a `Protocol` (an interface) listing those methods plus `closed`, `length`,
`point_at_u` (fractions of the length), `to_shapely` and `construction`. `CurveBase` is the
shared implementation every concrete curve inherits.

### Arc-length parameterization and its lookup table

Most curves are easy to evaluate at a **native parameter** `t` in `[0, 1]`, but `t` is not
distance. On a Bézier curve, equal steps of `t` give points that bunch where the curve is
slow and spread where it is fast (Figure 4.1, left). Spacing performers by `t` would give
uneven intervals.

![Thirteen points on one Bézier curve. Left: equal steps of the native parameter t. Right: equal steps of arc length s, from CurveBase's lookup table.](figures/fig_arclength.png)

`CurveBase` converts `s` to `t` with a lookup table:

1. Sample `t` at `TABLE_SAMPLES = 2048` evenly spaced values in `[0, 1]` (splines use 256 per
   segment instead).
2. Evaluate the points `P(t_i)` with the subclass's `_native(t)`.
3. Add up the chord lengths: `s_0 = 0`, `s_i = s_(i-1) + |P(t_i) - P(t_(i-1))|`. The last
   value is the length `L`.
4. To find the point at arc length `s`, find `t` by linear interpolation in the table
   (`np.interp(s, s_table, t_table)`), then evaluate `_native(t)`.

The table is built once per curve object, on first use, and cached with
`functools.cached_property`. The inverse is a monotone interpolation, so it is fast and
always defined. The chord sum slightly underestimates the true length; with 2048 samples the
error on a smooth curve is far below a millimeter.

Curves with exact formulas skip the table: a `Segment` knows its length is `|b - a|`, an arc
knows it is `r·|sweep|`. They override `length`, `_points` and `_tangents`.

```pycon
>>> import numpy as np
>>> from showpy.geo.shapes import arc, bezier, line
>>> b = bezier((0, 0), (0, 5), (1, 5), (7, 0))
>>> round(b.length(), 4)
11.2595
>>> b.point_at(0.0), b.point_at(b.length()).round(9)
(array([0., 0.]), array([7., 0.]))
>>> b.point_at([1.0, 2.0]).round(3)
array([[0.017, 1.   ],
       [0.091, 1.997]])
>>> b.point_at(99.0).round(9), b.point_at(-5.0)
(array([7., 0.]), array([0., 0.]))
>>> from guide_draw import sketch
>>> sketch.points(
...     b.point_at(np.linspace(0, b.length(), 13)),
...     curves=(b,),
...     numbered=True,
...     caption="13 points at equal arc length on the Bézier curve.",
... )
```

Read the outputs carefully:

- A scalar `s` returns shape `(2,)`. An array returns `(N, 2)`.
- An open curve **clamps** `s` to `[0, L]`: 99 gives the end, -5 gives the start.
- A closed curve **wraps** `s` modulo `L`, so walking past the end continues from the start.

### Tangents and normals

`tangent_at(s)` returns the unit direction of travel. `CurveBase` uses a central difference:
`(P(s + h) - P(s - h)) / |...|` with `h = 1e-6 · L` (at least `1e-6`), clamped at the ends of
an open curve. `normal_at(s)` is the tangent turned 90° counter-clockwise, `(-ty, tx)`: the
**left normal**. A zero-length curve raises `ZeroLengthError`, because it has no direction.

```pycon
>>> quarter = arc((0.0, 0.0), 2.0, 0.0, 90.0)
>>> quarter.tangent_at(0.0).round(6), quarter.normal_at(0.0).round(6)
(array([-0.,  1.]), array([-1., -0.]))
```

Walking up the right side of a counter-clockwise circle, the left normal points at the
center. That is why `face_normal` (chapter 11) calls the right of travel "outward".

### Projection: the closest point

`project(p)` returns the arc length of the point on the curve closest to `p`. It runs in two
stages:

1. **Scan.** Evaluate `PROJECT_SAMPLES = 512` evenly spaced points and keep the closest.
2. **Refine.** Run 60 steps of golden-section search on the interval of one sample step either
   side. Golden-section search keeps a bracket `[lo, hi]` and two probes at
   `hi - g·(hi - lo)` and `lo + g·(hi - lo)` with `g = (√5 - 1)/2 ≈ 0.618`. It drops the part
   beyond the worse probe. Each step shrinks the bracket by 0.618, so 60 steps shrink it by
   about `3·10⁻¹³`.

The scan protects against local minima: a spiral passes close to `p` several times, and only
the global scan finds the right pass.

```pycon
>>> line((0, 0), (10, 0)).project((3.7, 4.0))
3.7000000730004823
>>> round(quarter.project((5.0, 5.0)), 6), round(np.pi / 2, 6)
(1.570796, 1.570796)
```

The closest point of the quarter arc to `(5, 5)` is the middle of the arc, at
`s = r·π/4 = π/2`.

### Adaptive polyline subdivision

`to_polyline(tol)` returns vertices whose chords stay within `tol` meters of the curve. It
puts many vertices where the curve bends and few where it is straight.

1. Start from the curve's break points (`_breaks()`: the joints between pieces, for example
   spline knots) plus 0 and `L`. Split each interval into `INITIAL_SPLITS = 8` equal parts.
2. For an interval `[lo, hi]`, evaluate the curve at `lo`, `hi` and three probes at ¼, ½ and
   ¾. Compare each probe with the point at the same fraction along the straight chord.
3. If the largest gap is at most `tol`, keep `hi` as a vertex. Otherwise split at the middle
   and repeat on both halves, down to `MAX_SUBDIVISION_DEPTH = 24` levels.

Why start with 8 splits? One interval spanning a full S-bend could have probes that land on
the chord by accident. Eight starting pieces make that very unlikely. Why probe at three
places? One midpoint probe misses asymmetric bulges.

![A two-turn spiral as to_polyline() returns it at two chord tolerances. The coarse one uses 21 vertices, the fine one 71, and they cluster where curvature is high.](figures/fig_subdivision.png)

```pycon
>>> from showpy.geo.shapes import spiral
>>> s = spiral((0, 0), 0.5, 4.0, 2.0)
>>> len(s.to_polyline(0.2)), len(s.to_polyline(0.02)), len(s.to_polyline(0.002))
(21, 71, 214)
>>> len(line((0, 0), (10, 0)).to_polyline(0.001))
9
```

Each tenfold drop in tolerance costs about three times the vertices, because a circle's chord
error grows with the square of the chord length (`e ≈ c²/8r`). A straight line needs no
subdivision; its 9 vertices are the 8 initial splits.

`to_shapely(tol)` wraps the polyline as a Shapely `LineString`, or `LinearRing` for a closed
curve.

### construction() and rebuilding curves

Every curve is a Pydantic model with a `kind` field. `construction()` dumps it to a JSON-safe
dict, and `curve_from_construction(recipe)` rebuilds the right class by its `kind`. Forms and
routes store curves this way.

```pycon
>>> from showpy.geo.curves import curve_from_construction
>>> recipe = quarter.construction()
>>> recipe
{'closed': False, 'kind': 'arc', 'center': [0.0, 0.0], 'radius': 2.0, 'start_deg': 0.0, 'sweep_deg': 90.0}
>>> curve_from_construction(recipe) == quarter
True
>>> arc((0, 0), 0.0, 0.0, 90.0)
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: radius must be above 0, got 0.0 (hint: give a positive radius)
```

**Pitfall: stale caches.** The arc-length table is cached on the object. Pydantic's normal
`model_copy(update=...)` copies the cache too, so a copied spline with new points once kept
the old table and returned wrong positions. `CurveBase.model_copy` now rebuilds the object by
validation, which drops caches. A regression test guards this. Never bypass it with
`object.__setattr__`.

## The concrete curves: curves.py

All of these subclass `CurveModel`, which adds `substring(s0, s1)` and `reversed()`, both
returning a `TrimmedCurve` view.

| Class            | Fields                                       | Length and evaluation                              |
| ---------------- | -------------------------------------------- | -------------------------------------------------- | ------- | ---------------------------------------------------- |
| `Segment`        | `a`, `b`                                     | exact: `                                           | b - a   | `; `P(s) = a + s·û`                                  |
| `Polyline`       | `points`, `closed`                           | exact sum of pieces; breaks at every vertex        |
| `ArcCurve`       | `center`, `radius`, `start_deg`, `sweep_deg` | exact: `r·                                         | sweep   | ` in radians; positive sweep turns counter-clockwise |
| `CircleCurve`    | `center`, `radius`, `start_deg`, `ccw`       | exact circumference; closed; mirroring flips `ccw` |
| `EllipseCurve`   | `center`, `rx`, `ry`, `rotation_deg`         | table; closed, counter-clockwise                   |
| `SplineCurve`    | `points`, `alpha=0.5`, `closed`              | table; centripetal Catmull–Rom through every point |
| `BezierCurve`    | `control`                                    | table; Bernstein polynomials of any degree         |
| `SvgCurve`       | `d`, `transform`                             | table; one SVG subpath under a 3×3 affine map      |
| `SpiralCurve`    | `center`, `r0`, `r1`, `turns`, `start_deg`   | table; Archimedean, radius linear in angle         |
| `CompositeCurve` | `parts`, `closed`                            | exact sum; parts joined end to end                 |
| `TrimmedCurve`   | `base`, `s0`, `s1`                           | `                                                  | s1 - s0 | `; reversed when `s0 > s1`                           |

`AnyCurve` is the tagged union of all of them, discriminated by `kind`.

### Centripetal Catmull–Rom splines

Designers want a smooth curve that passes **through** the points they click, not one that is
only pulled toward them (as a Bézier curve is). A Catmull–Rom spline does that. Between two
consecutive points `P1` and `P2`, it builds a cubic from four points `P0, P1, P2, P3`.

The construction is the Barry–Goldman pyramid. Give each point a knot value `t_i`:

```text
t0 = 0
t1 = t0 + |P1 - P0|^α
t2 = t1 + |P2 - P1|^α
t3 = t2 + |P3 - P2|^α
```

For a parameter `t` between `t1` and `t2`, blend linearly three times:

```text
A1 = (t1 - t)/(t1 - t0)·P0 + (t - t0)/(t1 - t0)·P1
A2 = (t2 - t)/(t2 - t1)·P1 + (t - t1)/(t2 - t1)·P2
A3 = (t3 - t)/(t3 - t2)·P2 + (t - t2)/(t3 - t2)·P3
B1 = (t2 - t)/(t2 - t0)·A1 + (t - t0)/(t2 - t0)·A2
B2 = (t3 - t)/(t3 - t1)·A2 + (t - t1)/(t3 - t1)·A3
C  = (t2 - t)/(t2 - t1)·B1 + (t - t1)/(t2 - t1)·B2
```

At `t = t1`, `C = P1`; at `t = t2`, `C = P2`. So the curve passes through every point. This
is exactly `_catmull_rom` in `curves.py`.

The exponent `α` decides the knot spacing:

- `α = 0` (uniform): every gap counts as 1. Points that are close together still get a full
  unit of parameter, so the curve overshoots and can form cusps and small loops.
- `α = 0.5` (**centripetal**, the default): gaps count as the square root of the distance.
  Yuksel, Schaefer and Keyser proved (2011) that this never forms cusps or self-intersections
  within a segment. It hugs the control polygon.
- `α = 1` (chordal): gaps count as the distance. Very smooth, but it can swing wide.

![The same five points with three exponents. The uniform spline (red) overshoots into a sharp hook near the two close points; the centripetal spline (blue) does not.](figures/fig_catmull.png)

Two details complete the spline:

- **End points.** An open spline needs a `P0` before the first point and a `P3` after the
  last. `SplineCurve` mirrors the neighbor: the phantom start is `2·p0 - p1`. So the curve
  leaves the first point heading straight at the second.
- **Closed splines** wrap: the control list becomes `[p_last, p0, ..., p_last, p0, p1]`, and
  there is one segment per point instead of one fewer.
- `KNOT_FLOOR = 1e-9` keeps two identical points from making a zero knot gap and a division by
  zero.

```pycon
>>> from showpy.geo.shapes import curve_through
>>> c = curve_through((0, 0), (2, 2), (4, 0))
>>> c.point_at(c.project((2.0, 2.0))).round(6)
array([2., 2.])
>>> round(c.length(), 4), c._segments(), len(c._table[0])
(5.7783, 2, 513)
>>> curve_through((0, 0))
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: a spline needs at least 2 points (hint: pass two or more)
```

The spline passes exactly through `(2, 2)`. Two segments get `256·2 + 1 = 513` table rows.

### Arcs, circles, spirals and ellipses

- An `ArcCurve` point is `center + r·(cos a, sin a)` with
  `a = start + sweep·(s / L)` in math degrees. Its length is exact.
- A `CircleCurve` is a closed arc of 360° in the direction `ccw`.
- A `SpiralCurve` has radius `r0 + (r1 - r0)·u` at angle `start + 360°·turns·u`, for `u` in
  `[0, 1]`: an Archimedean spiral, whose turns are evenly spaced.
- An `EllipseCurve` point is the rotation of `(rx·cos a, ry·sin a)` by `rotation_deg`.

```pycon
>>> from showpy.geo.shapes import circle, ellipse
>>> round(circle((0, 0), 1.0).length(), 6), round(2 * np.pi, 6)
(6.283185, 6.283185)
>>> circle((0, 0), 1.0).point_at(7.0).round(4)
array([0.7539, 0.657 ])
>>> round(ellipse((0, 0), 2.0, 1.0).length(), 4)
9.6884
```

The circle wraps: `s = 7` is `7 - 2π = 0.717` m into a second lap. The ellipse has no
closed-form length; the table gives 9.6884 m, which matches Ramanujan's approximation
`π·(3(a + b) - √((3a + b)(a + 3b)))` = 9.6884 to four decimals.

### Joining, trimming and reversing

`CompositeCurve` chains parts. It maps `s` to the right part by the running lengths. A
`TrimmedCurve` views `base` from `s0` to `s1`; when `s0 > s1` it runs backwards. The engine
uses `TrimmedCurve` for follow-the-leader, and `split_form` uses it to cut a form.

```pycon
>>> from showpy.geo.shapes import join
>>> l_shape = join(line((0, 0), (3, 0)), line((3, 0), (3, 4)))
>>> l_shape.length(), l_shape.point_at(5.0)
(7.0, array([3., 2.]))
>>> back = l_shape.reversed()
>>> back.point_at(0.0), l_shape.substring(2.0, 4.0).point_at(1.0)
(array([3., 4.]), array([3., 0.]))
>>> join(line((0, 0), (3, 0)), line((5, 0), (5, 4)))
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: curve ends do not meet (hint: pass bridge=True to connect them with straight pieces)
```

## SVG paths: svg.py

`parse_path(d)` reads SVG path data, the `d` attribute of a `<path>` element, into subpaths
of pieces you can evaluate. It supports every command: `M L H V C S Q T A Z`, in absolute
(upper case) and relative (lower case) form.

How it works:

1. **Tokenize.** A regular expression splits the text into command letters and numbers,
   including forms like `-.5e-3`. Anything else raises `SchemaError` with the position.
2. **Walk.** For each command, read its number of arguments (`COMMAND_ARITY`: `M` takes 2,
   `C` takes 6, `A` takes 7). If numbers continue without a new letter, the command repeats;
   after `M` the repeat becomes `L`, as the SVG spec says.
3. **Relative commands** add the current point to their coordinates.
4. **Smooth curves** (`S`, `T`) reflect the previous control point through the current point:
   `c = 2·current - last_control`. If the previous command was not a curve of the same
   family, the control point is the current point.
5. `Z` closes the subpath with a straight piece back to its start and flushes it. `M` starts
   a new subpath.

Each piece is a `LinePiece`, `QuadPiece`, `CubicPiece` or `ArcPiece` with
`evaluate(u)` for `u` in `[0, 1]` and `to_d()` to write it back as absolute path data.

### Elliptical arcs: from endpoints to center

SVG writes an arc as `A rx ry φ large-arc sweep x y`: "from the current point to `(x, y)`
along an ellipse with radii `rx, ry`, rotated by `φ`." Two ellipses of that size pass through
both points, and each gives two arcs, so the two flags pick one of four (Figure 4.5).

- `large-arc = 1` picks the arc longer than 180°.
- `sweep = 1` picks the arc drawn in the direction of increasing angle.

![The four arcs `A 2 1.4 0 <large> <sweep>` from P1 = (0, 0) to P2 = (3, 1). Each flag combination picks a different arc of two possible ellipses.](figures/fig_svg_arc.png)

To evaluate the arc we need its center form: center `c`, start angle `θ1` and signed sweep
`Δθ`. `_arc_piece` follows SVG 1.1 implementation notes F.6.5 step by step:

1. Move to a frame centered between the endpoints and unrotated by `φ`:
   `(x1', y1') = R(-φ) · (P1 - P2)/2`.
2. **Correct out-of-range radii.** If `Λ = x1'²/rx² + y1'²/ry² > 1`, the ellipse is too small
   to reach both points; scale both radii by `√Λ`. (Browsers do the same.)
3. Solve for the center in that frame:
   `c' = ± √((rx²ry² - rx²y1'² - ry²x1'²)/(rx²y1'² + ry²x1'²)) · (rx·y1'/ry, -ry·x1'/rx)`.
   The sign is `-` when `large-arc == sweep`. A tiny negative under the root (rounding) is
   clamped to 0.
4. Rotate and shift back: `c = R(φ)·c' + (P1 + P2)/2`.
5. `θ1` is the angle from `(1, 0)` to `((x1' - cx')/rx, (y1' - cy')/ry)`, and `Δθ` the angle
   from that vector to `((-x1' - cx')/rx, (-y1' - cy')/ry)`.
6. Fix the sweep direction: if `sweep = 0` and `Δθ > 0`, subtract 360°; if `sweep = 1` and
   `Δθ < 0`, add 360°.

Two special cases follow the spec: an arc whose endpoints coincide is skipped, and an arc with
a zero radius is drawn as a straight line.

```pycon
>>> from showpy.geo.svg import parse_path
>>> [len(sub.pieces) for sub in parse_path("M0 0 l3 0 0 3 z M5 5 h1")]
[3, 1]
>>> piece = parse_path("M 0 0 A 2 1.4 0 0 1 3 1")[0].pieces[0]
>>> type(piece).__name__, piece.center, round(piece.dtheta_deg, 3)
('ArcPiece', (1.0212856252802927, 1.2037101308379698), 112.34)
>>> piece.evaluate(np.array([0.0, 1.0])).round(9)
array([[0., 0.],
       [3., 1.]])
>>> parse_path("M0 0 L1")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: L needs 2 numbers (hint: check the path data argument counts)
```

**Packed flags.** SVG allows `a1 1 0 011 1`, where the flags `0`, `1` and the next number
`1` run together. The tokenizer first reads `011` as one number, then `_unpack_arc_flags`
splits any multi-digit token in a flag slot into single digits, because SVG flags are always
one digit. `a1 1 0 011 1` and `a1 1 0 0 1 1 1` parse to the same arc.

`SvgCurve(d, transform)` wraps one subpath as a curve. `svg_outline` (next section) fits
whole SVG drawings into a box and returns one `SvgCurve` per subpath.

## Shape constructors: shapes.py

These functions validate input and return curve models. They are what scripts and forms call.

| Function                                                 | Returns           | Notes                                                 |
| -------------------------------------------------------- | ----------------- | ----------------------------------------------------- |
| `line(a, b)`                                             | `Segment`         | ends must differ                                      |
| `polyline(*pts, closed=False)`                           | `Polyline`        |                                                       |
| `arc(center, radius, start_deg, sweep_deg)`              | `ArcCurve`        | math angles                                           |
| `arc_through(a, m, b)`                                   | `ArcCurve`        | circle through three points; collinear raises         |
| `arc_from_chord(a, b, bulge)`                            | `ArcCurve`        | bow the chord by `bulge` m; positive bows left of a→b |
| `circle(center, radius, start_deg=0)`                    | `CircleCurve`     | counter-clockwise                                     |
| `ellipse(center, rx, ry, rotation_deg=0)`                | `EllipseCurve`    |                                                       |
| `curve_through(*pts, closed, alpha)`                     | `SplineCurve`     |                                                       |
| `bezier(*control)`                                       | `BezierCurve`     |                                                       |
| `spiral(center, r0, r1, turns, start_deg)`               | `SpiralCurve`     |                                                       |
| `rect(center, w, d, rotation_deg)`                       | closed `Polyline` | corners counter-clockwise from front-left             |
| `wedge(apex, length, spread_deg, facing_deg)`            | `Polyline`        | a V whose apex leads toward the facing                |
| `regular_polygon(center, radius, n, rotation_deg)`       | closed `Polyline` | first vertex upstage                                  |
| `star(center, r_outer, r_inner, n, rotation_deg)`        | closed `Polyline` | 2n vertices                                           |
| `svg_outline(svg, fit, path_index, keep_aspect, flip_y)` | `list[SvgCurve]`  | `d` text or SVG text; one curve per subpath           |
| `text_outline(text, font, height, at)`                   | `list[Polyline]`  | single-stroke letters                                 |
| `join(*curves, bridge=False)`                            | `CompositeCurve`  | gaps over 1 µm raise unless bridged                   |
| `offset(curve, distance, side)`                          | curve             | lines and arcs exact; others via a polyline           |

Worked example: `arc_from_chord(a, b, bulge)`. The chord has length `c` and the arc rises
`h = bulge` above its middle (the **sagitta**). The circle through both ends with that rise
has radius `r = (c²/4 + h²)/(2h)`. For a 4 m chord with 1 m bulge, `r = (4 + 1)/2 = 2.5`.

```pycon
>>> from showpy.geo.shapes import arc_from_chord, arc_through, rect, star, text_outline, wedge
>>> bow = arc_from_chord((-2, 0), (2, 0), 1.0)
>>> bow.radius, bow.point_at(bow.length() / 2).round(9)
(2.5, array([0., 1.]))
>>> arc_through((-1, 0), (0, 1), (1, 0)).sweep_deg
-180.0
>>> rect((0, 5), 4, 2).points
((-2.0, 4.0), (2.0, 4.0), (2.0, 6.0), (-2.0, 6.0))
>>> wedge((0, 10), 3.0, 90.0).points[1], len(star((0, 0), 2, 1, 5).points)
((0.0, 10.0), 10)
>>> [len(t.points) for t in text_outline("HI", "simplex", 2.0, (0, 0))]
[2, 2, 2, 2, 2, 2]
>>> arc_through((0, 0), (1, 1), (2, 2))
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: arc points are collinear (hint: move the middle point off the line)
>>> sketch.points(
...     wedge((0, 10), 3.0, 90.0).to_polyline(),
...     star((8, 10), 2, 1, 5).to_polyline(),
...     curves=(bow,),
...     caption="A wedge (apex toward the audience), a five-point star and the bowed chord.",
... )
```

`svg_outline` fits a drawing into a box: it computes the drawing's bounding box, then a scale
(equal in x and y when `keep_aspect`) and a translation that center it in `fit`. With
`flip_y=True` it also mirrors y, because SVG's y axis points down the page while the stage's
points away from the audience. The map is stored in each `SvgCurve.transform`, so the original
path text is kept and stays editable.

`text_outline` uses the built-in single-stroke font `simplex` from `text.py`: each glyph is a
few polylines on a 4 × 6 grid with an advance of 5. Stroke letters are better than filled
outline fonts for drill, because spots spaced along a stroke read as the letter itself.
`simplex` is one of five bundled single-line fonts (with `relief-singleline` and three Hershey
fonts), and `showpy.choreo.forms.text_form` spreads an exact number of spots over the same
strokes as an editable text form.

## Regions: regions.py

A region is an area. Functions take and return Shapely polygons (`Area` = `Polygon` or
`MultiPolygon`); stored data uses the `Region` model.

- `region(outline)` builds a valid polygon from a closed curve or a ring of points. Curves are
  flattened with `to_polyline(0.001)`.
- `buffer(area, d)` grows by `d` meters, or shrinks when `d < 0`.
- `union(*areas)`, `difference(a, b)`, `intersection(a, b)` are the set operations.

```pycon
>>> from showpy.geo.regions import buffer, difference, region, union
>>> square = region([(0, 0), (4, 0), (4, 4), (0, 4)])
>>> buffer(square, -1.0).area, round(buffer(square, 1.0).area, 3)
(4.0, 35.137)
>>> difference(square, region([(1, 1), (3, 1), (3, 3), (1, 3)])).area
12.0
>>> round(region(circle((0, 0), 1.0)).area, 4)
3.1403
>>> region([(0, 0), (1, 0)])
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: a region needs at least 3 points (hint: pass a closed curve or three or more points)
```

Growing a 4 × 4 square by 1 m gives `16 + 4·(4·1) + π·1² = 35.14` m²: the square, four
1 m strips along the sides and four quarter-circle corners. The polygonized unit circle has
area 3.1403, a little under π = 3.1416, because `region` flattens the curve to a polygon whose
chords stay within 1 mm of it, and an inscribed polygon is smaller than its circle.

## Spacing: spacing.py

Spacing functions place spots. They all return `(N, 2)` arrays.

### Along curves

- `space_along(curve, n, start=0, end=None, endpoints=True)` puts `n` spots at equal arc
  length between `start` and `end`. With `endpoints=False` the spots sit at the centers of
  `n` equal cells, which suits a closed curve. A closed curve spaced over its full length
  never repeats the start.
- `space_by_interval(curve, interval, start, n, align)` puts spots `interval` meters apart.
  Without `n` it places as many as fit: `floor(available/interval) + 1`. `align` shifts the
  run to the start, end or center of the spare length.
- `space_proportional(curves, n)` shares `n` spots across several curves so every curve has
  about the same interval. It uses **largest-remainder apportionment**: each curve gets 1 spot,
  the remaining `n - k` spots are divided by length, everyone gets the whole part of their
  quota, and the leftover spots go to the largest fractional parts (ties to the earlier curve).
- `space_with_gaps(curve, n, gaps)` spaces evenly but adds `extra_m` after chosen spots, for
  a hole in a line.

```pycon
>>> from showpy.geo.spacing import space_along, space_by_interval, space_proportional, space_with_gaps
>>> track = arc((0.0, 0.0), 10.0, 150.0, -120.0)
>>> pts = space_along(track, 5)
>>> pts.round(3)
array([[-8.66,  5.  ],
       [-5.  ,  8.66],
       [ 0.  , 10.  ],
       [ 5.  ,  8.66],
       [ 8.66,  5.  ]])
>>> np.linalg.norm(np.diff(pts, axis=0), axis=1).round(4)
array([5.1764, 5.1764, 5.1764, 5.1764])
>>> sketch.points(
...     pts,
...     curves=(track,),
...     numbered=True,
...     caption="space_along: five spots at equal arc length on a 120° arc of radius 10 m.",
... )
>>> (
...     len(space_by_interval(line((0, 0), (10, 0)), 3.0)),
...     space_by_interval(line((0, 0), (10, 0)), 3.0, align="center")[:, 0],
... )
(4, array([0.5, 3.5, 6.5, 9.5]))
>>> [len(p) for p in space_proportional([line((0, 0), (2, 0)), line((0, 1), (9, 1))], 7)]
[2, 5]
>>> space_with_gaps(line((0, 0), (10, 0)), 4, [(1, 2.0)])[:, 0].round(4)
array([ 0.    ,  2.6667,  7.3333, 10.    ])
>>> space_by_interval(line((0, 0), (10, 0)), 3.0, n=5)
Traceback (most recent call last):
  ...
showpy.core.errors.SpacingError: SPACING: 5 spots at 3.0 m do not fit in 10.00 m (hint: use at most 4 spots or a smaller interval)
```

The arc of radius 10 and sweep 120° has length `10·2π/3 = 20.94` m. Five spots make four
equal arcs of 5.236 m; the straight-line gaps are the chords `2r·sin(15°) = 5.176` m. Spacing
is by arc length, so **chords** are equal too only because the arc has constant curvature.

The proportional example has a 2 m and a 9 m line and 7 spots. Each gets one, leaving 5. The
quotas are `5·2/11 = 0.91` and `5·9/11 = 4.09`: whole parts 0 and 4, and the last spot goes
to the larger remainder (0.91). Result `[1 + 1, 1 + 4] = [2, 5]`.

### Blocks, fills and rings

- `block(origin, rows, cols, interval, facing=0, anchor="center")` builds a rectangular
  block, front row first, columns left to right as the audience sees a block facing 0°. The
  whole frame turns with `facing`; `anchor` says which point of the block sits on `origin`.
- `ranks_and_files(points, rows, cols)` indexes block points by row and column.
- `fill(area, interval, pattern, angle_deg, anchor, n, margin)` puts a lattice inside an
  area: `grid` (squares), `offset` (every other row shifted half a step) or `hex` (rows
  `interval·√3/2` apart, so every spot has six neighbors at `interval`). One lattice point
  sits on `anchor`. With `n`, it keeps the `n` points nearest the anchor.
- `concentric(center, radii, counts, start_deg)` spaces `counts[i]` spots around ring `i`.

![Spacing on blocks, lattices, rings and letters: a 3 × 4 block turned to face 30° (front row red), a hex fill, concentric rings of 4, 8 and 12, and 48 spots shared across the strokes of "SHOW".](figures/fig_spacing.png)

```pycon
>>> from showpy.geo.spacing import block, concentric, fill, ranks_and_files
>>> block((0, 10), 2, 3, 2.0).round(3).tolist()
[[-2.0, 9.0], [0.0, 9.0], [2.0, 9.0], [-2.0, 11.0], [0.0, 11.0], [2.0, 11.0]]
>>> block((0, 10), 2, 3, 2.0, facing=180.0).round(3).tolist()[:3]
[[2.0, 11.0], [0.0, 11.0], [-2.0, 11.0]]
>>> ranks_and_files(block((0, 0), 2, 3, 1.0), 2, 3)
[[0, 1, 2], [3, 4, 5]]
>>> len(fill(square, 1.0)), len(fill(square, 1.0, "hex")), len(fill(square, 1.0, n=5))
(25, 23, 5)
>>> [len(r) for r in concentric((0, 0), [2.0, 4.0], [6, 12])]
[6, 12]
```

Turning the block to face 180° (upstage) puts its front row at the back and reverses left and
right, because "front" and "left" are measured in the block's own frame.

### Scatter: Bridson Poisson-disk sampling plus farthest-point selection

An organic scatter must look random but never crowd two spots. The rule is a minimum gap `r`
between every pair. `scatter(area, n, min_gap, seed)` does it in two steps.

**Step 1: Bridson's algorithm** (2007) fills the area with as many points as fit at gap `r`:

1. Lay a background grid with cell size `r/√2`. A cell's diagonal is then `r`, so a cell can
   hold at most one accepted point. Store the grid as a dict from cell to point.
2. Accept a first point inside the area (Shapely's `representative_point`) and put it on an
   **active list**.
3. While the active list is not empty, pick a random active point. Try up to 30 candidates at
   random angle and distance between `r` and `2r` from it. A candidate is accepted if it lies
   in the area and no accepted point within `r` exists. Because a point within `r` must be at
   most two cells away, the check looks only at the 5 × 5 block of cells around the
   candidate: constant time.
4. If a candidate is accepted, it joins the active list. If all 30 fail, the base point
   leaves the active list.

The result is a "blue noise" set: every pair is at least `r` apart and gaps are not much
larger than `2r`. All randomness comes from `seeded_rng(seed)`.

**Step 2: farthest-point selection** keeps `n` of them, spread evenly:

1. Start with the candidate farthest from the centroid (first index on ties).
2. Repeat: add the candidate whose distance to its nearest chosen point is largest.

Every candidate pair was already at least `r` apart, so any subset keeps the gap. If fewer
than `n` candidates fit, `scatter` raises `SpacingError` with `context["max_fit"]`.
`distribute_on_points(candidates, n, method)` exposes step 2 alone, and also offers a seeded
random draw.

![Bridson samples in a pentagon at a 1.5 m gap (grey) and the 30 kept by farthest-point selection (red).](figures/fig_poisson.png)

```pycon
>>> from showpy.geo.spacing import distribute_on_points, scatter
>>> from showpy.geo.measure import distance_matrix
>>> field_area = region([(0, 0), (12, 0), (12, 8), (0, 8)])
>>> spots = scatter(field_area, 20, 1.5, seed=1)
>>> gaps = distance_matrix(spots, spots) + np.eye(20) * 99
>>> round(float(gaps.min()), 3)
1.613
>>> sketch.points(spots, caption="scatter(12 x 8 m, n=20, min_gap=1.5, seed=1).")
>>> distribute_on_points([(0, 0), (1, 0), (2, 0), (9, 0)], 2).tolist()
[[0.0, 0.0], [9.0, 0.0]]
>>> scatter(field_area, 200, 1.5)
Traceback (most recent call last):
  ...
showpy.core.errors.SpacingError: SPACING: only 29 spots fit at gap 1.5 m (hint: lower n or min_gap)
```

## Affine maps and transforms: affine.py, transforms.py, snapping.py

### Affine maps in homogeneous coordinates

An **affine map** is a linear map plus a shift: `p' = M·p + t`. It covers translation,
rotation, scaling, mirroring and shearing. Writing a point as `(x, y, 1)` turns it into one
3 × 3 matrix product:

```text
[x']   [a  b  tx] [x]
[y'] = [c  d  ty] [y]
[1 ]   [0  0  1 ] [1]
```

The top-left 2 × 2 block `L = [[a, b], [c, d]]` is the **linear part**. Composition is matrix
multiplication. A map "about a point" `q` is `T(q) · M · T(-q)`: move `q` to the origin,
apply `M`, move back.

| Builder                            | Matrix                                      | Note                               |
| ---------------------------------- | ------------------------------------------- | ---------------------------------- |
| `translation_matrix(dx, dy)`       | `[[1,0,dx],[0,1,dy],[0,0,1]]`               |                                    |
| `rotation_matrix(deg, about)`      | `[[cos,-sin],[sin,cos]]` about a point      | counter-clockwise                  |
| `scale_matrix(sx, sy, about)`      | `[[sx,0],[0,sy]]` about a point             |                                    |
| `mirror_matrix(a, b)`              | reflection across the line through `a`, `b` | `I - 2nnᵀ` for the unit normal `n` |
| `skew_matrix(deg_x, deg_y, about)` | `[[1, tan dx],[tan dy, 1]]` about a point   | shear                              |

`is_similarity(M)` reports whether `L` is a rotation, mirror or uniform scale: whether
`LᵀL = s²·I` for some `s`. Similarities keep angles and length ratios, so circles stay
circles.

### Why facings transform as vector_facing(M · v)

A facing is a direction, not a position. When a picture is transformed, a performer's facing
must point "the same way relative to the picture". Directions are differences of points, so
the shift `t` cancels and only `L` acts on them. The one rule (ADR 0001 decision 6) is:

```text
θ' = vector_facing(L · facing_vector(θ))
```

It covers every case with no special code:

- **Rotation by α:** `L` rotates the direction by α, so `θ' = θ + α`.
- **Mirror across x = c:** `L = diag(-1, 1)` flips `(sin θ, -cos θ)` to `(-sin θ, -cos θ)`,
  which is the facing `-θ = 360° - θ`. A spot facing 30° (front-right) ends facing 330°
  (front-left), as a mirror image should.
- **Uniform scale:** the direction does not change. The vector gets longer, but
  `vector_facing` ignores length.
- **Skew:** the facing tilts with the picture, the same way a line drawn along it would.

![Six facings carried through a skew and a mirror by θ' = vector_facing(L·v). The labels are the new facings.](figures/fig_affine_facing.png)

```pycon
>>> from showpy.geo.affine import (
...     is_similarity,
...     mirror_matrix,
...     rotation_matrix,
...     skew_matrix,
...     transform_facing,
...     transform_points,
... )
>>> m = mirror_matrix((0, 0), (0, 1))
>>> transform_points(np.array([[2.0, 5.0]]), m).round(9).tolist(), round(transform_facing(30.0, m), 9)
([[-2.0, 5.0]], 330.0)
>>> round(transform_facing(0.0, rotation_matrix(90, (5, 5))), 9)
90.0
>>> round(transform_facing(0.0, skew_matrix(45, 0, (0, 0))), 9)
315.0
>>> round(transform_facing(90.0, skew_matrix(0, 45, (0, 0))), 9)
135.0
>>> is_similarity(rotation_matrix(30, (0, 0))), is_similarity(skew_matrix(10, 0, (0, 0)))
(True, False)
```

Check the skew by hand. `skew_matrix(45, 0)` has `L = [[1, tan 45°], [0, 1]] = [[1, 1], [0, 1]]`.
The audience facing is the vector `(0, -1)`, and `L·(0, -1) = (-1, -1)`. Its facing is
`atan2(vx, -vy) = atan2(-1, 1) = -45°`, which wraps to 315°: the performer now looks front-left,
along the sheared picture. In the same way the y-shear turns a 90° facing to 135°.

### transform_curve: keeping the curve family

`transform_curve(curve, M)` maps a curve and keeps its kind whenever that is exact:

- Point-defined curves (segment, polyline, spline, Bézier, SVG) map their defining points.
  This is exact for any affine map, because those curves are affine-invariant combinations of
  their points.
- Arcs, circles and spirals stay arcs, circles and spirals under similarities: the center
  maps, the radius scales by `√|det L|` and the start angle is re-measured. A mirror
  (`det L < 0`) flips the sweep sign or `ccw`. A mirrored spiral becomes a polyline.
- Anything else (an ellipse, an arc under a skew) becomes a dense `Polyline` within 1 mm.

### The transform functions

`showpy.geo.transforms` works on three kinds of object and returns the same kind:

- `Points` arrays,
- curves,
- `Set`s, where only the **selected, on-field** placements move, facings follow affine maps,
  and pinned placements raise `LockedError` unless `force=True`.

| Function                                            | Does                                                                                          |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `shift(obj, dx, dy)`                                | translates                                                                                    |
| `move_to(obj, anchor, to)`                          | moves a box anchor (`center`, `front-left`, ...) onto a point                                 |
| `rotate(obj, deg, about="center")`                  | rotates counter-clockwise; `about` is a point, `"center"` (box center) or `"centroid"` (mean) |
| `scale(obj, sx, sy=None, about)`                    | resizes; factors must be positive                                                             |
| `expand(obj, d, about)` / `contract(obj, d, about)` | moves points `d` m away from / toward the anchor along their rays                             |
| `set_interval(obj, interval, anchor)`               | respaces ordered spots along their own polyline                                               |
| `mirror(obj, axis)`                                 | `"x"` (the line x = 0), `"center"`, `"y"`, or two points                                      |
| `symmetrize(set, sel, source_side, pairs, axis_x)`  | copies one side's mirror image onto partners                                                  |
| `skew(obj, deg_x, deg_y, about)`                    | shears                                                                                        |
| `affine(obj, matrix)`                               | any 2 × 3 or 3 × 3 matrix                                                                     |
| `interpolate_forms(a, b, u)`                        | blends two equal-length point sets                                                            |
| `snap(obj, precision, mode, axes)`                  | rounds to a grid; returns `(obj, SnapReport)`                                                 |
| `snap_to_guides(obj, sheet, tol, kinds)`            | pulls points within `tol` onto guide lines                                                    |
| `align(obj, axis, value)`                           | sets one coordinate to a number or to `mean`/`min`/`max`                                      |
| `distribute(obj, axis, start, end)`                 | evens points out along an axis, keeping their order                                           |

Under the hood, `rotate`, `scale`, `mirror`, `skew` and `affine` all build a matrix and call
`transform_base.apply_matrix(obj, M, sel, force)`. That function dispatches on the type: for
points it calls `transform_points`; for curves `transform_curve`; for a set it resolves the
selection to on-field spots, checks pins, maps positions and maps each facing with
`transform_facing`. `expand`, `snap` and `align` are not affine; they go through
`apply_pointwise`, which moves points but leaves facings alone.

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.geo.transforms import expand, mirror, rotate, set_interval, snap, symmetrize
>>> s1 = two_set_show().set("1")
>>> s1.positions().tolist()
[[0.0, 5.0], [2.0, 5.0], [4.0, 5.0], [6.0, 5.0]]
>>> turned = rotate(s1, 90.0, about=(3.0, 5.0))
>>> turned.positions().round(6).tolist(), [p.facing for p in turned.placements]
([[3.0, 2.0], [3.0, 4.0], [3.0, 6.0], [3.0, 8.0]], [90.0, 90.0, 90.0, 90.0])
>>> sketch.points(
...     s1.positions(),
...     turned.positions(),
...     labels=("set 1", "rotated 90° about (3, 5)"),
...     facings=([p.facing for p in s1.placements], [p.facing for p in turned.placements]),
...     caption="rotate() on a Set: positions turn about (3, 5) and every facing turns 90°.",
... )
>>> mirror(s1, "x").positions()[:, 0].tolist()
[0.0, -2.0, -4.0, -6.0]
>>> rotate(s1, 90.0, sel=["T1", "T2"]).positions().round(3).tolist()
[[1.0, 4.0], [1.0, 6.0], [4.0, 5.0], [6.0, 5.0]]
>>> set_interval(s1, 3.0).positions()[:, 0].tolist()
[-1.5, 1.5, 4.5, 7.5]
>>> expand(np.array([[2.0, 0.0], [0.0, 1.0]]), 1.0, about=(0.0, 0.0)).tolist()
[[3.0, 0.0], [0.0, 2.0]]
>>> snapped, report = snap(np.array([[0.26, 1.0], [0.74, 2.0]]), 0.5)
>>> snapped.tolist(), report
([[0.5, 1.0], [0.5, 2.0]], SnapReport(moved=2, max_shift=0.24))
>>> pinned = s1.with_placements({"T1": {"pinned": True}})
>>> rotate(pinned, 90.0)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: T1 is pinned in set 1 (hint: unpin it first, or pass force=True as the designer)
```

`rotate(..., sel=["T1", "T2"])` turned only two spots, about the center of _their_ bounding
box, `(1, 5)`. Anchors such as `"center"` are measured on the selected spots, not the whole
set.

`symmetrize` pairs left-side spots with right-side spots by an optimal assignment on mirrored
positions (Hungarian method), then copies each source spot's mirror image, position and
facing, onto its partner. Unmatched spots stay put.

## Measures and analysis: measure.py, analysis.py

### Static measures

| Function                                               | Returns                                                            |
| ------------------------------------------------------ | ------------------------------------------------------------------ |
| `on_field_ids(set, sel)`                               | selected spots that are on the field, in selection order           |
| `length(obj)`                                          | curve length, or polyline length through points in order           |
| `center(obj)` / `centroid(obj)`                        | bounding-box center / mean point (length-weighted for curves)      |
| `bounds(obj)`                                          | `Box2`                                                             |
| `interval(points, ordered)`                            | `IntervalStats`: consecutive gaps, or each spot's nearest neighbor |
| `distance(a, b)` / `distance_matrix(a, b)`             | Euclidean distances                                                |
| `neighbors(set, entity, k)` / `nearest(set, point, k)` | closest on-field spots, ties by natural ID                         |
| `reachable_region(start, counts, max_speed)`           | the disk reachable in `counts` at `max_speed` m/count              |
| `mirror_gaps(points, axis_x)`                          | per point, distance from its mirror image to the nearest point     |
| `form_metrics(points)`                                 | length, intervals, curvature range, symmetry error                 |
| `symmetry_error(set, sel, axis_x)`                     | largest mirror mismatch of selected spots                          |

`form_metrics` reads points as an ordered polyline. **Discrete curvature** at an interior
point is the turning angle there divided by the mean length of the two pieces meeting there:
a straight run has 0, and points on a circle of radius `r` have about `1/r`. Symmetry is
measured about the best-fitting vertical axis.

```pycon
>>> from showpy.geo.measure import form_metrics, interval, nearest, neighbors, symmetry_error
>>> stats = interval(np.array([[0.0, 0.0], [2.0, 0.0], [3.0, 0.0]]))
>>> stats.gaps, stats.mean, round(stats.std, 6)
((2.0, 1.0), 1.5, 0.5)
>>> neighbors(s1, "T2", k=2), nearest(s1, (5.0, 5.0), k=1)
([('T1', 2.0), ('T3', 2.0)], [('T3', 1.0)])
>>> metrics = form_metrics(space_along(circle((0, 0), 4.0), 12, endpoints=False))
>>> [round(v, 4) for v in metrics.curvature_range], round(metrics.symmetry_error, 9)
([0.2529, 0.2529], 0.0)
```

Twelve spots on a circle of radius 4 give curvature 0.2529, close to `1/4 = 0.25`; the
discrete measure is slightly larger because chords are shorter than arcs.

### Design analysis

These functions never pass or fail. They return numbers that inform design, and they count
only on-field spots.

- `density_map(set, sheet, cell=1)` counts spots per square cell over the sheet.
- `coverage(set, sheet, radius=1)` is the share of the walkable area within `radius` of a
  spot: the union of disks intersected with the walkable area, divided by its area.
- `balance(set, sheet, axis)` is the mean offset from the sheet center as a share of half the
  sheet: -1 is all left (or front), +1 all right (or back).
- `symmetry_score(set, axis_x)` is `1 - mean mirror gap / spread`, floored at 0, where
  spread is the RMS distance of spots from their centroid.
- `change_amount(a, b)` is the mean distance moved by spots on the field in both sets.

```pycon
>>> from showpy.examples import field_sheet
>>> from showpy.geo.analysis import balance, change_amount, coverage, symmetry_score
>>> show = two_set_show()
>>> balance(show.set("1"), field_sheet()), round(symmetry_score(show.set("1")), 4)
(0.15, 0.0)
>>> change_amount(show.set("1"), show.set("2")), round(coverage(show.set("1"), field_sheet(), 2.0), 4)
(4.0, 0.0444)
```

The example set stands right of center at x = 0, 2, 4 and 6, so its balance is
`mean(x) / 20 = 3/20 = 0.15`, and it is far from symmetric about `x = 0`.

> **Check your understanding 4.a.** Why does `space_along` on an arc give equal chords, while
> on a Bézier curve equal arc lengths do not give equal chords?
>
> **Check your understanding 4.b.** You mirror a spot facing 90° across the center line. What
> facing does it get, and why?
>
> **Check your understanding 4.c.** Why can `scatter` keep any subset of the Bridson samples
> without breaking the minimum gap?

## Exercises

**Exercise 4.1 (warm-up).** Space 9 spots on an arc of radius 20 m centered at `(0, 0)`,
starting at 60° and sweeping 60°. Return the points. The check verifies the arc-length gap
is `20·(π/3)/8`.

**Exercise 4.2.** Return the facing a spot facing 30° gets after the set is rotated 135°
counter-clockwise and then mirrored across the center line `x = 0`. Use the library.

**Exercise 4.3.** Build a closed centripetal spline through `(0, 0)`, `(4, 0)`, `(4, 3)` and
`(0, 3)` and return `(length, point at s = 0, number of table rows)`.

**Exercise 4.4.** Parse the SVG path `M0 0 a3 2 0 1 0 4 0` and return the arc piece's
center, `θ1` and `Δθ` in degrees (rounded to 6 places).

**Exercise 4.5 (harder).** Scatter as many spots as fit at a 2 m gap in a 10 m × 10 m square
with seed 0, then keep 15 with farthest-point selection. Return the 15 points. The check
verifies the gap and that your answer matches `scatter(..., 15, 2.0, seed=0)`.
