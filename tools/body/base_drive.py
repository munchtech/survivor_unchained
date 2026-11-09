"""The base rig's poser module name in older rig.json files (rig.json "poser": "tools.body.base_drive"): the drivers
and correctives now live in tools/body/rig_drive.py (its docstring has every law); base_drive.json is their data.

    drive(poser, G, rig) -> (G, {shape: weight})
"""
from __future__ import annotations

from tools.body.rig_drive import drive  # noqa: F401
