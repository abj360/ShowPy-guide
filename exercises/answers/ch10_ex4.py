#!/usr/bin/env python3

"""
ch10_ex4.py --- reference answer to exercise 10.4: the order-preserving DP by hand

Contains:
    solve(): returns increasing columns minimizing the summed cost
"""

import numpy as np


def solve(cost: np.ndarray) -> list[int]:
    """Returns increasing columns minimizing the summed cost."""
    rows, cols = cost.shape
    table = np.full((rows, cols), np.inf)
    back = np.zeros((rows, cols), dtype=int)
    table[0] = cost[0]
    for i in range(1, rows):
        best, arg = np.inf, 0
        for j in range(cols):
            table[i, j] = best + cost[i, j]
            back[i, j] = arg
            if table[i - 1, j] < best:
                best, arg = table[i - 1, j], j
    last = int(np.argmin(table[-1]))
    picked = [last]
    for i in range(rows - 1, 0, -1):
        picked.append(int(back[i, picked[-1]]))
    return picked[::-1]
