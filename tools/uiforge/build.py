"""Build the interface's art into godot/art/ui/ (docs/UI_ART_BRIEF.md, section 2.6 for the
look and how each family is made).

    python tools/uiforge/build.py [GROUP ...]     # all groups if none named
    python tools/uiforge/build.py --list

Each group writes its files from scratch. Forged pieces are made here; Blender pieces
render on the local Blender; painted pieces read their picks from the raw results in
tools/comfy/out/uiforge/ (ignored by git) and remake any that are missing on the local
ComfyUI with the prompt and seed recorded beside them.

  chrome     Blender-modelled metal, painted over: plate, buttons, slots, socket, tooltips,
             toast, prompt pill, tabs, row, segment, keycap, chip, bar groove and casing, the
             HUD's console, the well and the slab
  paper      the ledger paper and the hint note
  cards      the draft's cards, painted over forged guides
  painted    the map's frame, the boss's casing, ornaments
  logo       the title's logo, modelled as a relief (Cinzel's letters in forged steel, the chain)
  light      the focus ring and the bars' fills
  prompts    the pad's buttons, forged
  mapmarks   the map's marks, in ink on parchment
  glyphs     the interface's own marks as value art
  icons      the skills', arts', blessings' and evolutions' painted icons
  emblems    the icons remade as modelled emblems, painted over (after icons: they replace theirs)
  medals     round pieces modelled as reliefs: the level medallion, the medallion ring, the health
             globe's rim and glass, the (unused) heart medallion and its stone (after icons: the
             stone is the heart icon)
  pieces     frames modelled as reliefs: the page header, the attribute pillar, the crested card
             and row, the banner, the open book, the ribbon, the plaque's rule
  items      the items' painted icons
  cursors    the pointer, the hand, the refusal
  arrow      the survivor's arrow on the minimap
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
sys.path.insert(0, HERE)

import forge as F  # noqa: E402


def out(rel):
    return os.path.join(UI, rel)


def g_chrome():
    import chrome
    for name, fn in chrome.GROUPS.items():
        fn()


def g_paper():
    import paper
    paper.build(UI)


def g_cards():
    import cards
    cards.build_all(out("frames"))


def g_painted():
    import fitall
    # The minimap's rim and the art's ring are Blender pieces (chrome); the medallions are
    # reliefs (medals), and so is the logo (logo). Only what is still painted from text is
    # fitted here.
    for n in ("mapframe", "bosscasing", "rule", "flourish"):
        fitall.GROUPS[n]()


def g_logo():
    import logo
    logo.main()


def g_light():
    import lightpieces as L
    F.save(L.focus_ring(), out("frames/focus.png"))
    F.save(L.ember_fill(), out("bars/ember_fill.png"))
    F.save(L.experience_fill(), out("bars/experience_fill.png"))
    F.save(L.health_fill(), out("bars/health_fill.png"))


def g_prompts():
    import padprompts
    padprompts.build(out("icons/prompt"))


def g_mapmarks():
    import mapmarks
    mapmarks.build(out("icons/map"))


def g_glyphs():
    import valueglyphs
    valueglyphs.build(out("icons/glyph"))


def g_icons():
    import iconpicks
    iconpicks.main()


def g_emblems():
    import emblems
    emblems.build()


def g_medals():
    import medals
    for n in medals.BUILD:
        medals.build(n)


def g_pieces():
    import pieces
    for n in pieces.BUILD:
        pieces.build(n)


def g_items():
    import items
    for k in items.ITEMS:
        items.fit(k)


def g_cursors():
    import cursors
    cursors.build(out("cursors"))


def g_arrow():
    import smallforge
    F.save(smallforge.you_arrow(), out("minimap/you.png"))


GROUPS = {name[2:]: fn for name, fn in globals().items() if name.startswith("g_")}


def main():
    args = sys.argv[1:]
    if "--list" in args:
        print(" ".join(GROUPS))
        return
    for name in args or list(GROUPS):
        t = time.time()
        GROUPS[name]()
        print(f"{name}: {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    main()
