#!/usr/bin/env python3

"""
test_examples.py --- runs every tutorial example and compares its output with the stored copy

Contains:
    test_example_prints_stored_output(): runs one example and checks it prints its stored output
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
OUTPUTS = EXAMPLES / "output"
SCRIPTS = sorted(EXAMPLES.glob("t*.py"))
TIMEOUT_S = 300


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.stem)
def test_example_prints_stored_output(script: Path) -> None:
    """Runs one tutorial example and checks it prints exactly what the guide shows."""
    done = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout == (OUTPUTS / f"{script.stem}.txt").read_text()


def test_every_example_has_stored_output() -> None:
    """Checks no example is missing its stored output and no output is orphaned."""
    assert {path.stem for path in SCRIPTS} == {path.stem for path in OUTPUTS.glob("*.txt")}
