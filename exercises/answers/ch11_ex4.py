#!/usr/bin/env python3

"""
ch11_ex4.py --- reference answer to exercise 11.4: a rotation that compiles

Contains:
    solve(): returns the example show with T1 rotating 90° clockwise about (4, 5)
"""

from showpy.choreo.match_ops import with_set
from showpy.choreo.routes import rotate_path
from showpy.examples import two_set_show
from showpy.show.models import Show


def solve() -> Show:
    """Returns the example show with T1 rotating 90° clockwise about (4, 5)."""
    show = two_set_show()
    show = with_set(show, show.set("2").with_placements({"T1": {"x": 4.0, "y": 9.0}}))
    spec = rotate_path(show, show.transition(("1", "2")), ["T1"], (4.0, 5.0), -90.0)
    return show.model_copy(update={"transitions": (spec,)})
