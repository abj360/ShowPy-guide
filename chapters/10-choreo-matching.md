# showpy.choreo (2): matching spots to slots

When a form changes, someone must decide who goes where. With 8 spots and 8 slots there are
8! = 40,320 ways; with 100 spots, more than 10¹⁵⁷. A bad choice makes long moves, crossing
paths and collisions. **Matching** picks the assignment exactly and deterministically.

## The problem

Rows are spots, columns are slots, and the matrix holds the cost of sending spot `i` to slot
`j`. We need a one-to-one assignment of every spot to a distinct slot (there may be more
slots than spots) that is best under an objective. That is the **linear assignment problem**.

## The cost matrix: match_cost.py

`build_problem(from_, to_slots, entities, groups, slot_groups)` turns the input into a
`MatchProblem`: `from_` is a `Set` (its on-field spots, with their facings) or plain start
points; `to_slots` is slot points or forms whose slots are concatenated.

`build_costs(problem, options)` computes three things:

1. **Distance**: straight-line meters from every start to every slot.
2. **Penalties**, in meters, added to the distance:
   - `weights["backward"]`: per meter of the move that goes against the spot's facing
     (the negative part of `move · facing_vector`).
   - `weights["turn"]`: per degree between the facing and the travel direction.
   - `no_backward` as a number: a flat penalty for any backward move.
   - `cost_fn(spot, slot, start, target)`: any extra cost; infinity forbids the pair.
3. **Masks** of forbidden pairs, one per constraint, so an error can name the culprit:

| Option                             | Forbids                                                         |
| ---------------------------------- | --------------------------------------------------------------- |
| `keep_groups` (with `slot_groups`) | slots labeled for another group                                 |
| `group_slots={group: (slot, ...)}` | slots reserved for another group                                |
| `pinned={spot: slot}`              | every other slot for that spot, and that slot for everyone else |
| `forbid=((spot, slot), ...)`       | those pairs                                                     |
| `no_backward=True`                 | any move against facing                                         |
| `max_speed` (needs `counts`)       | moves longer than `max_speed · counts`                          |

The final cost is distance plus penalties, with `inf` wherever any mask forbids.
`cost_matrix(...)` in `match.py` returns it.

```pycon
>>> import numpy as np
>>> from showpy.choreo.match import bottleneck_value, cost_matrix, match, match_by_order
>>> from showpy.choreo.models import MatchOptions
>>> cost_matrix([(0, 0), (4, 0)], [(0, 3), (4, 3), (8, 3)]).round(3)
array([[3.   , 5.   , 8.544],
       [5.   , 3.   , 5.   ]])
>>> from showpy.examples import two_set_show
>>> s1 = two_set_show().set("1")
>>> cost_matrix(s1, [(0, 3), (0, 7)], entities=["T1"], options=MatchOptions(no_backward=True))
array([[ 2., inf]])
```

All spots face the audience (0°, the `-y` direction), so walking from `y = 5` to `y = 3` is
forward and `y = 7` is backward: `no_backward=True` forbids the second slot.

## The objectives

| `objective`                     | Minimizes                                                                 | Use when                                              |
| ------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------- |
| `sum`                           | `Σ cost^power`                                                            | total travel matters; `power > 1` punishes long moves |
| `sum_squares`                   | `Σ cost²`                                                                 | a classic compromise                                  |
| `bottleneck`                    | the largest single cost                                                   | the slowest performer sets the pace                   |
| `bottleneck_then_sum` (default) | the largest cost, then the total among assignments with that largest cost | almost always                                         |

Why the default? In drill, everyone moves in the same counts. The longest move decides the
step size the hardest-working performer must take, so minimize it first. Many assignments
share that optimum, so then pick the shortest total among them.

![The same five starts (dots) and slots (squares) under four rules. Minimizing the sum allows a 4.20 m move; the bottleneck rule caps the longest at 3.62 m but crosses more paths.](figures/fig_matching.png)

## The solvers: match_solve.py

### Min-sum: linear_sum_assignment

`solve_sum(cost)` calls SciPy's `linear_sum_assignment`, a modified Jonker–Volgenant
algorithm in the Hungarian family. It finds the exact minimum total in `O(n²·m)` for `n`
spots and `m` slots, handles `n < m`, and never visits most of the `m!/(m-n)!` assignments.

**Feasibility** comes first. `is_feasible(allowed)` asks whether every row can take a
distinct allowed column. It runs the same solver on a 0/1 matrix (0 allowed, 1 forbidden): a
full assignment exists exactly when the minimum total is 0.

### Bottleneck: an exact threshold search

The bottleneck value `B*` is the smallest `t` such that a full assignment exists using only
costs `≤ t`. `B*` must equal one of the matrix's costs, so:

1. Sort the unique finite costs: `v_0 < v_1 < ... < v_k`.
2. Binary search for the smallest `v_i` whose threshold matrix `cost ≤ v_i` is feasible.
   Feasibility is monotone: if `t` works, every larger `t` works too. So binary search is
   exact.

That is `ceil(log2(k + 1))` feasibility tests, each one assignment solve: about 13 solves for
a 100 × 100 matrix with 10,000 distinct costs. `min_max_threshold(cost)` returns `B*`;
`bottleneck_value(cost)` is the public wrapper.

Then:

- `bottleneck`: any assignment under the cap. The solver uses the 0/1 matrix
  `cost ≤ B* → 0, else 1`.
- `bottleneck_then_sum`: set every cost above `B*` to infinity and solve min-sum on the rest.

```pycon
>>> from showpy.choreo.match_solve import is_feasible, min_max_threshold, solve_ordered, solve_sum
>>> cost = np.array([[1.0, 9.0, 4.0], [2.0, 3.0, 8.0], [7.0, 6.0, 5.0]])
>>> solve_sum(cost).tolist(), float(cost[[0, 1, 2], solve_sum(cost)].sum())
([0, 1, 2], 9.0)
>>> min_max_threshold(cost), bottleneck_value(cost)
(5.0, 5.0)
>>> is_feasible(np.array([[True, False], [True, False]]))
False
```

Worked by hand: the sorted unique costs are 1, 2, 3, 4, 5, 6, 7, 8, 9. At threshold 4, row 2
(`7, 6, 5`) has no allowed slot, so it fails. At 5, rows can take `0→0`, `1→1`, `2→2`
(costs 1, 3, 5): feasible. So `B* = 5`.

### Order-preserving matching: dynamic programming

Sometimes the order must survive: a file of performers walks into a line and must not pass
each other. With `preserve_order=True`, spot `i` (in the order of `entities`) must take a
slot with a larger index than spot `i - 1`. `solve_ordered(cost, combine)` solves that exactly
with dynamic programming:

```text
T[0][j] = cost[0][j]
T[i][j] = cost[i][j] + min over k < j of T[i-1][k]          (combine = "sum")
T[i][j] = max(cost[i][j], min over k < j of T[i-1][k])      (combine = "max")
```

The inner minimum over all `k < j` is a **running prefix minimum** of the previous row, so
each row costs `O(m)` and the whole table `O(n·m)`. A back-pointer table remembers which `k`
gave the minimum; ties go to the smallest column. The answer is the minimum of the last row,
traced back. If that minimum is infinite, no ordered assignment exists.

```pycon
>>> solve_ordered(np.array([[0.0, 1.0, 5.0], [9.0, 0.0, 1.0]])).tolist()
[0, 1]
>>> starts = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
>>> slots = np.array([[2.5, 4.0], [1.5, 4.0], [0.5, 4.0], [5.0, 4.0]])
>>> free = match(starts, slots, options=MatchOptions(objective="sum", keep_groups=False))
>>> kept = match(
...     starts, slots, options=MatchOptions(objective="sum", keep_groups=False, preserve_order=True)
... )
>>> free.assignment, round(free.total_distance, 3)
({'0': 2, '1': 1, '2': 0}, 12.093)
>>> kept.assignment, round(kept.total_distance, 3), kept.crossings
({'0': 0, '1': 1, '2': 2}, 13.02, 3)
```

Read the last two results with care. The free min-sum match sends spot 0 to slot 2 at
`x = 0.5`, spot 2 to slot 0 at `x = 2.5`: straight up, no crossings, 12.093 m in total. With
`preserve_order=True` spot `i` must take a larger **slot index** than spot `i - 1`, and the
slot list here runs right to left. Keeping index order therefore forces every move to cross
(3 crossings, 13.02 m). Order preservation is about indexes, so list slots in the order the
file should take them.

### Crossings and the swap repair pass

Two straight moves **properly cross** when they meet strictly inside both. The test uses
orientations: `orient(a, b, c)` is the sign of the cross product `(b - a) × (c - a)`. Moves
`p→q` and `s→e` cross when `p, q` lie on opposite sides of line `s e` and `s, e` lie on
opposite sides of line `p q`:

```text
orient(p, q, s) · orient(p, q, e) < 0   and   orient(s, e, p) · orient(s, e, q) < 0
```

Touching ends, shared endpoints, collinear overlaps and zero-length moves do not count.
`crossing_mask` vectorizes this for one move against many; `count_crossings` counts pairs.

Exact solvers do not see crossings: a crossing is a property of two rows at once, which the
assignment model cannot express. When `weights["crossing"]` or `weights["group_spread"]` is
set, `match` runs `improve_by_swaps`, a local search in the spirit of 2-opt:

1. Score an assignment as its objective cost plus `crossing · (number of crossings)` plus
   `group_spread · (mean distance of each group's targets from their centroid)`.
2. One pass tries every pair swap `(i, k)`, then every move of a spot to a free slot, in
   index order, keeping a change only if the score drops (first improvement).
3. Changes that would exceed the bottleneck cap `B*` are refused, so the repair never undoes
   the main objective. Pinned spots never move.
4. Passes repeat until one changes nothing, or 25 passes (`MAX_SWAP_PASSES`).

It is a heuristic: it finds a local optimum, not always the global one.

### Determinism and good errors

`match` sorts spots naturally before solving (`T2` before `T10`), so the input order never
changes the answer. When no assignment exists, `_require_feasible` relaxes one constraint
at a time and reports the constraints whose removal would make it feasible, plus spots with
no allowed slot at all.

```pycon
>>> pts = [(0.0, 0.0), (1.0, 0.0)]
>>> match(
...     pts,
...     [(5.0, 0.0), (6.0, 0.0)],
...     options=MatchOptions(keep_groups=False, max_speed=0.5, counts=8.0),
... )
Traceback (most recent call last):
  ...
showpy.core.errors.MatchError: MATCH: no assignment satisfies max_speed (hint: relax max_speed; 0 have no allowed slot)
>>> match(pts, [(5.0, 0.0)])
Traceback (most recent call last):
  ...
showpy.core.errors.MatchError: MATCH: 2 spots but only 1 slots (hint: add 1 slots or match fewer spots)
>>> match(pts, [(0, 3), (1, 3)], options=MatchOptions(pinned={"0": 1, "1": 1}))
Traceback (most recent call last):
  ...
showpy.core.errors.MatchError: MATCH: 0 and 1 are both pinned to slot 1 (hint: pin each slot to one spot)
```

## Using match: match.py

`match(from_, to_slots, entities=None, options=None, groups=None, slot_groups=None)` returns
a `MatchResult`:

| Field                            | Meaning                                        |
| -------------------------------- | ---------------------------------------------- |
| `entities`                       | matched spots, in solver order                 |
| `assignment`                     | spot to slot index                             |
| `targets`, `target_points()`     | each spot's slot position                      |
| `total_distance`, `max_distance` | straight-line totals                           |
| `max_speed`                      | longest move / counts (when `counts` is given) |
| `crossings`                      | crossing pairs among the straight moves        |
| `unassigned_slots`               | slots nobody took                              |
| `explain`                        | plain-language lines                           |

`match_by_order(ordered_sel, form, from_=None)` assigns the `i`-th spot to the `i`-th slot,
with no optimization; it is what you get by reading a list.

```pycon
>>> result = match(s1, [(6, 12), (4, 12), (2, 12), (0, 12)], options=MatchOptions(counts=8.0))
>>> result.assignment, result.max_distance, result.max_speed, result.explain
({'T1': 3, 'T2': 2, 'T3': 1, 'T4': 0}, 7.0, 0.875, ('objective bottleneck_then_sum: largest move 7.00 m, total 28.00 m',))
>>> naive = match_by_order(["T1", "T2", "T3", "T4"], np.array([(6, 12), (4, 12), (2, 12), (0, 12)]), s1)
>>> naive.max_distance, naive.crossings
(9.219544457292887, 6)
>>> from guide_draw import sketch
>>> sketch.moves(
...     s1.positions(),
...     naive.target_points(),
...     caption="match_by_order: T1 takes slot 0 at the far right; six crossings.",
... )
>>> sketch.moves(
...     s1.positions(),
...     result.target_points(),
...     caption="match(): straight up, no crossings, longest move 7 m.",
... )
```

Under the hood: `match()` calls `build_problem`, sorts spots naturally, calls `build_costs`,
checks feasibility (`_require_feasible`), solves (`_solve`: min-sum, ordered DP, or
threshold search then min-sum), optionally repairs (`_improve` → `improve_by_swaps`), and
builds the result (`_result`, which also counts crossings).

## Applying matches to a show: match_ops.py

| Function                                  | Does                                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------------- |
| `with_set(show, new_set)`                 | replaces one set by ID                                                       |
| `clear_rows(show, tid, entities, force)`  | drops stored path rows; locked rows need `force`                             |
| `apply_match(show, tid, result, force)`   | writes targets into the destination set and drops those spots' path rows     |
| `swap(show, set_id, a, b, force)`         | swaps two spots' places (position, facing, form slot); form members swap too |
| `suggest_swaps(show, tid, k, same_group)` | ranks swaps that shrink the largest straight move or remove crossings        |

Moving a spot's target makes its stored path stale (a curve built for the old target would
miss the new one), so these functions drop the path rows and the spot walks straight.

```pycon
>>> from showpy.choreo.match_ops import apply_match, suggest_swaps, swap
>>> show = two_set_show()
>>> crossed = swap(show, "2", "T1", "T4")
>>> [(a, b, round(g, 3)) for a, b, g in suggest_swaps(crossed, ("1", "2"), k=2)]
[('T1', 'T4', 3.211), ('T1', 'T2', 0.0)]
>>> fixed = apply_match(show, ("1", "2"), match(show.set("1"), [(0, 3), (2, 3), (4, 3), (6, 3)]))
>>> fixed.set("2").positions().tolist()
[[0.0, 3.0], [2.0, 3.0], [4.0, 3.0], [6.0, 3.0]]
```

`suggest_swaps` says swapping T1 and T4 back would shrink the largest move by 3.211 m (from
`√(6² + 4²) = 7.211` to 4). The second suggestion has gain 0: it does not shrink the largest
move but removes crossings, the second ranking key.

> **Check your understanding 10.a.** Why is binary search over sorted costs enough to find
> the bottleneck exactly?
>
> **Check your understanding 10.b.** Why can't `linear_sum_assignment` minimize crossings by
> itself?

## Exercises

**Exercise 10.1 (warm-up).** Return the bottleneck value of the cost matrix
`[[4, 1, 3], [2, 0, 5], [3, 2, 2]]`.

**Exercise 10.2.** Match set 1 of `two_set_show()` to the slots `(0, 9)`, `(1, 9)`, `(2, 9)`,
`(3, 9)`, `(10, 9)` with the default options and return `(assignment, unassigned slots)`.

**Exercise 10.3.** Same starts, slots `(6, 3)`, `(4, 3)`, `(2, 3)`, `(0, 3)`, but `T1` is
pinned to slot 0. Return the result's `max_distance` and `crossings`.

**Exercise 10.4 (harder).** Implement the order-preserving DP yourself for `combine="sum"`
(no SciPy, no `solve_ordered`) as `solve(cost)` returning the column list. The check compares
it with `solve_ordered` on random matrices.
