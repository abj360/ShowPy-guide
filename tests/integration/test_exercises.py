#!/usr/bin/env python3

"""
test_exercises.py --- runs every exercise check against its reference answer and its empty stub

Contains:
    test_answer_passes(): checks the reference answer passes its exercise check
    test_stub_fails(): checks the untouched stub fails its exercise check
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXERCISES = ROOT / "exercises"
CHECKS = sorted(EXERCISES.glob("check_*.py"))
ANSWERS_FLAG = "--answers"
TIMEOUT_S = 300


def _run_check(script: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *flags],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        check=False,
    )


def _name(script: Path) -> str:
    return script.stem.removeprefix("check_")


@pytest.mark.parametrize("script", CHECKS, ids=_name)
def test_answer_passes(script: Path) -> None:
    """Checks the reference answer in answers/ passes its exercise check."""
    done = _run_check(script, ANSWERS_FLAG)
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith(f"PASS {_name(script)}")


@pytest.mark.parametrize("script", CHECKS, ids=_name)
def test_stub_fails(script: Path) -> None:
    """Checks the untouched stub in solutions_template/ fails its exercise check."""
    done = _run_check(script)
    assert done.returncode == 1, done.stdout + done.stderr
    assert done.stdout.startswith(f"FAIL {_name(script)}")


def test_every_check_has_answer_and_stub() -> None:
    """Checks every exercise check has exactly one answer and one stub."""
    names = {_name(script) for script in CHECKS}
    assert names == {path.stem for path in (EXERCISES / "answers").glob("*.py")}
    assert names == {path.stem for path in (EXERCISES / "solutions_template").glob("*.py")}
