"""Procedural placeholder layers for the storybook player's test file
(godot/data/storybook/test_plates.json): not art, but shapes that make the
player's behaviour plain in a frame. Hills at five depths with tick marks
(parallax), a flame (flicker, sway), water (water, ripple), frost and its
crack order map (reveal), a mist band (scroll), and an ink order map for a
transition. Writes godot/art/storybook/test/*.png and their .import files
(VRAM compressed, high quality, mipmaps), then Godot must import them:

    python tools/storybook/make_test_plates.py
    Godot_console.exe --headless --path godot --import
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "godot", "art", "storybook", "test")
W, H = 3200, 1800
rng = np.random.default_rng(7)


def save(img: Image.Image, name: str):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    write_import(path)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def write_import(png: str):
    """The storybook's import: VRAM compressed (BPTC, high quality) with mipmaps. An
    existing .import keeps its uid; only the params are set."""
    imp = png + ".import"
    res = "res://" + os.path.relpath(png, os.path.join(ROOT, "godot")).replace("\\", "/")
    params = {"compress/mode": "2", "compress/high_quality": "true", "mipmaps/generate": "true", "detect_3d/compress_to": "0"}
    if os.path.exists(imp):
        lines = open(imp, encoding="utf-8").read().splitlines()
        out, seen = [], set()
        for ln in lines:
            k = ln.split("=", 1)[0]
            if k in params:
                out.append(f"{k}={params[k]}"); seen.add(k)
            else:
                out.append(ln)
        if "[params]" not in lines:
            out += ["", "[params]", ""]
        out += [f"{k}={v}" for k, v in params.items() if k not in seen]
        open(imp, "w", encoding="utf-8").write("\n".join(out) + "\n")
        return
    body = ['[remap]', '', 'importer="texture"', 'type="CompressedTexture2D"', '', '[deps]', '', f'source_file="{res}"', '', '[params]', '']
    body += [f"{k}={v}" for k, v in params.items()]
    open(imp, "w", encoding="utf-8").write("\n".join(body) + "\n")


def font(size):
    for f in ["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def smooth_noise(w, h, cells, seed):
    r = np.random.default_rng(seed)
    small = r.random((cells[1] + 1, cells[0] + 1)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32) / 255


def rgba(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def sky(top, bottom, stars=True, name="sky.png", label=None):
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    c = np.array(top, np.float32) * (1 - y) + np.array(bottom, np.float32) * y
    c = np.broadcast_to(c, (H, W, 3)).copy()
    if stars:
        for _ in range(500):
            x, yy = rng.integers(0, W), rng.integers(0, int(H * 0.6))
            b = rng.uniform(80, 220)
            c[yy:yy + 3, x:x + 3] = np.maximum(c[yy:yy + 3, x:x + 3], b)
    a = np.full((H, W, 1), 255, np.float32)
    img = rgba(np.concatenate([c, a], 2))
    if label:
        ImageDraw.Draw(img).text((60, 40), label, fill=(255, 255, 255, 140), font=font(48))
    save(img, name)


def ridge(name, base, amp, color, seed, ticks=None, label=None):
    """A hill line across the canvas, filled below; tick marks with their depth written
    (so a frame shows how far each layer moved)."""
    xs = np.arange(W)
    r = np.random.default_rng(seed)
    yline = np.full(W, base, np.float32)
    for k, a in [(1.3, 1), (3.1, 0.45), (7.7, 0.2), (17, 0.08)]:
        ph = r.uniform(0, 6.28)
        yline += amp * a * np.sin(xs / W * k * 6.28 + ph)
    yy = np.arange(H)[:, None]
    fill = (yy >= yline[None, :]).astype(np.float32)
    # A soft lit edge along the top: painted, not cut out.
    edge = np.clip(1 - np.abs(yy - yline[None, :]) / 6, 0, 1)
    c = np.zeros((H, W, 4), np.float32)
    c[..., :3] = np.array(color, np.float32)
    c[..., :3] += edge[..., None] * 40
    c[..., 3] = np.clip(fill + edge * 0.5, 0, 1) * 255
    img = rgba(c)
    d = ImageDraw.Draw(img)
    if ticks:
        f = font(36)
        for x in range(100, W, 300):
            y0 = int(yline[x]) + 30
            d.rectangle([x - 3, y0, x + 3, y0 + 80], fill=(255, 255, 255, 170))
            d.text((x + 10, y0 + 10), ticks, fill=(255, 255, 255, 170), font=f)
    if label:
        d.text((60, int(base) + 140), label, fill=(255, 255, 255, 150), font=font(44))
    save(img, name)


def flame():
    """A flame tongue and its warm glow (an add layer), and its sway mask (the tongue only)."""
    w, h = 400, 640
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx - w / 2) / (w / 2)
    v = yy / h
    width = 0.15 + 0.55 * np.clip((v - 0.15) / 0.85, 0, 1) ** 0.7
    core = np.clip(1 - np.abs(u) / width, 0, 1) * np.clip((v - 0.12) / 0.3, 0, 1) * np.clip((1 - v) / 0.25, 0, 1)
    glow = np.exp(-((u ** 2) / 0.3 + ((v - 0.75) ** 2) / 0.12))
    a = np.clip(core * 1.4 + glow * 0.5, 0, 1)
    col = np.stack([255 * np.ones_like(a), 120 + 120 * core, 40 + 120 * core ** 2], -1)
    save(rgba(np.concatenate([col, a[..., None] * 255], -1)), "flame.png")
    m = np.clip(1 - v / 0.85, 0, 1) ** 0.6 * 255
    save(Image.fromarray(m.astype(np.uint8), "L").convert("RGBA"), "flame_sway.png")


def water():
    """A band of dark water with reflected light streaks; its mask (the surface only)."""
    w, h = 3200, 600
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n = smooth_noise(w, h, (80, 30), 3)
    base = np.stack([20 + 0 * n, 34 + 10 * n, 44 + 18 * n], -1)
    streak = np.exp(-((xx - 1600) / 140) ** 2) * (0.5 + 0.5 * np.sin(yy / 7.0)) * 140
    base += np.stack([streak * 1.0, streak * 0.75, streak * 0.4], -1)
    # Horizontal lines, so any bending of the surface is plain to see.
    lines = ((yy.astype(int) // 24) % 2 == 0) * 18
    base += lines[..., None]
    a = np.full((h, w, 1), 255, np.float32)
    save(rgba(np.concatenate([base, a], -1)), "water.png")
    m = np.clip(yy / 60, 0, 1) * 255
    save(Image.fromarray(m.astype(np.uint8), "L").convert("RGBA"), "water_mask.png")


def frost():
    """A frost sheet and its crack order map: dark along a crack's path, lighter away from it,
    so a reveal spreads out from the crack."""
    w, h = 1600, 500
    n = smooth_noise(w, h, (60, 20), 11)
    c = np.stack([180 + 50 * n, 200 + 40 * n, 220 + 30 * n], -1)
    a = np.full((h, w, 1), 230, np.float32)
    save(rgba(np.concatenate([c, a], -1)), "frost.png")
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    x, y = 40, h // 2
    pts = [(x, y)]
    while x < w - 40:
        x += rng.integers(30, 80)
        y = int(np.clip(y + rng.integers(-50, 50), 60, h - 60))
        pts.append((x, y))
    d.line(pts, fill=0, width=10)
    img = img.filter(ImageFilter.GaussianBlur(60))
    arr = np.asarray(img, np.float32)
    arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255
    # Along the crack, earlier from the left: the crack runs across, then spreads.
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    arr = np.clip(arr * 0.75 + xs * 64, 0, 255)
    save(Image.fromarray(arr.astype(np.uint8), "L").convert("RGBA"), "frost_order.png")


def mist():
    w, h = 1024, 256
    n = smooth_noise(w + 64, h, (16, 4), 5)[:, :w]
    # Wraps across x: the band repeats with no seam.
    k = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    n2 = smooth_noise(w + 64, h, (16, 4), 5)[:, :w][:, ::-1]
    n = n * (1 - k) + n2 * k
    v = np.sin(np.linspace(0, math.pi, h, dtype=np.float32))[:, None]
    a = np.clip((n - 0.3) * 1.6, 0, 1) * v * 200
    c = np.full((h, w, 3), 205, np.float32)
    save(rgba(np.concatenate([c, a[..., None]], -1)), "mist.png")


def ink_map():
    """An order map for an ink transition: from the lower left, in fat lobes."""
    w, h = 800, 450
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - 80) / w * 1.78, (yy - h + 60) / h)
    d = d / d.max()
    n = smooth_noise(w, h, (8, 5), 21) - 0.5
    o = np.clip(d * 0.85 + n * 0.3 + 0.05, 0, 1) * 255
    save(Image.fromarray(o.astype(np.uint8), "L").convert("RGBA").filter(ImageFilter.GaussianBlur(2)), "ink_map.png")


def card(name, color, text):
    img = Image.new("RGBA", (W, H), color)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 200):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 30), width=2)
    for y in range(0, H, 200):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 30), width=2)
    d.text((W // 2 - 300, H // 2 - 80), text, fill=(255, 255, 255, 200), font=font(140))
    save(img, name)


if __name__ == "__main__":
    sky((8, 12, 30), (60, 50, 70), name="sky.png", label="sky z 12")
    ridge("hills_far.png", 900, 120, (40, 44, 62), 1, ticks="z 5")
    ridge("hills_mid.png", 1150, 90, (30, 32, 40), 2, ticks="z 2.5")
    ridge("ground.png", 1400, 50, (22, 22, 24), 3, ticks="z 1")
    ridge("fore.png", 1650, 60, (8, 8, 8), 4, ticks="z 0.6")
    flame()
    water()
    frost()
    mist()
    ink_map()
    card("card_b.png", (70, 30, 24, 255), "plate B")
    card("card_c.png", (20, 50, 60, 255), "plate C")
    sky((10, 30, 26), (2, 8, 10), stars=False, name="under.png", label="under the water")
