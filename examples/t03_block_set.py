#!/usr/bin/env python3

"""
t03_block_set.py --- tutorial step 3: builds set 2 by placing the trumpets in a block form

Contains:
    add_block_set(): adds set 2 (16 counts) with the trumpets in a 2 x 4 block
    main(): prints the block's slots and the placed trumpets
"""

from showpy.choreo.form_place import filled_forms, place
from showpy.choreo.forms import block_form, slots
from showpy.choreo.match_ops import with_set
from showpy.show.changes import apply_change
from showpy.show.manage import add_set
from showpy.show.models import FormOp, Show

from t01_new_show import create_show
from t02_spots import add_performers

TRUMPET_IDS = tuple(f"T{i}" for i in range(1, 9))
STEP_8_TO_5 = 0.5715


def add_block_set(show: Show) -> Show:
    """Adds set 2 and stands the trumpets in a block four 8-to-5 steps apart."""
    show = add_set(show, "2", 16.0)
    form = block_form(
        "block", TRUMPET_IDS, origin=(0.0, 18.0), rows=2, cols=4, interval=4 * STEP_8_TO_5
    )
    placed = place(show, "2", [form])
    show = with_set(show, placed)
    stored = filled_forms(placed, [form])
    return apply_change(show, [FormOp(form=f) for f in stored])


def main() -> None:
    """Prints the block recipe, its slots and where each trumpet stands in set 2."""
    show = add_block_set(add_performers(create_show()))
    form = show.forms["block"]
    print("recipe:", form.geometry)
    print("slots:", slots(form).round(3).tolist())
    for p in show.set("2").placements:
        if p.form == "block":
            print(f"{p.entity}: ({p.x:.3f}, {p.y:.3f}) slot {p.order} facing {p.facing}")
    print("set 2 forms:", show.set("2").forms)


if __name__ == "__main__":
    main()
