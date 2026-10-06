"""The hand-over: her own body takes over on the cut into the last shot (docs/cinematics/README.md 5a)."""
import sys

LAST = {"c01": "12", "c02": "12", "c03": "13", "c04a": "A8", "c04b": "B5"}


def edit(shots, f):
    sid = LAST[f["id"]]
    s = shots[sid]
    cues = s.setdefault("cues", [])
    if not any(c.get("do") == "play" for c in cues):
        cues.insert(0, {"at": 0.0, "do": "play"})
    if f["id"] == "c04a":
        # A8 was a static long shot cut straight to play: it now blends into the game's camera over its last 1.5 s.
        s["cam"]["move"] = {"start": "end-1.5", "ease": "inout", "follow": True}
