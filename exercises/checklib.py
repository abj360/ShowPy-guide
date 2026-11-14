#!/usr/bin/env python3

"""
checklib.py --- loads a reader's exercise solution and reports PASS or FAIL with a hint

A check script calls `run(name, check)`. By default it loads the reader's file
`solutions_template/<name>.py`; with `--answers` it loads `answers/<name>.py` instead.

Contains:
    WrongAnswerError: signals a wrong answer and carries the hint to print
    expect(): raises WrongAnswerError with a hint unless a condition holds
    close(): reports whether two numbers or arrays agree within a tolerance
    load(): imports one solution file by exercise name
    run(): runs one check and prints PASS or FAIL
"""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import numpy as np

HERE = Path(__file__).resolve().parent
READER_DIR = HERE / "solutions_template"
ANSWER_DIR = HERE / "answers"
ANSWERS_FLAG = "--answers"


class WrongAnswerError(Exception):
    """Signals a wrong answer; the message is the hint shown to the reader."""


def expect(condition: object, hint: str) -> None:
    """Raises WrongAnswerError with `hint` unless `condition` is true."""
    if not condition:
        raise WrongAnswerError(hint)


def close(a: object, b: object, tol: float = 1e-6) -> bool:
    """Reports whether two numbers or arrays have equal shape and agree within `tol`."""
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return x.shape == y.shape and bool(np.all(np.abs(x - y) <= tol))


def load(name: str, answers: bool) -> ModuleType:
    """Imports `answers/<name>.py` or `solutions_template/<name>.py` as a module."""
    path = (ANSWER_DIR if answers else READER_DIR) / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"solution_{name}", path)
    if spec is None or spec.loader is None:
        raise WrongAnswerError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(name: str, check: Callable[[ModuleType], None]) -> None:
    """Runs `check` on the chosen solution, prints PASS or FAIL, and exits 0 or 1."""
    answers = ANSWERS_FLAG in sys.argv[1:]
    try:
        check(load(name, answers))
    except NotImplementedError:
        print(f"FAIL {name}: not solved yet; fill in the TODO in solutions_template/{name}.py")
        sys.exit(1)
    except WrongAnswerError as failure:
        print(f"FAIL {name}: {failure}")
        sys.exit(1)
    except Exception as error:
        print(f"FAIL {name}: the solution raised {type(error).__name__}: {error}")
        sys.exit(1)
    print(f"PASS {name}")
