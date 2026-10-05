"""Greybox kit: the UI design lead's layouts drawn plain at 1920x1080, in the game's own type,
before any art. Names follow the UI art lead's vocabulary (ground, band, panel, well, slot, rule,
tab, keycap, button, chip, node, tooltip card, price tag)."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'fonts')
GAME_FONTS = os.path.join(HERE, '..', '..', 'godot', 'art', 'fonts')
_fonts = {}


def font(name, size):
    """The game's own faces (its woff2 files, made TrueType once, into tools/uigreybox/fonts)."""
    k = (name, size)
    if k not in _fonts:
        ttf = os.path.join(F, name + '.ttf')
        if not os.path.exists(ttf):
            from fontTools.ttLib import TTFont
            os.makedirs(F, exist_ok=True)
            t = TTFont(os.path.join(GAME_FONTS, name + '.woff2'))
            t.flavor = None
            t.save(ttf)
        _fonts[k] = ImageFont.truetype(ttf, size)
    return _fonts[k]


DISPLAY, DISPLAY_L = 'cinzel-700', 'cinzel-600'
TEXT, TEXT_I, TEXT_B = 'alegreya-400', 'alegreya-400-italic', 'alegreya-700'
UI, UI_B, UI_H = 'alegreya-sans-500', 'alegreya-sans-700', 'alegreya-sans-800'

# Greys, darkest to lightest; colour only where it means something.
WORLD = (58, 61, 64)
GROUND = (27, 27, 29)
BAND = (40, 40, 43)
PANEL = (36, 36, 39)
PANEL_HI = (52, 52, 57)
WELL = (24, 24, 26)
SLOT = (17, 17, 19)
SLOT_EDGE = (9, 9, 10)
RULE = (62, 62, 68)
INK = (232, 228, 218)
INK2 = (196, 192, 184)
DIM = (138, 134, 126)
FAINT = (92, 90, 86)
GLYPH = (72, 72, 78)
EMBER = (222, 132, 58)
GOOD = (112, 200, 108)
BAD = (226, 92, 80)
NOTE = (56, 196, 220)
RARITY = {0: (184, 178, 166), 1: (112, 190, 92), 2: (90, 154, 230), 3: (176, 112, 224), 4: (232, 160, 64)}


class Canvas:
    def __init__(self, ground=GROUND):
        self.im = Image.new('RGB', (1920, 1080), ground)
        self.d = ImageDraw.Draw(self.im)

    # -- surfaces --------------------------------------------------------------
    def rect(self, x, y, w, h, fill, outline=None, width=1, r=0):
        if r:
            self.d.rounded_rectangle((x, y, x + w - 1, y + h - 1), r, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle((x, y, x + w - 1, y + h - 1), fill=fill, outline=outline, width=width)

    def panel(self, x, y, w, h, fill=PANEL):
        """A raised tonal panel: a shade lighter than the ground, its top edge catching light."""
        self.rect(x, y, w, h, fill, r=3)
        self.d.line((x + 3, y, x + w - 4, y), fill=PANEL_HI)

    def well(self, x, y, w, h):
        """A recessed area for a grid or a list."""
        self.rect(x, y, w, h, WELL, r=3)
        self.d.line((x + 2, y + 1, x + w - 3, y + 1), fill=(10, 10, 11))

    def frame(self, x, y, w, h):
        """The screen's one ornamental frame (drawn plain here)."""
        self.rect(x, y, w, h, None, outline=(110, 104, 92), width=3, r=4)

    def taper(self, x, y, w, h, fill, fade=90, frame=True, sides=True):
        """A surface that runs on past its contents and fades out over its last `fade` px into
        whatever is behind (the world, the page's backdrop), with its frame fading with it."""
        solid = h - fade
        self.rect(x, y, w, solid, fill)
        edge = (110, 104, 92)
        for i in range(fade):
            k = 1 - i / fade
            k = k * k
            yy = y + solid + i
            bg = self.im.getpixel((int(x + w / 2), int(yy)))
            col = tuple(int(fill[j] * k + bg[j] * (1 - k)) for j in range(3))
            self.d.line((x, yy, x + w - 1, yy), fill=col)
            if frame and sides:
                ec = tuple(int(edge[j] * k + bg[j] * (1 - k)) for j in range(3))
                self.d.line((x, yy, x + 2, yy), fill=ec)
                self.d.line((x + w - 3, yy, x + w - 1, yy), fill=ec)
        if frame:
            self.d.line((x, y, x + w - 1, y), fill=edge, width=3)
            if sides:
                self.d.line((x, y, x, y + solid), fill=edge, width=3)
                self.d.line((x + w - 2, y, x + w - 2, y + solid), fill=edge, width=3)

    def rule(self, x0, y, x1, color=RULE):
        self.d.line((x0, y, x1, y), fill=color)

    def vrule(self, x, y0, y1, color=RULE):
        self.d.line((x, y0, x, y1), fill=color)

    def slot(self, x, y, s, label=None, item=None, rarity=0, qty=None, price=None, dear=False, focus=False):
        """An empty slot is a quiet recessed tile with a faint glyph of what goes there; a filled one
        carries its rarity's colour as tint and edge."""
        if item is None:
            self.rect(x, y, s, s, SLOT, r=4)
            self.d.line((x + 3, y + 1, x + s - 4, y + 1), fill=SLOT_EDGE)
            if label:
                self.text(x + s / 2, y + s / 2 - 1, label, UI_B, max(11, s // 6), GLYPH, anchor='mm')
        else:
            c = RARITY[rarity]
            tint = tuple(int(SLOT[i] * 0.72 + c[i] * 0.16) for i in range(3))
            self.rect(x, y, s, s, tint, outline=tuple(int(v * 0.8) for v in c), width=2, r=4)
            m = s * 0.22
            self.d.ellipse((x + m, y + m, x + s - m, y + s - m), fill=(118, 116, 112))
            self.text(x + s / 2, y + s / 2, item, UI_H, max(11, s // 5), (40, 40, 44), anchor='mm')
            if qty:
                self.text(x + s - 5, y + s - 4, f'×{qty}', UI_H, 13, INK, anchor='rs')
        if price is not None:
            tw = self.d.textlength(f'{price}', font=font(UI_H, 13)) + 24
            self.rect(x + s - tw - 2, y + s - 19, tw, 17, (14, 14, 16), r=3)
            col = BAD if dear else (230, 196, 120)
            self.d.ellipse((x + s - 15, y + s - 15, x + s - 7, y + s - 7), fill=col)
            self.text(x + s - 19, y + s - 4, f'{price}', UI_H, 13, col, anchor='rs')
        if focus:
            self.rect(x - 3, y - 3, s + 6, s + 6, None, outline=EMBER, width=2, r=6)

    def grid(self, x, y, cols, rows, s=72, gap=8, items=None, pad=12):
        """A well with a grid of slots; items: {(col,row): dict(item=, rarity=, ...)}."""
        w, h = cols * s + (cols - 1) * gap + pad * 2, rows * s + (rows - 1) * gap + pad * 2
        self.well(x, y, w, h)
        items = items or {}
        for r in range(rows):
            for c in range(cols):
                kw = items.get((c, r), {})
                self.slot(x + pad + c * (s + gap), y + pad + r * (s + gap), s, **kw)
        return w, h

    # -- words -----------------------------------------------------------------
    def text(self, x, y, s, face, size, fill=INK, anchor='la'):
        self.d.text((x, y), s, font=font(face, size), fill=fill, anchor=anchor)
        return self.d.textlength(s, font=font(face, size))

    def width(self, s, face, size):
        return self.d.textlength(s, font=font(face, size))

    def wrap(self, x, y, s, face, size, fill, width, lh=None):
        lh = lh or int(size * 1.35)
        words, line = s.split(), ''
        for w_ in words:
            t = (line + ' ' + w_).strip()
            if self.width(t, face, size) > width and line:
                self.text(x, y, line, face, size, fill)
                y += lh
                line = w_
            else:
                line = t
        if line:
            self.text(x, y, line, face, size, fill)
            y += lh
        return y

    def section(self, x, y, w, title, note=None, right=None, right_color=EMBER):
        """A section head: small capitals, an optional note, a rule running on."""
        tw = self.text(x, y, title.upper(), UI_H, 14, (200, 186, 150))
        nx = x + tw + 10
        if note:
            nx += self.text(nx, y - 1, note, TEXT_I, 15, DIM) + 10
        rx = x + w
        if right:
            rw = self.width(right, UI_B, 15)
            self.text(x + w, y - 1, right, UI_B, 15, right_color, anchor='ra')
            rx = x + w - rw - 12
        self.rule(nx, y + 9, rx)

    def arrow(self, x, y, length, color, width=2):
        """A drawn arrow, pointing right, its shaft at y (the fonts have no arrow glyph)."""
        self.d.line((x, y, x + length, y), fill=color, width=width)
        self.d.polygon([(x + length + 2, y), (x + length - 6, y - 5), (x + length - 6, y + 5)], fill=color)
        return length + 8

    def keycap(self, x, y, k):
        w = max(22, self.width(k, UI_B, 13) + 12)
        self.rect(x, y, w, 22, (22, 22, 25), outline=(78, 76, 72), r=4)
        self.text(x + w / 2, y + 11, k, UI_B, 13, INK2, anchor='mm')
        return w

    def tabs(self, x, y, names, on, keys=None, size=17):
        """Text tabs; the open one has an ember underline."""
        for i, n in enumerate(names):
            tw = self.text(x, y, n, UI_B, size, INK if i == on else DIM)
            if keys:
                self.keycap(x + tw + 8, y, keys[i])
                tw += 8 + max(22, self.width(keys[i], UI_B, 13) + 12)
            if i == on:
                self.d.line((x, y + size + 8, x + tw, y + size + 8), fill=EMBER, width=2)
            x += tw + 28
        return x

    def button(self, x, y, label, primary=False, w=None, key=None):
        w = w or self.width(label, UI_B, 16) + 36 + (30 if key else 0)
        self.rect(x, y, w, 36, (64, 46, 28) if primary else (46, 46, 50), outline=EMBER if primary else (70, 70, 76), r=4)
        tx = x + 18
        if key:
            tx += self.keycap(x + 10, y + 7, key) + 8 - 8
        self.text(tx, y + 18, label, UI_B, 16, (255, 228, 190) if primary else INK2, anchor='lm')
        return w

    def chip(self, x, y, label, color=INK2):
        w = self.width(label, UI_B, 14) + 22
        self.rect(x, y, w, 26, (48, 48, 52), r=13)
        self.text(x + w / 2, y + 13, label, UI_B, 14, color, anchor='mm')
        return w

    def prompts(self, cx, y, items):
        """The foot's prompts, centred: keycap and what it does."""
        tot = sum(self.width(t, UI, 15) + max(22, self.width(k, UI_B, 13) + 12) + 8 for k, t in items) + 28 * (len(items) - 1)
        x = cx - tot / 2
        for k, t in items:
            x += self.keycap(x, y, k) + 8
            x += self.text(x, y + 2, t, UI, 15, DIM) + 28

    def note(self, x, y, s, anchor='la'):
        """An annotation for the reviewer (not part of the screen)."""
        self.text(x, y, s, UI_B, 14, NOTE, anchor=anchor)

    # -- her --------------------------------------------------------------------
    def figure(self, cx, top, h, label='her figure, live 3D', fill=(74, 74, 80)):
        """A plain standing silhouette, h tall from the crown, centred on cx."""
        u = h / 8.0  # a head
        d = self.d
        d.ellipse((cx - 0.42 * u, top, cx + 0.42 * u, top + u), fill=fill)
        d.rectangle((cx - 0.16 * u, top + 0.9 * u, cx + 0.16 * u, top + 1.25 * u), fill=fill)
        d.polygon([(cx - 1.0 * u, top + 1.35 * u), (cx + 1.0 * u, top + 1.35 * u), (cx + 0.78 * u, top + 3.0 * u),
                   (cx + 0.62 * u, top + 3.5 * u), (cx + 0.9 * u, top + 4.3 * u), (cx - 0.9 * u, top + 4.3 * u),
                   (cx - 0.62 * u, top + 3.5 * u), (cx - 0.78 * u, top + 3.0 * u)], fill=fill)
        for s in (-1, 1):
            d.polygon([(cx + s * 1.0 * u, top + 1.4 * u), (cx + s * 1.25 * u, top + 1.5 * u), (cx + s * 1.18 * u, top + 3.9 * u),
                       (cx + s * 0.98 * u, top + 3.9 * u), (cx + s * 0.86 * u, top + 1.9 * u)], fill=fill)
            d.polygon([(cx + s * 0.08 * u, top + 4.2 * u), (cx + s * 0.88 * u, top + 4.2 * u), (cx + s * 0.58 * u, top + 7.9 * u),
                       (cx + s * 0.25 * u, top + 7.9 * u)], fill=fill)
        if label:
            self.text(cx, top + 2.4 * u, label, UI_B, 14, (110, 110, 118), anchor='mm')

    def tooltip(self, x, y, w, name, rarity, kind, lines, foot=None, head=None, deltas=None):
        """A tooltip card: a raised panel with a rarity strip along its top, sections ruled."""
        h = 92 + len(lines) * 24 + (36 if foot else 0) + (26 if head else 0)
        self.rect(x + 6, y + 8, w, h, (8, 8, 9), r=4)
        self.rect(x, y, w, h, (32, 32, 35), outline=(70, 70, 76), r=4)
        c = RARITY[rarity]
        self.rect(x + 1, y + 1, w - 2, 4, c)
        yy = y + 14
        if head:
            self.text(x + 16, yy, head.upper(), UI_H, 12, DIM)
            yy += 26
        self.text(x + 16, yy, name, TEXT_B, 20, c)
        self.text(x + 16, yy + 28, kind, UI, 14, DIM)
        yy += 58
        self.rule(x + 16, yy, x + w - 16)
        yy += 10
        for i, ln in enumerate(lines):
            self.text(x + 16, yy, ln, UI, 15, INK2)
            if deltas and i < len(deltas) and deltas[i]:
                d_ = deltas[i]
                self.text(x + w - 16, yy, d_, UI_H, 15, GOOD if d_.startswith('+') else BAD, anchor='ra')
            yy += 24
        if foot:
            self.rule(x + 16, yy + 4, x + w - 16)
            self.text(x + 16, yy + 12, foot, UI, 14, DIM)
        return h

    def save(self, path):
        self.im.save(path)
