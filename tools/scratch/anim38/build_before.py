"""Builds the named clips with the stalker's base as captured (idle.STAND off), for before/after checks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "anim"))
from clips import idle  # noqa: E402
idle.STAND = {}
import build  # noqa: E402
build.main(sys.argv[1:])
