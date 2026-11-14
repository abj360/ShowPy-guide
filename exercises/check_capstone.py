#!/usr/bin/env python3

"""
check_capstone.py --- checks the capstone show against every stated requirement

Contains:
    MIN_GAP_M: names the smallest allowed gap between footprints, in meters
    MAX_SPEED_M_PER_COUNT: names the fastest allowed instant speed
    check(): validates the show, its gaps, its speeds and its design requirements
"""

from types import ModuleType

from showpy.choreo.avoid import min_gaps
from showpy.choreo.models import PathStyle
from showpy.choreo.motion_stats import speeds
from showpy.show.models import Show
from showpy.show.validate import validate_show

from checklib import expect, run

MIN_GAP_M = 0.3
MAX_SPEED_M_PER_COUNT = 1.0
MIN_SPOTS = 8
SETS = 4
MIN_FORM_KINDS = 2


def _design(show: Show) -> None:
    expect(len(show.sets) == SETS, f"the show needs exactly {SETS} sets, it has {len(show.sets)}")
    expect(len(show.cast.spots) >= MIN_SPOTS, f"use at least {MIN_SPOTS} spots")
    kinds = {form.kind for form in show.forms.values()}
    expect(len(kinds) >= MIN_FORM_KINDS, f"store forms of at least two kinds, found {kinds}")
    styled = [
        row.style
        for spec in show.transitions
        for row in spec.rows.values()
        if row.style != PathStyle.STRAIGHT
    ]
    expect(styled, "give at least one spot a non-straight path (curve, polyline, follow, ...)")


def _safety(show: Show) -> None:
    for tid in show.transition_ids():
        tightest = min_gaps(show, tid, top=1)
        if tightest:
            g = tightest[0]
            expect(
                g.gap >= MIN_GAP_M,
                f"{g.a} and {g.b} come within {g.gap:.3f} m in {tid[0]}→{tid[1]} at {g.tau:.2f}",
            )
        peak = float(speeds(show, tid)["max_instant"].max())
        expect(
            peak <= MAX_SPEED_M_PER_COUNT,
            f"a spot peaks at {peak:.3f} m/count in {tid[0]}→{tid[1]}; slow it down",
        )


def check(solution: ModuleType) -> None:
    """Builds the reader's show and tests every capstone requirement."""
    show = solution.build_show()
    report = validate_show(show)
    expect(report.ok, f"validate_show found errors:\n{report}")
    _design(show)
    _safety(show)


if __name__ == "__main__":
    run("capstone", check)
