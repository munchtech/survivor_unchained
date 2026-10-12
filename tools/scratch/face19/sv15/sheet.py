"""sheet.py: per outfit, rows behind/front(review)/3-4 x TODAY/NEW, columns k40-60, 400 px cells at 240 px."""
import os
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.abspath(__file__)); C = 240; KS = list(range(40, 61))
for od in ("warden", "reaver"):
    rows = [(vw, sw) for vw in ("bk", "rv", "r3") for sw in ("off", "on")]
    sh = Image.new("RGB", (len(KS) * C, len(rows) * C)); d = ImageDraw.Draw(sh)
    for r, (vw, sw) in enumerate(rows):
        im = Image.open(os.path.join(D, "%s_%s_%s.png" % (vw, od, sw))).convert("RGB")
        for i, k in enumerate(KS):
            x, y = k % 8 * 400, k // 8 * 400
            sh.paste(im.crop((x, y, x + 400, y + 400)).resize((C, C), Image.LANCZOS), (i * C, r * C))
            d.text((i * C + 4, r * C + 4), "%s %s %s k%d" % (od, {"bk": "behind", "rv": "front", "r3": "3/4"}[vw], "NEW" if sw == "on" else "TODAY", k), fill="yellow" if sw == "on" else "white")
    out = os.path.join(D, "pony_%s_k40-60.png" % od); sh.save(out); print(out, sh.size)
