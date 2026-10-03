"""Production batches on the local Krea (raw results to tools/comfy/out/uiforge/<tag>/).
Every prompt and seed is here, so any pick can be remade exactly.

    python tools/uiforge/batch.py NAME [NAME ...]
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

import krea

RAW = krea.OUT
G = os.path.join(RAW, "guides")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
DARK = "isolated on a pure black background, seen straight on, orthographic"
S = krea.STYLE


def on_black(src, dst):
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").save(dst)
    return dst


CARD = ("An empty tall portrait card frame for a dark fantasy game, hand-forged blackened iron strap border, large lamp-iron "
        "brackets with curled scrolls at the two top corners holding square coins with quatrefoil holes, small square coins "
        "nailed on the bottom corners, a short heavy chain riding over the top edge whose middle link is pried open, ")
RARITY = {
    "uncommon": CARD + "the iron overgrown by the wild wood: thorny bramble stems curling round the brackets and along the "
                       "strap, wet dark green moss in the corners, a few small green leaves, the twisted wire green-gold, "
                       "faint green light in the coins' holes, the inside plain flat dark iron, " + DARK,
    "rare": CARD + "cold as the river ford at night: sharp pale blue rime frost crystals grown over the brackets and along the "
                   "top, icy droplets, the twisted wire pale silver-blue, cold sapphire light in the coins' holes, the inside "
                   "plain flat dark iron, " + DARK,
    "epic": CARD + "the binders' work: square-cut violet amethysts set in the coins and brackets, angular silver sigil lines with "
                   "right-angled hooks like an old legion key pattern inlaid along the strap, a violet glow, the inside plain "
                   "flat dark iron, " + DARK,
    "legendary": CARD + "burnished gold and amber over the iron, the brackets wrought like the flames of a chapel lamp, the "
                        "twisted wire bright gold, warm golden light glowing from the coins, rays of dawn, the inside plain "
                        "flat dark iron, " + DARK,
    "evolution": CARD + "the whole border gilded gold, the chain at the top bursting apart with molten orange ember light "
                        "pouring from every break, glowing cracks of ember running along the gold strap, sparks, radiant, the "
                        "inside plain flat dark iron, " + DARK,
}


def cards():
    base = on_black(os.path.join(UI, "frames", "card_common.png"), os.path.join(G, "card_common_black.png"))
    for i, (name, p) in enumerate(RARITY.items()):
        krea.i2i(base, p + ". " + S, denoise=0.55, seed=600 + i, n=3, tag=f"card_{name}")
        print("card", name, flush=True)


def small():
    jobs = {
        "slot": ("An empty square inventory slot of a dark fantasy game: a recessed well sunk into hand-forged blackened "
                 "iron, a narrow hammered iron rim with a small hand-set rivet at each corner, the inside plain dark, calm "
                 "and even, " + DARK, 0.55),
        "wslot": ("A square skill socket of a dark fantasy game: hand-forged blackened iron with bevelled edges, a thin "
                  "twisted gold wire round it, a small square iron coin with a quatrefoil hole on each corner, a recessed "
                  "plain dark centre, " + DARK, 0.55),
        "chip": ("A small square badge of hand-forged blackened iron with rounded corners, a hammered rim and a tiny rivet "
                 "at each corner, the middle plain dark, " + DARK, 0.5),
        "toast": ("A small wide notification plate of hand-forged blackened iron strap with a thin twisted gold wire along "
                  "it and small square iron coins at its corners, the inside plain dark iron, " + DARK, 0.5),
        "prompt": ("A small long rounded pill-shaped plate of hand-forged blackened iron with rounded ends, a thin twisted "
                   "gold wire round its rim, the inside plain dark iron, " + DARK, 0.5),
        "button": ("A wide flat button plate of hand-forged blackened iron with cut corners, a thin gold wire inlaid round "
                   "it, a small rivet at each corner, the face plain dark iron, " + DARK, 0.5),
        "tooltip": ("An empty square tooltip frame of a dark fantasy game: a narrow hand-forged blackened iron strap border "
                    "with a thin twisted gold wire, small square iron coins with quatrefoil holes at the corners, the "
                    "inside plain nearly black, " + DARK, 0.5),
        "ring": ("An empty circular minimap frame: a thick round band of hand-forged blackened iron with two thin twisted "
                 "gold wires, four square iron coins with quatrefoil holes at north east south and west, at the north a "
                 "forged iron arrowhead standing out of the band, the middle completely empty and black, " + DARK, 0.55),
        "paper": ("An empty sheet of old warm cream parchment from a ledger, deckled and slightly darkened edges, faint "
                  "foxing at the rims, small blackened iron corner protectors riveted on the four corners, the middle "
                  "clean and even for writing, flat lay, " + DARK, 0.5),
        "hint": ("A small note of warm cream parchment pinned at its top left corner by a hand-forged square iron nail, a "
                 "drop of red sealing wax at the bottom right, deckled darker edges, the middle clean and even for writing, "
                 "flat lay, " + DARK, 0.6),
    }
    for i, (name, (p, d)) in enumerate(jobs.items()):
        krea.i2i(os.path.join(G, name + ".png"), p + ". " + S, denoise=d, seed=700 + i, n=3, tag=f"small_{name}")
        print("small", name, flush=True)


def t2i_set():
    jobs = [
        ("logo_c", "A dark fantasy video game title logo reading \"SURVIVOR UNCHAINED\" on two lines, tall carved Roman "
                   "capitals hand-forged from blackened iron with bevelled edges catching warm light, a thin edge of old gold, "
                   "a heavy iron chain running behind the letters between the two words, one link pried open in the middle "
                   "with molten orange ember light glowing at the break, embers drifting up, on a pure black background", 801),
        ("logo_d", "A dark fantasy video game title logo reading \"SURVIVOR UNCHAINED\", the word SURVIVOR in large carved old "
                   "gold Roman capitals with cracks glowing with molten ember, the word UNCHAINED below in smaller blackened "
                   "iron capitals, a broken iron chain hanging from the letters, sparks, on a pure black background", 802),
        ("rule", "A long very thin horizontal divider ornament: a slender bar of blackened iron drawn out thin under the "
                 "hammer, tapering to fine points at both ends, a thin twisted gold wire along it, and at the exact centre "
                 "one small iron chain link pried open with a glint of molten ember light at the break, symmetrical, "
                 + DARK + ". " + S, 803),
        ("boss_track", "A long empty boss health bar casing: a long narrow channel of hand-forged blackened iron, at each end "
                       "a horned iron end cap like a ram's skull with curled horns, thin red-gold trim, the inside of the "
                       "channel empty and black, symmetrical, " + DARK + ". " + S, 804),
        ("map_frame", "A square picture frame of old dark carved oak wood, weathered timber, brass corner caps with small nails, "
                      "a narrow frame, the inside plain warm parchment, seen straight on, " + DARK + ". " + S, 805),
        ("tab", "A ledger tab of old dark brown leather stitched at its edges, rounded at the top corners and flat at the "
                "bottom, a small brass rivet, the face plain, " + DARK + ". " + S, 806),
    ]
    for name, prompt, seed in jobs:
        size = (1344, 576) if name in ("logo_c", "logo_d", "rule", "boss_track") else (1024, 1024)
        krea.t2i(prompt, seed=seed, n=3, size=size, tag=name)
        print("t2i", name, flush=True)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        globals()[name]()
