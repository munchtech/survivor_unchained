"""Plots: rows of runs (label, fr, xs) by cells, one view (side: -z,y; top: -z,x; back: x,y)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
DPI = 90
VIEWS = {"side": (2, 1, -1), "top": (2, 0, -1), "back": (0, 1, 1), "rside": (2, 1, 1)}

def rows(rowsdef, cells, step, out, view="side", span=0.33, title="", size=2.0):
    a, b, sg = VIEWS[view]
    R = len(rowsdef); C = len(cells)
    fig, ax = plt.subplots(R, C, figsize=(size * C, size * R))
    ax = np.array(ax).reshape(R, C)
    for r, (label, fr, runs) in enumerate(rowsdef):
        for j, c in enumerate(cells):
            A = ax[r, j]; i = min(step * c, len(fr) - 1); d = fr[i]; ctr = d["target"][0]
            for k in range(len(d["r"])):
                p = d["at"][k]; w = d["across"][k]
                col = "steelblue" if d["behind"][k] else ("purple" if k == 0 else "teal")
                rr = d["r"][k] * 1.04
                A.add_patch(plt.Circle((sg * p[a], p[b]), rr, color=col, alpha=0.15))
                if w @ w > 0:
                    for q in (p + w, p - w): A.add_patch(plt.Circle((sg * q[a], q[b]), rr, color=col, alpha=0.05))
            hd = d["head"]; h0 = hd[0]
            A.plot([sg * h0[a], sg * (h0 + hd[2] * 0.1)[a]], [h0[b], (h0 + hd[2] * 0.1)[b]], color="green", lw=0.8)
            A.plot([sg * h0[a], sg * (h0 + hd[3] * 0.1)[a]], [h0[b], (h0 + hd[3] * 0.1)[b]], color="red", lw=0.8)
            t = d["target"]; A.plot(sg * t[:, a], t[:, b], "--", color="gray", lw=0.8)
            for n, (col, xs) in enumerate(runs):
                x = xs[i]
                A.plot(sg * x[:, a], x[:, b], "-o", color=col, ms=1.8, lw=1.1)
                A.plot(sg * x[7, a], x[7, b], "o", color="red", ms=2.2)
            if b == 1: A.axhline(d["ground"] + 0.015, color="k", lw=0.6)
            A.set_xlim(sg * ctr[a] - span, sg * ctr[a] + span); A.set_ylim(ctr[b] - span, ctr[b] + span)
            A.set_aspect("equal"); A.set_xticks([]); A.set_yticks([])
            A.set_title("%s c%d" % (label, c), fontsize=6, pad=1)
    fig.suptitle(title, fontsize=7); fig.tight_layout(pad=0.2); fig.savefig(out, dpi=DPI); plt.close(fig)
