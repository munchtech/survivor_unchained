# Body 2 B: grey + textured sanity sheet, original | B, rest and town idle (f0), front / back / 3/4, both arms.
#   python sheet.py <orig heroine.glb> <B heroine.glb> <out.png> [view scale m/px]
import os, sys
D_B = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2\d_b"
sys.path.insert(0, D_B)
import numpy as np
import cm, render
from PIL import Image, ImageDraw

a = sys.argv[1:]; cm.FILES["orig"] = a[0]; cm.FILES["B"] = a[1]; out = a[2]
px = float(a[3]) if len(a) > 3 else 0.0032


def rot(deg):
    r = np.radians(deg); return np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]])


VIEWS = [("front", rot(0)), ("back", rot(180)), ("3/4 R", rot(-35)), ("3/4 L", rot(35))]
PW, PH = 200, 210
cells = {}
for tag in ("orig", "B"):
    b = cm.load(tag); I = b.sk.index
    idl = b.clip("idle_reaver_town")
    for pn, G in (("rest", None), ("idle", b.globals(idl, 0))):
        P = b.P if G is None else b.pose(G)
        Gm = b.rest if G is None else G
        c = Gm[I["spine_03"]][:3, 3]
        for vn, Vm in VIEWS:
            w = PW * px; h = PH * px
            cc = Vm @ c
            box = (cc[0], cc[1] + 0.02, w * (1.0 if pn == "idle" else 1.0), h)
            pxx = px * (1.15 if pn == "idle" else 1.3)
            box = (cc[0], cc[1] + (-0.10 if pn == "idle" else -0.02), PW * pxx, PH * pxx)
            img = render.render(b, G, Vm, box, px=pxx)
            g, m = render.shade(img)
            uv = np.nan_to_num(img[..., 3:5]); mi = np.nan_to_num(img[..., 5]).astype(int)
            col = np.ones(g.shape + (3,), np.float32) * 0.95
            for k, tex in b.imgs.items():
                sel = m & (mi == k)
                if not sel.any(): continue
                H_, W_ = tex.shape[:2]
                xx = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); yy = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
                col[sel] = tex[yy[sel], xx[sel]] * (0.35 + 0.8 * g[sel])[:, None]
            cells[(tag, pn, vn, "grey")] = np.repeat(g[..., None], 3, 2); cells[(tag, pn, vn, "tex")] = col
        print("rendered", tag, pn, flush=True)
S = Image.new("RGB", (1600, 900), (255, 255, 255)); Dr = ImageDraw.Draw(S)
# rows: rest grey, rest tex, idle grey, idle tex; columns: per view, orig | B
for ri, (pn, sh) in enumerate([("rest", "grey"), ("rest", "tex"), ("idle", "grey"), ("idle", "tex")]):
    for vi, (vn, _) in enumerate(VIEWS):
        for ti, tag in enumerate(("orig", "B")):
            x = (vi * 2 + ti) * PW; y = 16 + ri * (PH + 12)
            im = Image.fromarray((np.clip(cells[(tag, pn, vn, sh)], 0, 1) * 255).astype(np.uint8))
            S.paste(im.resize((PW, PH)), (x, y))
            Dr.text((x + 3, y - 13), "%s %s %s" % (tag, pn, vn), fill=(0, 0, 0))
S.save(out); print("SHEET", out)
