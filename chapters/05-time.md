# showpy.time: the count timeline

Time in a show is counted in beats. `showpy.time` turns counts into seconds and back, names
moments with markers and cues, numbers measures, and holds the audio sync point. It knows
nothing about positions.

## The data: models.py

| Class            | Fields                                                                            | Meaning                                                  |
| ---------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `TimelineMode`   | `counts`, `seconds`, `cues`                                                       | how the show is timed                                    |
| `TempoSection`   | `at_count`, `counts_per_minute`, `ramp_to`, `ramp_counts`                         | tempo from a count on, optionally ramping linearly       |
| `Hold`           | `at_count`, `seconds`, `note`                                                     | the clock stops at a count for some seconds (a fermata)  |
| `Marker`         | `label`, `at_count`, `kind`                                                       | a named moment; `kind` is `rehearsal`, `cue` or `custom` |
| `MeasureSetting` | `counts_per_measure`, `start_measure`, `changes`                                  | optional measure numbering                               |
| `MeasureLabel`   | `measure`, `count_in_measure`                                                     | a 1-based display label                                  |
| `Cue`            | `label`, `order`, `estimated_seconds`                                             | a moment in cue mode, for theatre-style shows            |
| `AudioTrack`     | `file`, `label`, `sync_offset_s`, `gain`, `section`                               | playback audio; never changes timing                     |
| `Timeline`       | `mode`, `tempos`, `holds`, `markers`, `measures`, `cues`, `audio`, `total_counts` | the whole clock                                          |

Three modes exist because shows are timed differently:

- **counts**: marching and dance. Tempo sections convert counts to seconds.
- **seconds**: a show timed by the stopwatch. Without tempos the clock runs at 60 counts per
  minute, so one count is one second.
- **cues**: theatre. Moments follow a running order; `cue_to_seconds` estimates when a cue
  starts from the earlier cues' estimated durations. Counts cannot convert without a tempo.

## Editing a timeline: timeline.py

Every function returns a new `Timeline` and keeps lists sorted.

| Function                                                         | Does                                                                               |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `new_timeline(mode, counts_per_minute=None, total=None)`         | starts a timeline; counts mode needs a tempo, which becomes the section at count 0 |
| `add_tempo(tl, section)` / `remove_tempo(tl, at_count)`          | sets or drops a section; same count replaces                                       |
| `add_hold(tl, hold)` / `remove_hold(tl, at_count)`               | sets or drops a pause                                                              |
| `add_marker(tl, marker)` / `remove_marker(tl, label)`            | labels are unique                                                                  |
| `add_cue(tl, cue)` / `remove_cue(tl, label)`                     | cues stay in running order                                                         |
| `set_measures(tl, setting)` / `clear_measures(tl)`               | turns measure numbering on or off                                                  |
| `attach_audio(tl, track)` / `remove_audio(tl, label)`            | adds or drops playback audio                                                       |
| `set_sync(tl, label, offset_s)`                                  | sets the audio time that plays at count 0                                          |
| `marker_to_count(tl, label)` / `counts_from_markers(tl, labels)` | resolve labels to counts                                                           |
| `cue_to_seconds(tl, label)`                                      | sum of estimates of all cues with lower order                                      |
| `to_json(tl)` / `from_json(d)`                                   | JSON round trip; bad data raises `SchemaError`                                     |

```pycon
>>> from showpy.time.models import AudioTrack, Hold, Marker, MarkerKind, TempoSection, TimelineMode
>>> from showpy.time.timeline import (
...     add_hold,
...     add_marker,
...     add_tempo,
...     attach_audio,
...     new_timeline,
...     set_sync,
... )
>>> tl = new_timeline(TimelineMode.COUNTS, counts_per_minute=144.0)
>>> tl = add_tempo(tl, TempoSection(at_count=64.0, counts_per_minute=120.0))
>>> tl = add_hold(tl, Hold(at_count=32.0, seconds=2.0, note="fermata"))
>>> tl = add_marker(tl, Marker(label="hit", at_count=48.0, kind=MarkerKind.REHEARSAL))
>>> tl = set_sync(attach_audio(tl, AudioTrack(file="asset:opener.wav", label="opener")), "opener", 1.25)
>>> [(t.at_count, t.counts_per_minute) for t in tl.tempos], tl.audio[0].sync_offset_s
([(0.0, 144.0), (64.0, 120.0)], 1.25)
>>> add_marker(tl, Marker(label="hit", at_count=50.0))
Traceback (most recent call last):
  ...
showpy.core.errors.TimelineError: TIMELINE: marker 'hit' already exists (hint: pick another label or remove the existing marker first)
>>> new_timeline(TimelineMode.COUNTS)
Traceback (most recent call last):
  ...
showpy.core.errors.TimelineError: TIMELINE: a counts timeline needs a starting tempo (hint: pass counts_per_minute, e.g. new_timeline(TimelineMode.COUNTS, 144.0))
```

`sync_offset_s = 1.25` means the music file has 1.25 s of lead-in before count 0. Moving the
sync point slides the music under the show; it never changes when counts happen.

## The clock: clock.py

### Pieces

`clock.py` first cuts the timeline into **pieces**: stretches of counts where the tempo is
steady or changes linearly. Each piece knows its start count, end count, starting tempo `r0`
and slope `k` (counts per minute per count). Then:

1. Each tempo section becomes one steady piece, or a ramp piece plus a steady piece at the
   reached tempo if the ramp ends before the next section.
2. Every hold count splits the piece it falls in, so a hold always sits at a piece start.
3. The last piece runs to infinity.

`_require_valid_section` rejects bad sections: tempos must be positive, and `ramp_to` and
`ramp_counts` come together or not at all.

### Tempo ramps: integrating and inverting

A ramp changes tempo **linearly in counts**:

```text
r(c) = r0 + k·(c - c0),     k = (ramp_to - r0) / ramp_counts
```

One count lasts `60 / r(c)` seconds. The time from the piece start `c0` to count `c` is the
integral of that duration:

```text
seconds(c) = ∫ from c0 to c of 60 / (r0 + k·(x - c0)) dx
           = (60 / k) · ln( r(c) / r0 )
           = (60 / k) · log1p( k·(c - c0) / r0 )
```

For a steady piece (`k = 0`) the formula becomes the familiar `60·(c - c0)/r0`.

The inverse answers "which count is playing at this second?" Solve `s = (60/k)·ln(r/r0)` for
`r`, then for `c`:

```text
r = r0 · exp(k·s / 60)
c = c0 + (r - r0) / k = c0 + r0 · expm1(k·s / 60) / k
```

`log1p(x) = ln(1 + x)` and `expm1(x) = eˣ - 1` keep full precision when `x` is tiny, which
happens on a gentle ramp. Written as `ln(1 + x)`, a ramp of 0.001 cpm per count would lose
about half its digits to rounding. The inverse is exact, so `seconds_to_count` needs no
search.

![A ramp from 120 to 180 cpm over 32 counts, then 90 cpm from count 48, with a 3-second hold at count 40. Left: tempo. Right: seconds since count 0 (red) against a steady 120 cpm (dashed). The jump at count 40 is the hold.](figures/fig_tempo.png)

Worked example. The ramp 120 → 180 over 32 counts has `k = 60/32 = 1.875`. The 32 counts take
`(60/1.875)·ln(180/120) = 32·0.405465 = 12.975` s. At a steady 120 cpm they would take 16 s;
at 180, 10.667 s. The ramp lands between them. Look at the numbers the library prints:

```pycon
>>> from showpy.time.clock import (
...     count_to_seconds,
...     describe_count,
...     seconds_per_count,
...     seconds_to_count,
...     tempo_at,
... )
>>> from showpy.time.models import Timeline
>>> ramp = TempoSection(at_count=0.0, counts_per_minute=120.0, ramp_to=180.0, ramp_counts=32.0)
>>> rt = Timeline(mode=TimelineMode.COUNTS, tempos=(ramp,))
>>> round(count_to_seconds(rt, 32.0), 6), tempo_at(rt, 16.0), round(seconds_per_count(rt, 16.0), 6)
(12.974883, 150.0, 0.4)
>>> round(seconds_to_count(rt, count_to_seconds(rt, 21.7)), 9)
21.7
>>> import numpy as np
>>> from guide_draw import sketch
>>> counts = np.linspace(0.0, 40.0, 81)
>>> sketch.plot(
...     counts,
...     [count_to_seconds(rt, c) for c in counts],
...     counts * 0.5,
...     counts / 3.0,
...     labels=("ramp 120→180 then 180", "steady 120", "steady 180"),
...     xlabel="count",
...     ylabel="seconds",
...     caption="count_to_seconds() of the ramp timeline against two steady tempos.",
... )
```

12.975 s lies between 16 and 10.667, and `seconds_to_count` inverts `count_to_seconds`
exactly (to 9 decimals here; the property tests check the round trip on random timelines).

### Holds

A `Hold(at_count=h, seconds=d)` stops the counts at `h` for `d` seconds. The rule:

- `count_to_seconds(c)` adds the hold for every count **after** `h`, not at `h` itself. So
  count `h` is the moment the hold starts.
- `seconds_to_count(s)` returns `h` for every second inside the hold.

```pycon
>>> held = add_hold(new_timeline(TimelineMode.COUNTS, 120.0), Hold(at_count=8.0, seconds=3.0))
>>> [count_to_seconds(held, c) for c in (8.0, 8.5)]
[4.0, 7.25]
>>> [seconds_to_count(held, s) for s in (4.0, 5.5, 7.0, 7.25)]
[8.0, 8.0, 8.0, 8.5]
>>> describe_count(held, 8.5)
'count 8.5, 0:07.3, 120 cpm'
>>> count_to_seconds(held, -1.0)
Traceback (most recent call last):
  ...
showpy.core.errors.TimeRangeError: TIME_RANGE: counts -1.0 is before the show start (hint: counts start at 0, the show start)
```

Count 8 is at 4.0 s. The hold adds 3 s, so count 8.5 is at `4 + 3 + 0.25 = 7.25` s. Every
second from 4 to 7 maps back to count 8: the performers are frozen.

Under the hood, `count_to_seconds(tl, c)` calls `_pieces(tl)`, then walks the pieces in
order. For each piece that starts before `c` it adds the hold at the piece start (if any) and
`piece.seconds_to(min(c, piece.end))`. `seconds_to_count` walks the same pieces, subtracting
each hold and each piece's full duration until the remaining seconds fall inside one, then
calls `piece.count_after(remaining)`, the analytic inverse.

`describe_count(tl, c)` renders `count 8.5, 0:07.2, 120 cpm` (plus `(m. 3)` when measures are
on). The clock text rounds to tenths with `round_to` (chapter 3), half away from zero, so
7.25 s prints as `0:07.3`, the same rule as every other displayed number. The name
`describe_count` keeps it apart from a pack language's `describe` (ADR 0001 fix 5).

## Measures: measures.py

Designers often think in measures: "m. 33, count 3". A `MeasureSetting` has a starting length
`counts_per_measure`, the number of the first measure `start_measure` and a list of
`changes`, each `(count, new length)`. Each change starts a new measure at its count.

The timeline splits into segments at the changes. Inside a segment starting at count `s` with
length `m` and first measure number `k`:

```text
measure          = k + floor((c - s) / m)
count_in_measure = (c - s) mod m + 1
```

`measure_to_count` inverts it. Both are 1-based for display only.

```pycon
>>> from showpy.time.measures import count_to_measure, measure_to_count
>>> from showpy.time.models import MeasureSetting
>>> from showpy.time.timeline import set_measures
>>> mt = set_measures(
...     new_timeline(TimelineMode.COUNTS, 120.0),
...     MeasureSetting(counts_per_measure=4.0, changes=((32.0, 3.0),)),
... )
>>> (
...     count_to_measure(mt, 0.0),
...     count_to_measure(mt, 31.0),
...     count_to_measure(mt, 32.0),
...     count_to_measure(mt, 40.0),
... )
(MeasureLabel(measure=1, count_in_measure=1.0), MeasureLabel(measure=8, count_in_measure=4.0), MeasureLabel(measure=9, count_in_measure=1.0), MeasureLabel(measure=11, count_in_measure=3.0))
>>> measure_to_count(mt, 11, 3.0)
40.0
>>> describe_count(mt, 40.0)
'count 40 (m. 11), 0:20.0, 120 cpm'
```

Eight measures of four counts take counts 0 to 31. The change at 32 starts measure 9 in 3/4.
Count 40 is 8 counts in: two full measures (9 and 10) and the third count of measure 11.

## Validation: validate.py

`validate_timeline(tl)` checks tempos (first at count 0, sorted, positive, ramps complete),
holds, unique marker and cue labels, measure lengths and audio sections, and returns a
`ValidationReport`. It never raises.

```pycon
>>> from showpy.time.validate import validate_timeline
>>> bad = Timeline(
...     mode=TimelineMode.COUNTS, tempos=(TempoSection(at_count=4.0, counts_per_minute=-10.0),)
... )
>>> print(validate_timeline(bad))
E: TEMPO_START tempo at 4: first tempo does not start at count 0 (hint: add a tempo section at count 0)
E: TEMPO_NONPOSITIVE tempo at 4: tempo is not positive (hint: use tempos > 0)
```

> **Check your understanding 5.a.** Why does the clock use `log1p` and `expm1` rather than
> `log` and `exp`?
>
> **Check your understanding 5.b.** A hold of 2 s sits at count 16. At 120 cpm, what is
> `count_to_seconds` at 16 and at 17?
>
> **Check your understanding 5.c.** You change `sync_offset_s` from 0 to 3. Which counts move
> in time?

## Exercises

**Exercise 5.1 (warm-up).** At 144 cpm with a 2-second hold at count 32, return the seconds
at count 64.

**Exercise 5.2.** For the ramp 120 → 180 cpm over 32 counts, return the count playing at
10 seconds. Use the library, then confirm it with the closed-form inverse.

**Exercise 5.3.** With 4 counts per measure and a change to 3 at count 32, return the
`MeasureLabel` of count 50 as a tuple `(measure, count_in_measure)`.

**Exercise 5.4 (harder).** In the same ramp, find the count where the tempo reaches 150 cpm
and the seconds at that count. Return `(count, seconds)`. Derive the seconds by hand from
`(60/k)·ln(r/r0)` first.
