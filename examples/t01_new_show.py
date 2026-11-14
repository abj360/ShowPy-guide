#!/usr/bin/env python3

"""
t01_new_show.py --- tutorial step 1: creates an empty show on a high-school football field

Contains:
    create_show(): builds the empty tutorial show with a 144 cpm count timeline
    main(): prints what the new show holds
"""

from showpy.sheet.templates import get_sheet
from showpy.show.manage import new_show
from showpy.show.models import Show
from showpy.time.models import TimelineMode
from showpy.time.timeline import new_timeline

TEMPO_CPM = 144.0


def create_show() -> Show:
    """Builds the empty tutorial show on the NFHS field template."""
    sheet = get_sheet("sheet:hs-football")
    timeline = new_timeline(TimelineMode.COUNTS, counts_per_minute=TEMPO_CPM)
    return new_show("opener", "Tutorial opener", sheet, timeline)


def main() -> None:
    """Prints the sheet, the sets and the pinned sheet version of the new show."""
    show = create_show()
    print(f"sheet: {show.sheet.ref}, {show.sheet.name}")
    width, depth = show.sheet.size_m
    print(f"size: {width:.3f} m wide x {depth:.3f} m deep")
    print(f"sets: {show.set_ids()}, first set counts: {show.sets[0].counts}")
    print(f"dependencies: {show.dependencies}")
    print(f"tempo: {show.timeline.tempos[0].counts_per_minute} cpm from count 0")


if __name__ == "__main__":
    main()
