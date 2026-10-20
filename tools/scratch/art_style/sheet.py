"""Contact sheets for the style frames.

    python sheet.py frame OUT.png TITLE TODAY.png A.png B.png C.png [PITCH_A PITCH_B PITCH_C]
        A | B | C at full size, today's graded frame as a small inset in the header.
    python sheet.py overview OUT.png ROWLABEL=A.png,B.png,C.png ...   (3 rows: the 3x3 overview)
    python sheet.py grid OUT.png COLS WIDTH IMG ... [--labels]        (working looks; labels from file stems)
    python sheet.py four OUT.png TITLE LABEL=IMG LABEL=IMG ...         (r2: today | A | target | engine at full size;
                                                                        IMG "-" leaves a dark panel with its label)
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

def font(n):
    for f in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, n)
    return ImageFont.load_default()

BG, FG, DIM = (18, 18, 20), (235, 232, 225), (170, 168, 160)
COLS = ["A  vibrant grade, in engine", "B  painterly realism (paint-over)", "C  bolder painterly (paint-over)"]

def frame(out, title, today, a, b, c, pitches=None):
    ims = [Image.open(p).convert("RGB") for p in (a, b, c)]
    W, H = ims[0].size; gap = 16; head = 340
    sh = Image.new("RGB", (3 * W + 2 * gap, head + H), BG); d = ImageDraw.Draw(sh)
    t = Image.open(today).convert("RGB").resize((480, 270), Image.LANCZOS)
    d.text((16, 2), "Today, as built", font=font(26), fill=DIM)
    sh.paste(t, (16, 36)); d.rectangle((15, 35, 16 + 480, 36 + 270), outline=DIM)
    d.text((540, 8), title, font=font(46), fill=FG)
    for i, im in enumerate(ims):
        x = i * (W + gap); sh.paste(im, (x, head))
        d.text((x + 540 * (i == 0) + 12, 250), COLS[i], font=font(38), fill=FG)
        if pitches and i < len(pitches): d.text((x + 540 * (i == 0) + 12, 296), pitches[i], font=font(26), fill=DIM)
    sh.save(out); print(out, sh.size)

def overview(out, rows):
    cw, ch, lw, top, gap = 960, 540, 230, 64, 10
    sh = Image.new("RGB", (lw + 3 * cw + 2 * gap, top + len(rows) * (ch + gap)), BG); d = ImageDraw.Draw(sh)
    for i, c in enumerate(COLS): d.text((lw + i * (cw + gap) + 8, 12), c, font=font(34), fill=FG)
    for r, (label, files) in enumerate(rows):
        y = top + r * (ch + gap)
        d.multiline_text((10, y + ch // 2 - 40), label.replace("|", "\n"), font=font(30), fill=FG)
        for i, f in enumerate(files): sh.paste(Image.open(f).convert("RGB").resize((cw, ch), Image.LANCZOS), (lw + i * (cw + gap), y))
    sh.save(out); print(out, sh.size)

def grid(out, cols, width, files, labels):
    ims = [Image.open(f).convert("RGB") for f in files]
    h = round(ims[0].height * width / ims[0].width); gap = 6
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * width + (cols - 1) * gap, rows * h + (rows - 1) * gap), BG); d = ImageDraw.Draw(sh)
    for i, (im, f) in enumerate(zip(ims, files)):
        x, y = (i % cols) * (width + gap), (i // cols) * (h + gap)
        sh.paste(im.resize((width, h), Image.LANCZOS), (x, y))
        if labels:
            s = os.path.splitext(os.path.basename(f))[0]; fo = font(max(14, width // 40))
            d.rectangle((x, y, x + d.textlength(s, font=fo) + 10, y + fo.size + 8), fill=(0, 0, 0)); d.text((x + 5, y + 3), s, font=fo, fill=FG)
    sh.save(out, quality=88) if out.lower().endswith(".jpg") else sh.save(out); print(out, sh.size)

def four(out, title, cols):
    ims = [None if f == "-" else Image.open(f).convert("RGB") for _, f in cols]
    W, H = next(im for im in ims if im is not None).size; gap = 16; head = 120
    sh = Image.new("RGB", (len(cols) * W + (len(cols) - 1) * gap, head + H), BG); d = ImageDraw.Draw(sh)
    d.text((16, 6), title, font=font(46), fill=FG)
    for i, ((label, _), im) in enumerate(zip(cols, ims)):
        x = i * (W + gap)
        d.text((x + 12, 66), label, font=font(36), fill=FG)
        if im is None: d.rectangle((x, head, x + W - 1, head + H - 1), fill=(30, 30, 34)); continue
        sh.paste(im.resize((W, H), Image.LANCZOS) if im.size != (W, H) else im, (x, head))
    sh.save(out); print(out, sh.size)

if __name__ == "__main__":
    k, out = sys.argv[1], sys.argv[2]
    if k == "frame": frame(out, sys.argv[3], *sys.argv[4:8], pitches=sys.argv[8:11] or None)
    elif k == "four": four(out, sys.argv[3], [(c.split("=", 1)[0], c.split("=", 1)[1]) for c in sys.argv[4:]])
    elif k == "overview": overview(out, [(r.split("=", 1)[0], r.split("=", 1)[1].split(",")) for r in sys.argv[3:]])
    else:
        rest = [x for x in sys.argv[5:] if x != "--labels"]
        grid(out, int(sys.argv[3]), int(sys.argv[4]), rest, "--labels" in sys.argv)
