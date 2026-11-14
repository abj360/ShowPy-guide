#!/usr/bin/env python3

"""
t11_publish.py --- tutorial step 11: publishes the show, lets performers claim spots, republishes

Contains:
    main(): publishes, claims, swaps, builds a performer view and lists change notices
"""

from datetime import UTC, datetime
from pathlib import Path

from showpy.export.models import Performer
from showpy.export.publish import (
    claim_spot,
    notify_changes,
    performer_view,
    publish,
    qr_code,
    swap_claims,
    unclaimed,
    who_is_on,
)
from showpy.show.manage import set_counts

from t05_paths import build_tutorial_show
from t08_notes_validate import add_notes

PUBLISHED_AT = datetime(2026, 11, 12, 18, 0, tzinfo=UTC)
FIGURES = Path(__file__).resolve().parent.parent / "figures"
ADA = Performer(id="ada", name="Ada")
BO = Performer(id="bo", name="Bo")
CY = Performer(id="cy", name="Cy", role="crew")


def main() -> None:
    """Publishes, claims T1 and T2, swaps them, then republishes a retimed show."""
    show = add_notes(build_tutorial_show())
    pub = publish(show, "opener-live", "https://shows.example/p", PUBLISHED_AT)
    print("link:", pub.link, "status:", pub.status, "revision:", pub.revision[:12])
    (FIGURES / "tutorial_qr.png").write_bytes(qr_code(pub, size=256))

    pub, claim = claim_spot(pub, show, ADA, "T1", PUBLISHED_AT)
    pub, _ = claim_spot(pub, show, BO, "T2", PUBLISHED_AT)
    print("claim:", claim.spot, claim.performer.name, "locked:", claim.locked)
    try:
        claim_spot(pub, show, CY, "T3", PUBLISHED_AT)
    except Exception as error:
        print("crew on a performer spot:", type(error).__name__)
    pub = swap_claims(pub, "T1", "T2")
    holder = who_is_on(pub, "T1")
    name = holder.name if holder else "nobody"
    print("T1 is now:", name, "| unclaimed:", len(unclaimed(pub, show)))

    view = performer_view(pub, show, ADA)
    print("Ada's spot:", view.spot)
    for set_id, text, counts in view.sets:
        print(f"  set {set_id} ({counts:g} counts): {text}")

    slower = set_counts(show, "3", 24.0, rescale=True)
    republished = publish(slower, "opener-live", "https://shows.example/p", PUBLISHED_AT, pub)
    print("claims kept on republish:", len(republished.claims))
    for performer, summary in notify_changes(republished, show, slower):
        print(f"notify {performer.name}: {summary}")


if __name__ == "__main__":
    main()
