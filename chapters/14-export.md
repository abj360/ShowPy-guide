# showpy.export: how a show leaves the app

`showpy.export` turns a show into things people use: a live link performers claim spots on,
coordinate sheets and charts, a dependency-free PDF, JSON and CSV data, and 2D video. Every
function is pure. Publications are immutable values, time stamps are explicit, and
notifications are returned, never sent.

## The data: models.py

| Class               | Holds                                                                                                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SheetRow`          | one set on a spot's coordinate sheet: counts, cumulative count, measure, worded position, `xy`, facing, behavior (`delay 2, move 6`), guide lines crossed, note |
| `CoordinateSheet`   | one spot's part through the whole show (and the claimer's name)                                                                                                 |
| `ChartRow`, `Chart` | every spot of one set, for the designer                                                                                                                         |
| `TextTable`         | a titled table of display strings, shared by CSV, text and PDF output                                                                                           |
| `Performer`         | `id`, `name`, `contact` (never kept by a publication), `role` (`performer` or `crew`)                                                                           |
| `Claim`             | `spot`, `performer`, `claimed_at`, `locked`                                                                                                                     |
| `Publication`       | `id`, `show_id`, `revision`, `link` (no token), `status` (`live`, `paused`, `closed`), `published_at`, `claims`, `join_token_sha256`                            |
| `PerformerView`     | what one performer sees: their spot's position text and counts in every set                                                                                     |

The coordinate-sheet type is called `CoordinateSheet`, not `Sheet`, because `Sheet` already
means the design surface (ADR 0001 fix 1).

## Printouts: print_sheets.py and pdf.py

- `coordinate_sheet(show, entity, precision=None, publication=None)` builds one spot's part,
  one row per set. Positions are worded by the show's `CoordinateSystem`. Facing, the
  behavior text and the guide lines crossed on the way come from the `PathEngine`, so a sheet
  can never disagree with the video.
- `coordinate_sheets(show, sel, ...)` builds many, sharing one engine.
- `chart(show, set_id, publication=None)` builds the designer's chart of a set.
- `cue_sheet(show)` lists set labels and cues, timeline markers and cue-mode cues in count
  order, as a DataFrame.

**Guide crossings** are found by intersecting the spot's drawn path with each guide line
(Shapely), sorted by the arc length where they happen, so a performer reads "cross the 45,
then the 40" in walking order.

`to_pdf(obj, layout)` prints a `CoordinateSheet` (`sheet`), a list of them (`book`), charts
(`chart_pages`) or the cue sheet (`cue_sheet`) as **PDF 1.4 written by hand**, with no
dependency at all. The writer:

1. lays tables out in the built-in Helvetica fonts on US Letter landscape, measuring text
   with a fixed average character width, and spills rows onto more pages;
2. writes each page's content stream (`BT ... Tj ... ET` text operators);
3. writes the objects (catalog, pages tree, fonts, pages, streams), records each object's
   byte offset, and writes the cross-reference table and trailer that PDF readers use to find
   them.

Text uses WinAnsiEncoding (cp1252); characters outside it print as `?`, and `→` prints as
`->`. `escape_text` escapes `(`, `)` and `\` and writes non-ASCII bytes as octal escapes. No
dates or IDs are embedded, so the same input gives byte-identical PDFs.

```pycon
>>> from showpy.examples import two_set_show
>>> from showpy.export.data import to_text
>>> from showpy.export.pdf import escape_text, to_pdf
>>> from showpy.export.print_sheets import chart, coordinate_sheet, cue_sheet
>>> show = two_set_show()
>>> print(to_text(coordinate_sheet(show, "T3")))
T3
set  counts  cumulative  measure  position                                              x  y  facing  behavior  crossings  note
1    0       0                    4.00 m right of center, 5.00 m upstage of front edge  4  5  0       start
2    8       8                    4.00 m right of center, 9.00 m upstage of front edge  4  9  0       move 8
>>> [(r.entity, r.xy) for r in chart(show, "2").rows][:2]
[('T1', (0.0, 9.0)), ('T2', (2.0, 9.0))]
>>> pdf = to_pdf(coordinate_sheet(show, "T3"))
>>> pdf[:8], pdf.count(b"/Type /Page "), to_pdf(coordinate_sheet(show, "T3")) == pdf
(b'%PDF-1.4', 1, True)
>>> escape_text("T(1) 90°")
b'T\\(1\\) 90\\260'
>>> to_pdf(chart(show, "2"), "sheet")
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: layout sheet prints CoordinateSheet objects, got Chart (hint: sheet: one CoordinateSheet; book: CoordinateSheets; chart_pages: Charts; cue_sheet: the cue_sheet() DataFrame)
```

## Data interchange: data.py and positions.py

- `export_json(show, include=None)` dumps `{"schema": "showpy.show.v1", "show": {...}}`;
  `include` keeps only some top-level fields (the ID always). `import_json(d)` refuses any
  other schema tag. The schema itself is committed as `schemas/showpy.show.v1.json`.
- `export_frames_csv(show, per_count=1)` samples every spot through the engine from count 0
  to the end: `count, seconds, entity, x, y, facing, on_field`.
- `as_table(obj)`, `to_csv(obj)`, `to_text(obj)` turn a coordinate sheet, chart or DataFrame
  into a `TextTable`, CSV (every cell quoted by the `csv` module) or aligned text.
- `FormatRegistry` holds named exporters and importers immutably; `register_exporter`,
  `register_importer` and `formats` manage it. `DEFAULT_FORMATS` has `json` and `frames_csv`.
- `import_positions(base, text, group, columns=None, force=False)` merges CSV rows of `set,
counts, entity, x, y[, facing]` into a show: missing sets are created in file order,
  missing spots join `group`, and every spot ends up placed in every set (holding its previous
  placement, or off the field before it first appears).

```pycon
>>> from showpy.export.data import DEFAULT_FORMATS, export_frames_csv, export_json, formats, import_json
>>> from showpy.export.positions import import_positions
>>> doc = export_json(show)
>>> doc["schema"], import_json(doc) == show
('showpy.show.v1', True)
>>> export_frames_csv(show).splitlines()[:3]
['count,seconds,entity,x,y,facing,on_field', '0,0,T1,0,5,0,true', '0,0,T2,2,5,0,true']
>>> formats(DEFAULT_FORMATS)
{'export': ['frames_csv', 'json'], 'import': ['json']}
>>> merged = import_positions(show, "set,counts,entity,x,y\n3,4,T1,1,1\n3,4,N1,5,5\n", "trumpets")
>>> merged.set_ids(), merged.set("3").get("T1").point, merged.set("1").get("N1").on_field
(['1', '2', '3'], (1.0, 1.0), False)
>>> import_json({"schema": "showpy.show/1", "show": {}})
Traceback (most recent call last):
  ...
showpy.core.errors.SchemaError: SCHEMA: document schema is 'showpy.show/1', not 'showpy.show.v1' (hint: export with export_json(); documents start {"schema": "showpy.show.v1"})
```

## Publishing and claims: publish.py

Publishing turns a revision of the show into a link. Performers open it and claim one spot
each, for the whole show. Claims are part of an **immutable** `Publication` (ADR 0001
fix 13): every claim function returns a new publication. There is no hidden claim
registry, so the result never depends on call order across processes.

| Function                                                                             | Does                                                                                                                                              |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `publish(show, publication_id, base_url, at, previous=None, *, join_token=None)`     | a live publication of the show's revision; claims of `previous` carry over when the spot still exists and the performer's role can still claim it |
| `join_link(pub, token)` / `verify_join_token(pub, token)`                            | the link performers open, `<link>?t=<token>`, once the token matches / whether it matches                                                         |
| `unpublish(pub)` / `pause(pub)`                                                      | closes it (claims stay on record) / pauses claiming                                                                                               |
| `qr_code(pub, token, size=512)`                                                      | a PNG QR code of the join link (segno), with whole-pixel modules and the standard quiet zone                                                      |
| `claim_spot(pub, show, performer, spot, at)`                                         | one spot per performer, one performer per spot; the claim is locked                                                                               |
| `claims(pub)`, `who_is_on(pub, spot)`, `unclaimed(pub, show)`                        | queries                                                                                                                                           |
| `swap_claims(pub, a, b)`, `reassign(pub, spot, performer, at)`, `release(pub, spot)` | designer edits                                                                                                                                    |
| `performer_view(pub, show, performer)`                                               | the performer's own view                                                                                                                          |
| `notify_changes(pub, old_show, new_show)`                                            | performers whose part changed, each with a summary; nothing is sent (ADR 0001 fix 20)                                                             |

A spot's `claimable` (`performer`, `crew`, `none`) must match the performer's `role`.

The link is a secret: whoever holds it can claim a spot. The first `publish` takes a
`join_token` (22 to 256 characters of `[A-Za-z0-9_-]`; draw it with
`secrets.token_urlsafe(16)`), stores only its SHA-256, and builds `pub.link` without it. The
host keeps the token and hands `join_link(pub, token)` to performers; a republish may omit the
token to keep it, or pass a new one to rotate it. `base_url` must be https, with no query,
fragment or credentials. Publications never keep contacts either: a `Claim` drops the
performer's `contact`, and the host keeps contacts in its own roster keyed by `Performer.id`.

```pycon
>>> from datetime import UTC, datetime
>>> from showpy.export.models import Performer
>>> from showpy.export.publish import (
...     claim_spot,
...     join_link,
...     notify_changes,
...     pause,
...     performer_view,
...     publish,
...     qr_code,
...     unclaimed,
...     who_is_on,
... )
>>> at = datetime(2026, 11, 12, 18, 0, tzinfo=UTC)
>>> token = "guide-join-token-0123456789"
>>> pub = publish(show, "opener", "https://shows.example/p", at, join_token=token)
>>> join_link(pub, token)
'https://shows.example/p/opener?t=guide-join-token-0123456789'
>>> pub.link, pub.status, unclaimed(pub, show)
('https://shows.example/p/opener', 'live', ['T1', 'T2', 'T3', 'T4'])
>>> ada = Performer(id="ada", name="Ada", contact="ada@example.org")
>>> pub, claim = claim_spot(pub, show, ada, "T2", at)
>>> claim.performer.contact is None
True
>>> claim.locked, who_is_on(pub, "T2").name, performer_view(pub, show, ada).sets[1]
(True, 'Ada', ('2', '2.00 m right of center, 9.00 m upstage of front edge', 8.0))
>>> claim_spot(pub, show, ada, "T3", at)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: Ada already holds T2 (hint: one spot per performer; ask the designer to reassign you)
>>> claim_spot(pause(pub), show, Performer(id="bo", name="Bo"), "T1", at)
Traceback (most recent call last):
  ...
showpy.core.errors.LockedError: LOCKED: publication opener is paused (hint: claims open only while the publication is live)
>>> from showpy.examples import with_targets
>>> notify_changes(pub, show, with_targets({"T2": {"x": 3.0}}))
[(Performer(id='ada', name='Ada', contact=None, role='performer'), 'moved in set 2')]
>>> from guide_draw import sketch
>>> sketch.image(qr_code(pub, token, size=200), caption="qr_code(): the join link as a PNG QR code.")
```

## 2D video: video.py

- `video_canvas(show, px_per_m)` builds a `SheetCanvas` over the sheet whose pixel size is
  even, because H.264 with `yuv420p` needs even width and height.
- `render_frame(show, frame, canvas)` draws one engine `Frame` over the sheet: each on-field
  spot is a dot of its footprint radius in its group's color, with a black tick toward its
  facing. Off-field spots are not drawn.
- `export_video(show, count_range, fps, audio, px_per_m)` renders MP4 bytes.

### How export_video works, and how audio stays in sync

1. Check `fps > 0` and the count range `0 ≤ t0 < t1 ≤ total`.
2. Ask the engine for frames with `engine.frames(t0, t1, fps=fps)`. This samples **per second
   of music**, not per count: it converts `t0` and `t1` to seconds with `count_to_seconds`,
   spaces `fps` frames per second between them, and converts each frame time back with
   `seconds_to_count`. A hold therefore shows as repeated frames, and a tempo ramp as frames
   that cover fewer counts per second as the tempo slows. The video's duration equals the
   music's duration.
3. Pipe each frame's RGB bytes to the ffmpeg binary bundled by `imageio-ffmpeg`, encoding
   H.264.
4. With `audio` (a mapping from the track's file URI to its bytes), mux the timeline's first
   track. The audio must start at the moment of count `t0`. That moment, in audio time, is
   `sync_offset_s + count_to_seconds(t0)`. ffmpeg's input seek `-ss` skips exactly that much
   of the audio before muxing, and `-shortest` ends at the shorter stream.

Audio only plays: nothing in this path changes when counts happen.

```pycon
>>> from showpy.choreo.engine import PathEngine
>>> from showpy.export.video import export_video, render_frame, video_canvas
>>> canvas = video_canvas(show, 7.0)
>>> canvas.size, [n % 2 for n in canvas.size]
((294, 176), [0, 0])
>>> frame = render_frame(show, PathEngine(show).sample(4.0), canvas)
>>> frame.size, frame.mode
((294, 176), 'RGB')
>>> clip = export_video(show, (0.0, 2.0), fps=4, px_per_m=4.0)
>>> clip[4:8], len(clip) > 1000
(b'ftyp', True)
>>> sketch.frames(
...     show, (0.0, 4.0, 8.0), caption="render_frame() of two_set_show() at counts 0, 4 and 8."
... )
>>> export_video(show, (4.0, 20.0))
Traceback (most recent call last):
  ...
showpy.core.errors.TimeRangeError: TIME_RANGE: count range 4.0–20.0 is outside the show (0–8.0) or empty (hint: pass 0 <= start < end <= 8.0)
```

Worked example of the sync. A track has 1.25 s of lead-in (`sync_offset_s = 1.25`), the show
runs at 120 cpm, and you export counts 8 to 16. Count 8 is at 4 s of show time, so the audio
seek is `1.25 + 4 = 5.25` s: the first frame (count 8) plays with the music that sounds at
5.25 s into the file.

> **Check your understanding 14.a.** Why are claims stored inside an immutable
> `Publication` instead of a module-level dictionary?
>
> **Check your understanding 14.b.** A show has a 3-second hold. How many extra frames does a
> 30 fps video contain because of it?

## Exercises

**Exercise 14.1 (warm-up).** Return the `behavior` texts of T1's coordinate sheet in
`two_set_show()` with T1 delayed by 2 counts in transition `1→2`.

**Exercise 14.2.** Export `two_set_show()` frames as CSV at 2 samples per count and return
the row for `T4` at count 4 as a list of strings.

**Exercise 14.3.** Publish `two_set_show()` with a join token, let Ada claim T1 and Bo claim
T2, swap them as the designer, and return `who_is_on` for T1 and T2 (names).

**Exercise 14.4 (harder).** For a timeline at 120 cpm with an audio track whose
`sync_offset_s` is 1.25 and a 2-second hold at count 4, return the audio seek in seconds that
`export_video` uses for the range starting at count 8.
