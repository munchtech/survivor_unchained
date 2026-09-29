"""Two frames side by side, labelled: the web game and the Godot slice.

    python3 tools/godot/compare.py web.png godot.png out.png [title]

Scales both to the same height (720), labels each, and writes one image.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

H = 720


def label(im, text):
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', 28)
    except OSError:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), text, font=font)
    d.rectangle((0, 0, box[2] + 28, box[3] + 20), fill=(0, 0, 0, 200))
    d.text((14, 8), text, fill=(243, 217, 160), font=font)
    return im


def main():
    a, b, out = sys.argv[1:4]
    ims = []
    for path, text in ((a, 'Now: three.js (web engine)'), (b, 'Test: Godot 4.5')):
        im = Image.open(path).convert('RGB')
        im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
        ims.append(label(im, text))
    gap = 12
    sheet = Image.new('RGB', (ims[0].width + ims[1].width + gap, H), (20, 18, 22))
    sheet.paste(ims[0], (0, 0))
    sheet.paste(ims[1], (ims[0].width + gap, 0))
    sheet.save(out, quality=92)
    print(out)


if __name__ == '__main__':
    main()
