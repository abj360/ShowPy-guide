#!/usr/bin/env python3

"""
ch01_ex3.py --- reference answer to exercise 1.3: measure which packages a package imports

Contains:
    solve(): returns the other showpy packages that `package` imports at run time
"""

import ast
from pathlib import Path

import showpy

SHOWPY_DIR = Path(showpy.__file__).resolve().parent


def solve(package: str) -> set[str]:
    """Returns the other showpy packages that `package` imports at run time."""
    found: set[str] = set()
    for path in (SHOWPY_DIR / package).glob("*.py"):
        tree = ast.parse(path.read_text())
        guarded = {
            id(node)
            for branch in ast.walk(tree)
            if isinstance(branch, ast.If) and "TYPE_CHECKING" in ast.unparse(branch.test)
            for node in ast.walk(branch)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and id(node) not in guarded:
                parts = (node.module or "").split(".")
                if parts[0] == "showpy" and len(parts) > 1 and parts[1] != package:
                    found.add(parts[1])
    return found
