"""fold_probe: how deep a crease is along a set of points, on any surface against a reference surface (measure only).

Core (no names): `dihedral` (signed fold angle per mesh edge, valley +), `depth` (mm a point lies under the mean of its
ring `k` rows away, along its normal: valley +), `rows_from`, `edge_ratio`. Surfaces are [points, 3] on one triangle set.

  python tools/body/fold_probe.py dump  POSES TAG      her: published / composed / A carried on every model point
                                                        -> out/shoulder/fold_probe/dump_TAG.npz (+ adj.npz), ~30 s
                                                        --today: her config without its further gate stages (gate2 ...)
  python tools/body/fold_probe.py measure TAG [--k 3] [--top 12] [--side l] [--ref TAG0]
                                                        --ref: the fold set and "B" from dump TAG0 (today), TAG's composed as "new"
  python tools/body/fold_probe.py sweep TAG0 [--rows 14,16,20,all] [--wall 12] [--smooth 0,60] [--ramp 1,0] [--deg 90,130]
                                                        a further gate stage on a dump of today: the REAL share
                                                        (carried_target.support_region), the surface recomposed
  python tools/body/fold_probe.py same NEW.npz OLD.npz  two stored targets (carried_target target): max |new - old| on the
                                                        composed points they share, per pose, by the arm's elevation
Facts: docs/handoff/body_facts/chest_fold.md
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
OUTD = HERE / "out" / "shoulder" / "fold_probe"


def s01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def rows_from(adj, m):
    """[n] rows (graph steps) from the set m (0 on it; n where unreachable)."""
    n = adj.shape[0]
    d = np.where(m, 0, n)
    f, k = np.asarray(m, bool).copy(), 0
    while True:
        g = (adj @ f > 0) & (d == n)
        if not g.any():
            return d
        k += 1
        d[g] = k
        f = g


def normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for j in range(3):
        np.add.at(N, T[:, j], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-30), fn


def dihedral(V, T):
    """(edges [m, 2], deg [m]): the angle between the two triangles of each inner edge, + where they make a valley."""
    fn = normals(V, T)[1]
    fn = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-30)
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    opp = np.concatenate([T[:, 2], T[:, 0], T[:, 1]])
    tri = np.tile(np.arange(len(T)), 3)
    key = e[:, 0].astype(np.int64) * (V.shape[0] + 1) + e[:, 1]
    o = np.argsort(key, kind="stable")
    same = np.nonzero(key[o][1:] == key[o][:-1])[0]
    a, b = o[same], o[same + 1]
    ang = np.degrees(np.arccos(np.clip((fn[tri[a]] * fn[tri[b]]).sum(1), -1, 1)))
    return e[a], ang * np.sign((fn[tri[a]] * (V[opp[b]] - V[opp[a]])).sum(1))


def ring(adj, k):
    """Sparse [n, n]: the points exactly k rows from each point."""
    A = (adj + sp.identity(adj.shape[0], format="csr")).astype(bool).astype(np.float32)
    R, prev = A, None
    for _ in range(k - 1):
        prev, R = R, ((R @ A) > 0).astype(np.float32)
    return R if prev is None else (R - prev).tocsr()


def depth(V, T, R):
    """[n] mm: how far each point lies under the mean of its ring R (ring(adj, k)), along its own normal (valley +)."""
    c = (R @ V) / np.maximum(np.asarray(R.sum(1)), 1)
    return (((c - V) * normals(V, T)[0]).sum(1)) * 1000.0


def edge_ratio(V, V0, E):
    return np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1), 1e-12)


def mesh_of(Z, adj, k):
    """What every pose of a dump shares: triangles, rest, edges, the ring, the rest's depth and fold angles."""
    T, V0 = Z["T"], Z["V0"]
    R = ring(adj, k)
    ee, a0 = dihedral(V0, T)
    parts = [str(x) for x in Z["parts"]]
    return NS(T=T, V0=V0, adj=adj, n=len(V0), R=R, E=np.stack(sp.triu(adj, 1).nonzero(), 1), d0=depth(V0, T, R), ee=ee, a0=a0,
              parts=parts, part=Z["part"], br=Z["part"] == parts.index("breast"))


def pose_ctx(Z, M, nm, s, top):
    """One pose of a dump: the surfaces B (composed), A (carried at share 1), pub; the share; the side's own gated
    part; the fold set `cl` (see the facts file) and its edges `m`."""
    n = M.n
    sd = s if nm[-2:] not in (":l", ":r") else nm[-1]
    gl = f"girdle_{sd}"
    rp, lst, dg, dw = Z[f"rp_{gl}"], Z[f"list_{sd}"], Z[f"dg_{sd}"], Z[f"dwall_open_{sd}"]
    pub, comp = Z[f"{nm}|pub"], Z[f"{nm}|comp"]
    Dw = np.where(Z[f"{nm}|wok"][:, None], Z[f"{nm}|Dw"], 0.0)
    Dw[rp] = Z[f"{nm}|D|{gl}"]                      # A carried, share 1: the region's own carrier on its points
    sh = np.zeros(n)
    sh[rp] = Z[f"{nm}|share|{gl}"]
    own = M.br & (dg <= Z[f"dg_{'r' if sd == 'l' else 'l'}"])
    el = float(Z[f"{nm}|elev"]["lr".index(sd)])
    S = {"B": comp, "A": pub + Dw, "pub": pub}
    zone = (own | ((sh > 0) & (sh < 1))) & (rows_from(M.adj, own) <= 14) & (rows_from(M.adj, np.isin(np.arange(n), lst)) <= 14)
    dd = {a: depth(V, M.T, M.R) - M.d0 for a, V in S.items()}
    f = np.where(zone, dd["B"] - dd["A"], -1e9)
    ids = np.argsort(-f)[:top]
    cl = zone & (f > 0.5 * f[ids[0]]) & (rows_from(M.adj, np.isin(np.arange(n), ids[:1])) <= 12)
    return NS(nm=nm, sd=sd, gl=gl, rp=rp, lst=lst, dg=dg, dw=dw, pub=pub, comp=comp, Dw=Dw, sh=sh, own=own, el=el, S=S, zone=zone,
              dd=dd, ids=ids, cl=cl, m=cl[M.ee].all(1))


def stats(M, c, V, ramp):
    """(fold depth mean, max mm; valley angle over rest on the fold's edges mean, max deg; worst edge ratio on `ramp`)."""
    d = depth(V, M.T, M.R) - M.d0
    da_ = dihedral(V, M.T)[1] - M.a0
    return (float(d[c.cl].mean()), float(d[c.cl].max()), float(da_[c.m].mean()) if c.m.any() else 0.0,
            float(da_[c.m].max()) if c.m.any() else 0.0, float(edge_ratio(V, M.V0, M.E)[ramp].max()))


def cmd_measure(argv):
    tag = argv[0]
    opt = dict(zip(argv[1::2], argv[2::2]))
    k, top, s = int(opt.get("--k", 3)), int(opt.get("--top", 12)), opt.get("--side", "l")
    Zn = np.load(OUTD / f"dump_{tag}.npz")
    Z = np.load(OUTD / f"dump_{opt['--ref']}.npz") if "--ref" in opt else Zn
    adj = sp.load_npz(OUTD / "adj.npz")
    M = mesh_of(Z, adj, k)
    T, V0, part, parts, n, E = M.T, M.V0, M.part, M.parts, M.n, M.E
    for nm in [str(x) for x in Zn["names"]]:
        if f"{nm}|comp" not in Z:
            continue
        c = pose_ctx(Z, M, nm, s, top)
        sd, gl, rp, lst, dg, dw, pub, comp, Dw, sh, own, el, S, dd, ids, cl = (c.sd, c.gl, c.rp, c.lst, c.dg, c.dw, c.pub, c.comp, c.Dw,
                                                                              c.sh, c.own, c.el, c.S, c.dd, c.ids, c.cl)
        shn = sh
        if Zn is not Z:                              # the build under test against today's dump
            S["new"] = Zn[f"{nm}|comp"]
            shn = np.zeros(n)
            shn[Zn[f"rp_{gl}"]] = Zn[f"{nm}|share|{gl}"]
        # candidates: the wall standing back R rows (second gate stage), ramp W rows; (c) the ramp's share diffused
        for lab, Rw, W in (("a:wall back 14", 14, 12), ("a:wall back 20", 20, 12), ("a:no wall", 10 ** 6, 12), ("b:ramp 20", 8, 20)) if Zn is Z else ():
            w = s01(rows_from(adj, own & (dg >= Rw)) / W) if (own & (dg >= Rw)).any() else np.ones(n)
            w = np.where(own | (sh > 0), np.where(own, w, np.maximum(sh, np.minimum(w, np.where(sh > 0, 1, 0)) * (sh >= s01(dw / 12) - 1e-9) + sh * (sh < s01(dw / 12) - 1e-9))), 0.0)
            S[lab] = comp + (w - sh)[:, None] * Dw
        if Zn is Z:
            w = sh.copy()
            mv = own | ((sh > 0) & (sh < 1) & (dw <= 12))
            P = sp.diags(1.0 / np.maximum(np.asarray(adj.sum(1)).ravel(), 1)) @ adj
            for _ in range(60):
                w = np.where(mv, P @ w, sh)
            S["c:diffused"] = comp + (w - sh)[:, None] * Dw
        dd = {a: depth(V, T, M.R) - M.d0 for a, V in S.items()}
        print(f"\n== {nm} side {sd} elev {el:.0f}: fold = the points of the zone where B's depth over A's is at least half the worst, within 12 rows of it: {int(cl.sum())} points")
        print("  id      part      share rows:list wall | depth-rest mm (k=%d): B   A   pub | carry-pub mm: normal tangent" % k)
        Np = normals(pub, T)[0]
        for i in ids:
            dn = float(Dw[i] @ Np[i]) * 1000
            print(f"  {i:6d} {parts[part[i]]:9s} {sh[i]:5.2f} {dg[i]:4d} {dw[i]:4d} | {dd['B'][i]:6.2f} {dd['A'][i]:6.2f} {dd['pub'][i]:6.2f} | {dn:6.1f} {np.sqrt(max(Dw[i] @ Dw[i] * 1e6 - dn * dn, 0)):6.1f}")
        ee, a0 = M.ee, M.a0
        ramp = ((sh[E] > 0) & (sh[E] < 1)).any(1) | own[E].any(1) | ((shn[E] > 0) & (shn[E] < 1)).any(1)
        reg = (np.maximum(sh, shn)[E] > 0).any(1) | own[E].any(1)
        print("  surface          fold depth mean / max mm | valley angle over rest, fold edges mean / max deg | worst edge ratio on ramp + breast rows | edges over 2.5x in the region + part")
        for a, V in S.items():
            st = stats(M, c, V, ramp)
            print(f"  {a:16s} {st[0]:6.2f} {st[1]:6.2f} | {st[2]:6.1f} {st[3]:6.1f} | {st[4]:5.2f} | {int((edge_ratio(V, V0, E)[reg] > 2.5).sum()):3d}  moved off B max {np.linalg.norm(V - comp, axis=1).max() * 1000:5.1f} mm")
        up = np.argmax(V0.max(0) - V0.min(0))
        print("  A's lift over published on the own breast part, by rows from the list (mean mm along the long axis | |carry-pub| mean | share mean (new)):")
        print("   " + "  ".join(f"r{r}: {Dw[own & (dg == r)][:, up].mean() * 1000:.1f}|{np.linalg.norm(Dw[own & (dg == r)], axis=1).mean() * 1000:.1f}|{sh[own & (dg == r)].mean():.2f} ({shn[own & (dg == r)].mean():.2f})" for r in (1, 2, 4, 6, 8, 10, 14, 20, 26) if (own & (dg == r)).any()))
        # the pinch: the sharpest valley edge of B inside the list, the same edge on A carried and published
        dB, dA, dP = (dihedral(S[a], T)[1] for a in ("B", "A", "pub"))
        inl = np.isin(ee, lst).all(1)
        j = np.argsort(-np.where(inl, dB, -1e9))[:3]
        print("  pinch (sharpest valley edges in the list): " + "; ".join(f"edge {tuple(ee[x])} share {sh[ee[x]].min():.2f} B {dB[x]:.0f} A {dA[x]:.0f} pub {dP[x]:.0f} rest {a0[x]:.0f} deg" for x in j))
        print(f"  list valley edges over 60 deg: B {int((dB[inl] > 60).sum())}, A {int((dA[inl] > 60).sum())}, pub {int((dP[inl] > 60).sum())}; over 90: B {int((dB[inl] > 90).sum())}, A {int((dA[inl] > 90).sum())}")


def cmd_sweep(argv):
    """A further gate stage tried on a dump of TODAY (dump ... --today): the stage's real share from
    carried_target.support_region, blended by the pose's elevation as region_target.Model.blend does, the surface
    recomposed as comp + (share - today's share) x the unshared delta (the dump's wide carrier off today's region)."""
    sys.path.insert(0, str(HERE))
    import carried_target as ct
    tag = argv[0]
    opt = dict(zip(argv[1::2], argv[2::2]))
    k = int(opt.get("--k", 3))
    Z = np.load(OUTD / f"dump_{tag}.npz")
    adj = sp.load_npz(OUTD / "adj.npz")
    M = mesh_of(Z, adj, k)
    sup, s0, tw, n = json.loads(str(Z["sup"])), str(Z["s0"]), Z["tw"], M.n
    core = np.isin(np.arange(n), Z[f"list_{s0}"])
    own0 = M.br & (Z[f"dg_{s0}"] <= Z[f"dg_{'r' if s0 == 'l' else 'l'}"])
    lo2, hi2 = (float(x) for x in opt.get("--deg", "90,130").split(","))
    names = [str(x) for x in Z["names"]]
    ctx = {nm: pose_ctx(Z, M, nm, "l", 12) for nm in names}
    print("pose (elevation; fold points): depth mean / max mm, valley angle max deg, worst edge on ramp + part, edges over 2.5x in region + part")
    for nm, c in ctx.items():
        ramp = ((c.sh[M.E] > 0) & (c.sh[M.E] < 1)).any(1) | c.own[M.E].any(1)
        reg = (c.sh[M.E] > 0).any(1) | c.own[M.E].any(1)
        for a in ("B", "A"):
            st = stats(M, c, c.S[a], ramp)
            print(f"  {nm:24s} ({c.el:3.0f}; {int(c.cl.sum()):2d}) {a}: {st[0]:5.2f} / {st[1]:5.2f}, {st[3]:5.1f}, {st[4]:4.2f}, {int((edge_ratio(c.S[a], M.V0, M.E)[reg] > 2.5).sum())}")
    print("\nrows wall smooth ramp | " + " | ".join(f"{nm} g2 {float(s01((c.el - lo2) / (hi2 - lo2))):.2f}" for nm, c in ctx.items()))
    for N in opt.get("--rows", "14,16,20,all").split(","):
        for W in opt.get("--wall", "12").split(","):
            for K in opt.get("--smooth", "0,60").split(","):
                for rmp in opt.get("--ramp", "1").split(","):
                    st2 = {"rows": own0 if N == "all" else int(N), "wall_rows": int(W), "smooth": int(K), "ramp": rmp == "1"}
                    ids, closed, shares, n1 = ct.support_region(adj, Z["sr_moved"], core, Z["sr_stiff"], M.br, sup["rows"], sup["ring"],
                                                                sup["gate_rows"], sup["wall_rows"], [st2])
                    A = np.zeros((3, n))
                    A[:, ids] = closed, *shares
                    cells = []
                    for nm, c in ctx.items():
                        C, O, S2 = A if c.sd == s0 else A[:, tw]
                        g = float(s01((c.el - sup["gate_deg"][0]) / (sup["gate_deg"][1] - sup["gate_deg"][0])))
                        b = (1 - g) * C + g * O
                        err = float(np.abs(b - c.sh).max())                       # stage 1 = the dump's share
                        g2 = float(s01((c.el - lo2) / (hi2 - lo2))) if c.el > lo2 else 0.0
                        b = (1 - g2) * b + g2 * S2
                        V = c.comp + (b - c.sh)[:, None] * c.Dw
                        ramp = ((c.sh[M.E] > 0) & (c.sh[M.E] < 1)).any(1) | c.own[M.E].any(1) | ((b[M.E] > 0) & (b[M.E] < 1)).any(1)
                        reg = (np.maximum(b, c.sh)[M.E] > 0).any(1) | c.own[M.E].any(1)
                        st = stats(M, c, V, ramp)
                        cells.append(f"{st[0]:5.2f}/{st[1]:5.2f} {st[3]:5.1f} {st[4]:4.2f} {int((edge_ratio(V, M.V0, M.E)[reg] > 2.5).sum()):2d}" + ("" if err < 1e-9 else f" !stage1 {err:.1e}"))
                    print(f"{N:>4s} {W:>4s} {K:>6s} {rmp:>4s} | " + " | ".join(cells) + f" | +{len(ids) - n1} points", flush=True)


def cmd_same(argv):
    new, old = (np.load(a if Path(a).is_absolute() or Path(a).exists() else HERE / "out" / "shoulder" / a, allow_pickle=False) for a in argv[:2])
    io = {str(x): i for i, x in enumerate(old["name"])}
    common, ia, ib = np.intersect1d(new["ids_c"], old["ids_c"], return_indices=True)
    info = json.loads(str(new["info"]))
    print(f"composed points: new {len(new['ids_c'])}, old {len(old['ids_c'])}, shared {len(common)}")
    for i, nm in enumerate(str(x) for x in new["name"]):
        if nm not in io:
            print(f"{nm:28s} not in the old file")
            continue
        d = np.abs(new["Xc"][i][ia] - old["Xc"][io[nm]][ib]).max(1)
        dl = np.abs(new["X"][i] - old["X"][io[nm]]).max()
        print(f"{nm:28s} elev {info[i]['elev']:6.1f}  max |new - old| {d.max() * 1000:.6g} mm (exactly 0: {bool(d.max() == 0)}), points moved {int((d > 0).sum())}; the list's X {dl * 1000:.6g} mm")


def cmd_dump(argv):
    """HER (carried_target.Her): for each pose, on every model point: published, composed, each region's unshared delta and
    share, and A carried by a plain wide carrier under the side's girdle part pose (Dw; wok: where it found A)."""
    import time
    sys.path.insert(0, str(HERE))
    import carried_target as ct
    OUTD.mkdir(parents=True, exist_ok=True)
    import copy
    import re
    names = argv[0].split(",")
    t = time.time()
    hc = copy.deepcopy(ct.HER)
    if "--today" in argv:                               # her config without its further gate stages
        for rc in hc["regions"].values():
            for kk in [x for x in rc.get("support", {}) if re.fullmatch(r"gate\d+", x)]:
                del rc["support"][kk]
    h = ct.Her(hc, verbose=False)
    md, bd, Ab, cfg = h.md, h.bd, h.Ab, h.cfg
    F = md.first
    print("her", round(time.time() - t, 1), "s; md.n", md.n, "V0", len(bd.V0), "src", len(md.src), flush=True)
    z = np.load(h.OUT / "poses.npz")
    ix = {str(n): i for i, n in enumerate(z["name"])}
    print("mirror poses present:", [n for n in ("x:abd150:r", "x:abd170:r", "x:flex170:r") if n in ix])
    wide = ct.Carrier(Ab.V0, Ab.T, bd.V0[F], h.N0[F], rad=cfg["rad"], k=cfg["k"], nw=cfg["nw"], pocket_rows=0)
    print("wide not ok", int((~wide.ok).sum()), flush=True)
    ibm = bd.p.skel.ibm
    out = {"names": np.array(names)}
    # static
    T = md.src[bd.T[(bd.T < len(md.src)).all(1)]]
    T = T[(T >= 0).all(1)]
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    out["T"] = T
    out["V0"] = bd.V0[F]
    out["part"] = md.part
    out["parts"] = np.array(md.parts)
    out["tw"] = md.tw
    sup = cfg["regions"]["girdle_{s}"]["support"]
    gate = md.part == md.parts.index(sup["gated_part"])
    s0 = min(cfg["sides"])                              # support_region's inputs (Her.grow), for `sweep`
    MP, MA = h.motion("girdle_{s}", sup)
    j = bd.p.index[sup["stiff"].replace("{s}", s0)]
    out["sr_moved"] = (MP > sup["eps_mm"]) | (MA > sup["eps_mm"])
    out["sr_stiff"] = (bd.W[F] * np.isin(bd.J[F], sorted(set(bd.p.subtree(j)) | {j}))).sum(1) >= sup["rigid"]
    out["s0"], out["sup"] = np.array(s0), np.array(json.dumps(sup))
    for s in "lr":
        core = np.zeros(md.n, bool)
        core[md.S[s]["ids"]] = True
        out[f"list_{s}"] = md.S[s]["ids"]
        out[f"new_{s}"] = h.ext[s]
        out[f"closed_{s}"] = md.grown[s]["closed"]
        out[f"opened_{s}"] = md.grown[s]["opened"]
        dg = ct.rows_from(md.adj, core)
        out[f"dg_{s}"] = dg
        out[f"dwall_open_{s}"] = ct.rows_from(md.adj, gate & (dg >= sup["gate_rows"]))
        out[f"dwall_shut_{s}"] = ct.rows_from(md.adj, gate)
        out[f"beta_{s}"] = md.beta
    for n, rg in h.regions.items():
        k = md.src[np.minimum(rg.pts, len(md.src) - 1)]
        k = np.where(rg.pts < len(md.src), k, -1)
        out[f"rp_{n}"] = k                      # md point of each region point (-1: outside the model)
    sp.save_npz(OUTD / "adj.npz", sp.csr_matrix(md.adj))
    for nm in names:
        i = ix[nm]
        G, s = z["G"][i], str(z["side"][i])
        Vp = h.rt.published(bd, G)
        X = h.compose(G, Vp)
        out[f"{nm}|pub"] = Vp[F]
        out[f"{nm}|comp"] = X[F]
        out[f"{nm}|elev"] = np.array([md.elevation(G, "l"), md.elevation(G, "r")])
        for n, rg in h.regions.items():
            P = h.part(G, n)
            out[f"{nm}|D|{n}"] = np.einsum("nij,nj->ni", P["M"], P["cf"] - P["Pg"])      # unshared delta (filled carry)
            out[f"{nm}|Dr|{n}"] = np.einsum("nij,nj->ni", P["M"], P["cr"] - P["Pg"])     # carry alone
            out[f"{nm}|share|{n}"] = rg.share_at(G)
        # A's girdle deformation on EVERY md point (wide plain carrier), the side's girdle part pose
        rg = h.regions[cfg["out_region"].replace("{s}", s)]
        P = h.part(G, rg.name)
        cw = wide.carry(P["Va"])
        Pg = h.rt.published(bd, P["Gr"])[F]
        M, sig, u = ct.relative_place(G @ ibm, P["Gr"] @ ibm, bd.J[F], bd.W[F], cfg["sig_lo"], cfg["sig_hi"])
        out[f"{nm}|Dw"] = np.einsum("nij,nj->ni", M, cw - Pg)
        out[f"{nm}|wok"] = wide.ok
        out[f"{nm}|pubpart"] = Pg              # B published, the girdle's part pose
        out[f"{nm}|cw"] = cw                   # A carried, the part pose's frame
        print(nm, s, "elev", out[f"{nm}|elev"], "stored-vs-live comp", flush=True)
    c0 = wide.carry(Ab.V0)
    out["cw0"] = c0
    np.savez_compressed(OUTD / ("dump_" + argv[1] + ".npz"), **out)
    print("done", round(time.time() - t, 1), "s")


if __name__ == "__main__":
    {"measure": cmd_measure, "dump": cmd_dump, "sweep": cmd_sweep, "same": cmd_same}[sys.argv[1]](sys.argv[2:])
