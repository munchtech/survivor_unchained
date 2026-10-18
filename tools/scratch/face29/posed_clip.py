"""Her hair passing into her body, head and outfit pieces at creation's Look, posed and moving, as the game draws it.
Reads the dumps of the game's --hairdump DIR (godot/src/Game/HairDump.cs: CPU-skinned hair plus the hair shader's
chain/sway/forearm displacement, world space, every 0.25 s) and reports per run:
  strands (non-cap, non-tie, UV.y >= 0.1), roots (UV.y < 0.1) and ties, against each surface (body, head, each piece):
  % of the group's vertices behind the surface by > 1 mm and > 3 mm, worst depth, by region (the vertex's dominant bone:
  head, neck, back = spine/pelvis, shoulder = clavicle/upperarm), as the max over frames and the median frame;
  each chain's 8 points: the minimum signed distance to body or pieces per frame, the worst, which point.
Signed distance (clipmeasure.Surf): exact point-triangle, k nearest by centroid, sign from the nearest triangle's
normal, only within 15 mm (beyond, the sign is unreliable).
  python posed_clip.py RUN_DIR [RUN_DIR...]   (prints the report; --worst N lists the worst cases overall)"""
import sys, os, numpy as np
from scipy.spatial import cKDTree

def closest(p, a, b, c):
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den[den == 0] = 1e-12
    v = vb / den; w = vc / den
    res = a + ab * v[:, None] + ac * w[:, None]
    m = (d1 <= 0) & (d2 <= 0); res[m] = a[m]
    m = (d3 >= 0) & (d4 <= d3); res[m] = b[m]
    m = (d6 >= 0) & (d5 <= d6); res[m] = c[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-12, d1 - d3); res[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-12, d2 - d6); res[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-12, (d4 - d3) + (d5 - d6)); res[m] = (b + (c - b) * t[:, None])[m]
    return res

class Surf:
    def __init__(self, T):
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); l = np.linalg.norm(n, axis=1); ok = l > 1e-12
        self.T, self.N = T[ok], n[ok] / l[ok][:, None]; self.kd = cKDTree(self.T.mean(1)) if ok.any() else None
    def sd(self, P, k=12, reach=0.015):
        if self.kd is None: return np.full(len(P), np.inf)
        d, idx = self.kd.query(P, k=k, distance_upper_bound=reach + 0.02)
        best = np.full(len(P), np.inf); sgn = np.ones(len(P))
        for c in range(k):
            ok = np.isfinite(d[:, c]); ii = idx[ok, c]
            if not ok.any(): continue
            q = closest(P[ok], self.T[ii, 0], self.T[ii, 1], self.T[ii, 2])
            dist = np.linalg.norm(P[ok] - q, axis=1)
            better = dist < best[ok]
            s = np.sign(((P[ok] - q) * self.N[ii]).sum(1))
            bo = np.where(ok)[0][better]; best[bo] = dist[better]; sgn[bo] = s[better]
        return np.where(best < reach, best * sgn, np.inf)

REG = ("head", "neck", "back", "shoulder", "other")
def reg_of(n):
    return ("head" if n == "Head" or n.startswith("FACIAL") else "neck" if n.startswith("neck") else
            "back" if n.startswith("spine") or n == "pelvis" else "shoulder" if n.startswith(("clavicle", "upperarm")) else "other")

def load(run):
    S, B, C = [], {}, []
    for ln in open(os.path.join(run, "meta.txt")):
        f = ln.split()
        if f[0] == "S": S.append(dict(i=int(f[1]), kind=f[2], name=f[3], mat=f[4], n=int(f[5]), t=int(f[6]), cap=f[7] == "1", tie=f[8] == "1"))
        elif f[0] == "B": B[int(f[1])] = f[2]
        elif f[0] == "C": C.append(f[2])
    for s in S:
        if s["kind"] == "body":
            s["I"] = np.fromfile(os.path.join(run, f"s{s['i']:02d}.idx"), np.int32).reshape(-1, 3)
        else:
            a = np.fromfile(os.path.join(run, f"s{s['i']:02d}.attr"), np.float32).reshape(-1, 5)
            s["uvy"], s["uv2y"] = a[:, 0], a[:, 2]
            s["reg"] = np.array([reg_of(B.get(int(b), "?")) for b in a[:, 4].view(np.int32)])
    ks = sorted(f for f in os.listdir(run) if f.startswith("k") and f.endswith(".bin"))
    return S, C, ks

def target(s):
    return "body" if s["name"] == "Heroine" else "head" if s["name"] == "HeroineHead" else s["name"]

def measure(run):
    S, C, ks = load(run)
    hair = [s for s in S if s["kind"] == "hair" and not s["cap"]]
    groups = {"strands": [], "roots": [], "tie": []}
    # per frame: {(group, region, target): (n, n1, n3, worst_m)}
    frames, chainf = [], []
    for k in ks:
        raw = np.fromfile(os.path.join(run, k), np.float32)
        o = 1; pos = {}
        for s in S: pos[s["i"]] = raw[o:o + 3 * s["n"]].reshape(-1, 3).astype(np.float64); o += 3 * s["n"]
        ch = raw[o:].reshape(-1, 8, 3).astype(np.float64)
        HP = np.concatenate([pos[s["i"]] for s in hair]); uvy = np.concatenate([s["uvy"] for s in hair])
        reg = np.concatenate([s["reg"] for s in hair]); tie = np.concatenate([np.full(s["n"], s["tie"]) for s in hair])
        grp = np.where(tie, "tie", np.where(uvy < 0.1, "roots", "strands"))
        lo, hi = HP.min(0) - 0.05, HP.max(0) + 0.05
        res = {}; chd = []
        tsd = {}
        for s in S:
            if s["kind"] != "body": continue
            # (Godot's front faces wind clockwise: reversed to glTF's order, so the normals point out)
            T = pos[s["i"]][s["I"][:, [0, 2, 1]]]; c = T.mean(1); near = ((c > lo) & (c < hi)).all(1)
            if not near.any(): continue
            sf = Surf(T[near]); t = target(s)
            d = sf.sd(HP)
            tsd[t] = np.minimum(tsd.get(t, np.inf), d) if t in tsd else d
            if t != "head" and len(ch): chd.append(sf.sd(ch.reshape(-1, 3)))
        for t, d in tsd.items():
            for g in ("strands", "roots", "tie"):
                for r in REG:
                    m = (grp == g) & (reg == r)
                    if not m.any(): continue
                    x = d[m]; x = x[np.isfinite(x)]
                    res[(g, r, t)] = (int(m.sum()), int((x < -0.001).sum()), int((x < -0.003).sum()), float(-x.min()) if len(x) and x.min() < 0 else 0.0)
        frames.append(res)
        if chd:
            cd = np.min(np.array(chd), 0).reshape(len(ch), 8); chainf.append(cd)
    return S, C, ks, frames, chainf

def report(run, worst_list):
    S, C, ks, frames, chainf = measure(run)
    tag = os.path.basename(run.rstrip("/\\"))
    out = [f"== {tag}: {len(ks)} frames"]
    keys = sorted({k for f in frames for k in f}, key=lambda k: (("strands", "roots", "tie").index(k[0]), REG.index(k[1]), k[2]))
    for key in keys:
        vals = [f.get(key) for f in frames]; vals = [v for v in vals if v]
        n = vals[0][0]
        p1 = np.array([v[1] / n for v in vals]) * 100; p3 = np.array([v[2] / n for v in vals]) * 100; w = np.array([v[3] for v in vals]) * 1000
        if p1.max() == 0 and w.max() < 1: continue
        kw = int(np.argmax(w)); kp = int(np.argmax(p1))
        out.append(f"  {key[0]:7s} {key[1]:8s} {key[2]:20s} n={n:6d}  >1mm max {p1.max():5.2f}% (k{kp:02d}) med {np.median(p1):5.2f}%  "
                   f">3mm max {p3.max():5.2f}% med {np.median(p3):5.2f}%  worst {w.max():5.1f} mm (k{kw:02d}) med {np.median(w):4.1f}")
        worst_list.append((w.max(), tag, kw, key[0], key[1], key[2], p1[kw]))
    for ci, name in enumerate(C):
        if not chainf: break
        a = np.array([c[ci] for c in chainf])          # frames x 8 (signed, m; inf beyond 15 mm)
        mn = a.min(1); k = int(np.argmin(mn)); pt = int(np.argmin(a[k]))
        fin = np.isfinite(mn)
        out.append(f"  chain {name}: min signed {'clear >15' if not fin.any() else f'{mn[k]*1000:6.1f}'} mm"
                   + (f" (k{k:02d}, point {pt}); frames < 0: {int((mn < 0).sum())}/{len(mn)}, median {np.median(np.where(fin, mn, 0.015))*1000:.1f} mm" if fin.any() else ""))
    return out

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    nw = int(sys.argv[sys.argv.index("--worst") + 1]) if "--worst" in sys.argv else 0
    if nw: args = [a for a in args if a != str(nw)]
    W = []
    for r in args: print("\n".join(report(r, W)), flush=True)
    if "--tsv" in sys.argv:
        for w in W: print("WORST\t" + "\t".join(str(x) for x in w))
    if nw:
        print(f"== worst {nw}")
        for w in sorted(W, reverse=True)[:nw]: print(f"  {w[1]:22s} k{w[2]:02d} {w[3]:7s} {w[4]:8s} {w[5]:20s} {w[0]:5.1f} mm ({w[6]:.2f}% >1mm that frame)")
