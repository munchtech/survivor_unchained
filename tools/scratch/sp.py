"""Scratch helpers: paths and contact sheets for looking at art at real size."""
import os
from PIL import Image, ImageDraw

S = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(S, "v")
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a"
OLD = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843"
UI = os.path.join(W, "godot", "art", "ui")
OUT = os.path.join(W, "tools", "comfy", "out", "uiforge")
os.makedirs(V, exist_ok=True)


def on_bg(im, bg=(28, 24, 22)):
    im = im.convert("RGBA")
    b = Image.new("RGBA", im.size, bg + (255,))
    b.alpha_composite(im)
    return b.convert("RGB")


def sheet(images, sizes=(None,), bg=(28, 24, 22), pad=8, labels=None):
    """Each image at each size (None = native), in a row per image."""
    rows = []
    for im in images:
        cells = []
        for s in sizes:
            c = im if s is None else im.resize((s, round(im.height * s / im.width)), Image.LANCZOS)
            cells.append(on_bg(c, bg))
        rows.append(cells)
    w = max(sum(c.width for c in r) + pad * (len(r) + 1) for r in rows)
    h = sum(max(c.height for c in r) + pad for r in rows) + pad
    out = Image.new("RGB", (w, h), bg)
    y = pad
    for r in rows:
        x = pad
        for c in r:
            out.paste(c, (x, y))
            x += c.width + pad
        y += max(c.height for c in r) + pad
    return out


def zoom(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)
