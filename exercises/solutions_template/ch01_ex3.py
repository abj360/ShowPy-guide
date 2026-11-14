#!/usr/bin/env python3

"""
ch01_ex3.py --- your solution to exercise 1.3: measure which packages a package imports

Contains:
    solve(): returns the other showpy packages that `package` imports at run time
"""

from pathlib import Path

import showpy

SHOWPY_DIR = Path(showpy.__file__).resolve().parent


def solve(package: str) -> set[str]:
    """Returns the other showpy packages that `package` imports at run time."""
    raise NotImplementedError("TODO")
