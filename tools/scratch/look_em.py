"""Look sheet for emblem icons: per key a row of guide + paintings (256 px), then the old
icon and each painting fitted, at 128/44/17 on a dark backing."""
import glob
import os
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import emblems  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCR = os.path.dirname(os.path.abspath(__file__))
BG = (20, 16, 12, 255)


def on_bg(img, s):
    im = img.convert("RGBA").resize((s, s), Image.LANCZOS)
    b = Image.new("RGBA", (s, s), BG)
    b.alpha_composite(im)
    return b


def sizes(img):
    w = 128 + 44 + 17 + 24
    t = Image.new("RGBA", (w, 128), BG)
    x = 0
    for s in (128, 44, 17):
        t.paste(on_bg(img, s), (x, 0))
        x += s + 8
    return t


def row(key, pattern):
    guide = os.path.join(emblems.RAW, f"{key}_guide.png")
    cands = sorted(glob.glob(os.path.join(emblems.RAW, pattern.format(key=key))))
    tiles = [Image.open(guide).convert("RGBA").resize((256, 256))] if os.path.exists(guide) else []
    tiles += [Image.open(c).convert("RGBA").resize((256, 256)) for c in cands]
    old = os.path.join(emblems.UI, key + ".png")
    smalls = [sizes(Image.open(old))] if os.path.exists(old) else []
    for c in cands:
        dst = os.path.join(SCR, "fit", f"{os.path.basename(c)}")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        emblems.fit(key, c, dst)
        smalls.append(sizes(Image.open(dst)))
    W = max(len(tiles) * 264, 1) + 16
    W2 = len(smalls) * 230
    img = Image.new("RGBA", (max(W, W2), 256 + 140 + 24), (8, 8, 8, 255))
    d = ImageDraw.Draw(img)
    d.text((4, 2), key, fill=(255, 220, 160, 255))
    for i, t in enumerate(tiles):
        img.paste(t, (i * 264, 14))
    for i, t in enumerate(smalls):
        img.paste(t, (i * 230, 14 + 264))
    return img


if __name__ == "__main__":
    pat = sys.argv[1]
    keys = sys.argv[2:]
    rows = [row(k, pat) for k in keys]
    W = max(r.size[0] for r in rows)
    H = sum(r.size[1] for r in rows)
    sheet = Image.new("RGBA", (W, H), (8, 8, 8, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.size[1]
    out = os.path.join(SCR, "look_" + "_".join(keys)[:60] + ".png")
    sheet.convert("RGB").save(out)
    print(out)
