# Glossary and a "where is X?" index

## Glossary

| Term             | Meaning                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Anchor           | What a note or comment is attached to: a set, a transition, a point, an area or spots. A tagged model (`kind` plus one payload).     |
| Arc angle        | An angle in the math convention: 0° is `+x`, counter-clockwise positive. Used by arcs, circles, spirals and rotations. Not a facing. |
| Arc length       | Distance travelled along a curve, in meters. Curves are parameterized by it.                                                         |
| Audio sync       | `AudioTrack.sync_offset_s`: the audio time that plays at count 0. Audio never changes timing.                                        |
| Bottleneck       | The largest single move in an assignment. The default matching minimizes it first.                                                   |
| Cast             | All groups and spots of a show.                                                                                                      |
| Chart            | A designer's table of every spot in one set.                                                                                         |
| Claim            | A performer on a spot, stored inside a `Publication`; locked once made.                                                              |
| Continuity       | A path must end within 1e-6 m of its target placement, or the engine raises `ContinuityError`.                                       |
| Coordinate sheet | One spot's part through the whole show, one row per set.                                                                             |
| CoordinateSystem | How positions are worded for people; display only.                                                                                   |
| Count            | The unit of time: one musical beat. Global count 0 is the show start.                                                                |
| Easing           | A monotone map of `[0, 1]` onto itself, from time share to distance share.                                                           |
| Engine           | `PathEngine`, the only code that turns paths into positions over time.                                                               |
| Facing           | Where a spot looks: degrees, 0 toward the audience, counter-clockwise positive. Vector `(sin θ, -cos θ)`.                            |
| Facing override  | A facing forced on spots over a global count range, on top of paths.                                                                 |
| Finding          | A validation result; safety findings come from a separate checker.                                                                   |
| Form             | A stored shape recipe plus ordered members; placements are generated from it.                                                        |
| Frame            | Every spot's state at one moment.                                                                                                    |
| Front-center     | The origin `(0, 0)`: the middle of the sheet's front edge.                                                                           |
| Group            | A designer-made set of spots with shared defaults.                                                                                   |
| Hold             | A pause in the clock at a count, in seconds.                                                                                         |
| Knot             | A point of the engine's time map: a local count and an arc length.                                                                   |
| Landmark         | A named point, line or area on a sheet, such as "front hash".                                                                        |
| Local count      | Counts since the start of the current transition (τ).                                                                                |
| Marker           | A named moment on the timeline.                                                                                                      |
| MotionPlan       | A spot's compiled move: a curve plus a time map.                                                                                     |
| On field         | Whether a spot is drawn and collision-checked in a set.                                                                              |
| Pack             | Domain rules and wording, such as marching (out of scope here).                                                                      |
| Path row         | `PathRow`: one spot's instructions for one transition. Rows are sparse.                                                              |
| Pin              | The designer's lock on a spot, form, set or transition. Edits need `force=True`.                                                     |
| Placement        | One spot's state in one set: position, facing, form, order, pin, on-field.                                                           |
| Publication      | A published revision of a show plus its claims.                                                                                      |
| Revision         | One saved state in a repository: ID, parent, time and changed paths. Who saved it, and why, is the host's record.                    |
| Route            | A shared curve that a file follows, leader first.                                                                                    |
| Segment          | A piece of motion linear in both space and time, within a tolerance, for exact collision checks.                                     |
| Selection        | An ordered, duplicate-free set of spot IDs.                                                                                          |
| Set              | A snapshot of every spot's placement at one moment.                                                                                  |
| Sheet            | The 2D design surface.                                                                                                               |
| Slot             | A position a form generates; members stand on slots, open slots are filled by matching.                                              |
| Spot             | One dot that lasts the whole show, later claimed by a performer.                                                                     |
| Tempo section    | Counts per minute from a count on, optionally ramping linearly.                                                                      |
| Transition       | The movement between two consecutive sets, written `a→b`.                                                                            |
| Waiver           | A designer-approved exception to a checker finding.                                                                                  |
| Workspace        | One show exposed as files at one revision, like a working copy.                                                                      |
| Zone             | An area with rules on a sheet or show, optionally active in count windows.                                                           |

## Where is X?

| I want to...                         | Module                        | Function or class                                        |
| ------------------------------------ | ----------------------------- | -------------------------------------------------------- |
| convert units                        | `showpy.core.units`           | `convert`, `register_unit`                               |
| turn a facing into a vector, or back | `showpy.core.units`           | `facing_vector`, `vector_facing`                         |
| compare floats                       | `showpy.core.util`            | `approx_equal`                                           |
| get randomness                       | `showpy.core.util`            | `seeded_rng`                                             |
| hash content                         | `showpy.core.util`            | `content_hash`                                           |
| expand `T1-T8`                       | `showpy.core.util`            | `parse_range`, `format_ranges`                           |
| build a line, arc, spline or Bézier  | `showpy.geo.shapes`           | `line`, `arc`, `curve_through`, `bezier`                 |
| fit SVG art or text into a box       | `showpy.geo.shapes`           | `svg_outline`, `text_outline`                            |
| parse SVG path data                  | `showpy.geo.svg`              | `parse_path`                                             |
| rebuild a curve from JSON            | `showpy.geo.curves`           | `curve_from_construction`                                |
| space spots on a curve               | `showpy.geo.spacing`          | `space_along`, `space_by_interval`, `space_proportional` |
| make a block, fill or scatter        | `showpy.geo.spacing`          | `block`, `fill`, `scatter`                               |
| rotate, mirror, scale or skew        | `showpy.geo.transforms`       | `rotate`, `mirror`, `scale`, `skew`, `affine`            |
| snap or align                        | `showpy.geo.transforms`       | `snap`, `snap_to_guides`, `align`, `distribute`          |
| map a facing through a matrix        | `showpy.geo.affine`           | `transform_facing`                                       |
| measure spacing or symmetry          | `showpy.geo.measure`          | `interval`, `form_metrics`, `symmetry_error`             |
| judge balance or coverage            | `showpy.geo.analysis`         | `balance`, `coverage`, `symmetry_score`                  |
| make a timeline                      | `showpy.time.timeline`        | `new_timeline`, `add_tempo`, `add_hold`, `add_marker`    |
| convert counts and seconds           | `showpy.time.clock`           | `count_to_seconds`, `seconds_to_count`                   |
| label measures                       | `showpy.time.measures`        | `count_to_measure`, `measure_to_count`                   |
| add groups and spots                 | `showpy.cast.spots`           | `add_group`, `add_spot`, `add_spots_along`, `fill_spots` |
| relabel or regroup                   | `showpy.cast.spots`           | `relabel`, `regroup`                                     |
| select spots by expression           | `showpy.cast.select`          | `select`                                                 |
| pick spots by place                  | `showpy.cast.select`          | `in_region`, `near`, `ordered_along`, `mirror_pairs`     |
| get a sheet template                 | `showpy.sheet.templates`      | `get_sheet`, `sheet_templates`, `blank_sheet`            |
| find a landmark                      | `showpy.sheet.bounds`         | `landmark`, `nearest_landmarks`                          |
| word a position                      | `showpy.sheet.coords`         | `to_coords`, `from_coords`                               |
| draw a sheet                         | `showpy.sheet.render`         | `render_sheet`, `SheetCanvas`, `draw_sheet`              |
| fit matched landmarks                | `showpy.sheet.replace`        | `similarity_fit`                                         |
| add notes                            | `showpy.notes.notes`          | `add_note`, `notes_for`, `notes_near`, `accept_draft`    |
| build a form                         | `showpy.choreo.forms`         | `line_form`, `arc_form`, `block_form`, ...               |
| get slots and facings                | `showpy.choreo.forms`         | `slots`, `slot_poses`, `placements`                      |
| edit a form                          | `showpy.choreo.form_ops`      | `edit`, `reorder`, `gate`, `transform_form`              |
| recognize a form                     | `showpy.choreo.form_fit`      | `detect_form`                                            |
| build a set from forms               | `showpy.choreo.form_place`    | `place`, `filled_forms`, `rebuild`                       |
| match spots to slots                 | `showpy.choreo.match`         | `match`, `match_by_order`                                |
| apply a match or swap                | `showpy.choreo.match_ops`     | `apply_match`, `swap`, `suggest_swaps`                   |
| edit paths                           | `showpy.choreo.paths`         | `delay`, `stagger`, `curve_path`, `set_easing`, ...      |
| follow the leader, counter-march     | `showpy.choreo.routes`        | `make_route`, `follow_and_set_targets`, `counter_march`  |
| set facings                          | `showpy.choreo.facing`        | `face_*`, `add_facing_override`                          |
| register a custom motion             | `showpy.choreo.motion`        | `register_motion`                                        |
| know where a spot is at a count      | `showpy.choreo.engine`        | `PathEngine.position`, `state_at`, `sample`              |
| get collision segments               | `showpy.choreo.engine`        | `PathEngine.segments`                                    |
| measure speed                        | `showpy.choreo.motion_stats`  | `speed`, `speeds`, `energy_curve`                        |
| find tight gaps                      | `showpy.choreo.avoid`         | `min_gaps`, `closest_approach`                           |
| fix a tight gap                      | `showpy.choreo.avoid`         | `suggest_delays`, `suggest_waypoint`, `apply_fix`        |
| create a show                        | `showpy.show.manage`          | `new_show`                                               |
| add, retime or renumber sets         | `showpy.show.manage`          | `add_set`, `insert_subset`, `set_counts`, `renumber`     |
| count spots per set                  | `showpy.show.counts`          | `spot_counts`                                            |
| apply edit ops                       | `showpy.show.changes`         | `apply_change`, `store_paths`                            |
| pin something                        | `showpy.show.pinning`         | `pin`, `unpin`                                           |
| validate structure                   | `showpy.show.validate`        | `validate_show`                                          |
| save and load                        | `showpy.show.storage`         | `open_workspace`, `load_show`, `save_show`               |
| keep history on disk                 | `showpy.show.file_repository` | `FileRepository`                                         |
| revert, diff                         | `showpy.show.history`         | `revert`, `diff_show`, `changelog`                       |
| propose and accept edits             | `showpy.show.collab`          | `propose`, `preview_proposal`, `accept`                  |
| print coordinate sheets              | `showpy.export.print_sheets`  | `coordinate_sheet`, `chart`, `cue_sheet`                 |
| make a PDF                           | `showpy.export.pdf`           | `to_pdf`                                                 |
| export or import data                | `showpy.export.data`          | `export_json`, `import_json`, `export_frames_csv`        |
| import positions from CSV            | `showpy.export.positions`     | `import_positions`                                       |
| publish and claim                    | `showpy.export.publish`       | `publish`, `claim_spot`, `notify_changes`                |
| render frames or video               | `showpy.export.video`         | `render_frame`, `export_video`                           |

Every name in the right column is also reachable as `showpy.<name>` through the lazy
top-level API.

```pycon
>>> import showpy
>>> for name in ("closest_approach", "space_along", "similarity_fit", "spot_counts"):
...     print(name, "->", getattr(showpy, name).__module__)
closest_approach -> showpy.choreo.avoid
space_along -> showpy.geo.spacing
similarity_fit -> showpy.sheet.replace
spot_counts -> showpy.show.counts
```

## Exercises

**Exercise 17.1 (warm-up).** Return the module that defines `suggest_swaps`, using
`import showpy` and attribute access.

**Exercise 17.2.** Return the sorted public names in `showpy.__all__` that contain `"note"`.

**Exercise 17.3 (harder).** For every chapter-12 function in the index above
(`min_gaps`, `closest_approach`, `suggest_delays`, `suggest_waypoint`, `apply_fix`), return a
dict from name to the first line of its docstring.
