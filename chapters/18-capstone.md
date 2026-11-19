# Capstone project: a four-set mini show

You now know every part of the library. The capstone asks you to use them together and to
prove the result is sound with a check script, the way a safety checker does for a real show.

## The brief

Write `build_show()` in `exercises/solutions_template/capstone.py`. It must return
a `Show` that meets every requirement below. Then run:

```text
uv run python exercises/check_capstone.py
```

| Requirement | Limit                                  | How the check measures it                                                                       |
| ----------- | -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Structure   | `validate_show(show).ok`               | every spot in every set, paths compile, timeline sound                                          |
| Size        | exactly 4 sets, at least 8 spots       | `len(show.sets)`, `len(show.cast.spots)`                                                        |
| Forms       | stored forms of at least 2 kinds       | `{f.kind for f in show.forms.values()}`                                                         |
| Paths       | at least one non-straight path row     | a `curve`, `polyline`, `follow`, `rotate`, `custom` or `hold` row                               |
| Spacing     | no gap below 0.3 m                     | `min_gaps(show, tid, top=1)` for every transition (gap = centre distance minus both footprints) |
| Speed       | no instant speed above 1.0 m per count | `speeds(show, tid)["max_instant"]` for every transition                                         |

1.0 m per count is about 1¾ steps of 8-to-5 per count: fast but marchable. The check prints
`PASS capstone`, or `FAIL capstone:` and the first broken requirement, for example
`B2 and B3 come within 0.214 m in 1→2 at 7.40`.

## A plan that works

1. **Sheet and clock.** `new_show` on `sheet:hs-football` with `new_timeline(COUNTS, 144)`.
2. **Spots.** One group of 8 with `add_group` and `add_spots_along` on a line in set 1.
3. **Sets 2–4.** For each, `add_set(show, id, 16)`, build a form with **open** slots, match
   the previous set's spots to the slots with `match`, put the members on the form in slot
   order, and `place` it. Store the set it returns with `with_set` and the filled form with
   `apply_change([FormOp(...)])`. Use at least two kinds: for example a block, an arc and a
   circle.
4. **Paths.** Ease the first transition and curve two spots in the last one with
   `curve_path`; store each spec with `store_paths`.
5. **Measure as you go.** After each set, print `min_gaps` and `speeds`. If a gap is tight,
   try the fixes from chapter 12, a bigger interval, or a different form position. If a speed
   is high, give the transition more counts.

## The reference solution

{{code: exercises/answers/capstone.py}}

{{check: capstone}}

Measured on the reference show:

```pycon
>>> import sys
>>> sys.path.insert(0, "exercises/answers")
>>> import capstone
>>> from showpy.choreo.avoid import min_gaps
>>> from showpy.choreo.motion_stats import speeds
>>> show = capstone.build_show()
>>> for tid in show.transition_ids():
...     gap = min_gaps(show, tid, top=1)[0]
...     peak = float(speeds(show, tid)["max_instant"].max())
...     print(f"{tid[0]}->{tid[1]}: tightest {gap.a}-{gap.b} {gap.gap:.3f} m, peak {peak:.3f} m/count")
1->2: tightest B2-B3 0.742 m, peak 0.879 m/count
2->3: tightest B5-B7 1.375 m, peak 0.462 m/count
3->4: tightest B2-B7 2.744 m, peak 0.751 m/count
>>> from guide_draw import sketch
>>> sketch.frames(
...     show,
...     (0.0, 16.0, 32.0, 40.0, 48.0),
...     caption="The reference capstone show at each set and mid-way into the circle: line, block, arc, ring.",
... )
```

Why it passes:

- **Matching** every set with `bottleneck_then_sum` keeps the longest move short and avoids
  most crossings, so footprints never meet.
- **16 counts** per transition keep the longest move (about 13 m from the line to the block,
  eased) under the speed limit; `ease_in_out` raises the peak above the mean, which is why the
  first transition is the fastest at 0.879 m per count.
- **The curves** in the last transition swing B1 and B8 outward, away from the ring's other
  members.

## Going further

- Add a group of four flags that follows a route through the show, and keep every check
  green.
- Add a 2-second hold at count 32 and export a video with `export_video`: the frames repeat
  during the hold.
- Publish the show and write a check that every spot is claimable.
