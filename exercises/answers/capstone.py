#!/usr/bin/env python3

"""
capstone.py --- reference answer to the capstone: a four-set mini show that passes every check

Contains:
    build_show(): designs, places, matches and paths the four-set show
"""

from showpy.cast.models import Group
from showpy.cast.spots import add_group, add_spots_along
from showpy.choreo.form_place import place
from showpy.choreo.forms import arc_form, block_form, circle_form, slots
from showpy.choreo.match import match
from showpy.choreo.match_ops import with_set
from showpy.choreo.models import Form
from showpy.choreo.paths import curve_path, set_easing
from showpy.geo.shapes import line
from showpy.sheet.templates import get_sheet
from showpy.show.changes import apply_change, store_paths
from showpy.show.manage import add_set, new_show
from showpy.show.models import FormOp, PathsOp, Show
from showpy.time.models import TimelineMode
from showpy.time.timeline import new_timeline

IDS = tuple(f"B{i}" for i in range(1, 9))
COUNTS = 16.0


def _place_matched(show: Show, set_id: str, form: Form) -> Show:
    prev = show.set_ids()[show.set_index(set_id) - 1]
    result = match(show.set(prev), slots(form), list(IDS))
    members = tuple(sorted(result.assignment, key=result.assignment.__getitem__))
    form = form.model_copy(update={"members": members})
    placed, filled = place(show, set_id, [form])
    return apply_change(with_set(show, placed), [FormOp(form=f) for f in filled])


def build_show() -> Show:
    """Builds a line, a block, an arc and a circle, 16 counts apart, with curved moves."""
    timeline = new_timeline(TimelineMode.COUNTS, counts_per_minute=144.0)
    show = new_show("capstone", "Capstone", get_sheet("sheet:hs-football"), timeline)
    show = add_group(show, Group(key="brass", label_prefix="B", color="#c0392b"))
    show = add_spots_along(show, line((-10.5, 10.0), (10.5, 10.0)), 8, "brass", "1")
    show = add_set(show, "2", COUNTS)
    show = _place_matched(show, "2", block_form("block", [], (0.0, 16.0), 2, 4, 3.0))
    show = add_set(show, "3", COUNTS)
    show = _place_matched(show, "3", arc_form("arc", [], (0.0, 8.0), 14.0, 140.0, -100.0, n=8))
    show = add_set(show, "4", COUNTS)
    show = _place_matched(show, "4", circle_form("ring", [], (0.0, 16.0), 6.0, 90.0, n=8))
    spec = set_easing(show.transition(("1", "2")), list(IDS), "ease_in_out")
    show = store_paths(show, PathsOp(spec=spec))
    curving = show.transition(("3", "4"))
    for entity in ("B1", "B8"):
        a, b = show.set("3").get(entity).point, show.set("4").get(entity).point
        curving = curve_path(curving, entity, ((a[0] + b[0]) / 2 * 1.2, (a[1] + b[1]) / 2))
    return store_paths(show, PathsOp(spec=curving))
