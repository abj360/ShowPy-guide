# showpy.sheet: the design surface

A **sheet** is the 2D surface a show is drawn on: a football field, a proscenium stage, a gym
floor, or a plain rectangle. `showpy.sheet` builds the templates, looks things up on them,
words positions for people, draws sheets as images, and moves a show onto a different sheet.

## The data: models.py

| Class                | Holds                                                                                                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Sheet`              | `ref`, `name`, `surface_type`, `size_m`, `outline`, `walkable` (a `Region`), `guides`, `landmarks`, `zones`, `grid`, `default_coordinates`, `based_on`, `owner`, `thumbnail` |
| `Grid`               | background grid: `origin`, `spacing`, `major_every`, `rotation_deg`, `unit_name`                                                                                             |
| `GuideLine`          | a drawn line: `id`, `kind` (`yard`, `hash`, `sideline`, `center`, `edge`, `spike`, `custom`), `points`, `label`                                                              |
| `Landmark`           | a named reference: `point` (1 point), `line` (2+) or `area` (3+); `aliases`                                                                                                  |
| `Zone`               | an area with rules: `kind` (`restricted`, `pit`, `wings`, `staging`, `audience`, `safety`, `custom`), `polygon`, `applies_to`, `active` count windows                        |
| `CoordinateSystem`   | how positions are worded: `kind`, `origin`, `audience_side`, `units`, `precision`, `labels`                                                                                  |
| `SheetReplaceReport` | what moved when a sheet was replaced                                                                                                                                         |

`Zone.is_active(t)` is true when `active` is `None` (always) or `t` falls in one of its
`(start, end)` windows. A `CoordinateSystem` is **display only**: changing it changes labels,
never stored positions.

## Templates and storage: templates.py and surfaces.py

`sheet_templates(surface_type=None)` lists the built-in sheets. Every one puts `(0, 0)` at
the front-center.

| Reference                  | Size               | Highlights                                                |
| -------------------------- | ------------------ | --------------------------------------------------------- |
| `sheet:blank-20x15@1`      | 20 × 15 m          | a center line and front edge                              |
| `sheet:hs-football@1`      | 109.728 × 48.768 m | NFHS hashes 53 ft 4 in from each sideline                 |
| `sheet:college-football@1` | same               | NCAA hashes 60 ft from each sideline                      |
| `sheet:nfl-football@1`     | same               | NFL hashes 70 ft 9 in from each sideline                  |
| `sheet:proscenium-stage@1` | 12 × 9 m           | 1.5 m wings, a center line, spike marks, nine stage areas |
| `sheet:gym-basketball@1`   | 28.651 × 15.240 m  | a 94 × 50 ft court: lines, center circle, lanes, baskets  |

`football_field(ref_id, name, hash)` draws yard lines every 5 yards, the hashes, sidelines and
end lines, and adds landmarks for the center, every yard line and the front (home) and back
(visitor) hash points on every yard line. Rule-book sizes stay in feet and yards in the code
and go through `convert`, so `160 ft` is written once as 160 feet.

![render_sheet() of three templates: the high-school football field, the proscenium stage with its wings and spike marks, and the gym floor.](figures/fig_sheets.png)

`get_sheet(ref, store=None)` resolves a reference against the templates first, then an
optional store. A reference without a version means the template or the latest saved
version.

Saving: sheets are saved through an injected **store** (ADR 0001 fix 13), never global state.
`SheetStore` is a protocol with `get(ref)` and `put(sheet, scope)`. `InMemorySheetStore` is the
in-process implementation. `save_sheet(store, sheet, scope)` stores the sheet under the next
free version and records `based_on`. Saving identical content again returns the existing
reference.

Editing returns a new sheet: `customize(sheet, name=..., grid=..., size=...)` (resizing only
blank sheets), `add_zone`, `add_landmark`, `add_guide`, `remove_zone`, `remove_landmark`,
`remove_guide`. `blank_sheet(width_m, depth_m, grid_spacing, units)` builds a plain rectangle.

```pycon
>>> from showpy.sheet.templates import (
...     InMemorySheetStore,
...     add_zone,
...     blank_sheet,
...     customize,
...     get_sheet,
...     save_sheet,
...     sheet_templates,
... )
>>> [s.ref for s in sheet_templates()][:3]
['sheet:blank-20x15@1', 'sheet:hs-football@1', 'sheet:college-football@1']
>>> stage_sheet = get_sheet("sheet:proscenium-stage")
>>> [z.id for z in stage_sheet.zones], stage_sheet.default_coordinates.kind.value
(['wing-sr', 'wing-sl'], 'stage')
>>> store = InMemorySheetStore()
>>> mine = customize(blank_sheet(10.0, 6.0), name="Studio B")
>>> ref = save_sheet(store, mine)
>>> ref, get_sheet(ref, store).name, save_sheet(store, mine) == ref
('sheet:blank-10x6@2', 'Studio B', True)
>>> customize(stage_sheet, size=(14.0, 9.0))
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: sheet:proscenium-stage@1 is a stage sheet; only blank sheets resize (hint: pick a template of the right size, or start from blank_sheet())
>>> get_sheet("sheet:hs-futball")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown sheet 'sheet:hs-futball' (hint: did you mean hs-football, nfl-football, college-football?)
>>> from guide_draw import sketch
>>> sketch.sheet(
...     stage_sheet,
...     px_per_m=30.0,
...     caption="render_sheet(proscenium stage): wings, center line, spike marks.",
... )
```

The customized blank sheet was saved as version 2, because version 1 is the template it came
from. Saving it again returned the same reference: the store is idempotent.

## Looking things up: bounds.py

| Function                                | Does                                                                 |
| --------------------------------------- | -------------------------------------------------------------------- |
| `on_surface(sheet, p)`                  | true when `p` is on the outline or inside it                         |
| `walkable(sheet, p)`                    | true when `p` is in the walkable area (holes excluded)               |
| `landmark(sheet, name)`                 | finds by name, ID or alias; case and repeated spaces ignored         |
| `landmark_keys(mark)`                   | a landmark's normalized names, for matching                          |
| `landmark_anchor(mark)`                 | the point it stands for: the point, or the vertex centroid           |
| `nearest_landmarks(sheet, p, k, kinds)` | closest landmarks with distances; ties by ID                         |
| `zones_at(show, p, t=None)`             | sheet zones, then show zones, covering `p`, optionally active at `t` |

Distance to a landmark is distance to its geometry: zero inside an area, perpendicular to a
line.

```pycon
>>> from showpy.sheet.bounds import landmark, nearest_landmarks, on_surface, walkable, zones_at
>>> field = get_sheet("sheet:hs-football")
>>> landmark(field, "Home  HASH").id, landmark(field, "home hash").geometry[0]
('front-hash', (-45.72, 16.256))
>>> [(m.name, round(d, 3)) for m, d in nearest_landmarks(field, (3.0, 16.0), k=2)]
[('front hash', 0.256), ('right 45 yard line', 1.572)]
>>> on_surface(field, (0.0, -1.0)), walkable(stage_sheet, (0.0, 4.0))
(False, True)
>>> from showpy.examples import two_set_show
>>> [z.id for z in zones_at(two_set_show(), (0.0, -1.0))]
['pit']
```

The front hash is a line landmark running the length of the field at `y = 16.256` (53 ft
4 in), so a point at `y = 16` is 0.256 m from it.

## Wording positions: coords.py

People do not read `(3.5, 2.0)`. They read "3.50 m right of center, 2.00 m upstage of front
edge". `to_coords(show, p, style)` words a point in the show's `CoordinateSystem`;
`from_coords(show, text)` reads it back exactly (to the system's precision).

- **Long style**: `3.50 m right of center, 2.00 m upstage of front edge`.
- **Short style**: `R3.50 U2.00`.
- Directions are as the audience sees the sheet from `audience_side`. The `showpy` kind uses
  the performer's stage left and right instead: audience right is **stage left**.
- `coordinate_presets(sheet)` lists systems that suit a sheet; `set_coordinates(show,
system)` swaps the system and never moves a stored position.

Under the hood: `to_coords` subtracts the system's origin (a point or a landmark's anchor),
rotates into the audience frame (`FRAMES` holds one 2 × 2 frame per audience side), converts
meters to the system's unit, rounds with `round_to(precision)` and picks the direction word.
`from_coords` parses each clause, converts back with the registry and undoes the frame.

```pycon
>>> from showpy.sheet.coords import coordinate_presets, from_coords, set_coordinates, to_coords
>>> from showpy.sheet.models import CoordinateSystem
>>> show = two_set_show()
>>> to_coords(show, (3.5, 2.0)), to_coords(show, (3.5, 2.0), "short")
('3.50 m right of center, 2.00 m upstage of front edge', 'R3.50 U2.00')
>>> from_coords(show, "2.00 m upstage of front edge, 3.50 m left of center")
(-3.5, 2.0)
>>> feet = set_coordinates(show, CoordinateSystem(units="ft", precision=0.5))
>>> to_coords(feet, (3.5, 2.0)), feet.set("1") == show.set("1")
('11.5 ft right of center, 6.5 ft upstage of front edge', True)
>>> [p.kind.value for p in coordinate_presets(stage_sheet)]
['stage', 'grid', 'grid', 'stage']
>>> from_coords(show, "3.5 m sideways of center")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: cannot read 'sideways' in '3.5 m sideways of center' (hint: use one of: right, left, upstage, downstage)
```

3.5 m is 11.48 ft, which rounds to the half-foot 11.5. The sets did not change: a coordinate
system only changes words. The stage has four presets: its default (stage wording from the
front-center), metric and feet grids, and stage wording measured from the `center-stage`
landmark. Kinds repeat because presets differ by origin or unit.

## Drawing sheets: render.py

`SheetCanvas` maps meters to image pixels. The audience sits at the **bottom** of the image,
so y is flipped:

```text
px = (x - min_x) · px_per_m
py = (max_y - y) · px_per_m
```

`SheetCanvas.for_sheet(sheet, px_per_m, margin_m)` fits everything drawn on the sheet plus a
margin. `to_px`, `from_px` and `ring_px` convert. `draw_sheet(draw, canvas, sheet)` paints the
outline, walkable area, zones, guides and landmarks onto a Pillow drawing.
`render_sheet(sheet, fmt, px_per_m)` returns a printable blank sheet as SVG (written by
hand), PNG or PDF (both through Pillow). Video frames and printouts reuse `SheetCanvas` and
`draw_sheet`, so every picture of a show sits on the same background.

```pycon
>>> from showpy.sheet.render import SheetCanvas, render_sheet
>>> canvas = SheetCanvas.for_sheet(blank_sheet(10, 6), px_per_m=10, margin_m=1)
>>> canvas.size, canvas.to_px((0.0, 0.0)), canvas.from_px((60.0, 70.0))
((120, 80), (60.0, 70.0), (0.0, 0.0))
>>> render_sheet(blank_sheet(4, 4), "svg")[:38]
b'<?xml version="1.0" encoding="UTF-8"?>'
>>> render_sheet(blank_sheet(4, 4), "gif")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: unknown sheet format 'gif' (hint: use svg, png or pdf)
```

The 10 × 6 m sheet plus a 1 m margin is 12 × 8 m, 120 × 80 px at 10 px/m. The origin, the
front-center, is 60 px from the left and 70 px down: 1 m of margin above the bottom edge.

## Replacing a sheet: replace.py

`replace_sheet(show, sheet, mapping, force)` moves a whole show onto another sheet. It fits
**one** affine map and applies it to placements (with facings), form curves, path waypoints,
pivots, facing targets, route curves and show zones. It returns `(show, report)`. It does not
run checks; the caller runs its own safety checker afterwards (ADR 0001 fix 22).

Three mappings:

- `landmarks`: fit a similarity to the point landmarks the two sheets share by name or alias.
  With fewer than two shared landmarks it falls back to `origin`.
- `origin`: keep coordinates as they are.
- `scale`: scale x and y by the ratio of sheet sizes.

### The least-squares similarity fit (Umeyama)

Given matched points `x_i` (old sheet) and `y_i` (new sheet), find the rotation `R`, uniform
scale `s` and translation `t` that minimize `Σ |s·R·x_i + t - y_i|²`. Umeyama (1991) gives a
closed form; `similarity_fit` implements it line by line:

1. Center both sets: `x̄ = mean(x)`, `ȳ = mean(y)`. The spread is
   `σ² = mean |x_i - x̄|²`.
2. Covariance: `Σ = (1/n)·Σ (y_i - ȳ)(x_i - x̄)ᵀ`, a 2 × 2 matrix.
3. Singular value decomposition: `Σ = U·D·Vᵀ`.
4. `S = diag(1, ±1)`, with `-1` only when `det(U)·det(V) < 0`. This forbids a reflection,
   so the fit never mirrors the show.
5. `R = U·S·Vᵀ`, `s = trace(D·S)/σ²`, `t = ȳ - s·R·x̄`.

Fewer than two distinct points cannot fix a rotation and a scale, so it raises
`GeometryError`.

```pycon
>>> import numpy as np
>>> from showpy.sheet.replace import replace_sheet, similarity_fit
>>> src = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 5.0]])
>>> dst = src @ np.array([[0.0, 1.0], [-1.0, 0.0]]) * 2.0 + [3.0, 4.0]
>>> fit = similarity_fit(src, dst)
>>> np.allclose(fit, [[0.0, -2.0, 3.0], [2.0, 0.0, 4.0], [0.0, 0.0, 1.0]], atol=1e-9)
True
>>> moved, report = replace_sheet(two_set_show(), blank_sheet(80, 40), "scale")
>>> report.mapping, report.moved["T2"], moved.sheet.ref, moved.dependencies
('scale', ((2.0, 9.0), (4.0, 18.0)), 'sheet:blank-80x40@1', {'sheet:blank-80x40': '1'})
>>> similarity_fit(np.array([[1.0, 1.0], [1.0, 1.0]]), np.array([[0.0, 0.0], [1.0, 1.0]]))
Traceback (most recent call last):
  ...
showpy.core.errors.GeometryError: GEOMETRY: similarity fit needs at least two distinct matched points (hint: match two or more landmarks that are not on top of each other)
```

The fit is compared with `np.allclose` because its zero entries carry rounding noise near
`1e-16`, whose sign depends on the machine. The destination points were the source rotated 90°, scaled by 2 and shifted by `(3, 4)`;
the fit recovered exactly that matrix. In the `scale` example the 40 × 20 m test field went
onto an 80 × 40 m sheet, so every coordinate doubled: T2 moved from `(2, 9)` to `(4, 18)`.
The report also lists spots that land off the new sheet (`outside`) or in a restricted zone
(`in_zones`), and form recipes it changed (`form_notes`). The show's sheet dependency is
re-pinned to the new sheet's version.

> **Check your understanding 7.a.** On the proscenium stage, a performer at `x = +3` is on
> which side in `showpy` wording, and why?
>
> **Check your understanding 7.b.** Why does `similarity_fit` force `det(R) = +1`?

## Exercises

**Exercise 7.1 (warm-up).** Return the hash distance from the front sideline, in meters, of
the college template, read from its `front-hash` landmark.

**Exercise 7.2.** Word the point `(-2.25, 7.0)` in short style for `two_set_show()`, then
read it back. Return `(text, point)`.

**Exercise 7.3.** With `SheetCanvas.for_sheet(blank_sheet(20, 10), px_per_m=5, margin_m=2)`,
return the pixel of the stage point `(5, 5)`.

**Exercise 7.4 (harder).** Points `(0, 0)`, `(4, 0)`, `(0, 3)` were moved to `(10, 10)`,
`(10, 14)`, `(7, 10)`. Use `similarity_fit` and return `(scale, rotation in degrees,
translation)`.
