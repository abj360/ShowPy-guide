#!/usr/bin/env python3

"""
t04_arc_set.py --- tutorial step 4: builds set 3 as an arc and matches trumpets to its slots

Contains:
    compare_objectives(): matches the block to the arc under three rules and returns the results
    add_arc_set(): adds set 3 with the trumpets on the arc, using the default matching
    main(): prints how the matching objectives differ and the final assignment
"""

from showpy.choreo.form_place import filled_forms, place
from showpy.choreo.forms import arc_form, slots
from showpy.choreo.match import match, match_by_order
from showpy.choreo.match_ops import with_set
from showpy.choreo.models import Form, MatchOptions, MatchResult
from showpy.show.changes import apply_change
from showpy.show.manage import add_set
from showpy.show.models import FormOp, Show

from t01_new_show import create_show
from t02_spots import add_performers
from t03_block_set import TRUMPET_IDS, add_block_set

ARC_CENTER = (0.0, 6.0)
ARC_RADIUS = 14.0


def empty_arc() -> Form:
    """Returns the set 3 arc with eight open slots, running from audience left to right."""
    return arc_form("arc", [], ARC_CENTER, ARC_RADIUS, start_deg=135.0, sweep_deg=-90.0, n=8)


def compare_objectives(show: Show) -> dict[str, MatchResult]:
    """Matches the trumpets from the set 2 block to the arc slots in three ways."""
    targets = slots(empty_arc())
    start = show.set("2")
    return {
        "by order": match_by_order(TRUMPET_IDS, targets, from_=start),
        "sum": match(start, targets, TRUMPET_IDS, MatchOptions(objective="sum", counts=16)),
        "bottleneck_then_sum": match(start, targets, TRUMPET_IDS, MatchOptions(counts=16)),
    }


def add_arc_set(show: Show) -> Show:
    """Adds set 3 (16 counts) with the trumpets on the arc in the default matched order."""
    show = add_set(show, "3", 16.0)
    best = compare_objectives(show)["bottleneck_then_sum"]
    members = tuple(sorted(best.assignment, key=best.assignment.__getitem__))
    form = empty_arc().model_copy(update={"members": members})
    placed = place(show, "3", [form])
    show = with_set(show, placed)
    return apply_change(show, [FormOp(form=f) for f in filled_forms(placed, [form])])


def main() -> None:
    """Prints largest move, total travel and crossings for each matching rule."""
    show = add_block_set(add_performers(create_show()))
    for name, result in compare_objectives(add_set(show, "3", 16.0)).items():
        print(
            f"{name:>19}: largest {result.max_distance:6.3f} m, "
            f"total {result.total_distance:7.3f} m, crossings {result.crossings}"
        )
    show = add_arc_set(show)
    print("arc members:", show.forms["arc"].members)
    print("explain:", list(compare_objectives(show)["bottleneck_then_sum"].explain))
    for p in show.set("3").placements[:8]:
        print(f"{p.entity}: ({p.x:7.3f}, {p.y:7.3f}) slot {p.order} facing {p.facing:6.2f}")


if __name__ == "__main__":
    main()
