"""Build the interface's art into godot/art/ui/ (docs/UI_ART_BRIEF.md).

    python tools/uiforge/build.py [GROUP ...]     # all groups if none named
    python tools/uiforge/build.py --list

Groups are the families of docs/UI_ART_BRIEF.md section 4 and 5. Forged and
light pieces are made here from scratch; painted pieces are fitted from the
picks recorded in picks.json (each a raw Krea result in tools/comfy/out/,
remade exactly from its recorded prompt and seed if it is missing).
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


def g_prompts():
    import padprompts
    padprompts.build(out("icons/prompt"))


def g_mapmarks():
    import mapmarks
    mapmarks.build(out("icons/map"))


def g_light():
    import lightpieces as L
    F.save(L.focus_ring(), out("frames/focus.png"))
    F.save(L.ember_fill(), out("bars/ember_fill.png"))
    F.save(L.experience_fill(), out("bars/experience_fill.png"))
    F.save(L.health_fill(), out("bars/health_fill.png"))


def g_buttons():
    import buttons as B
    for primary in (False, True):
        for state in ("normal", "hover", "pressed", "disabled"):
            if primary and state == "disabled":
                continue
            name = ("button_primary" if primary else "button") + ("" if state == "normal" else "_" + state)
            F.save(B.button(state, primary), out(f"frames/{name}.png"))


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
