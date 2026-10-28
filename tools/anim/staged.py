"""staged: the clip as the GAME plays it. build.pack stages every heroine clip through clavhold, then armroll (and
armroll's chain-bone tracks) before packing; the JSONs in out/clips are as the clip code wrote them. Checks (motion.py,
audit.py, armscheck.py) call staged_json / use skin.Body.clip, which stages in memory (no file writes) when
ENV STAGED_CLIPS=1. Their mains set it on unless `--raw` is given (the old numbers). CLAV_HOLD=0 / ARM_ROLL=0 /
ARM_CHAIN=0 switch the passes off here as in build.pack."""
from __future__ import annotations

import os
from functools import lru_cache

from rig import DATA, Skeleton


def want() -> bool:
    return os.environ.get("STAGED_CLIPS") == "1"


def set_from_argv(argv):
    """Turns staging on (env, inherited by worker processes) unless --raw is in argv; returns argv without --raw."""
    raw = "--raw" in argv
    os.environ["STAGED_CLIPS"] = "0" if raw else "1"
    return [a for a in argv if a != "--raw"]


@lru_cache(maxsize=1)
def _sk():
    return Skeleton.load(DATA / "heroine_skeleton.json")


def staged_json(d, sk=None):
    """Her clip dict `d` after clavhold, armroll and the chain tracks: what build.pack writes to packed_heroine."""
    import armroll
    import clavhold
    sk = sk or _sk()
    if clavhold.on():
        d = clavhold.hold_json(sk, d)
    if armroll.on():
        d = armroll.solve_json(sk, d)
        if os.environ.get("ARM_CHAIN", "1") != "0":
            armroll.chain_tracks(d)
    return d
