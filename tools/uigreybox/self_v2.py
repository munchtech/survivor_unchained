"""Self, revised after the owner's look at the dressed board (5 October):
- "we like to see our beautiful game": Self becomes a side panel over the live world, the Pack's
  panel in the Pack's place, and she stands in the world beside it;
- the four big attribute boxes were "horribly ai and bloated": they become one compact strip
  (number, name, a small spend control), the description on hover, the preview deltas kept;
- where a full page stays, its ground is slightly translucent over the blurred world.

    python tools/uigreybox/self_v2.py OUTDIR BUSY.png DARK.png

BUSY and DARK are 1920x1080 frames of the world with no HUD (the game's --nohud), so the
translucency is judged against what the player would really see behind it."""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter
from gb import *

BOOK = ['Pack', 'Self', 'Arts', 'Journal', 'Map']
KEYS = ['I', 'C', 'K', 'J', 'M']
PX, PW = 864, 1040
TITLE = (200, 186, 150)
WARM_PANEL = (34, 31, 33)


def over(c, x, y, w, h, color, alpha, fade=0):
    """A surface laid over what is already drawn at an opacity; with fade, its last `fade` px
    run out into what is behind (the taper)."""
    layer = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    solid = h - fade
    d.rectangle((x, y, x + w - 1, y + solid - 1), fill=color + (int(255 * alpha),))
    for i in range(fade):
        k = (1 - i / fade) ** 2
        d.line((x, y + solid + i, x + w - 1, y + solid + i), fill=color + (int(255 * alpha * k),))
    c.im = Image.alpha_composite(c.im.convert('RGBA'), layer).convert('RGB')
    c.d = ImageDraw.Draw(c.im)


def shade_toward(c, x0, x1, right=True):
    """The world shaded only toward the panel (Overlay.SidePanel's gradient)."""
    layer = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x in range(x0, x1):
        t = (x - x0) / (x1 - x0)
        if not right:
            t = 1 - t
        a = 0.25 * (t / 0.4) if t < 0.4 else 0.25 + 0.6 * (t - 0.4) / 0.6
        d.line((x, 0, x, 1079), fill=(5, 4, 8, int(255 * a)))
    c.im = Image.alpha_composite(c.im.convert('RGBA'), layer).convert('RGB')
    c.d = ImageDraw.Draw(c.im)


def world_frame(path, shift=0, blur=0, dim=1.0):
    im = Image.open(path).convert('RGB').resize((1920, 1080))
    if shift:
        # The camera's shift for a side panel (Overlay.CameraShift): she stands left of centre.
        # (what the shifted camera would bring in at the right is unknown: the frame's own right
        # edge, mirrored, stands in for it, under the panel)
        moved = Image.new('RGB', im.size, (12, 12, 14))
        moved.paste(im.crop((shift, 0, 1920, 1080)), (0, 0))
        moved.paste(im.crop((1920 - shift, 0, 1920, 1080)).transpose(Image.FLIP_LEFT_RIGHT), (1920 - shift, 0))
        im = moved
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if dim != 1.0:
        im = Image.eval(im, lambda v: int(v * dim))
    c = Canvas()
    c.im = im
    c.d = ImageDraw.Draw(c.im)
    return c


def round_btn(c, x, y, s, sign, lit=True):
    c.rect(x, y, s, s, (64, 46, 28) if lit else (46, 44, 48), outline=EMBER if lit else (84, 80, 86), r=s // 2)
    c.text(x + s / 2, y + s / 2, sign, UI_H, int(s * 0.62), (255, 228, 190) if lit else INK2, anchor='mm')


def attribute_strip(c, x, y, w, preview=0):
    """The four attributes on one line each a compact cell: the number, its name, a small spend
    control. What a point gives is on hover (shown here for Might, hovered); a preview shows
    the number's next value in green and a take-back."""
    attrs = [('Might', 6), ('Finesse', 3), ('Wits', 3), ('Resolve', 6)]
    gap = 10
    cw = (w - 3 * gap) / 4
    for i, (n, v) in enumerate(attrs):
        cx = x + i * (cw + gap)
        c.panel(cx, y, cw, 48, (40, 37, 40))
        tx = cx + 14
        c.text(tx, y + 6, f'{v}', DISPLAY, 28, INK)
        tx += c.width(f'{v}', DISPLAY, 28) + 6
        if i == preview:
            tx += c.arrow(tx, y + 25, 12, GOOD, 2)
            c.text(tx, y + 6, f'{v + 1}', DISPLAY, 28, GOOD)
            tx += c.width(f'{v + 1}', DISPLAY, 28)
        c.text(tx + 10, y + 16, n.upper(), DISPLAY_L, 15, (210, 196, 160))
        round_btn(c, cx + cw - 36, y + 11, 26, '+')
        if i == preview:
            round_btn(c, cx + cw - 68, y + 11, 26, '–', lit=False)
    return y + 48


def hover_card(c, x, y, w, title, lines):
    h = 44 + len(lines) * 22
    c.rect(x + 5, y + 6, w, h, (8, 8, 9), r=4)
    c.rect(x, y, w, h, (32, 30, 33), outline=(84, 80, 76), r=4)
    c.text(x + 14, y + 10, title, TEXT_B, 17, INK)
    for i, ln in enumerate(lines):
        c.text(x + 14, y + 38 + i * 22, ln, UI, 15, INK2)


def trait_track(c, x, y, w):
    """Levelled traits as a track (taken, next, later); the traits given for deeds as chips at
    its end, under a small caption. Labels stay short so neighbours never touch: the next one
    says only "Next" (its hover says "one of three, chosen when you reach it")."""
    deeds = ('Wolfsbane', 'Lamp-lit')
    chips_w = sum(c.width(n, UI_B, 14) + 22 for n in deeds) + 8 * (len(deeds) - 1)
    levels = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    x0, x1, yy = x + 24, x + w - chips_w - 48, y + 22
    c.rule(x0, yy, x1, (78, 74, 76))
    step = (x1 - x0) / (len(levels) - 1)
    for i, lv in enumerate(levels):
        px = x0 + i * step
        if lv == 2:
            c.d.ellipse((px - 18, yy - 18, px + 18, yy + 18), fill=(110, 100, 84), outline=(200, 180, 130), width=2)
            c.text(px, yy, 'ic', UI_H, 12, (40, 36, 30), anchor='mm')
            c.text(px, yy + 25, 'Steady Hand', UI_B, 14, INK, anchor='ma')
        elif lv == 4:
            c.d.ellipse((px - 18, yy - 18, px + 18, yy + 18), fill=(40, 30, 22), outline=EMBER, width=3)
            c.text(px, yy, '4', DISPLAY, 16, (255, 220, 170), anchor='mm')
            c.text(px, yy + 25, 'Next', UI_B, 14, EMBER, anchor='ma')
        else:
            c.d.ellipse((px - 5, yy - 5, px + 5, yy + 5), fill=(64, 60, 64))
            c.text(px, yy + 12, f'{lv}', UI_B, 12, FAINT, anchor='ma')
    cx = x + w - chips_w
    c.text(cx, y - 6, 'FOR DEEDS', UI_H, 11, DIM)
    for n in deeds:
        cx += c.chip(cx, y + 10, n) + 8
    return y + 62


STATS = [
    [('STAYING ALIVE', [('Health', '212', '+4'), ('Armour', '8 · 29%', None), ('Regeneration', '0.7/s', None), ('Healing', '+18%', None), ('Dodge', '0%', None)])],
    [('DEALING DEATH', [('Damage', '+15%', '+2.5%'), ('Critical chance', '6%', None), ('Critical dmg', '×1.5', None), ('Weapon speed', '+3%', None), ('Area', '+6%', None)])],
    [('WARDING', [('Fire', '12%', None), ('Frost', '22%', None), ('Storm', '0%', None), ('Venom', '0%', None)]),
     ('FORTUNE', [('Experience', '+6%', None), ('Gold found', '0%', None)])],
    [('MOVING', [('Speed', '5.2', None), ('Dashes', '2', None), ('Reach', '2.4 m', None)]),
     ('THE ART IN HAND', [('Shield Bash', 'rank II', None), ('Strength', '+6%', None), ('Wait', '7 s', None)])],
]


def standing(c, x, y, w, size=16, gap=28, row=28):
    colw = (w - 3 * gap) / 4
    end = 0
    for ci, groups in enumerate(STATS):
        cx = x + ci * (colw + gap)
        yy = y
        for gname, rows in groups:
            c.text(cx, yy, gname, UI_H, 12, TITLE)
            yy += 21
            for (label, val, delta) in rows:
                c.text(cx, yy, label, UI, size, INK2)
                c.text(cx + colw - 44, yy, val, UI_B, size, INK, anchor='ra')
                if delta:
                    c.text(cx + colw, yy + 1, delta, UI_B, size - 2, GOOD, anchor='ra')
                c.rule(cx, yy + row - 4, cx + colw, (52, 49, 52))
                yy += row
            yy += 10
        end = max(end, yy)
    return end


def calling_row(c, x, y, w, gap=28):
    colw = (w - 3 * gap) / 4
    for i, (k, n, t) in enumerate([('CALLING', 'Warden', 'Hold the line.'), ('ORIGIN', 'Hunter', 'You read the ground and its animals.'),
                                    ('KNOWS', 'Beastlore', 'It opens words and ways.'), ('RENOWN', 'A stranger', 'The Waystation has not decided.')]):
        cx = x + i * (colw + gap)
        c.text(cx, y, k, UI_H, 12, TITLE)
        c.text(cx, y + 18, n, TEXT_B, 18, INK)
        c.wrap(cx, y + 44, t, TEXT_I, 14, DIM, colw)
    return y + 84


def chained_title(c, cx, y, text, size=30):
    """The title between two short lengths of chain, each ending at the name in a link pried
    open (UI art draws it; plain links here)."""
    tw = c.width(text, DISPLAY, size)
    c.text(cx, y, text, DISPLAY, size, INK, anchor='ma')
    my = y + size * 0.62
    for side in (-1, 1):
        x = cx + side * (tw / 2 + 18)
        for k in range(5):
            lx = x + side * k * 22
            a = 140 - k * 22
            col = (a, a - 8, a - 20)
            c.d.ellipse((lx - 10, my - 5, lx + 10, my + 5), outline=col, width=2)
        c.d.ellipse((x - 3, my - 3, x + 3, my + 3), fill=EMBER)


def chain_tabs(c, x, y, names, on, keys, size=16):
    """The book's tabs riding a chain: a run of links under the names, alternately face-on and
    edge-on, each a little different; under the open tab one link is pried open with ember in
    the break. Turning a tab slides the whole chain along until that link settles under the new
    tab (built in the game, with a rattle); here, at rest under Self."""
    xs = []
    tx = x
    for i, n in enumerate(names):
        tw = c.text(tx, y, n, UI_B, size, INK if i == on else DIM)
        tw += 8 + c.keycap(tx + tw + 8, y, keys[i])
        xs.append((tx, tx + tw))
        tx += tw + 28
    cy = y + size + 14
    x0, x1 = x - 14, tx - 14
    gap = 13
    k = 0
    lx = x0
    mid = (xs[on][0] + xs[on][1]) / 2
    while lx < x1:
        fade = min(1, (lx - x0) / 40, (x1 - lx) / 40)
        a = int(60 + 70 * fade) + (k * 37 % 3) * 6
        col = (a, a - 6, a - 18)
        if abs(lx - mid) < gap / 2 + 1:
            # The opened link: a gap in its ring, the ember inside.
            c.d.arc((lx - 9, cy - 6, lx + 9, cy + 6), 40, 320, fill=(196, 160, 110), width=2)
            c.d.ellipse((lx + 3, cy - 3, lx + 9, cy + 3), fill=EMBER)
        elif k % 2 == 0:
            c.d.ellipse((lx - 8, cy - 5, lx + 8, cy + 5), outline=col, width=2)
        else:
            c.d.line((lx - 7, cy, lx + 7, cy), fill=col, width=3)
        lx += gap
        k += 1
    return tx


# ------------------------------------------------------------------------ A: a panel over the world
def self_panel(world_path):
    c = world_frame(world_path, shift=430)
    shade_toward(c, 0, PX)
    top = 16
    # The panel hugs what it holds and tapers into the world below.
    over(c, PX, top, PW, 964, WARM_PANEL, 0.94, fade=110)
    c.rect(PX, top, PW, 3, (110, 104, 92))
    chain_tabs(c, PX + 28, 34, BOOK, 1, KEYS)
    c.button(PX + PW - 128, 32, 'Close', key='C', w=100)
    chained_title(c, PX + PW / 2, 80, 'WREN')
    c.text(PX + PW / 2, 122, 'Level 4  ·  Warden  ·  Hunter, who knows Beastlore', TEXT_I, 16, DIM, anchor='ma')
    bx = PX + PW / 2 - 110
    c.rect(bx, 150, 220, 4, (24, 24, 26), r=2)
    c.rect(bx, 150, 124, 4, (120, 160, 210), r=2)
    c.text(bx + 228, 144, '340 / 600', UI_B, 13, DIM)
    X, W = PX + 32, PW - 64
    # Attributes: one strip; Undo and Confirm take the head's end while a spend is open.
    y = 182
    c.section(X, y, W - 300, 'Attributes', 'hover: what a point gives')
    c.text(X + W - 280, y - 1, '1 of 2 spent', UI_B, 15, EMBER)
    c.button(X + W - 170, y - 9, 'Undo', w=64)
    c.button(X + W - 96, y - 9, 'Confirm', primary=True, w=96)
    y = attribute_strip(c, X, y + 32, W)
    # Traits.
    y += 28
    c.section(X, y, W, 'Traits', 'one of three at every second level, and some for what you do')
    y = trait_track(c, X, y + 32, W)
    # Standing.
    y += 26
    c.section(X, y, W, 'Standing', 'hover a number: where it comes from')
    y = standing(c, X, y + 30, W)
    # Who she is.
    y += 14
    c.section(X, y, W, 'Calling and origin')
    y = calling_row(c, X, y + 30, W)
    c.prompts(PX + PW / 2, y + 22, [('Arrows', 'Move'), ('Enter', 'Spend'), ('Bksp', 'Take back'), ('[ ]', 'Turn'), ('C', 'Close')])
    # Hovering Might: what a point gives, on the world side.
    hover_card(c, PX - 14 - 300, 214, 300, 'Might', ['+2.5% damage a point', '+4 health a point', 'from 6 to 7, Health 212 to 216'])
    return c, y + 60


# ------------------------------------------------------------------ B: a full page, translucent
def self_page(world_path, alpha, blur=14, dim=0.62):
    c = world_frame(world_path, blur=blur, dim=dim)
    # The sheet: translucent over the blurred world, tapering into it below.
    over(c, 0, 0, 1920, 88, (40, 38, 40), 0.96)
    over(c, 0, 88, 1920, 830, (27, 26, 28), alpha, fade=130)
    c.rule(0, 88, 1920, (96, 90, 80))
    c.text(36, 30, '[', UI_B, 16, DIM)
    x = c.tabs(60, 28, BOOK, 1, KEYS)
    c.text(x - 6, 30, ']', UI_B, 16, DIM)
    chained_title(c, 960, 12, 'WREN', 34)
    c.text(960, 56, 'Level 4  ·  Warden  ·  Hunter, who knows Beastlore', TEXT_I, 16, DIM, anchor='ma')
    c.button(1784, 26, 'Close', key='Esc', w=100)
    c.figure(290, 112, 840)
    X, W = 560, 1320
    y = 112
    c.section(X, y, W - 300, 'Attributes', 'hover: what a point gives')
    c.text(X + W - 280, y - 1, '1 of 2 spent', UI_B, 15, EMBER)
    c.button(X + W - 170, y - 9, 'Undo', w=64)
    c.button(X + W - 96, y - 9, 'Confirm', primary=True, w=96)
    y = attribute_strip(c, X, y + 32, W)
    y += 32
    c.section(X, y, W, 'Traits', 'one of three at every second level, and some given for what you do')
    y = trait_track(c, X, y + 32, W)
    y += 30
    c.section(X, y, W, 'Standing', 'hover a number: where it comes from')
    y = standing(c, X, y + 32, W, size=17, gap=36, row=31)
    y += 16
    c.section(X, y, W, 'Calling and origin')
    calling_row(c, X, y + 32, W, gap=36)
    c.prompts(960, 1040, [('Arrows', 'Move'), ('Enter', 'Spend'), ('Bksp', 'Take back'), ('[ ]', 'Turn the page'), ('Esc', 'Close')])
    return c


def strips(out):
    """The attribute strip alone, before and after, at 1:1: what the space given back looks like."""
    c = Canvas((27, 26, 28))
    c.text(40, 20, 'Before: four boxes, 120 px tall', UI_B, 15, DIM)
    for i, (n, v, per) in enumerate([('Might', 6, '+2.5% damage, +4 health a point'), ('Finesse', 3, '+0.6% critical chance, +1% speed'),
                                     ('Wits', 3, '+1% weapon speed, +2% area and ember'), ('Resolve', 6, '+3 health, +0.5 armour, +0.08 regeneration')]):
        x = 40 + i * 334
        c.panel(x, 50, 318, 120)
        c.text(x + 22, 58, f'{v}', DISPLAY, 46, INK)
        c.text(x + 22, 116, n.upper(), DISPLAY_L, 18, (210, 196, 160))
        c.text(x + 22, 142, per, UI, 14, DIM)
        round_btn(c, x + 318 - 52, 62, 34, '+')
    c.text(40, 200, 'After: one strip, 48 px tall; what a point gives is on hover', UI_B, 15, DIM)
    attribute_strip(c, 40, 230, 1320)
    c.im = c.im.crop((0, 0, 1400, 300))
    c.save(out)


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for tag, wp in zip(('busy', 'dark', 'fight'), sys.argv[2:]):
        c, _ = self_panel(wp)
        c.save(os.path.join(out, f'self_panel_{tag}.png'))
        for a in (0.85, 0.90):
            self_page(wp, a).save(os.path.join(out, f'self_page_{int(a * 100)}_{tag}.png'))
        # A lighter hand: the world less blurred and less dimmed, the ground at 80%.
        self_page(wp, 0.80, blur=7, dim=0.8).save(os.path.join(out, f'self_page_80_{tag}.png'))
    # 1:1 crops of one stretch of the page (the standing over the world's busiest part), side by side.
    box = (1180, 330, 1800, 640)
    names = [f'self_page_{a}_{t}' for t in ('busy', 'dark') for a in (90, 85, 80)]
    ims = [Image.open(os.path.join(out, n + '.png')).crop(box) for n in names]
    w, h = ims[0].size
    sheet = Image.new('RGB', (w * 3 + 20, h * 2 + 70), (12, 12, 14))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(zip(names, ims)):
        x, y = (i % 3) * (w + 10), 30 + (i // 3) * (h + 40)
        sheet.paste(im, (x, y))
        d.text((x + 6, y - 22), n.replace('self_page_', '').replace('_', '% over the ', 1) + (' (lighter blur)' if n.startswith('self_page_80') else ''), font=font(UI_B, 16), fill=(200, 196, 188))
    sheet.save(os.path.join(out, 'self_page_translucency_1to1.png'))
    strips(os.path.join(out, 'self_attributes_strip.png'))
    print('drew Self v2')
