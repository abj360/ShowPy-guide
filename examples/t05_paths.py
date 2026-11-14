#!/usr/bin/env python3

"""
t05_paths.py --- tutorial step 5: adds a stagger, curved paths and a follow-the-leader route

Contains:
    add_paths(): stores the path instructions of both transitions
    build_tutorial_show(): runs steps 1 to 5 and returns the finished show
    main(): prints the stored path rows and the route
"""

from showpy.cast.select import ordered_along
from showpy.choreo.models import FacingMode
from showpy.choreo.paths import curve_path, paths_table, set_easing, set_facing, stagger
from showpy.choreo.routes import follow_and_set_targets, make_route
from showpy.show.changes import store_paths
from showpy.show.models import PathsOp, Show

from t01_new_show import create_show
from t02_spots import add_performers
from t03_block_set import TRUMPET_IDS, add_block_set
from t04_arc_set import add_arc_set

OPENING = ("1", "2")
CURVING = ("2", "3")
FLAG_FILE = ("F4", "F3", "F2", "F1")
FLAG_WAYPOINTS = ((12.0, 28.0), (4.0, 32.0))


def add_paths(show: Show) -> Show:
    """Staggers the opening, curves the outer trumpets and leads the flags along a route."""
    left_to_right = ordered_along(show.set("1"), list(TRUMPET_IDS), by="x").ids
    opening = stagger(show.transition(OPENING), left_to_right, step=1.0)
    opening = set_easing(opening, list(TRUMPET_IDS), "ease_in_out")
    show = store_paths(show, PathsOp(spec=opening))

    curving = show.transition(CURVING)
    for entity, bend in (("T1", (-12.0, 12.0)), ("T4", (12.0, 12.0))):
        here = show.set("2").get(entity).point
        curving = curve_path(curving, entity, ((here[0] + bend[0]) / 2, bend[1]))
    show = store_paths(show, PathsOp(spec=curving))

    route = make_route(show, CURVING, "F4", FLAG_WAYPOINTS, list(FLAG_FILE))
    show = follow_and_set_targets(show, CURVING, route)
    spec = set_facing(show.transition(CURVING), list(FLAG_FILE), FacingMode.TRAVEL, turn_counts=2)
    return store_paths(show, PathsOp(spec=spec))


def build_tutorial_show() -> Show:
    """Returns the tutorial show after steps 1 to 5."""
    return add_paths(add_arc_set(add_block_set(add_performers(create_show()))))


def main() -> None:
    """Prints the non-default path rows of both transitions and the flag route."""
    show = build_tutorial_show()
    columns = ["entity", "style", "start", "end", "facing_mode", "turn_counts"]
    for tid in (OPENING, CURVING):
        print(f"transition {tid[0]}->{tid[1]}, {show.transition(tid).counts:g} counts")
        print(paths_table(show.transition(tid))[columns].to_string(index=False))
    route = show.transition(CURVING).routes["route"]
    print("route members:", route.members)
    print("route offsets:", [round(o, 3) for o in route.offsets], "travel:", round(route.travel, 3))
    print("F1 in set 3:", tuple(round(v, 3) for v in show.set("3").get("F1").point))


if __name__ == "__main__":
    main()
