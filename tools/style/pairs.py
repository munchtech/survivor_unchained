"""Pairs for a judge: each game frame (DIR/frames/NN_id.png) beside its G1 target (a2/targets.json), both at 960x540,
labelled, into OUT/NN_id_pair.jpg, plus OUT/pairs_sheet.jpg (all thirteen at 640x180 per pair).
    python tools/style/pairs.py GAME_DIR OUT [LABEL]   (L1 Stage C: a judge sees each frame beside its target)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

L1 = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1"


def fit(im, w, h):
    im = im.convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def main(game, out, label="game"):
    os.makedirs(out, exist_ok=True)
    t = json.load(open(os.path.join(L1, "a2", "targets.json"), encoding="utf-8"))["frames"]
    try: font = ImageFont.truetype("arial.ttf", 20)
    except OSError: font = ImageFont.load_default()
    rows = []
    for k, v in t.items():
        gp = os.path.join(game, "frames", k + ".png")
        tp = os.path.join(L1, v.split(" ")[0].replace("/", os.sep))
        if not os.path.exists(gp) or not os.path.exists(tp):
            print("skip", k, os.path.exists(gp), os.path.exists(tp)); continue
        P = Image.new("RGB", (1920, 540))
        P.paste(fit(Image.open(gp), 960, 540), (0, 0)); P.paste(fit(Image.open(tp), 960, 540), (960, 0))
        d = ImageDraw.Draw(P)
        for x, s in ((8, f"{k}  {label}"), (968, f"{k}  G1 target ({os.path.basename(tp)})")):
            d.rectangle((x - 4, 4, x + 12 * len(s), 30), fill=(0, 0, 0)); d.text((x, 6), s, fill=(255, 255, 255), font=font)
        P.save(os.path.join(out, k + "_pair.jpg"), quality=90); rows.append(P)
        print("pair", k)
    S = Image.new("RGB", (1280, 180 * ((len(rows) + 1) // 2)))
    for i, P in enumerate(rows):
        S.paste(P.resize((640, 180), Image.LANCZOS), ((i % 2) * 640, (i // 2) * 180))
    S.save(os.path.join(out, "pairs_sheet.jpg"), quality=88)


if __name__ == "__main__":
    main(*sys.argv[1:])
