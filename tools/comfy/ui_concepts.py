"""Concept mockups for the interface's screens (docs/UI_DESIGN.md, "Concepts"):
each a layout drawn here, from real pieces of the running game (the survivor's
figure, icons, the map's ink, the world behind), then painted over by Krea 2
turbo (img2img, the darkbrush LoRA) for the look. Saved side by side, the
labelled layout and the painting, in docs/ui_review/concepts/.

    python tools/comfy/ui_concepts.py [concept ...]      # all, or those named
    python tools/comfy/ui_concepts.py --list

Needs the game's screenshots in godot/.shots/ (after_*.png, taken with
--shot) for its pieces, Pillow, numpy and the local ComfyUI.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHOTS = os.path.join(ROOT, "godot", ".shots")
WORK = os.path.join(HERE, "out", "ui_concepts")
DOCS = os.path.join(ROOT, "docs", "ui_review", "concepts")
sys.path.insert(0, HERE)
import comfy  # noqa: E402

W, H = 1920, 1080
GOLD, GOLDHI, GOLDDIM = (217, 181, 106), (243, 217, 160), (138, 111, 62)
EMBER, BLOOD, DAY = (255, 138, 58), (200, 50, 58), (134, 176, 216)
INK, INKDIM = (232, 220, 196), (168, 156, 136)
RARITY = [(200, 192, 176), (111, 212, 106), (90, 168, 255), (192, 112, 255), (255, 176, 64), (255, 106, 58)]


def font(name, size):
    return ImageFont.truetype(os.path.join(WORK, f"{name}.ttf"), size)


def shot(name):
    return Image.open(os.path.join(SHOTS, name)).convert("RGB")


class Canvas:
    """A layout at 1920x1080: what is painted (img) and the same with its zones named (lab)."""

    def __init__(self, backdrop, dim=0.45):
        bg = shot(backdrop).resize((W, H))
        self.img = Image.blend(Image.new("RGB", (W, H), (8, 6, 10)), bg, dim)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.labels = []

    def label(self, x, y, text):
        self.labels.append((x, y, text))

    # ---------------------------------------------------------- frames --
    def vignette(self, strength=0.75, ember=True):
        """Dark at the edges, the world faint in the middle; an ember glow along the foot."""
        v = Image.new("L", (W, H), 0)
        ImageDraw.Draw(v).ellipse([W * 0.12, H * 0.08, W * 0.88, H * 0.92], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160)).point(lambda p: int(255 * (1 - strength) + p * strength * 0.5))
        dark = Image.new("RGB", (W, H), (6, 4, 8))
        self.img = Image.composite(self.img, dark, v)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        if ember:
            for i in range(120):
                a = int(28 * (1 - i / 120))
                self.d.line([(0, H - i), (W, H - i)], fill=(255, 110, 40, a))

    def plate(self, x, y, w, h, tone=(24, 21, 28), gold=True, name=None):
        d = self.d
        for i in range(h):
            k = i / max(1, h - 1)
            c = tuple(int(tone[j] * (1.15 - 0.45 * k)) for j in range(3))
            d.line([(x, y + i), (x + w, y + i)], fill=c + (245,))
        d.rectangle([x, y, x + w, y + h], outline=(6, 5, 8, 255), width=2)
        d.line([(x + 2, y + 2), (x + w - 2, y + 2)], fill=(90, 80, 100, 160))
        if gold:
            d.rectangle([x + 6, y + 6, x + w - 6, y + h - 6], outline=GOLDDIM + (200,), width=1)
            for cx, cy, sx, sy in [(x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)]:
                d.line([(cx + 4 * sx, cy + 4 * sy), (cx + 30 * sx, cy + 4 * sy)], fill=GOLD + (255,), width=3)
                d.line([(cx + 4 * sx, cy + 4 * sy), (cx + 4 * sx, cy + 30 * sy)], fill=GOLD + (255,), width=3)
                d.polygon([(cx + 4 * sx, cy - 3 * sy + 4 * sy), (cx + 11 * sx, cy + 4 * sy), (cx + 4 * sx, cy + 11 * sy), (cx - 3 * sx, cy + 4 * sy)], fill=GOLDHI + (255,))
        if name:
            self.label(x + 12, y + 12, name)

    def well(self, x, y, w, h, name=None):
        d = self.d
        d.rectangle([x, y, x + w, y + h], fill=(10, 8, 12, 235), outline=(60, 50, 40, 255), width=1)
        for i in range(10):
            d.line([(x + 1, y + 1 + i), (x + w - 1, y + 1 + i)], fill=(0, 0, 0, 120 - i * 12))
        if name:
            self.label(x + 8, y + 8, name)

    def paper(self, x, y, w, h, name=None):
        d = self.d
        d.rectangle([x, y, x + w, y + h], fill=(228, 214, 182, 255))
        for i in range(14):
            d.rectangle([x + i, y + i, x + w - i, y + h - i], outline=(150 - i * 4, 110 - i * 3, 60, 70 - i * 5))
        if name:
            self.label(x + 14, y + 14, name)

    def title(self, x, y, text, size=40, color=GOLDHI, centre=False, face="cinzel-700"):
        f = font(face, size)
        tw = self.d.textlength(text, font=f)
        if centre:
            x -= tw / 2
        self.d.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0, 200))
        self.d.text((x, y), text, font=f, fill=color + (255,))
        return tw

    def plaque(self, cx, y, text, size=44):
        """A heading between two gold rules with stones (the house's title plaque)."""
        tw = self.title(cx, y, text, size, centre=True)
        for s in (-1, 1):
            x0 = cx + s * (tw / 2 + 24)
            self.d.line([(x0, y + size * 0.62), (x0 + s * 220, y + size * 0.62)], fill=GOLD + (220,), width=2)
            self.d.polygon([(x0, y + size * 0.62 - 6), (x0 + s * 6, y + size * 0.62), (x0, y + size * 0.62 + 6), (x0 - s * 6, y + size * 0.62)], fill=EMBER + (255,))

    def lines(self, x, y, w, n, size=16, gap=10, color=INKDIM, short=0.7):
        for i in range(n):
            ww = w * (short if i == n - 1 else 0.92 + 0.08 * ((i * 37) % 3) / 3)
            self.d.rounded_rectangle([x, y + i * (size + gap), x + ww, y + i * (size + gap) + size * 0.45], 3, fill=color + (200,))

    def text(self, x, y, s, size=18, color=INK, face="alegreya-sans-700"):
        self.d.text((x, y), s, font=font(face, size), fill=color + (255,))

    # ---------------------------------------------------------- pieces --
    def figure(self, x, y, w, h, src=("after_self.png", (226, 250, 520, 556))):
        im = shot(src[0]).crop(src[1])
        k = min(w / im.width, h / im.height)
        im = im.resize((int(im.width * k), int(im.height * k)))
        self.img.paste(im, (int(x + (w - im.width) / 2), int(y + (h - im.height) / 2)))

    def crop(self, src, box, x, y, w, h):
        self.img.paste(shot(src).crop(box).resize((int(w), int(h))), (int(x), int(y)))

    def slot(self, x, y, s, r=0, item=None):
        d = self.d
        d.rectangle([x, y, x + s, y + s], fill=(16, 13, 18, 255), outline=RARITY[r] + (220 if item is not None else 60,), width=2)
        if item is not None:
            cells = [(861, 251), (948, 251), (1035, 251), (1122, 251), (1209, 251), (1296, 251), (1383, 251), (1470, 251), (861, 338), (948, 338)]
            cx, cy = cells[item % len(cells)]
            self.img.paste(shot("after_pack_pad.png").crop((cx + 4, cy + 4, cx + 76, cy + 76)).resize((int(s - 8), int(s - 8))), (int(x + 4), int(y + 4)))

    def grid(self, x, y, cols, rows, s, gap=8, items=10):
        for j in range(rows):
            for i in range(cols):
                n = j * cols + i
                self.slot(x + i * (s + gap), y + j * (s + gap), s, [0, 2, 1, 3, 4, 1, 0, 2, 1, 0][n % 10] if n < items else 0, n if n < items else None)

    def icon(self, cx, cy, r, which=0):
        discs = [(611, 390), (959, 378), (1307, 390)]
        sx, sy = discs[which % 3]
        im = shot("after_draft_pad.png").crop((sx - 54, sy - 54, sx + 54, sy + 54)).resize((2 * r, 2 * r))
        m = Image.new("L", (2 * r, 2 * r), 0)
        ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
        self.img.paste(im, (int(cx - r), int(cy - r)), m)

    def medallion(self, cx, cy, r, text, color=GOLDHI, ring=GOLD):
        d = self.d
        d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=(6, 5, 8, 255))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 26, 16, 255), outline=ring + (255,), width=4)
        d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], outline=GOLDDIM + (200,), width=1)
        f = font("cinzel-700", int(r * 0.9))
        tw = d.textlength(text, font=f)
        d.text((cx - tw / 2, cy - r * 0.62), text, font=f, fill=color + (255,))

    def globe(self, cx, cy, r, color, k=0.8, label=None):
        d = self.d
        d.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(10, 8, 10, 255), outline=GOLD + (255,), width=4)
        level = cy + r - 2 * r * k
        for yy in range(int(level), int(cy + r)):
            dx = (r * r - (yy - cy) ** 2) ** 0.5
            t = (yy - level) / max(1, cy + r - level)
            c = tuple(int(color[j] * (1.2 - 0.6 * t)) for j in range(3))
            d.line([(cx - dx, yy), (cx + dx, yy)], fill=tuple(min(255, v) for v in c) + (255,))
        d.ellipse([cx - r * 0.55, cy - r * 0.8, cx - r * 0.1, cy - r * 0.45], fill=(255, 255, 255, 40))
        if label:
            f = font("alegreya-sans-700", 22)
            tw = d.textlength(label, font=f)
            d.text((cx - tw / 2, cy - 12), label, font=f, fill=(255, 244, 234, 255))

    def bar(self, x, y, w, h, color, k):
        d = self.d
        d.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], fill=(6, 5, 8, 255), outline=GOLDDIM + (255,))
        d.rectangle([x, y, x + w * k, y + h], fill=color + (255,))
        d.rectangle([x, y, x + w * k, y + h * 0.35], fill=tuple(min(255, c + 60) for c in color) + (255,))

    def card(self, x, y, w, h, r, which=0, title="Duelist's Grace", lift=0):
        y -= lift
        self.plate(x, y, w, h, tone=tuple(int(18 + RARITY[r][j] * 0.06) for j in range(3)))
        d = self.d
        d.rectangle([x + 10, y + 10, x + w - 10, y + 54], fill=RARITY[r] + (70,))
        self.icon(x + w / 2, y + 150, 70, which)
        d.ellipse([x + w / 2 - 74, y + 76, x + w / 2 + 74, y + 224], outline=RARITY[r] + (255,), width=3)
        self.title(x + w / 2, y + 250, title, 26, centre=True)
        self.lines(x + 30, y + 300, w - 60, 3, 18, 12, INK)
        if lift:
            d.rectangle([x - 6, y - 6, x + w + 6, y + h + 6], outline=(255, 196, 106, 200), width=3)

    def save(self, cid, prompt, denoise=0.55, seed=31337):
        os.makedirs(WORK, exist_ok=True)
        os.makedirs(DOCS, exist_ok=True)
        flat = os.path.join(WORK, f"{cid}_layout.png")
        self.img.resize((1344, 756)).save(flat)
        lab = self.img.copy()
        dl = ImageDraw.Draw(lab, "RGBA")
        f = font("alegreya-sans-700", 22)
        for x, y, t in self.labels:
            tw = dl.textlength(t, font=f)
            dl.rectangle([x - 4, y - 2, x + tw + 6, y + 26], fill=(0, 0, 0, 190), outline=(255, 196, 106, 255))
            dl.text((x, y), t, font=f, fill=(255, 220, 150, 255))
        painted = paint(flat, prompt, denoise, seed)
        out = Image.new("RGB", (1920, 540 + 48), (14, 12, 16))
        out.paste(lab.resize((960, 540)), (0, 48))
        out.paste(Image.open(painted).convert("RGB").resize((960, 540)), (960, 48))
        dh = ImageDraw.Draw(out)
        dh.text((16, 10), f"{cid}: layout", font=font("alegreya-sans-700", 24), fill=GOLDHI)
        dh.text((976, 10), "painted (Krea 2 img2img over the layout)", font=font("alegreya-sans-700", 24), fill=GOLDHI)
        dst = os.path.join(DOCS, f"{cid}.jpg")
        out.save(dst, quality=84)
        print(dst, flush=True)


STYLE = ("A screenshot of a dark fantasy action RPG's user interface, {what}. Forged black iron panels with thin gold "
         "filigree trim and corner ornaments, ember-orange glow, warm parchment, hand-painted, AAA game UI in the style of "
         "Diablo IV and Hades, crisp edges, sharp and legible, high detail.")


def paint(path, prompt, denoise, seed):
    img = comfy.upload(path)
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "11": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "krea2_darkbrush.safetensors", "strength_model": 0.6}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": img}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["11", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0],
                                                    "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "ui_concept"}},
    }
    got = comfy.run(g, WORK)
    dst = path.replace("_layout.png", "_painted.png")
    os.replace(got[0], dst)
    return dst


# ====================================================================== concepts

def survivor_pane(c, x, y, w, h, slots=True):
    """The survivor large, what they wear round them (the pack's and the self's left pane)."""
    c.plate(x, y, w, h, name="the survivor, large")
    c.d.ellipse([x + w / 2 - 230, y + 60, x + w / 2 + 230, y + h - 140], fill=(60, 34, 18, 90))
    c.figure(x + w / 2 - 190, y + 60, 380, h - 220)
    if slots:
        for i in range(4):
            c.slot(x + 30, y + 80 + i * 112, 92, [0, 1, 0, 2][i], [None, 5, 1, 3][i])
            c.slot(x + w - 122, y + 80 + i * 112, 92, [3, 0, 1, 0][i], [4, None, 3, None][i])
        c.label(x + 30, y + 52, "worn: round the figure")


def book_header(c, title, tabs=("Pack", "Self", "Arts", "Journal", "Map"), on=0):
    c.d.rectangle([0, 0, W, 92], fill=(10, 8, 12, 235))
    c.d.line([(0, 92), (W, 92)], fill=GOLD + (200,), width=2)
    x = 60
    for i, t in enumerate(tabs):
        tw = c.d.textlength(t, font=font("alegreya-sans-700", 22)) + 40
        if i == on:
            c.d.rectangle([x, 26, x + tw, 92], fill=(58, 38, 20, 255), outline=GOLDHI + (255,))
        c.text(x + 20, 44, t, 22, GOLDHI)
        x += tw + 8
    c.plaque(W / 2 + 120, 22, title, 40)
    c.label(60, 98, "the book's tabs (LB/RB)")


def hud_a():
    c = Canvas("after_arena.png", 0.9)
    c.bar(560, 24, 840, 12, EMBER, 0.6)
    c.bar(70, 1015, 360, 26, BLOOD, 0.8)
    for i in range(6):
        c.slot(730 + i * 77, 985, 67, i % 4, i if i < 4 else None)
    c.globe(1830, 990, 44, (60, 40, 30), 1)
    c.label(70, 980, "health: far left")
    c.label(1560, 940, "hands: far right")
    c.label(730, 950, "skills")
    c.save("hud_a_corners", STYLE.format(what="a top-down horde survival fight with the health bar at the bottom left, skills at the bottom centre and abilities at the bottom right"))


def hud_b():
    c = Canvas("after_arena.png", 0.9)
    c.bar(560, 24, 840, 12, EMBER, 0.6)
    c.plate(560, 940, 800, 140, name="the console")
    c.globe(640, 975, 78, BLOOD, 0.75, "184")
    for i in range(6):
        c.slot(742 + i * 72, 970, 64, i % 4, i if i < 4 else None)
    c.globe(1280, 975, 78, (110, 70, 30), 1.0)
    c.icon(1280, 975, 40, 1)
    c.label(570, 870, "health globe")
    c.label(1190, 870, "art in hand")
    c.save("hud_b_console", STYLE.format(what="a top-down horde survival fight with one ornate console at the bottom centre: a red health globe on the left, a row of skill slots, a round ability globe on the right"))


def hud_c():
    c = Canvas("after_arena.png", 0.9)
    c.bar(0, 0, W, 18, EMBER, 0.6)
    for i in range(6):
        c.slot(20 + i * 50, 30, 44, i % 4, i if i < 4 else None)
    c.d.ellipse([920, 520, 1000, 600], outline=BLOOD + (255,), width=6)
    c.label(20, 82, "skills: small, top left")
    c.label(900, 610, "health: a ring round the survivor")
    c.save("hud_c_minimal", STYLE.format(what="a minimal top-down horde survival fight with a full-width experience bar along the top, small skill icons at the top left and a health ring around the hero"))


def pack_a():
    c = Canvas("after_town_day.png", 0.45)
    c.plate(210, 145, 1500, 790, name="one box in the middle")
    c.figure(420, 220, 200, 330)
    c.grid(860, 250, 8, 3, 82)
    c.plate(860, 545, 830, 260, gold=False)
    c.save("pack_a_box", STYLE.format(what="an inventory window in a box over the town: the hero in the middle, a grid of items, an item description"))


def pack_b():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    book_header(c, "PACK", on=0)
    survivor_pane(c, 40, 120, 760, 820)
    c.bar(80, 880, 680, 14, DAY, 0.7)
    c.plate(830, 120, 1050, 820, name="what you carry")
    c.well(870, 200, 970, 330)
    c.grid(886, 216, 9, 3, 98, 8)
    c.plate(870, 560, 970, 340, tone=(18, 16, 22), name="the chosen thing, read closely")
    c.slot(900, 590, 110, 3, 3)
    c.title(1030, 600, "Fleet Silver Ring of Cinders", 30, RARITY[3], face="alegreya-sans-700")
    c.lines(1030, 650, 760, 4, 18, 12, INK)
    c.save("pack_b_two_panes", STYLE.format(what="a full-screen inventory: the hero standing large on the left with equipment slots around them, and on the right a grid of item icons above a detailed item card"))


def pack_c():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    book_header(c, "PACK", on=0)
    c.figure(660, 140, 600, 760)
    for i in range(5):
        c.slot(560, 160 + i * 140, 100, i % 5, [None, 5, 1, 3, 4][i])
        c.slot(1260, 160 + i * 140, 100, (i + 2) % 5, [4, None, 3, None, 2][i])
    c.plate(1420, 120, 470, 820, name="what you carry")
    c.grid(1450, 180, 4, 6, 96)
    c.plate(30, 120, 500, 820, name="the chosen thing")
    c.save("pack_c_hero_centre", STYLE.format(what="a full-screen inventory with the hero standing large in the centre surrounded by equipment slots, an item grid on the right and an item card on the left"))


def self_a():
    c = Canvas("after_town_day.png", 0.45)
    c.plate(210, 145, 1500, 790, name="three columns of words")
    c.figure(230, 230, 290, 330)
    c.lines(550, 250, 450, 14, 16, 14, INK)
    c.lines(1050, 250, 450, 18, 14, 12, INKDIM)
    c.save("self_a_columns", STYLE.format(what="a character sheet window in a box with a hero portrait and columns of text stats"))


def self_b():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    book_header(c, "ASHE", on=1)
    survivor_pane(c, 40, 120, 560, 820, slots=False)
    c.medallion(320, 800, 50, "4")
    c.bar(140, 870, 360, 14, DAY, 0.7)
    for i, (n, v) in enumerate([("MIGHT", "6"), ("FINESSE", "3"), ("WITS", "3"), ("RESOLVE", "6")]):
        x = 630 + i * 205
        c.plate(x, 120, 190, 400, tone=(30, 24, 22), name=None)
        c.medallion(x + 95, 210, 58, v)
        c.title(x + 95, 290, n, 24, centre=True)
        c.lines(x + 20, 340, 150, 3, 14, 12, INKDIM)
        c.d.rectangle([x + 55, 440, x + 135, 490], fill=(70, 40, 16, 255), outline=GOLDHI + (255,))
        c.title(x + 95, 445, "+", 34, EMBER, centre=True)
    c.label(630, 528, "four attributes as pillars: the number is the hero")
    for i in range(3):
        c.plate(630 + i * 273, 560, 262, 120, tone=(22, 20, 26))
        c.text(650 + i * 273, 580, ["Iron Constitution", "Quick Hands", "Killer's Eye"][i], 20, GOLDHI)
        c.lines(650 + i * 273, 616, 220, 2, 12, 10, INKDIM)
    c.label(630, 690, "traits to choose, as cards")
    for g in range(4):
        c.plate(1470, 120 + g * 205, 420, 190, tone=(20, 18, 24))
        c.text(1490, 140 + g * 205, ["STAYING ALIVE", "DEALING DEATH", "MOVING", "FORTUNE"][g], 18, GOLD)
        c.lines(1490, 175 + g * 205, 380, 4, 14, 14, INK)
    c.label(1470, 98, "standing, grouped")
    c.save("self_b_pillars", STYLE.format(what="a full-screen character sheet: the hero on the left, four tall attribute cards with large round numbered medallions in the middle, trait cards below, grouped stat panels on the right"))


def self_c():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    c.paper(300, 80, 1320, 920, name="a character sheet on paper")
    c.figure(340, 140, 360, 480)
    for i in range(4):
        c.d.ellipse([760 + i * 200, 160, 880 + i * 200, 280], outline=(90, 60, 30, 255), width=4)
    c.lines(760, 330, 780, 16, 16, 14, (90, 70, 50))
    c.save("self_c_paper_sheet", STYLE.format(what="a character sheet drawn on old parchment like a tabletop sheet, an inked portrait, circled attribute numbers, lines of handwritten stats"))


def arts_a():
    c = Canvas("after_town_day.png", 0.45)
    c.plate(290, 140, 1340, 820, name="list and words")
    c.lines(320, 260, 440, 10, 30, 30, INK)
    c.lines(820, 260, 760, 6, 16, 14, INKDIM)
    c.save("arts_a_list", STYLE.format(what="a skills window with a list of abilities on the left and a description on the right"))


def arts_b():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    book_header(c, "ARTS", on=2)
    c.plate(40, 120, 520, 820, name="every art, as a medallion")
    for j in range(4):
        for i in range(3):
            c.icon(130 + i * 160, 230 + j * 180, 56, (i + j) % 3)
            c.d.ellipse([130 + i * 160 - 60, 230 + j * 180 - 60, 130 + i * 160 + 60, 230 + j * 180 + 60], outline=(GOLD if j < 2 else GOLDDIM) + (255,), width=3)
    c.plate(590, 120, 1290, 820, name="the art in hand")
    c.d.arc([800, 160, 1100, 460], -90, 150, fill=EMBER + (255,), width=10)
    c.d.ellipse([800, 160, 1100, 460], outline=(60, 50, 40, 255), width=2)
    c.icon(950, 310, 120, 1)
    c.title(1140, 230, "SHIELD BASH", 50)
    c.lines(1140, 310, 680, 4, 18, 14, INK)
    for i in range(4):
        x = 640 + i * 305
        c.plate(x, 560, 290, 330, tone=(28, 22, 20) if i < 2 else (18, 16, 20))
        c.medallion(x + 145, 600, 26, ["I", "II", "", ""][i], EMBER if i < 2 else GOLDDIM)
        c.lines(x + 24, 660, 240, 5, 14, 12, INK if i < 2 else INKDIM)
    c.label(640, 530, "four facets; two sockets open by rank")
    c.save("arts_b_altar", STYLE.format(what="a full-screen ability screen: a grid of round ability medallions on the left, a large ability icon with a glowing rank ring in the centre, four facet cards with numbered sockets below"))


def arts_c():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    c.icon(960, 300, 130, 1)
    for i, (x, y) in enumerate([(560, 640), (820, 700), (1100, 700), (1360, 640)]):
        c.d.line([(960, 430), (x + 60, y)], fill=GOLD + (200,), width=3)
        c.icon(x + 60, y + 60, 60, i % 3)
    c.label(800, 120, "the art and its facets as a tree")
    c.save("arts_c_tree", STYLE.format(what="a skill tree: a large central ability icon with four branches leading down to smaller round upgrade nodes, glowing gold lines"))


def journal_a():
    c = Canvas("after_town_day.png", 0.45)
    c.paper(340, 215, 1240, 685, name="a sheet of paper")
    c.lines(370, 260, 300, 8, 18, 16, (90, 70, 50))
    c.save("journal_a_sheet", STYLE.format(what="a quest journal as a single sheet of parchment in a window"))


def journal_b():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    c.d.rounded_rectangle([170, 90, 1750, 1010], 26, fill=(60, 30, 18, 255), outline=(30, 14, 8, 255), width=6)
    c.paper(210, 120, 750, 860)
    c.paper(960, 120, 750, 860)
    for i in range(30):
        c.d.line([(960 - 15 + i, 120), (960 - 15 + i, 980)], fill=(40, 25, 10, int(110 * (1 - abs(i - 15) / 15))))
    for i, t in enumerate(["Quests", "People", "Deeds", "Codex"]):
        c.d.polygon([(330 + i * 150, 60), (450 + i * 150, 60), (450 + i * 150, 130), (390 + i * 150, 112), (330 + i * 150, 130)], fill=[(140, 30, 30), (40, 80, 50), (50, 60, 110), (110, 90, 30)][i] + (255,))
        c.text(345 + i * 150, 72, t, 20, (250, 236, 210))
    c.label(330, 30, "sections as ribbon bookmarks")
    c.title(270, 170, "Under way", 30, (90, 40, 20), face="cinzel-700")
    c.lines(270, 230, 600, 9, 20, 22, (90, 70, 50))
    c.title(1020, 170, "The Beast Problem", 36, (60, 30, 15))
    c.lines(1020, 240, 620, 16, 18, 20, (80, 60, 40))
    c.label(1020, 140, "the entry, on the facing page")
    c.save("journal_b_open_book", STYLE.format(what="a quest journal drawn as a large open leather-bound book with two parchment pages, handwritten entries, coloured ribbon bookmarks along the top"))


def journal_c():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    c.d.rectangle([200, 120, 1720, 980], fill=(70, 50, 32, 255))
    for i in range(6):
        x, y = 260 + (i % 3) * 480, 180 + (i // 3) * 400
        c.paper(x, y, 400, 330)
        c.d.ellipse([x + 190, y - 8, x + 210, y + 12], fill=(160, 30, 30, 255))
        c.lines(x + 30, y + 50, 330, 7, 16, 14, (90, 70, 50))
    c.label(200, 96, "notes pinned to a board")
    c.save("journal_c_board", STYLE.format(what="a quest log as parchment notes pinned to a wooden notice board with red pins"))


def map_a():
    c = Canvas("after_map_verge.png", 1.0)
    c.label(100, 120, "the known world, tiny at the edge")
    c.save("map_a_square", STYLE.format(what="a map screen with a parchment map square and a list panel"))


def map_b():
    c = Canvas("after_town_day.png", 0.3)
    c.crop("after_map_town.png", (90, 90, 990, 990), 0, 0, 1920, 1080)
    c.d.rectangle([0, 0, W, H], fill=(20, 12, 4, 40))
    for i in range(80):
        c.d.rectangle([i, i, W - i, H - i], outline=(30, 18, 8, int(120 * (1 - i / 80))))
    c.plate(1440, 110, 450, 870, tone=(18, 16, 22), name="where to go, nearest first")
    c.lines(1470, 200, 380, 14, 18, 26, INK)
    c.plaque(520, 30, "THE WAYSTATION", 44)
    c.label(40, 120, "the map is the screen; fitted to what you know")
    c.save("map_b_full_bleed", STYLE.format(what="a full-screen hand-drawn parchment town map with ink buildings, trees and labels, a title plaque at the top, and a dark iron panel on the right listing places"))


def map_c():
    c = Canvas("after_town_day.png", 0.3)
    c.d.rectangle([0, 0, W, H], fill=(60, 40, 24, 255))
    c.crop("after_map_town.png", (90, 90, 990, 990), 260, 90, 900, 900)
    for x, y in [(600, 300), (800, 520), (450, 640)]:
        c.d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(170, 30, 30, 255))
    c.paper(1220, 140, 560, 800, name="a ledger of places")
    c.label(260, 60, "a map on a table, pinned")
    c.save("map_c_table", STYLE.format(what="a parchment map lying on a dark wooden table with red pins, beside an open ledger"))


def draft_a():
    c = Canvas("after_arena.png", 0.35)
    for i in range(3):
        c.card(452 + i * 348, 280, 320, 452, [4, 2, 1][i], i)
    c.save("draft_a_cards", STYLE.format(what="a level-up choice of three tall cards with round icons"))


def draft_b():
    c = Canvas("after_arena.png", 0.3)
    c.plaque(960, 60, "EMBER 12", 54)
    for i in range(3):
        y = 190 + i * 210
        c.plate(360, y, 1200, 180, tone=tuple(int(18 + RARITY[[4, 2, 1][i]][j] * 0.06) for j in range(3)))
        c.icon(460, y + 90, 70, i)
        c.title(560, y + 40, ["Duelist's Grace", "Cinderfall", "Vitality"][i], 34)
        c.lines(560, y + 95, 760, 2, 18, 14, INK)
    c.well(560, 860, 800, 80, name="your build")
    c.save("draft_b_rows", STYLE.format(what="a level-up choice of three wide horizontal rows, each with a round icon on the left, a title and a description"))


def draft_c():
    c = Canvas("after_arena.png", 0.3)
    for r in range(300, 0, -6):
        c.d.ellipse([960 - r * 2.6, 520 - r, 960 + r * 2.6, 520 + r], fill=(255, 120, 40, 3))
    c.plaque(960, 70, "EMBER 12", 56)
    for i in range(3):
        c.card(430 + i * 370, 260, 340, 480, [4, 2, 1][i], i, ["Duelist's Grace", "Cinderfall", "Vitality"][i], 18 if i == 1 else 0)
    c.well(560, 800, 800, 84, name="your build: what a card touches lights")
    for i in range(6):
        c.slot(600 + i * 70, 812, 60, i % 4, i if i < 3 else None)
    c.label(430, 230, "rarity crest on each card")
    c.save("draft_c_crested_cards", STYLE.format(what="a level-up choice of three ornate tall cards with coloured crest bands at the top and large round glowing icons, the middle card raised and glowing, a dark rail of skill slots below, ember glow behind"))


def talk_a():
    c = Canvas("after_talk.png", 1.0)
    c.label(260, 600, "portrait boxed inside the panel")
    c.save("talk_a_boxed", STYLE.format(what="a dialogue box at the bottom of the screen with a small framed portrait"))


def talk_b():
    c = Canvas("after_town_day.png", 0.35)
    c.plate(150, 700, 1620, 340, name=None)
    c.figure(120, 260, 520, 780, ("after_talk.png", (262, 640, 492, 908)))
    c.d.rectangle([600, 680, 900, 730], fill=(40, 26, 14, 255), outline=GOLDHI + (255,), width=2)
    c.title(620, 686, "MOTHER ROOK", 32)
    c.lines(640, 760, 1060, 3, 26, 18, INK)
    for i in range(3):
        c.text(660, 880 + i * 44, ["1  A toll clerk with money?", "2  What of the wolves?", "3  Something else."][i], 24, GOLDHI)
    c.label(130, 230, "the person, large, over the frame")
    c.save("talk_b_portrait", STYLE.format(what="a dialogue scene: a large character portrait standing on the left, overlapping a dark ornate dialogue box at the bottom with a gold name plaque and three numbered reply choices"))


def talk_c():
    c = Canvas("after_town_day.png", 0.6)
    c.plate(1280, 0, 640, 1080, name="the talk as a column")
    c.lines(1320, 120, 560, 26, 18, 16, INK)
    c.save("talk_c_column", STYLE.format(what="a dialogue log as a tall dark column on the right side of the screen with lines of conversation text"))


def shop_a():
    c = Canvas("after_shop.png", 1.0)
    c.label(260, 340, "three columns in a box")
    c.save("shop_a_box", STYLE.format(what="a shop window with two item grids and an item card between them"))


def shop_b():
    c = Canvas("after_town_day.png", 0.3)
    c.vignette()
    c.plate(40, 120, 460, 820, name="the merchant")
    c.figure(60, 140, 420, 560, ("after_talk.png", (262, 640, 492, 908)))
    c.title(270, 720, "HARLAN COYLE", 30, centre=True)
    c.lines(80, 780, 380, 3, 16, 14, INK)
    c.plate(530, 120, 820, 820, tone=(46, 30, 20), name="the counter: their wares")
    c.grid(570, 200, 6, 3, 118, 10)
    c.plate(570, 610, 740, 300, tone=(18, 16, 22), name="the chosen thing, priced")
    c.plate(1380, 120, 510, 820, name="your pack")
    c.grid(1410, 200, 5, 5, 86, 8)
    c.save("shop_b_counter", STYLE.format(what="a full-screen merchant shop: the merchant's portrait on the left, wares laid on a wooden counter in the middle with an item card, the player's bag of items on the right"))


def shop_c():
    c = Canvas("after_town_day.png", 0.4)
    c.plate(160, 140, 760, 800, name="theirs")
    c.grid(200, 220, 6, 6, 104)
    c.plate(1000, 140, 760, 800, name="yours")
    c.grid(1040, 220, 6, 6, 104)
    c.save("shop_c_two_grids", STYLE.format(what="a trade screen with two large item grids side by side"))


def create_a():
    c = Canvas("after_create.png", 1.0)
    c.label(60, 40, "rows in a plate; the figure; the lore")
    c.save("create_a_rows", STYLE.format(what="a character creation screen by a campfire with a list of choices on the left and a description on the right"))


def create_b():
    c = Canvas("after_create.png", 0.75)
    c.d.rectangle([0, 0, 600, H], fill=(8, 6, 10, 220))
    for i, n in enumerate(["WARDEN", "REAVER", "ARCANIST", "STALKER"]):
        y = 180 + i * 190
        c.plate(60, y, 480, 170, tone=(40, 26, 16) if i == 0 else (20, 18, 24))
        c.icon(150, y + 85, 60, i % 3)
        c.title(240, y + 40, n, 34)
        c.lines(240, y + 100, 260, 2, 14, 12, INKDIM)
    c.plaque(300, 70, "WHO SITS HERE?", 36)
    c.label(60, 150, "callings as crested cards")
    c.save("create_b_crested", STYLE.format(what="a character creation screen at a campfire at night, on the left four large ornate class cards with round crest icons, the hero standing by the fire"))


def pause_a():
    c = Canvas("after_pause_pad.png", 1.0)
    c.label(740, 230, "a box in the middle")
    c.save("pause_a_box", STYLE.format(what="a pause menu box in the centre of the screen"))


def pause_b():
    c = Canvas("after_town_day.png", 0.5)
    c.d.rectangle([0, 0, 640, H], fill=(8, 6, 10, 235))
    c.d.line([(640, 0), (640, H)], fill=GOLD + (220,), width=2)
    c.plaque(320, 90, "PAUSED", 48)
    for i, t in enumerate(["RESUME", "SAVE", "SETTINGS", "CONTROLS", "LEAVE TO THE TITLE", "QUIT"]):
        c.title(110, 220 + i * 70, t, 36, (255, 242, 216) if i == 0 else (203, 189, 159))
    c.d.polygon([(80, 238), (90, 228), (100, 238), (90, 248)], fill=EMBER + (255,))
    for i in range(5):
        c.icon(120 + i * 100, 820, 36, i % 3)
    c.label(80, 770, "the book, one press away")
    c.save("pause_b_side", STYLE.format(what="a pause menu as a tall dark panel on the left side with large gold capital menu items and a row of round icons, the game world visible on the right"))


def result_a():
    c = Canvas("after_result.png", 1.0)
    c.label(430, 400, "two plain boxes")
    c.save("result_a_boxes", STYLE.format(what="an end-of-run results screen with numbers and two panels"))


def result_b():
    c = Canvas("after_arena.png", 0.3)
    c.vignette()
    c.d.polygon([(560, 80), (1360, 80), (1400, 140), (1360, 200), (560, 200), (520, 140)], fill=(60, 30, 14, 240), outline=GOLDHI + (255,))
    c.plaque(960, 104, "THE ARENA IS WON", 50)
    for i, (v, n) in enumerate([("35:34", "SURVIVED"), ("1,840", "SLAIN"), ("27", "EMBER"), ("5:34", "BEYOND")]):
        c.medallion(510 + i * 300, 330, 92, v if len(v) < 4 else "", GOLDHI)
        c.title(510 + i * 300, 290, v, 40, centre=True)
        c.text(470 + i * 300, 440, n, 18, GOLD)
    c.plate(380, 520, 560, 400, name="what you take out")
    c.grid(420, 580, 4, 2, 100)
    c.plate(980, 520, 560, 400, tone=(16, 14, 18), name="what stays: faded")
    c.save("result_b_spoils", STYLE.format(what="a victorious end-of-run screen: a gold banner across the top, four large round medallions with numbers, a panel of loot item icons and a faded panel of lost skills"))


CONCEPTS = {f.__name__: f for f in [hud_a, hud_b, hud_c, pack_a, pack_b, pack_c, self_a, self_b, self_c, arts_a, arts_b, arts_c,
                                    journal_a, journal_b, journal_c, map_a, map_b, map_c, draft_a, draft_b, draft_c, talk_a, talk_b, talk_c,
                                    shop_a, shop_b, shop_c, create_a, create_b, pause_a, pause_b, result_a, result_b]}

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        print(" ".join(CONCEPTS))
    else:
        for n in args or list(CONCEPTS):
            CONCEPTS[n]()
