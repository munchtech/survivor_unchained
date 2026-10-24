"""RETIRED (armor 17 N3): no longer in heroine_body_post's chain. A max judge (OJ1) failed both steps: the caps' dome
was her own deltoid (a thinner shell could not fix it) and the notch still showed. heroine_outfits.py now cuts both
right at the source (CAP_TOP / CAP_LIFT / CAP_THICK, KEEP_SYM). Kept for its measures.

The arcanist top's shoulder caps fitted and its collar made even (armor 16 N1, 22 October 2026; max judges J4/J5/A2
at the close-up: "the cap sleeves read as inflated pads"; "a small notch in the neckline, screen-left of her throat").

Two post-steps on the built outfit gltf, in place, each with its done-mark in the asset extras (a marked file is
skipped; --force runs it again on purpose). Every arcanist.top.* mesh (the leather shell and the riders on it: stitching,
binding) is moved by the same field, so the riders stay on the leather; normals are carried as bust_shell_post does.

  caps ("arc_caps"): the leather over each deltoid stood ~6 mm off her skin (inner face ~3.2 mm, outer ~6 mm, the
    built lift 3.5 mm plus a 2.8 mm shell) with its hem a thick 6 mm lip over her arm: at the close-up it read as a
    padded sleeve. Over the cap (her skin's upper-arm weight, CAP_W) each point's offset along her skin normal g goes to
    CAP_A + CAP_B * g (inner ~1.0 mm, outer ~3.0 mm: a 2 mm leather hugging her), and closer still at the hem
    (HEM_A, HEM_B within HEM_R of the cap's lower edge: its lip ~2.4 mm); never closer than MIN_GAP over her tucked skin.
  collar ("arc_collar"): the high collar's top edge on her right ran up to 2.5 cm lower than her left's over the front
    of her neck (the leather's cut there follows her Head weight, which is higher on her right side of the neck), so the
    V's edge on her right turned out early: a step at the collar's corner. Her right's collar is stretched up (and at the
    back down, where it ran 1 cm higher) to her left's mirror: round the neck axis, a point at angle t and height y
    goes to Y0 + (y - Y0) * k(t), k = (topL(t) - Y0) / (topR(t) - Y0) (each side's top edge, smoothed), and back onto her
    skin at its own offset (its height on the neck slides; the shell's thickness is kept). Faded out past COLLAR_R from
    the neck axis.

Order in heroine_body_post: after heroine_arm_shape (both read her final skin), before the LODs.

    python tools/assets/arc_fit_post.py <art dir> [--force] [--only caps|collar]
"""
import os
import struct
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl  # noqa: E402
from breast_sym_post import _vn, _closest_tri  # noqa: E402
from bust_shell_post import _normals  # noqa: E402

OUTFIT = "arcanist"
PREFIX = "arcanist.top."
SHELL = "arcanist.top.plumleather"
TUCK = "armor_tuck/arcanist.top.bin"
CAP_MARK, COLLAR_MARK = "arc_caps", "arc_collar"
# caps
CAP_W = (0.25, 0.60)      # her skin's upper-arm weight (upperarm, its twist and share bones): 0 -> 1 over this
CAP_A, CAP_B = float(os.environ.get("ARC_CAP_A", "-0.00129")), float(os.environ.get("ARC_CAP_B", "0.714"))
HEM_A, HEM_B = float(os.environ.get("ARC_HEM_A", "-0.0016")), float(os.environ.get("ARC_HEM_B", "0.65"))
HEM_R = (0.006, 0.020)    # full hem mapping within HEM_R[0] of the cap's lower edge, easing to the cap's by HEM_R[1]
MIN_GAP = 0.0010          # the inner face's least gap over her tucked skin
# collar
NECK_C = (0.0, -0.035)    # the neck axis (x, z)
Y0 = 1.50                 # the stretch's foot
COLLAR_R = (0.100, 0.125)  # full within COLLAR_R[0] of the neck axis, none past COLLAR_R[1]
THETA = (32.0, 150.0)     # angles round the neck the map covers (0 front, 90 side), eased over 6 deg at each end


def _skin(art):
    """Her rest skin (body and the neck graft: node Heroine), points, normals, tree, arm weights per side, and the
    tucked skin's points (the arcanist top's armor_tuck record, 10 mm x the mark as her shader draws it)."""
    H = _Gl(os.path.join(art, "heroine.glb"))
    g = H.g
    nd = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    names = [g["nodes"][j]["name"] for j in g["skins"][nd["skin"]]["joints"]]
    Vs, Fs, Ws, off = [], [], [], 0
    for p in g["meshes"][nd["mesh"]]["primitives"]:
        if g["materials"][p["material"]].get("name") == "skin_head":
            continue
        V = H.get(p["attributes"]["POSITION"]).astype(float)
        F = H.get(p["indices"]).reshape(-1, 3).astype(int)
        J = H.get(p["attributes"]["JOINTS_0"]).astype(int)
        W = H.get(p["attributes"]["WEIGHTS_0"]).astype(float)
        if W.max() > 1.5:
            W = W / W.sum(1, keepdims=True)
        arm = {}
        for sd in "lr":
            ks = [i for i, n in enumerate(names) if n in (f"upperarm_{sd}", f"upperarm_share_{sd}") or (n.startswith("upperarm_twist_") and n.endswith("_" + sd))]   # (twist_01, or her whole chain: helpers twist_chain)
            arm[sd] = (np.isin(J, ks) * W).sum(1)
        Vs.append(V); Fs.append(F + off); Ws.append(np.c_[arm["l"], arm["r"]]); off += len(V)
    B, F, AW = np.concatenate(Vs), np.concatenate(Fs), np.concatenate(Ws)
    # (welded by place, so a seam's copies share a normal)
    _, first, wid = np.unique(np.round(B * 1e6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    wid = wid.ravel()
    U = B[first]
    FU = wid[F]
    FU = FU[(FU[:, 0] != FU[:, 1]) & (FU[:, 1] != FU[:, 2]) & (FU[:, 2] != FU[:, 0])]
    N = _vn(U, FU)
    AWU = np.zeros((len(U), 2)); AWU[wid] = AW
    T = None
    pth = os.path.join(art, TUCK)
    if os.path.isfile(pth):
        raw = open(pth, "rb").read()
        n = struct.unpack("<I", raw[:4])[0]
        rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("k", "<i4", 3), ("t", "<f4")])
        d = {tuple(int(v) for v in r["k"]): float(r["t"]) for r in rec}
        t = np.array([d.get(tuple(k), 0.0) for k in np.round(U * 1e5).astype(np.int64)])
        t = np.round(np.clip(t, 0, 1) * 255) / 255
        Tp = U - (0.010 * np.where(t > 0.973, 1.0, t))[:, None] * N
        keep = t < 0.995
        T = (Tp[keep], N[keep], cKDTree(Tp[keep]))
    return U, N, cKDTree(U), AWU, T, FU


def _off(X, U, N, tree):
    _, j = tree.query(X)
    return ((X - U[j]) * N[j]).sum(1), j


def _prims(G):
    return [(m["name"], m["primitives"][0]) for m in G.g["meshes"] if m["name"].startswith(PREFIX)]


def _apply(G, moves, tag):
    big = 0.0
    for name, pr in _prims(G):
        if name not in moves:
            continue
        P0 = G.get(pr["attributes"]["POSITION"]).astype(float)
        P1 = moves[name]
        moved = np.linalg.norm(P1 - P0, axis=1) > 1e-7
        if not moved.any():
            continue
        G.put(pr["attributes"]["POSITION"], P1.astype(np.float32))
        if "NORMAL" in pr["attributes"]:
            G.put(pr["attributes"]["NORMAL"], _normals(G, pr, P0, P1, moved).astype(np.float32))
        Pf = G.get(pr["attributes"]["POSITION"]).astype(float)
        a = G.g["accessors"][pr["attributes"]["POSITION"]]
        a["min"], a["max"] = Pf.min(0).tolist(), Pf.max(0).tolist()
        mm = float(np.linalg.norm(P1 - P0, axis=1).max())
        big = max(big, mm)
        print("%s:   %s: %d points moved, largest %.2f mm" % (tag, name, int(moved.sum()), mm * 1000))
    return big


def caps(G, sk):
    U, N, tree, AW, T = sk[:5]
    P = G.get(dict(_prims(G))[SHELL]["attributes"]["POSITION"]).astype(float)
    # the hem: the binding and its stitching (the riders) over the cap lie only along its lower edge
    hp = []
    for name, prm in _prims(G):
        if name in (PREFIX + "darkpurple", PREFIX + "thread"):
            X = G.get(prm["attributes"]["POSITION"]).astype(float)
            _, jx = tree.query(X)
            hp.append(X[AW[jx, (X[:, 0] < 0).astype(int)] > 0.4])
    hem_pts = np.concatenate(hp) if hp else P[:0]
    moves = {}
    for name, prm in _prims(G):
        X = G.get(prm["attributes"]["POSITION"]).astype(float)
        _, jx = tree.query(X)
        awx = AW[jx, (X[:, 0] < 0).astype(int)]
        w = np.clip((awx - CAP_W[0]) / (CAP_W[1] - CAP_W[0]), 0, 1)
        w = w * w * (3 - 2 * w)
        sel = w > 0
        if not sel.any():
            continue
        g, jj = _off(X[sel], U, N, tree)
        if len(hem_pts):
            dh, _ = cKDTree(hem_pts).query(X[sel])
            h = np.clip((HEM_R[1] - dh) / (HEM_R[1] - HEM_R[0]), 0, 1)
        else:
            h = np.zeros(sel.sum())
        a_ = CAP_A + (HEM_A - CAP_A) * h
        b_ = CAP_B + (HEM_B - CAP_B) * h
        g1 = a_ + b_ * g
        dg = (g1 - g) * w[sel]
        Y = X.copy()
        Y[sel] = X[sel] + dg[:, None] * N[jj]
        if T is not None and name == SHELL:
            # (never closer than MIN_GAP over her tucked skin)
            Tp, TN, tt = T
            _, k = tt.query(Y[sel])
            gt = ((Y[sel] - Tp[k]) * TN[k]).sum(1)
            push = np.maximum(MIN_GAP - gt, 0) * (gt < 0.004)
            Y[sel] += push[:, None] * TN[k]
        moves[name] = Y
    return moves


def _closest(X, U, FU, tree, inc, k=8):
    """Each point's closest point on her skin's triangles (those round its k nearest skin points)."""
    _, jj = tree.query(X, k=k)
    best = np.full(len(X), np.inf)
    C = X.copy()
    for col in range(k):
        for slot in range(8):
            ts = np.array([inc[j][slot] if slot < len(inc[j]) else inc[j][0] for j in jj[:, col]])
            c = _closest_tri(X, U[FU[ts]])
            d = np.linalg.norm(X - c, axis=1)
            b = d < best
            best[b], C[b] = d[b], c[b]
    return C, best


def _theta(X):
    return np.degrees(np.arctan2(np.abs(X[:, 0] - NECK_C[0]), X[:, 2] - NECK_C[1]))


def _rad(X):
    return np.hypot(X[:, 0] - NECK_C[0], X[:, 2] - NECK_C[1])


def collar(G, sk):
    U, N, tree = sk[:3]
    FU = sk[5]
    inc = [[] for _ in range(len(U))]
    for t_, f_ in enumerate(FU):
        for v_ in f_:
            inc[v_].append(t_)
    pr = dict(_prims(G))[SHELL]
    P = G.get(pr["attributes"]["POSITION"]).astype(float)
    th, r = _theta(P), _rad(P)
    bins = np.arange(20.0, 172.0, 2.0)
    tops = {}
    for s, sd in ((1, "l"), (-1, "r")):
        tp = np.full(len(bins), np.nan)
        for i, b in enumerate(bins):
            k = (P[:, 0] * s > 0) & (th >= b) & (th < b + 2) & (r < 0.10) & (P[:, 1] > Y0)
            if k.any():
                tp[i] = P[k, 1].max()
        ok = ~np.isnan(tp)
        tp = np.interp(np.arange(len(bins)), np.nonzero(ok)[0], tp[ok])
        tops[sd] = gaussian_filter1d(tp, float(os.environ.get("ARC_COLLAR_SMOOTH", "3.0")), mode="nearest")
    k_ = (tops["l"] - Y0) / np.maximum(tops["r"] - Y0, 0.005)
    print("ARC_COLLAR: top edge left - right (mm) by angle:",
          " ".join("%d:%+.0f" % (b, (tops["l"][i] - tops["r"][i]) * 1000) for i, b in enumerate(bins) if i % 4 == 0))
    def kf(t):
        return np.interp(t, bins + 1.0, k_)
    moves = {}
    for name, prm in _prims(G):
        X = G.get(prm["attributes"]["POSITION"]).astype(float)
        t, rr = _theta(X), _rad(X)
        w = np.clip((COLLAR_R[1] - rr) / (COLLAR_R[1] - COLLAR_R[0]), 0, 1)
        w *= np.clip((t - THETA[0]) / 6.0, 0, 1) * np.clip((THETA[1] - t) / 6.0, 0, 1)
        w *= (X[:, 0] < -0.002) * (X[:, 1] > Y0)
        sel = w > 0
        if not sel.any():
            continue
        Xs = X[sel]
        C0, g = _closest(Xs, U, FU, tree, inc)
        y1 = Y0 + (Xs[:, 1] - Y0) * kf(t[sel])
        Y = Xs.copy()
        Y[:, 1] = Xs[:, 1] + (y1 - Xs[:, 1]) * w[sel]
        # (back onto her skin at its own distance, along the line from her closest point: the shell's thickness and
        # the riders' height kept)
        for _ in range(3):
            C1, _ = _closest(Y, U, FU, tree, inc)
            dv = Y - C1
            Y = C1 + dv / np.maximum(np.linalg.norm(dv, axis=1, keepdims=True), 1e-9) * g[:, None]
        Z = X.copy()
        Z[sel] = Y
        moves[name] = Z
    return moves


def run(art, force=False, only=None):
    path = os.path.join(art, f"heroine_outfit_{OUTFIT}.gltf")
    G = _Gl(path)
    ex = G.g.setdefault("asset", {}).setdefault("extras", {})
    sk = None
    done = []
    for mark, fn, tag in ((COLLAR_MARK, collar, "ARC_COLLAR"), (CAP_MARK, caps, "ARC_CAPS")):
        if only and not mark.endswith(only):
            continue
        if ex.get(mark) is not None and not force:
            print("%s: %s has had it" % (tag, os.path.basename(path)))
            continue
        sk = sk or _skin(art)
        # (the collar's map in three passes: each reads both top edges again, so her right's meets her left's)
        big = 0.0
        for _ in range(int(os.environ.get("ARC_COLLAR_PASSES", "2")) if mark == COLLAR_MARK else 1):
            big = max(big, _apply(G, fn(G, sk), tag))
        ex[mark] = round(big * 1000, 3)
        done.append(mark)
    if done:
        G.save()
    return done


if __name__ == "__main__":
    a = sys.argv[1:]
    art = next((x for x in a if not x.startswith("--") and x not in ("caps", "collar")), "godot/art/people")
    run(art, "--force" in a, a[a.index("--only") + 1] if "--only" in a else None)
