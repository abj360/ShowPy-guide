#!/usr/bin/env python3

"""
ch04_ex2.py --- reference answer to exercise 4.2: facing after rotate then mirror

Contains:
    solve(): returns the facing of a 30° spot after a 135° rotation and a mirror across x = 0
"""

from showpy.geo.affine import mirror_matrix, rotation_matrix, transform_facing


def solve() -> float:
    """Returns the facing of a 30° spot after a 135° rotation and a mirror across x = 0."""
    turned = transform_facing(30.0, rotation_matrix(135.0, (0.0, 0.0)))
    return transform_facing(turned, mirror_matrix((0.0, 0.0), (0.0, 1.0)))
