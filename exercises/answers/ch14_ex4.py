#!/usr/bin/env python3

"""
ch14_ex4.py --- reference answer to exercise 14.4: the audio seek with a hold

Contains:
    solve(): returns the audio seek for a range starting at count 8
"""

from showpy.time.clock import count_to_seconds
from showpy.time.models import AudioTrack, Hold, TimelineMode
from showpy.time.timeline import add_hold, attach_audio, new_timeline


def solve() -> float:
    """Returns the audio seek for a range starting at count 8."""
    tl = add_hold(new_timeline(TimelineMode.COUNTS, 120.0), Hold(at_count=4.0, seconds=2.0))
    tl = attach_audio(tl, AudioTrack(file="a.wav", label="a", sync_offset_s=1.25))
    return tl.audio[0].sync_offset_s + count_to_seconds(tl, 8.0)
