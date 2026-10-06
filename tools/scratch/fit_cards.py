import os
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import batch  # noqa: E402
import cards  # noqa: E402

out_dir = os.path.join(WT, "godot", "art", "ui", "frames")
for kind in sys.argv[1:]:
    src, coins = cards.PICKS[kind]
    dst = os.path.join(out_dir, f"card_{kind}.png")
    cards.fit(os.path.join(cards.RAW, *src.split("/")), dst, kind=kind, hole_light=0.35, coins=coins,
              heal_prompt=(batch.RARITY.get(kind, "") + ". " + batch.S) if coins else None)
    cards.lengthen(dst)
    print(dst)
