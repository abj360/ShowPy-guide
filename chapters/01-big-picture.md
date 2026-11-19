# The big picture

## The problem ShowPy solves

ShowPy is a choreography design library. It starts with marching band drill. A marching show is a
sequence of pictures. Each picture says where every performer stands at one moment. Between
two pictures, every performer walks from the old spot to the new one in a fixed number of
musical counts.

Writing a show by hand is slow. The designer places every dot, decides who goes where, plans
every path, and checks that nobody collides, that steps are not too large and that everyone
stays on the field. Then the designer prints charts for performers, and does it all again when
anything changes.

ShowPy splits the work. The designer decides what the show should look like. The library
makes it exact: it builds shapes, matches performers to spots, computes motion, finds tight
gaps and produces exports. Safety rules (collision limits, step sizes, waivers) belong to a
separate checker that consumes ShowPy. The library never imports a consumer.

## The mental model in ten words

Learn these ten terms first. Every later chapter builds on them.

| Term        | What it is                                                                                                                                    | Where it lives          |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| Sheet       | The 2D design surface: a football field, a stage or a gym floor. It has an outline, guide lines, landmarks and zones.                         | `showpy.sheet`          |
| Spot        | One dot that lasts the whole show. A performer later claims it. Its ID, such as `T4`, never changes.                                          | `showpy.cast`           |
| Group       | A designer-made set of spots, such as trumpets. It gives defaults: a label prefix, a color, a footprint radius.                               | `showpy.cast`           |
| Set         | A snapshot of every spot at one moment. Each spot has one `Placement`: position, facing, form membership, pin flag, on-field flag.            | `showpy.choreo.models`  |
| Transition  | The movement between two consecutive sets, written `12→13`. Its length in counts is the destination set's `counts`.                           | `showpy.choreo.models`  |
| Form        | A stored shape, such as an arc or a block, plus the ordered spots on it. Placements are generated from the form. Edit the form, not the dots. | `showpy.choreo.forms`   |
| Path        | How one spot moves in one transition, stored as a `PathRow`. A spot with no row walks straight over all the counts.                           | `showpy.choreo.paths`   |
| Engine      | `PathEngine`, the only code that turns paths into positions over time.                                                                        | `showpy.choreo.engine`  |
| Timeline    | The show clock. Counts are the unit. Tempo, holds, markers and cues convert counts to seconds.                                                | `showpy.time`           |
| Publication | A published revision of the show plus the claims performers made on spots.                                                                    | `showpy.export.publish` |

A `Show` holds all of these together: the sheet, the cast of groups and spots, the timeline,
the sets in order, the forms, the stored transitions, the notes and the designer's pins.

## A show, step by step

Here is the life of a show in the order the tutorial in chapter 15 follows.

1. Pick a sheet from the templates, for example the high-school football field.
2. Create a show. It starts with one set, `1`, at count 0.
3. Add groups, then draw spots. Each new spot gets a placement in every set.
4. Add sets. Build each set from forms: a block, an arc, a line.
5. When a form has open slots, match spots to slots so moves are short and do not cross.
6. Add paths: delays, staggers, curves, follow-the-leader routes, rotations, easing.
7. Ask the engine where everyone is at any count, how they face and how fast they go.
8. Find tight gaps and try suggested fixes. The designer and the checker make the final call.
9. Add notes, validate the structure, save to a repository and merge edits from others.
10. Export: video frames, coordinate sheets, data. Publish a link so performers claim spots.

## How the packages depend on each other

The library has nine packages. Figure 1.1 shows how their logic is layered: a package's
functions call only functions in the packages below it.

![The logic layers of `showpy`. Each arrow points from the importing package to the package it imports. The data classes in each package's `models.py` sit below all of this logic; see the text.](figures/fig_packages.png)

The same picture in text:

```text
            export      video, print sheets, data, pdf, publish
              |
             show       Show, manage, storage, history, collab, validate
              |
            choreo      sets, forms, matching, paths, motion, PathEngine, avoid
           /  |   \
       cast sheet notes groups and spots | sheet surfaces | design notes
          \   |   /
            geo   time   geometry (curves, spacing, transforms) | count clock
              \   /
              core      errors, ids, types, units, util, selection, validation

   below the logic: the data classes (cast/models, sheet/models, choreo/models, ...)
```

There are really two tiers.

1. **Data classes.** Each package keeps its frozen Pydantic models in `models.py` (the engine
   keeps its own in `engine_models.py`). A models module imports only `core` and other models
   modules. For example `choreo/models.py` (with `Set` and `Placement`) imports only `core`.
2. **Logic.** Functions live in the other modules. A logic module may import any data class,
   but only logic from its own package or a lower one.

That is why `showpy.geo.transforms` can accept a `Set` (a data class from `choreo.models`)
without importing any choreo logic. `showpy.geo` never imports the engine.

Why the layering exists:

- **No import cycles.** Python runs a module top to bottom when it is imported. If module A
  imported module B and B imported A, one of them would see the other half built. In `showpy`
  the module graph is a directed acyclic graph (a DAG): you can always import a module after
  everything it needs. Exercise 1.3 asks you to measure this graph yourself.
- **One reason to change.** `geo` is pure geometry. It knows nothing about time. `time` knows
  nothing about geometry. Motion, which needs both, lives one level up in `choreo`.
- **Testable in isolation.** You can test `geo.curves` with no show, no sheet and no clock.
- **One motion source.** Every consumer of motion (canvas, checker, exports, analysis) sits
  above `choreo.engine` and asks it. None of them computes positions on its own.

Two rules from ADR 0001 keep the graph clean.

- Subpackage `__init__.py` files hold only a docstring. Code always imports the submodule, as
  in `from showpy.geo.curves import Segment`. The top-level `showpy/__init__.py` re-exports the
  public API lazily, so `import showpy; showpy.PathEngine` also works.
- A few modules act on a `Show` but sit below `show`, for example `cast.spots`,
  `sheet.coords` and `notes.notes`. They import `Show` only for type checking. They edit a
  show with `show.model_copy(update=...)`, which does not need the class at run time.

Saving and loading paths through the workspace lives in `showpy/show/paths_store.py`, not in
`showpy.choreo`, because it needs `showpy.show.storage`, which is one layer up. The rule holds:
no package imports a package above it.

```pycon
>>> import showpy
>>> showpy.PathEngine.__module__
'showpy.choreo.engine'
>>> len(showpy.__all__)
564
```

Under the hood: `import showpy` runs only `showpy/__init__.py`. That file holds a table from
public name to submodule. The first time you touch `showpy.PathEngine`, a module-level
`__getattr__` imports `showpy.choreo.engine` and returns the class. Nothing else loads early.

> **Check your understanding 1.a.** Why can `showpy.geo.measure` take a `Set` as an argument
> without breaking the layering?
>
> **Check your understanding 1.b.** A spot has no path row in a transition. What does it do?

## What is not here

- Safety checking is not here. Collision limits, step-size limits and waivers belong to the
  designer and to a checker that consumes ShowPy. The library never imports a consumer.
- Apps and assistants that build on ShowPy keep their own code, such as scripting and drafting
  tools, in their own repositories. ShowPy holds only shared domain logic.
- Marching rule packs and field wording, and an API registry, are not part of ShowPy.
- There is no 3D. The 2D core must never depend on 3D.
- There is no music analysis. Audio is only played back. It never changes timing.

## Exercises

Each exercise has a stub file to fill in and a check script. Edit
`exercises/solutions_template/ch01_ex1.py`, then run
`uv run python exercises/check_ch01_ex1.py` from the repository root. The check
prints `PASS` or `FAIL` with a hint. Worked answers are in the answer key at the end.

**Exercise 1.1 (warm-up).** Return the dotted name of the module that defines `PathEngine`.
Do not type it: ask Python.

**Exercise 1.2.** Load `showpy.examples.two_set_show()` and return a tuple
`(number of spots, number of sets, number of stored transitions)`.

**Exercise 1.3 (harder).** Write `solve(package)` that reads every `.py` file of
`showpy/<package>/` with `ast` and returns the set of other `showpy` packages it imports at run
time (skip imports inside `if TYPE_CHECKING:`). For `"geo"` the answer explains why the text
talks about two tiers.
