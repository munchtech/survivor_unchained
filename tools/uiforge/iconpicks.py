"""Which painted candidate each colour icon uses (icons/glyph_color/KEY.png), chosen by
eye at the sizes the game shows them: KEY -> (seed, place). Anything not named
takes the first candidate of seed 900.

    python tools/uiforge/iconpicks.py         # fit every icon into godot/art/ui
"""
from __future__ import annotations

import os
import sys

import icons

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "icons")
OUT = os.path.join(ROOT, "godot", "art", "ui", "icons", "glyph_color")

PICKS = {
    "aegis": (900, 1), "arrow_rain": (900, 1), "beam_sun": (900, 1), "dagger_flurry": (900, 1), "disc_reckon": (900, 1),
    "herd_hunt": (900, 1), "mark": (900, 1), "moonfall": (900, 1), "mote_star": (900, 1), "spiritwolf": (900, 1),
    "skull": (900, 1), "hand": (900, 1), "slash_quake": (900, 1), "slash_spin": (900, 1), "spear_ice": (900, 1),
    "zone_sanct": (900, 1), "zone_pyre": (900, 1), "zone_bloom": (900, 1), "shard_deep": (900, 1),
    # Second takes.
    "slash_steel": (950, 1), "disc": (950, 0), "mote": (960, 1), "mote_cascade": (960, 2), "tether_mark": (950, 0),
    "beam_gaze": (950, 1), "consecrate": (950, 0), "bolt": (950, 1), "magnet": (950, 2),
}


def src(key):
    seed, j = PICKS.get(key, (900, 0))
    p = os.path.join(RAW, f"{key}_{seed}_{j}.png")
    if not os.path.exists(p):
        p = os.path.join(RAW, f"{key}_900_0.png")
    return p


def main(keys=None):
    for k in keys or list(icons.SUBJECTS):
        icons.fit(src(k), os.path.join(OUT, k + ".png"))
    print("icons", len(keys or icons.SUBJECTS))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
