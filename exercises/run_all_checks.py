#!/usr/bin/env python3

"""
run_all_checks.py --- proves every exercise check passes on the answers and fails on the stubs

Run from the repository root: `uv run python exercises/run_all_checks.py`.

Contains:
    main(): runs each check twice and exits non-zero on any surprise
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMEOUT_S = 300
# Some ShowPy hashes still follow set order (its defect ledger, Priority 0 #9).
FIXED_HASH_SEED = {"PYTHONHASHSEED": "0"}


def _passes(script: Path, answers: bool) -> bool:
    args = [sys.executable, str(script), *(["--answers"] if answers else [])]
    env = {**os.environ, **FIXED_HASH_SEED}
    done = subprocess.run(
        args, capture_output=True, text=True, timeout=TIMEOUT_S, check=False, env=env
    )
    return done.returncode == 0 and done.stdout.startswith("PASS")


def main() -> None:
    """Checks answers pass and untouched stubs fail for every check script."""
    scripts = sorted(HERE.glob("check_*.py"))
    surprises = []
    for script in scripts:
        if not _passes(script, answers=True):
            surprises.append(f"E: {script.name} fails on the reference answer")
        if _passes(script, answers=False):
            surprises.append(f"E: {script.name} passes on the empty stub")
    for line in surprises:
        print(line)
    if surprises:
        sys.exit(1)
    print(f"Checked {len(scripts)} exercises: answers pass, stubs fail")


if __name__ == "__main__":
    main()
