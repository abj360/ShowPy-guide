#!/usr/bin/env python3

"""
t06_engine.py --- tutorial step 6: asks the PathEngine where spots are, how they face and how fast

Contains:
    main(): prints positions, a full state, speeds and the time-linear segments of one spot
"""

from showpy.choreo.engine import PathEngine
from showpy.choreo.motion_stats import speeds
from showpy.show.manage import index
from showpy.time.clock import describe_count

from t05_paths import build_tutorial_show


def main() -> None:
    """Samples the tutorial show with the engine and prints what it finds."""
    show = build_tutorial_show()
    engine = PathEngine(show)
    for entry in index(show).entries:
        print(f"set {entry.set}: count {entry.start_count:g}, {entry.seconds:.3f} s")
    for t in (0.0, 4.0, 8.0, 16.0):
        p = engine.position("T8", t)
        print(f"T8 at count {t:>4g}: ({p[0]:7.3f}, {p[1]:7.3f})")
    print(describe_count(show.timeline, 24.0))
    state = engine.state_at("F1", 24.0)
    print(
        f"F1 at 24: position ({state.position[0]:.3f}, {state.position[1]:.3f}), "
        f"facing {state.facing:.2f}, velocity ({state.velocity[0]:.3f}, {state.velocity[1]:.3f})"
    )
    table = speeds(show, ("1", "2"))
    print(table.round(3).head(4).to_string(index=False))
    segments = engine.entity_segments("T1", ("2", "3"))
    print(
        f"T1 curve 2->3: {len(segments)} time-linear segments, first ends at count "
        f"{segments[0].t1:.4f}"
    )
    print(f"T1 drawn path: {len(engine.path_geometry('T1', ('2', '3')))} vertices")


if __name__ == "__main__":
    main()
