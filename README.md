# ShowPy study guide

A 190-page study guide to ShowPy, the Python choreography library (import name `showpy`). It teaches every package from first principles, with runnable snippets, an end-to-end tutorial, 65 graded exercises and a capstone project. One command rebuilds it into `showpy-guide.pdf`.

## Why

Documentation drifts the moment the code moves. This guide cannot: the build runs every one of its 104 snippets, 11 tutorial files and 65 exercise checks against the pinned ShowPy, and fails if any printed output differs from the text. `uv run pytest` runs the same checks (163 tests, about 70 s on a laptop) without printing the PDF.

## Features

- **19 chapters plus an answer key:** conventions, `core`, `geo`, `time`, `cast`, `sheet`, `notes`, four chapters on `choreo`, `show`, `export`, a tutorial, testing, a glossary and a capstone.
- **Executed snippets:** every `>>>` block runs in the build, and its real output (or exception) prints under it.
- **Pictures from real results:** 56 figures, each drawn from numbers the library computed.
- **Graded exercises:** each has a stub, a check script that prints `PASS` or `FAIL` with a hint, and a reference answer.
- **Tutorial as code:** chapter 15 includes the files in `examples/` and their captured output.

## Quickstart

```bash
# No ports: the guide is a document.
uv sync && uv run pytest
```

## The pinned library

The guide is checked against one exact ShowPy build: the wheel in `vendor/`. `vendor/SHA256SUMS` holds its SHA-256, `uv.lock` records the same hash, and CI runs `sha256sum --check` before installing it. To move the guide to another ShowPy version, vendor a new wheel built from a branch or tag of the ShowPy repository:

```bash
scripts/refresh_wheel.sh <path-or-url-of-ShowPy-repository> <ref>
uv sync && uv run pytest && uv run python build_guide.py
```

The script clones the ref with its tags, builds the wheel, replaces the one in `vendor/`, rewrites `SHA256SUMS`, points `pyproject.toml` at the new file and re-locks. Commit the wheel, the checksum, `pyproject.toml`, `uv.lock` and the rebuilt PDF together.

## Usage

Build the PDF:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0   # WeasyPrint's libraries
uv run python build_guide.py
```

| Flag                | Effect                                                     |
| ------------------- | ---------------------------------------------------------- |
| `--update-snippets` | rewrites stored snippet outputs instead of failing on them |
| `--skip-examples`   | reuses the stored tutorial output                          |
| `--skip-figures`    | reuses the drawn figures                                   |
| `--skip-exercises`  | skips the exercise checks                                  |
| `--only TEXT`       | runs only chapters whose file name contains `TEXT`         |
| `--no-pdf`          | stops before printing the PDF                              |

Work an exercise: fill in the `TODO` in `exercises/solutions_template/ch02_ex1.py`, then run:

```bash
uv run python exercises/check_ch02_ex1.py             # checks your solution
uv run python exercises/check_ch02_ex1.py --answers   # checks the reference answer
```

## Structure

```text
build_guide.py        runs examples, figures, checks and snippets, then prints the PDF
guide_draw.py         draws pictures of snippet results (sketch.points, sketch.frames, ...)
guide.css             print stylesheet
chapters/             00-preface.md ... 18-capstone.md, 99-answers.md
examples/             t01_new_show.py ... t11_publish.py, and output/ with their stdout
exercises/            check_*.py, checklib.py, run_all_checks.py
  answers/            reference answers
  solutions_template/ stubs for the reader
figures/              make_figures.py, the figures it draws, and snippets/ drawn by the build
tests/integration/    pytest wrappers around examples, exercises and snippets
vendor/               the pinned showpy wheel and its SHA256SUMS
scripts/              refresh_wheel.sh, which vendors a new showpy wheel
showpy-guide.pdf      the built guide
```

## Development

```bash
uv sync
uv run ruff format . && uv run ruff check .
uv run mypy .                                   # strict
npm ci && npx prettier --check "**/*.{md,yml,yaml,json}"
```

After editing a chapter, run `uv run python build_guide.py --update-snippets --only <chapter>` and read the diff before committing it. Commit the rebuilt PDF with the change.

## Testing and CI

`uv run pytest` runs three suites:

| Suite               | Checks                                                           |
| ------------------- | ---------------------------------------------------------------- |
| `test_examples.py`  | every tutorial file prints exactly its stored output             |
| `test_exercises.py` | every reference answer passes its check, and every stub fails it |
| `test_snippets.py`  | every chapter's snippets print exactly what the chapter shows    |

CI (`.github/workflows/ci.yml`) runs ruff, `mypy --strict`, Prettier, pytest and `pip-audit` on Ubuntu with Python 3.14, on every push to `main` and every pull request. It verifies the vendored wheel's SHA-256 first and stops on a mismatch.

## Docs

- `showpy-guide.pdf`: the guide.
- `chapters/`: its Markdown sources.
- The ShowPy repository: the library, its `docs/showpy-api-reference.md` and its ADRs in `docs/adr/`.

## License

MIT. See `LICENSE`.

Maintained by abj360.
