#!/usr/bin/env python3

"""
t02_spots.py --- tutorial step 2: adds two groups and draws their spots in set 1

Contains:
    add_performers(): adds eight trumpets on a line and four flags on a shorter line
    main(): prints the cast and set 1 as a table
"""

from showpy.cast.models import Group, Shape
from showpy.cast.select import select
from showpy.cast.spots import add_group, add_spots_along, define_selection, set_shape
from showpy.geo.shapes import line
from showpy.show.models import Show

from t01_new_show import create_show

TRUMPETS = Group(key="trumpets", label_prefix="T", color="#c0392b")
FLAGS = Group(key="flags", label_prefix="F", color="#2c7fb8")
FLAG_SHAPE = Shape(kind="rectangle", width_m=1.2, depth_m=0.5)


def add_performers(show: Show) -> Show:
    """Adds eight trumpets on the front hash area and four flags behind them."""
    show = add_group(show, TRUMPETS)
    show = add_group(show, FLAGS)
    show = add_spots_along(show, line((-8.0, 12.0), (8.0, 12.0)), 8, "trumpets", "1")
    show = add_spots_along(show, line((-6.0, 24.0), (6.0, 24.0)), 4, "flags", "1")
    show = set_shape(show, "group:flags", FLAG_SHAPE)
    return define_selection(show, "ends", "T1 + T8")


def main() -> None:
    """Prints the cast, a selection and set 1's placements."""
    show = add_performers(create_show())
    print("spots:", ", ".join(show.cast.ids()))
    print("ends:", select(show, "sel:ends").ids)
    print("flag footprint radius:", round(show.cast.spot("F1").shape.extent_m, 3), "m")
    table = show.set("1").table()[["entity", "x", "y", "facing", "on_field"]]
    print(table.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
