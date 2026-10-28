"""pit close-up (2x) with the loop map's fold cuts drawn: python pitviz.py out.png frame:side ..."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
import k, m, viz, harness as h, sh
def cut_ids(sd, feat, key):
    mp = json.load(open(m.LOOPMAP)); bs = k.base(); ids = []
    for pt in mp[sd][feat][key][0]:
        pr, v = pt[0]; ids.append(int(bs.wid[bs.offs[pr] + v]))
    return np.array(ids)
def draw(body, f, sd, kind="pit", zoom=2, cuts=True):
    fr = k.frame(f); bx = viz.box(fr, sd, kind); g = k.geom(fr, body)
    rgb, ids = sh.clay(fr, g, bx)
    im = Image.fromarray(rgb).resize((rgb.shape[1] * zoom, rgb.shape[0] * zoom), Image.LANCZOS)
    if cuts:
        d = ImageDraw.Draw(im)
        Xu = k.posed_welded(fr, body)
        for feat, key, col in (("front_fold", "+0", (255, 230, 0)), ("front_fold", "-4", (0, 255, 0)), ("front_fold", "+4", (0, 160, 255)), ("back_fold", "+0", (255, 0, 255)), ("delt_groove", "-2", (255, 120, 0)), ("delt_front", "-2", (255, 0, 0)), ("delt_back", "-2", (160, 0, 255))):
            try:
                ii = cut_ids(sd, feat, key)
            except Exception:
                continue
            q = h.project(fr.Pm, Xu[ii])
            # visible only: depth test against the raster
            for (x, y), v in zip(q, ii):
                xi, yi = int((x - bx[0]) * h.SS), int((y - bx[1]) * h.SS)
                if 0 <= yi < ids.shape[0] and 0 <= xi < ids.shape[1] and ids[yi, xi] >= 0:
                    tri = g["I"][ids[yi, xi]]
                    if abs(g["z"][tri].mean() - np.linalg.norm(Xu[v] - fr.campos)) < 0.01:
                        X, Y = (x - bx[0]) * zoom, (y - bx[1]) * zoom
                        d.ellipse([X - 1.5, Y - 1.5, X + 1.5, Y + 1.5], fill=col)
    return im
if __name__ == "__main__":
    out = sys.argv[1]; ims = []
    for a in sys.argv[2:]:
        f, sd = a.split(":")[:2]; kind = a.split(":")[2] if a.count(":") > 1 else "pit"
        ims.append(draw(k.Body(), f, sd, kind))
    W = sum(i.width for i in ims) + 4 * (len(ims) - 1); H = max(i.height for i in ims)
    S = Image.new("RGB", (W, H), (255, 0, 255)); x = 0
    for i in ims:
        S.paste(i, (x, 0)); x += i.width + 4
    S.save(out); print(S.size)
