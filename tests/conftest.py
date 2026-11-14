#!/usr/bin/env python3

"""
conftest.py --- runs every guide subprocess under one fixed hash seed

Contains:
    pytest_configure(): pins PYTHONHASHSEED for the examples, checks and snippets the tests start
"""

import os

HASH_SEED_VAR = "PYTHONHASHSEED"
HASH_SEED = "0"


def pytest_configure() -> None:
    """Pins the hash seed that every subprocess started by the tests inherits.

    Some ShowPy hashes still follow set order (its defect ledger, Priority 0 #9), so a
    revision printed by the tutorial changes with the seed.
    """
    os.environ[HASH_SEED_VAR] = HASH_SEED
