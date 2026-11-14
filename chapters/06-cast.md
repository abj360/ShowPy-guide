# showpy.cast: groups, spots and the selection language

The **cast** is everything that stands on the sheet: groups and their spots. `showpy.cast`
draws spots, manages groups and labels, and resolves selection expressions such as
`group:trumpets - T3`.

## The data: models.py

- `Shape(kind, radius_m, width_m, depth_m, rotation_deg)`: a spot's footprint. A `circle`
  uses `radius_m` (default 0.3 m). A `rectangle` is `width_m` across the facing direction and
  `depth_m` along it, and turns with the spot's facing plus `rotation_deg`. Use rectangles for
  props. `extent_m` is the radius of the smallest circle that holds the footprint; collision
  helpers use it.
- `Group(key, name, label_prefix, symbol, color, default_radius, limits, moves)`: a
  designer-made set of spots. `limits` holds per-group overrides that only a safety checker reads;
  `moves=False` marks a stationary group such as a pit.
- `Spot(id, group, symbol, color, tags, active, shape, claimable)`: one dot for the whole
  show. `symbol` and `color` of `None` inherit the group's. `active=False` leaves the spot out
  of forms and checks. `claimable` is `performer`, `crew` or `none`.
- `LabelScheme(prefixes, start, pad)`: labeling rules. A group's prefix is
  `prefixes[group.key]` if present, else the group's own `label_prefix` (ADR 0001 fix 17).
- `Cast(groups, spots, selections, label_scheme)`: everything together. `cast.spot(id)`
  raises `UnknownRefError` with close matches; `cast.ids()` lists IDs in creation order.

```pycon
>>> from showpy.cast.models import Cast, Group, LabelScheme, Shape
>>> round(Shape(kind="rectangle", width_m=1.2, depth_m=0.5).extent_m, 4), Shape().extent_m
(0.65, 0.3)
>>> scheme = LabelScheme(prefixes={"trumpets": "TP"}, pad=2)
>>> scheme.prefix_for(Group(key="trumpets", label_prefix="T")), scheme.label("TP", 7)
('TP', 'TP07')
>>> from showpy.examples import two_set_show
>>> show = two_set_show()
>>> show.cast.spot("T7")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown spot 'T7' (hint: did you mean T4, T3, T2?)
```

The rectangle's extent is half its diagonal: `√(0.6² + 0.25²) = 0.65` m.

## Drawing and managing spots: spots.py

Every function takes a show and returns a new show. The central rule: **a spot exists in
every set.** Adding a spot adds a placement for it to every set. Removing one removes it
everywhere it is mentioned.

| Function                                                          | Does                                                                      |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `add_spot(show, point, group, set_id)`                            | adds one spot at `point`, on the field from `set_id` on and off it before |
| `add_spots_along(show, curve, n, group, set_id)`                  | adds `n` spots evenly by arc length                                       |
| `fill_spots(show, region, group, set_id, interval=None, n=None)`  | fills an area with a grid                                                 |
| `duplicate_spots(show, sel, offset, set_id)`                      | copies spots shifted by `offset`, under new labels                        |
| `delete_spots(show, sel, force=False)`                            | removes spots and every reference to them                                 |
| `regroup(show, sel, group)`                                       | moves spots to another group and relabels them; returns `(show, mapping)` |
| `add_group(show, group)` / `edit_group(show, key, **changes)`     | adds or edits a group                                                     |
| `remove_group(show, key, reassign_to=None)`                       | moves its spots first; returns `(show, mapping)`                          |
| `relabel(show, scheme)`                                           | renumbers every group under a scheme; returns `(show, mapping)`           |
| `define_selection(show, name, sel)`                               | stores a named selection usable as `sel:<name>`                           |
| `set_shape(show, sel, shape)` / `set_claimable(show, sel, value)` | edit spot fields                                                          |

How a new spot is placed: in sets before `set_id` it gets a placement with `on_field=False`
at the same point, so it is invisible but has somewhere to walk from. From `set_id` on it is
on the field at `point`. Its label is the **lowest free number** under the group's prefix.

```pycon
>>> from showpy.cast.spots import add_group, add_spot, add_spots_along, delete_spots, regroup
>>> from showpy.geo.shapes import line
>>> show2 = add_spot(show, (1.0, 2.0), "trumpets", "2")
>>> show2.cast.ids()[-1], [s.get("T5").on_field for s in show2.sets]
('T5', [False, True])
>>> show3 = add_spots_along(show, line((-4, 14), (4, 14)), 3, "trumpets", "1")
>>> show3.set("1").positions(["T5", "T6", "T7"]).tolist()
[[-4.0, 14.0], [0.0, 14.0], [4.0, 14.0]]
>>> from guide_draw import sketch
>>> sketch.frames(
...     show3,
...     (0.0, 8.0),
...     caption="add_spots_along: T5-T7 join on y = 14 in every set; render_frame at counts 0 and 8.",
... )
>>> brass, mapping = regroup(add_group(show, Group(key="brass", label_prefix="B")), ["T4"], "brass")
>>> mapping, brass.cast.spot("B1").group
({'T4': 'B1'}, 'brass')
>>> delete_spots(show, "T2-T3").cast.ids(), delete_spots(show, "T2-T3").set("2").entity_ids()
(('T1', 'T4'), ('T1', 'T4'))
>>> add_spot(show, (0.0, 0.0), "tubas", "1")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown group 'tubas' (hint: did you mean trumpets?)
```

`regroup` relabeled `T4` to `B1` and rewrote the ID **everywhere**: cast, every set's
placements, forms, path rows, routes, note anchors, facing overrides and zones. That is the
job of `rewrite.py`, below.

`fill_spots` with only `n` needs an interval. It finds the largest grid interval at which at
least `n` lattice points fit, by bisection between a small and a large spacing
(`FILL_SEARCH_STEPS = 40` halvings), then keeps the `n` points nearest the area's centroid.
More spacing means fewer points, so the count is monotone in the interval and bisection is
safe.

`delete_spots` refuses pinned placements, locked forms and locked paths unless `force=True`.
It also refuses to delete a spot that other spots face (`TOWARD_ENTITY`), raising
`ValidationError`, because those facings would point at nothing.

## The selection language: select.py

### Why a language

Scripts and the agent pick spots all the time: "the trumpets except T3", "everyone in form
`arc` and tagged `soloist`". A small expression language is shorter and safer than code, and
it can explain its errors.

### The grammar

```text
expression := term (operator term)*
operator   := "+"  (union)  |  "-"  (difference)  |  "&"  (intersection)
term       := word | "(" expression ")"
word       := "all"
            | <ID>                         e.g. T4
            | <ID> "-" <ID>                a range, e.g. T1-T8 (no spaces)
            | <prefix> "*"                 every label whose prefix is exactly <prefix>
            | "group:" <key> | "form:" <id> | "tag:" <tag>
            | "shape:" ("circle" | "rectangle") | "sel:" <name>
```

All operators have **equal precedence and apply left to right**. `A - B + C` means
`(A - B) + C`. Use parentheses to group. This is simpler than arithmetic precedence, and for
set operations there is no standard order anyway.

### How the parser works

1. **Tokenize.** The regular expression `[+\-&()]|[^\s+&()\-][^\s+&()]*` splits the text. An
   operator or parenthesis is one token. A word starts with any character except space, an
   operator or a parenthesis, and continues until space, `+`, `&` or a parenthesis. A word
   may contain `-` after its first character, so `T1-T8` stays one word (a range). Hence the
   rule: **put spaces (or parentheses) around every operator.** `T1-T4 - T2` is a range minus
   T2. A glued operator, as in `T1+T2`, is rejected with a `SchemaError` that gives its
   position, because the same text glued to `-` would otherwise be read as a range.
2. **Parse** with a small recursive-descent parser `_Parser`:
   - `_expression()` reads a term, then loops while the next token is an operator, reading the
     operator and the next term and combining them with `|`, `-` or `&` on `Selection`.
   - `_term()` reads a word and resolves it, or reads `(`, an expression and `)`.
   - `parse()` checks that every token was used.
3. **Resolve words** against a "universe": the show, a set, or a cast. A set knows its
   placements and forms but not groups or tags; a cast knows groups but not forms.

Order rules: a range keeps range order and skips missing middle labels (but both ends must
exist); other words keep creation order; `form:` keeps the form's member order.

```pycon
>>> from showpy.cast.select import select, is_label_dependent
>>> select(show, "T1-T4 - (T2 + T3)").ids
('T1', 'T4')
>>> select(show, "T1-T4 - T2 + T3").ids
('T1', 'T3', 'T4')
>>> select(show, "T* & T2-T3").ids, select(show, "group:trumpets").description
(('T2', 'T3'), 'group:trumpets')
>>> select(show, ["T4", "T1"]).ids
('T4', 'T1')
>>> is_label_dependent("group:trumpets - T3"), is_label_dependent("group:trumpets")
(True, False)
```

`T1-T4 - T2 + T3` is `((T1-T4) - T2) + T3`: T3 comes back at the end of the order, because a
union appends new IDs after the left side's IDs.

What if you get it wrong?

```pycon
>>> select(show, "T1 + T2 - T3").ids
('T1', 'T2')
>>> select(show, "T1+T2-T3").ids
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: operator '+' must be separated by spaces or parentheses (hint: use T4, T1-T8, T*, all, group:<key>, form:<id>, tag:<tag>, shape:circle|rectangle or sel:<name>, joined by + (union), - (difference), & (intersection) and parentheses; put spaces or parentheses around operators (T1 + T2 - T3); T2-T3 without spaces is a range)
>>> select(show, "group:trumpet")
Traceback (most recent call last):
  ...
showpy.core.errors.UnknownRefError: UNKNOWN_REF: unknown group 'trumpet' (hint: did you mean trumpets?)
>>> select(show, "(T1 + T2")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: expression ended, expected ) (hint: use T4, T1-T8, T*, all, group:<key>, form:<id>, tag:<tag>, shape:circle|rectangle or sel:<name>, joined by + (union), - (difference), & (intersection) and parentheses; put spaces or parentheses around operators (T1 + T2 - T3); T2-T3 without spaces is a range)
>>> select(show.set("1"), "group:trumpets")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: group: needs the cast, which a Set does not hold (hint: pass the Show or its Cast to select by group, tag, shape or sel)
>>> try:
...     select(show, "T1 + T9")
... except Exception as error:
...     print(error.context)
{'position': 5, 'spot': 'T9'}
```

Reading these:

- `T1 + T2 - T3` with spaces means `(T1 + T2) - T3`. Written without spaces, `T1+T2-T3` could
  be read as `T1 + (T2-T3 range)`, which is a different selection, so the parser refuses it
  and points at the first glued operator (position 2). Until 2026-11-12 it silently returned
  the range reading; the regression test `test_regression_glued_operators_raise_instead_of_misparsing`
  keeps it from coming back.
- Misspelled names get close matches in the hint.
- The `SchemaError` hint lists the whole grammar.
- `context["position"]` is the character offset of the bad token (here `T9` starts at
  index 5), so an editor can underline it.

`is_label_dependent(expr)` reports whether an expression names spots by label (IDs, ranges,
prefixes). Such an expression changes meaning when spots are relabeled, so `rewrite.py`
freezes it into an explicit ID list when it rewrites IDs.

### Spatial picks and ordering

| Function                              | Does                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------- |
| `in_region(set, shape)`               | on-field spots inside a ring or polygon; the boundary counts as inside    |
| `near(set, point, radius)`            | on-field spots within `radius`, in placement order                        |
| `where(set, predicate)`               | spots whose placement passes a Python predicate (off-field included)      |
| `ordered_along(set, sel, by)`         | order by `"form"` order, `"x"`, `"y"`, or projected arc length on a curve |
| `split(sel, k)`                       | `k` consecutive groups whose sizes differ by at most one, larger first    |
| `alternate(sel, k=2)`                 | deal into `k` interleaved groups                                          |
| `mirror_pairs(set, sel, axis_x, tol)` | pairs left spots with right partners by minimum total mismatch            |
| `label_prefix(spot_id)`               | the part before the trailing number, or `None`                            |

```pycon
>>> from showpy.cast.select import alternate, in_region, mirror_pairs, near, ordered_along, split
>>> s1 = show.set("1")
>>> in_region(s1, [(1, 4), (5, 4), (5, 6), (1, 6)]).ids, near(s1, (0, 5), 2.0).ids
(('T2', 'T3'), ('T1', 'T2'))
>>> ordered_along(s1, "all", by=line((10, 0), (-10, 0))).ids
('T4', 'T3', 'T2', 'T1')
>>> (
...     [p.ids for p in split(["A", "B", "C", "D", "E"], 2)],
...     [p.ids for p in alternate(["A", "B", "C", "D", "E"])],
... )
([('A', 'B', 'C'), ('D', 'E')], [('A', 'C', 'E'), ('B', 'D')])
>>> from showpy.geo.transforms import mirror
>>> both = s1.with_placements({"T1": {"x": -6.0}, "T2": {"x": -4.1}})
>>> mirror_pairs(both, "all", axis_x=0.0, tol=0.2)
[('T1', 'T4'), ('T2', 'T3')]
>>> sketch.points(
...     both.positions(),
...     numbered=True,
...     caption="mirror_pairs: T1 (0) pairs with T4 (3), T2 (1) with T3 (2); T2 misses its mirror partner by 0.1 m, inside tol.",
... )
```

`mirror_pairs` mirrors each left spot across `x = axis_x`, then solves an assignment
(Hungarian method, `scipy.optimize.linear_sum_assignment`) that minimizes the total distance
from mirror images to right spots. Pairs farther apart than `tol` are dropped.

## Renaming everywhere: rewrite.py

`rewrite_spot_ids(show, rename)` applies a function from old ID to new ID (or `None` to drop)
to every reference in a show: the cast, named selections, placements, forms (members), path
rows (keys, entities, `TOWARD_ENTITY` facing values), routes, note anchors, facing overrides
and show zones. A string selector that depends on labels is frozen to the rewritten ID list;
others, such as `group:trumpets`, stay as written. Callers check that the result keeps IDs
unique. `faces_entity(mode, value)` returns the spot a facing aims at, if any.

`relabel`, `regroup`, `remove_group`, `delete_spots` and `history.rename_entities` all use it,
so no code path can forget a reference.

> **Check your understanding 6.a.** What does `T1-T8 - group:flags & tag:lead` mean? Write it
> with parentheses.
>
> **Check your understanding 6.b.** Why does `add_spot` give the new spot a placement in sets
> before it enters?

## Exercises

**Exercise 6.1 (warm-up).** In `two_set_show()`, select every trumpet except `T2` and `T3`
using one expression with `group:`. Return the IDs.

**Exercise 6.2.** Add a group `flags` (prefix `F`) and four flags evenly spaced on the line
`(-3, 12)`–`(3, 12)`, entering at set `2`. Return the new show.

**Exercise 6.3.** Return the IDs of the on-field spots of set 1 within 2.5 m of `(3, 5)`,
ordered by `x` from right to left.

**Exercise 6.4 (harder).** Write `solve(show, expr)` that returns the character position of
the first bad token in `expr`, or `-1` when the expression is valid. Use the error context;
do not parse yourself.
