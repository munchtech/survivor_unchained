"""Why a garment's helper weights differ from the skin under it: python wdiag.py outfit..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree
from gapcheck import load, dense
import helpers as hp
for o in sys.argv[1:]:
    b = load("after", o)
    skin = np.nonzero(b.kind == "skin")[0]; gar = np.nonzero(b.kind == "garment")[0]
    d, ns = cKDTree(b.P[skin]).query(b.P[gar]); ns = skin[ns]
    lim = ((b.part[ns] != 0) | (b.part[gar] != 0)) & (d < 0.02)
    g, s = gar[lim], ns[lim]
    I = b.sk.index
    H = [I[n] for n in hp.names() if n in I]
    C = sorted(set(H) | {I[n] for n in I if n.split("_")[0] in ("clavicle", "upperarm", "lowerarm", "thigh", "calf")})
    dg, ds = dense(b, g), dense(b, s)
    diff = np.abs(dg[:, H] - ds[:, H]).sum(1)
    gs, ss = dg[:, C].sum(1), ds[:, C].sum(1)
    full = (b.W[g] > 1e-4).sum(1) == 4
    cat = np.where(gs < 0.02, "A none on limb", np.where(np.abs(gs - ss) > 0.1, "B limb total differs", np.where(full, "C four bones full", "D other")))
    top = diff > np.percentile(diff, 95)
    print(f"{o}: {lim.sum()} pts, p95 {np.percentile(diff, 95):.3f}")
    for c in sorted(set(cat)):
        m = cat == c
        print(f"   {c:22s} {m.sum():7d} pts  mean diff {diff[m].mean():.3f}  share of top 5%: {(top & m).sum() / top.sum():.2f}")
    # the bones the worst garment points ride, and the skin's
    w = np.argsort(-diff)[:2000]
    gb = np.bincount(b.J[g[w]][:, 0], minlength=len(b.sk.names)); sb = np.bincount(b.J[s[w]][:, 0], minlength=len(b.sk.names))
    print("   worst 2000: garment's top bone", [(b.sk.names[i], int(gb[i])) for i in np.argsort(-gb)[:4]], "skin's", [(b.sk.names[i], int(sb[i])) for i in np.argsort(-sb)[:4]])
