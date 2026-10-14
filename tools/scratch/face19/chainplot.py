import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def sideframes(fr, runs, frames, out, title="", span=0.4, view=(2, 1, -1)):
    a, b, sg = view
    n = len(frames); cols = min(n, 8); rows = (n + cols - 1) // cols
    fig, ax = plt.subplots(rows, cols, figsize=(2.8 * cols, 2.8 * rows))
    ax = np.array(ax).reshape(rows, cols)
    colors = ["gold", "lime", "magenta", "cyan"]
    path = np.array([d["target"][0] for d in fr])
    for j, i in enumerate(frames):
        A = ax[j // cols, j % cols]; d = fr[i]; ctr = d["target"][0]
        for k in range(len(d["r"])):
            p = d["at"][k]; col = "steelblue" if d["behind"][k] else ("purple" if k == 0 else "teal")
            if d["r"][k] > 0: A.add_patch(plt.Circle((sg * p[a], p[b]), d["r"][k], color=col, alpha=0.2))
        A.plot(sg * path[:, a], path[:, b], ":", color="k", lw=0.7)
        t = d["target"]; A.plot(sg * t[:, a], t[:, b], "--", color="gray", lw=1)
        for r, (name, xs) in enumerate(runs):
            x = xs[i]; A.plot(sg * x[:, a], x[:, b], "-o", color=colors[r], ms=2.5, lw=1.3, label=name if j == 0 else None)
            A.plot(sg * x[7, a], x[7, b], "o", color="red", ms=3)
        if b == 1: A.axhline(d["ground"] + 0.015, color="k", lw=0.8)
        A.set_xlim(sg * ctr[a] - span, sg * ctr[a] + span); A.set_ylim(ctr[b] - span, ctr[b] + span)
        A.set_aspect("equal"); A.set_xticks([]); A.set_yticks([]); A.set_title("f%d (c%.1f)" % (i, i / 3), fontsize=8)
    if runs: ax[0, 0].legend(fontsize=6, loc="lower left")
    fig.suptitle(title, fontsize=9); fig.tight_layout(); fig.savefig(out, dpi=75); plt.close(fig)
