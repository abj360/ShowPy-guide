#!/usr/bin/env python3

"""
t07_avoid.py --- tutorial step 7: finds the tightest gaps and tries the suggested fixes

Contains:
    main(): prints the tightest pairs of each transition and fixes for the worst one
"""

from showpy.choreo.avoid import apply_fix, min_gaps, suggest_delays, suggest_waypoint
from showpy.show.changes import store_paths
from showpy.show.models import PathsOp

from t05_paths import OPENING, build_tutorial_show


def main() -> None:
    """Lists tight pairs, then applies the best delay fix and measures the pair again."""
    show = build_tutorial_show()
    for tid in show.transition_ids():
        print(f"transition {tid[0]}->{tid[1]}:")
        for gap in min_gaps(show, tid, top=3):
            print(f"  {gap.a}-{gap.b}: gap {gap.gap:6.3f} m at local count {gap.tau:.3f}")
    worst = min_gaps(show, OPENING, top=1)[0]
    pair = (worst.a, worst.b)
    delays = suggest_delays(show, OPENING, pair)
    for fix in delays[:3]:
        print(f"delay {fix.params}: new gap {fix.new_gap:.3f} m, peak {fix.max_speed_after:.3f}")
    bends = suggest_waypoint(show, OPENING, pair[0], pair[1])
    for fix in bends:
        point = tuple(round(v, 3) for v in fix.params["point"])
        print(f"waypoint {point} at {fix.params['at']:.3f}: new gap {fix.new_gap:.3f} m")
    fixed = store_paths(show, PathsOp(spec=apply_fix(show.transition(OPENING), delays[0])))
    after = min_gaps(fixed, OPENING, sel=list(pair), top=1)[0]
    print(f"after the delay: {after.a}-{after.b} gap {after.gap:.3f} m")
    tightest = min_gaps(fixed, OPENING, top=1)[0]
    print(f"tightest pair now: {tightest.a}-{tightest.b} gap {tightest.gap:.3f} m")


if __name__ == "__main__":
    main()
