"""plot(fr, xs, cells, out): side (z,y) and top (z,x) views of chain per cell; xs list of chains per frame (model output)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot(fr, runs, cells, out, title=""):
    n = len(cells)
    fig, ax = plt.subplots(3, n, figsize=(3.6 * n, 10.8))
    if n == 1: ax = ax[:, None]
    cols = ["gold", "lime", "magenta", "cyan"]
    for j, c in enumerate(cells):
        i = min(3 * c, len(fr) - 1); d = fr[i]
        hd = d["head"]
        ctr = d["target"][0]
        for row, (a, b, sg) in enumerate([(2, 1, -1), (2, 0, -1), (0, 1, 1)]):
            A = ax[row, j]
            for k in range(len(d["r"])):
                p = d["at"][k]; w = d["across"][k]
                col = "steelblue" if d["behind"][k] else ("purple" if k == 0 else "teal")
                A.add_patch(plt.Circle((sg*p[a], p[b]), d["r"][k], color=col, alpha=0.18))
                if w @ w > 0:
                    A.add_patch(plt.Circle((sg*(p + w)[a], (p + w)[b]), d["r"][k], color=col, alpha=0.06))
                    A.add_patch(plt.Circle((sg*(p - w)[a], (p - w)[b]), d["r"][k], color=col, alpha=0.06))
                if d["behind"][k]:
                    bk = d["back"][k]; A.plot([sg*p[a], sg*(p + bk * 0.05)[a]], [p[b], (p + bk * 0.05)[b]], color="steelblue", lw=0.6)
            # head axes: y (up of head) green, z (face forward) red
            h0 = hd[0]
            A.plot([sg*h0[a], sg*(h0 + hd[2] * 0.12)[a]], [h0[b], (h0 + hd[2] * 0.12)[b]], color="green", lw=1)
            A.plot([sg*h0[a], sg*(h0 + hd[3] * 0.12)[a]], [h0[b], (h0 + hd[3] * 0.12)[b]], color="red", lw=1)
            t = d["target"]; A.plot(sg*t[:, a], t[:, b], "--", color="gray", lw=1)
            for r, (name, xs) in enumerate(runs):
                x = xs[min(i, len(xs) - 1)]
                A.plot(sg*x[:, a], x[:, b], "-o", color=cols[r], ms=2.5, lw=1.4, label=name if j == 0 and row == 0 else None)
                A.plot(sg*x[7, a], x[7, b], "o", color="red", ms=3)
            if row != 1: A.axhline(d["ground"] + 0.015, color="k", lw=0.8)
            A.set_xlim(sg*ctr[a] - 0.35, sg*ctr[a] + 0.35); A.set_ylim(ctr[b] - 0.4 if row != 1 else ctr[b] - 0.35, ctr[b] + 0.3 if row != 1 else ctr[b] + 0.35)
            A.set_aspect("equal"); A.set_xticks([]); A.set_yticks([])
            A.set_title(("c%d f%d side" % (c, i)) if row == 0 else ("top (x down)" if row == 1 else "back view (x right)"), fontsize=9)
    if runs: ax[0, 0].legend(fontsize=6, loc="lower left")
    fig.suptitle(title, fontsize=9); fig.tight_layout(); fig.savefig(out, dpi=80); plt.close(fig)
