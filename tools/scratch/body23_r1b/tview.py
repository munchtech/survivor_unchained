"""targets over the game frame: A's silhouette red, the target green (2x zoom tiles round each region)"""
import sys, numpy as np, c3lib as c, targets as T
from PIL import Image
TILES = {"w_p45": [("upperarm_r", 0, 40, 90)], "w_m45": [("upperarm_l", -10, 40, 90)],
         "look_f": [("upperarm_r", 0, 40, 90), ("upperarm_l", 0, 40, 90)],
         "w_m80": [("lowerarm_l", 0, 0, 75), ("upperarm_l", 0, 40, 90)], "rL90_m45": [("lowerarm_l", 0, 0, 75), ("upperarm_l", 0, 40, 90)],
         "s_p45": [("lowerarm_r", 0, 0, 75), ("upperarm_r", 0, 40, 90)]}


def draw(f, fr, B, tiles, extra=None):
    a = Image.open(c.os.path.join(c.DUMP, f + ".png")).convert("RGB")
    A2 = np.asarray(a.resize((3840, 2160), Image.LANCZOS)).copy()
    p = B["p"]; q = p + B["n"] * B["D"][:, None]
    layers = [(p, (255, 40, 40)), (q[B["W"] > 0], (40, 255, 80))]
    if extra is not None:
        layers.append((extra, (40, 200, 255)))
    for pts, col in layers:
        xy = np.round(pts * 2).astype(int)
        ok = (xy[:, 0] >= 0) & (xy[:, 0] < 3839) & (xy[:, 1] >= 0) & (xy[:, 1] < 2159)
        A2[xy[ok, 1], xy[ok, 0]] = col
    out = []
    for jn, dx, dy, hw in tiles:
        j = c.jscreen(fr, jn); cx, cy = int(j[0] + dx) * 2, int(j[1] + dy) * 2
        out.append(Image.fromarray(A2).crop((cx - hw * 2, cy - hw * 2, cx + hw * 2, cy + hw * 2)))
    return out


if __name__ == "__main__":
    out = []
    frames = sys.argv[2:] or list(TILES)
    for f in frames:
        fr = c.frame(f); B = T.build(fr)
        print(f, {k: (None if v is None else {kk: (round(vv, 1) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk in ("ac", "aV", "fill", "r0", "R")}) for k, v in B["info"].items()})
        out += draw(f, fr, B, TILES[f])
    c.sh.sheet(out, sys.argv[1])
