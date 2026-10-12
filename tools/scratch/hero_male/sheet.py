"""Contact sheets for the body-bar judge: python sheet.py (in b1). Full-body shots are
cropped to the middle 760 px (the figure); close-ups kept whole."""
import os
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))


def load(n, h):
    p = os.path.join(D, n)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGB")
    if n.split("_")[-1] in ("front.png", "side.png", "back.png", "q.png") and not n.startswith("mh/"):
        c = im.width // 2
        im = im.crop((c - 380, 0, c + 380, im.height))
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def row(names, h, out):
    ims = [(n, load(n, h)) for n in names]
    ims = [(n, i) for n, i in ims if i is not None]
    W = sum(i.width for _, i in ims) + 8 * (len(ims) - 1)
    s = Image.new("RGB", (W, h + 28), (20, 20, 20))
    x = 0
    d = ImageDraw.Draw(s)
    for n, i in ims:
        s.paste(i, (x, 28))
        d.text((x + 6, 6), n, fill=(230, 230, 230))
        x += i.width + 8
    s.save(os.path.join(D, out), quality=93)
    print(out, s.size)


row(["hero_front.png", "hero_side.png", "hero_back.png", "hero_q.png"], 1421, "s1_body.jpg")
row(["hero_front.png", "her_front.png", "mh/hero_male_front.png", "hero_back.png", "her_back.png", "mh/hero_male_back.png"], 1100, "s2_compare.jpg")
row(["hero_face.png", "hero_face34.png", "her_face.png"], 900, "s3_face.jpg")
row(["hero_torsoF.png", "hero_torsoS.png", "hero_torsoB.png", "hero_legs.png"], 900, "s4_definition.jpg")
