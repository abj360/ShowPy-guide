#!/usr/bin/env python3

"""
ch09_ex2.py --- reference answer to exercise 9.2: the front-left slot of a turned block

Contains:
    solve(): returns the slot index of the stage front-left slot of the block facing 180°
"""

import numpy as np
from showpy.choreo.forms import block_form, slots


def solve() -> int:
    """Returns the slot index of the stage front-left slot of the block facing 180°."""
    pts = slots(block_form("b", [], (0.0, 20.0), 3, 4, 2.0, direction_deg=180.0))
    order = np.lexsort((pts[:, 0], pts[:, 1]))
    return int(order[0])
