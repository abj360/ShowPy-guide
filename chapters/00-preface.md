# How to use this guide

This guide teaches the ShowPy library (import name `showpy`) from first principles. It is
written for anyone who builds on ShowPy and wants to know exactly how every part works. It
assumes you can read Python. It does not assume you know drill writing, computational geometry
or assignment algorithms.

## What the guide covers

- Chapter 1 gives the big picture: what ShowPy does, the mental model, and how the packages
  depend on each other.
- Chapter 2 explains the conventions every module follows: units, the origin, angles, time,
  immutability, determinism, errors and locks.
- Chapters 3 to 14 walk through the packages bottom up: `core`, `geo`, `time`, `cast`,
  `sheet`, `notes`, four chapters on `choreo`, then `show` and `export`. Every public function
  and class is listed with what it does, its inputs and outputs, an example and its pitfalls.
- Chapter 15 is an end-to-end tutorial. It builds a three-set show, inspects it, stores it,
  saves an edit from a second workspace, exports it and publishes it.
- Chapter 16 covers the tests and quality gates.
- Chapter 17 is a glossary and a "where is X?" index.
- Chapter 18 is a capstone project: a four-set show with its own check script.
- The appendix holds the answer key: answers to every "Check your understanding" question and
  worked solutions to every exercise.

## Exercises and checks

Every chapter ends with graded exercises, from warm-up to harder. Each one has three files
under `exercises/`:

| File                             | Purpose                                                       |
| -------------------------------- | ------------------------------------------------------------- |
| `solutions_template/chNN_exK.py` | Your stub. Replace the `TODO` body.                           |
| `check_chNN_exK.py`              | Runs your solution and prints `PASS` or `FAIL` with a hint.   |
| `answers/chNN_exK.py`            | The reference answer. `--answers` checks it instead of yours. |

Run a check from the repository root, for example
`uv run python exercises/check_ch02_ex1.py`. To run the snippets yourself, put the
repository root on `PYTHONPATH` so `from guide_draw import sketch` works.

You can read straight through. If you only want the engine, read chapters 2, 11 and 12.

## How the examples were checked

Every example in this guide ran against ShowPy on 2026-11-14.

- Every code block is followed by an **Output** box. The build script executes every
  snippet while it makes the PDF and prints what really came out, so the PDF cannot drift
  from the code. A red box shows a real exception: what happens when you get a call wrong.
- In the Markdown sources the same snippets are stored in `>>>` form with their outputs. The
  build fails if a stored output differs from a fresh run.
- When a result is spatial or changes over time, a picture drawn from that very result sits
  under the output. Snippets draw it with `sketch` from `guide_draw.py`.
- The tutorial in chapter 15 is a set of real files in `examples/`. The build runs
  each file and pastes its output into this document.
- Every figure is drawn from numbers the library computes. The figure script is
  `figures/make_figures.py`.

## Rebuilding this PDF

Run one command from the repository root:

```text
uv sync && uv run python build_guide.py
```

`uv sync` installs ShowPy and the pinned build tools from `uv.lock`. Add `--update-snippets`
after editing a chapter to refresh the outputs of its `>>>` examples, then read the diff
before you commit it.

## Notation

- Code names are in `monospace`. A trailing `()` marks a function, as in `match()`.
- `m` is meters, `cpm` is counts per minute, `s` is seconds.
- Points are written `(x, y)` in meters. Angles are in degrees unless the text says radians.
- "Returns a new show" means the input is unchanged and a new object comes back.
- `CLAUDE.md`, `docs/HANDOFF.md` and "ADR" numbers (`docs/adr/`) refer to files in the ShowPy
  repository.
- A "pitfall" is a mistake that is easy to make with the function, or a case where it behaves
  in a way you might not expect.
