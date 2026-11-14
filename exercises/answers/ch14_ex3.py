#!/usr/bin/env python3

"""
ch14_ex3.py --- reference answer to exercise 14.3: claim, then swap as the designer

Contains:
    solve(): returns the names on T1 and T2 after the designer swaps them
"""

from datetime import UTC, datetime

from showpy.examples import two_set_show
from showpy.export.models import Performer
from showpy.export.publish import claim_spot, publish, swap_claims, who_is_on


def solve() -> tuple[str, str]:
    """Returns the names on T1 and T2 after the designer swaps them."""
    show = two_set_show()
    at = datetime(2026, 11, 12, 18, 0, tzinfo=UTC)
    pub = publish(show, "p", "https://shows.example/p", at)
    pub, _ = claim_spot(pub, show, Performer(id="ada", name="Ada"), "T1", at)
    pub, _ = claim_spot(pub, show, Performer(id="bo", name="Bo"), "T2", at)
    pub = swap_claims(pub, "T1", "T2")
    names = [p.name if (p := who_is_on(pub, spot)) else "" for spot in ("T1", "T2")]
    return names[0], names[1]
