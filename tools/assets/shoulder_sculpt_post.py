"""Her raised-arm shoulder join SCULPTED at the key poses, replacing the skinned surface there (Body 9, 24 Oct 2026).

Five rounds of small correctives on the skinned join (bumps, hollows, folds, the 8-weight helper rig, the reweight) left
every judge saying the raised arm looks PLUGGED IN: the deltoid a ball on the torso's corner with a notch under it,
the pec not tenting into the arm, the arm's underside one sausage into a pinched pit crease. The fault is big form, so
this pass doesn't nudge the skinned surface: at each key pose Godot dumped (tools/assets/shoulder_sculpt_poses.json)
her body is skinned with all 8 weights (NO shoulder shapes) and the arm-chest-shoulder region is RE-SOLVED as a new
surface in her chest's frame, then carried back to the bind shape through the inverse of each point's blended skin
matrix (pit_hollow_post's machinery), so at the key it lands exactly and between keys it rides with the skin.

The construction (per side, at each key; m in her rest unless said):
  region  within 0.10-0.135 of the shoulder joint (eased), the breast's core, the sternum side (x < 0.07-0.11) and
          the neck kept: those and everything outside are the boundary, three rings of it held (tangent continuity)
  solve   least squares on the uniform Laplacian: each point's Laplacian made her REST one turned into the pose
          (min |L X - R dU|^2), so the skin keeps its own curvature and spacing but not the skinning's ball, notch
          and slot; the turn R is the skin's own (polar of the blended matrix) blended toward the humerus' turn on
          the cap and arm (arm-ness 0 at 0.08 medial of the joint plane, 1 at 0.04 down the arm), so the deltoid's
          mass moves with the arm instead of sitting on the torso's corner
  flat    in the pit and the front crease (the under side about the humerus, and its front-under side out from
          0.035 medial of the joint plane, inside 0.115 of the joint) her rest curvature is dropped (the A-pose's
          closed pit valley isn't carried up): a thin-plate fill there; at the pit's core the spacing too
  pull    before the solve: the breast's upper-outer edge drawn along her skin toward the front fold's arm end
          (PULL, the edge only, not the areola), so the fold runs into the breast
  folds   then anchors on the filled surface: the FRONT axillary fold out along its spine (RIDGE, a sine along the
          rest path from the breast's upper-outer edge to the arm's front-inner side 0.095 down the humerus), the
          back fold (BACK, from the lat's edge to the arm's back-inner side), the pit pushed in as one elliptic dome
          between them along its own axis (DOME, 50 x 38 mm, long along the arm), the deltoid's front and middle
          heads one teardrop on the arm's top-outer side (DELT, peak ~0.04 down the humerus), re-solved once
  relax   last, the pit's core relaxed (RELAX, 15 Laplacian passes): the fold's leftover nick under the arm's root
Keys and slots: the reaver_show key (right A 113.5, az 23) and the cast key (l A 117 az 70, r A 114 az 61) give the
A 117 slots: per point the abd117 and flex117 shapes solved so Play/ShoulderPsd's weights at each key give back that
key's sculpt exactly (the left's show key is the right's mirrored); the old overhead cast (l A 148, r A 155) gives
the 140 and 175 slots and their shrug twins (shared accessors). So nothing up to A 90 (the Look and the idles move
0.00 mm), eased in to A 117. pit_hollow_post's shapes in those slots are REPLACED (they were authored on the
pre-reweight weights and are the old nudges): run on its output, this pass takes them off first. The hero and NPCs
carry no such shapes: untouched.

    SHOULDER_SCULPT=1 python tools/assets/shoulder_sculpt_post.py <src.glb> <dst.glb>
Run after shoulder_reweight_post.py (weights read and kept). Without SHOULDER_SCULPT=1 it copies unchanged.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
import scipy.sparse as sps
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import splu

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from worn_reaver_post import _sparse  # noqa: E402
import pit_hollow_post as ph  # noqa: E402
import shoulder_psd_post as sp  # noqa: E402

POSES = os.path.join(HERE, "shoulder_sculpt_poses.json")
_E = os.environ.get
P = dict(ridge=float(_E("SCULPT_RIDGE", 0.006)), back=float(_E("SCULPT_BACK", 0.003)), dome=float(_E("SCULPT_DOME", 0.011)),
         dRu=0.05, dRv=0.038, pull=float(_E("SCULPT_PULL", 0.012)), delt=float(_E("SCULPT_DELT", 0.005)),
         cr=0.2, cd=0.02, cl=0.05, aw=(0.08, 0.12), sf=(0.15, 0.035),
         relax=float(_E("SCULPT_RELAX", 1.0)), relaxIt=int(_E("SCULPT_RELAX_IT", 15)))
SLOTS117 = ("shoulder_abd117", "shoulder_flex117")
SLOTS150 = ("shoulder_abd140", "shoulder_flex140", "shoulder_up175", "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s")


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _polar(Bm):
    U_, _, Vt = np.linalg.svd(Bm)
    R = U_ @ Vt
    neg = np.linalg.det(R) < 0
    if neg.any():
        U_[neg, :, 2] *= -1
        R[neg] = U_[neg] @ Vt[neg]
    return R


class Her:
    """the welded body (pit_hollow_post.Body), its uniform Laplacian, rest Laplacian coordinates, edge graph"""

    def __init__(s, G):
        b = s.b = ph.Body(G)
        n = len(b.U)
        s.L = (sps.diags(1.0 / b.deg) @ b.A - sps.identity(n)).tocsr()
        s.dU = s.L @ b.U
        s.M0 = np.linalg.inv(b.ibm)
        s.NU = ph.vn(b.U, b.F)
        E = np.unique(np.sort(np.r_[b.F[:, [0, 1]], b.F[:, [1, 2]], b.F[:, [2, 0]]], axis=1), axis=0)
        el = np.linalg.norm(b.U[E[:, 0]] - b.U[E[:, 1]], axis=1)
        s.GR = sps.coo_matrix((np.r_[el, el], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()

    def rings(s, m, k):
        out = m.copy()
        for _ in range(k):
            out = out | (s.b.A @ out.astype(float) > 0)
        return out

    def smooth(s, f, k):
        for _ in range(k):
            f = 0.5 * f + 0.5 * (s.b.A @ f) / s.b.deg
        return f

    def path(s, a, c):
        _, pred = dijkstra(s.GR, indices=a, return_predecessors=True)
        p = [c]
        while p[-1] != a:
            p.append(pred[p[-1]])
        return np.array(p[::-1])


class Side:
    """one side's rest fields: the region, the flat sector, arm-ness, the fold anchors and spines, the pit's apex"""

    def __init__(s, H, side, p=P):
        b, U = H.b, H.b.U
        sg = 1 if side == "l" else -1
        J0 = H.M0[b.I["upperarm_" + side]][:3, 3]
        h0 = _unit(H.M0[b.I["lowerarm_" + side]][:3, 3] - J0)
        v = U - J0
        t0 = v @ h0
        rj = np.linalg.norm(v, axis=1)
        s.aw = b.arm_w(side)
        s.bw = b.Wd[:, b.I["breast_" + side]]
        x = U[:, 0] * sg
        up = _unit(np.array([0, 1.0, 0]) - h0[1] * h0)
        fr = _unit(np.array([0, 0, 1.0]) - h0[2] * h0 - (np.array([0, 0, 1.0]) @ up) * up)
        c = np.cross(h0, fr)
        med = c if c[0] * sg < 0 else -c
        rr = v - t0[:, None] * h0
        rn = np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
        cosu, cosf = (rr @ up) / rn, (rr @ fr) / rn
        phi = _ss((0.135 - rj) / 0.035) * (1 - _ss((s.bw - 0.35) / 0.3)) * _ss((x - 0.07) / 0.04)
        phi *= 1 - _ss((U[:, 1] - 1.53) / 0.03) * _ss((0.13 - x) / 0.04)
        s.phi = phi * (x > 0.02)
        sect = np.maximum(_ss((-0.1 - cosu) / 0.5),
                          _ss((p["sf"][0] - cosu) / 0.35) * _ss((cosf - 0.15) / 0.4) * _ss((t0 + p["sf"][1]) / 0.03))
        s.kap = 1 - sect * _ss((0.115 - rj) / 0.035) * (1 - _ss((t0 - 0.06) / 0.05))
        s.arm = _ss((t0 + p["aw"][0]) / p["aw"][1])
        s.core = _ss((-0.3 - cosu) / 0.4) * _ss((0.09 - rj) / 0.03)

        def arm_pt(t, d):
            i = np.nonzero((s.aw > 0.8) & (np.abs(t0 - t) < 0.006))[0]
            return int(i[np.argmax(H.NU[i] @ d)])
        s.a_fa = arm_pt(0.095, _unit(0.75 * fr + 0.66 * med))
        s.a_ba = arm_pt(0.090, _unit(-0.75 * fr + 0.66 * med))
        Bm = s.bw > 0.3
        Bc = (U[Bm] * s.bw[Bm, None]).sum(0) / s.bw[Bm].sum()
        i = np.nonzero((s.bw > 0.2) & (s.bw < 0.4) & (U[:, 2] > Bc[2] - 0.02))[0]
        s.a_fc = int(i[np.argmax((U[i] - Bc) @ _unit(np.array([0.75 * sg, 0.66, 0.0])))])
        d = np.linalg.norm(U - np.array([0.125 * sg, 1.31, -0.085]), axis=1)
        s.a_bc = int(np.argmin(np.where(s.aw < 0.2, d, 9)))
        s.faf, s.baf = H.path(s.a_fc, s.a_fa), H.path(s.a_bc, s.a_ba)
        s.apex = ph.apex(b, U, side)


def _solve(H, Pin, phi, delta, anchors=None, c_core=1e-7, c_fix=1e2):
    """min sum |(L X)_i - delta_i|^2 + c_i |X_i - Pin_i|^2 (+ anchors' |X_i - target_i|^2 w) over phi's points and
    three rings beyond; c from phi (held where phi is 0)"""
    act = H.rings(phi > 1e-4, 3)
    ia, io = np.nonzero(act)[0], np.nonzero(~act)[0]
    ir = np.nonzero(H.rings(act, 1))[0]
    Lr = H.L[ir]
    LA, LO = Lr[:, ia], Lr[:, io]
    c = c_core + c_fix * (1 - phi[ia]) ** 2
    cw, tgt = np.zeros(len(Pin)), Pin.copy()
    for idx, T, w in anchors or []:
        cw[idx] += w
        tgt[idx] = T
    lu = splu((LA.T @ LA + sps.diags(c + cw[ia])).tocsc())
    rhs = LA.T @ (delta[ir] - LO @ Pin[io]) + c[:, None] * Pin[ia] + cw[ia, None] * tgt[ia]
    X = Pin.copy()
    X[ia] = np.stack([lu.solve(rhs[:, k]) for k in range(3)], 1)
    return X


def author(H, S, d, side, p=P, info=None):
    """(D the posed move in her chest frame, B blended chest-frame matrices) for one side at one key"""
    b = H.b
    F = b.F
    M, T, X0, B = b.pose(d)
    J = (T @ M["upperarm_" + side])[:3, 3]
    h = _unit((T @ M["lowerarm_" + side])[:3, 3] - J)
    Sa = T @ M["upperarm_" + side] @ b.ibm[b.I["upperarm_" + side]]
    Ra = _polar(Sa[None, :3, :3])[0]
    ra = _polar((1 - S.arm)[:, None, None] * np.eye(3)[None] + S.arm[:, None, None] * Ra[None])
    w = S.phi[:, None, None]
    R = _polar((1 - w) * _polar(B[:, :3, :3]) + w * ra)
    dR = np.einsum("nab,nb->na", R, H.dU)
    # the breast's upper-outer edge drawn along her skin toward the front fold's arm end
    N0 = ph.vn(X0, F)
    m = S.bw > 0.3
    Bc = (X0[m] * S.bw[m, None]).sum(0) / S.bw[m].sum()
    du = _unit(X0[S.a_fa] - Bc)
    rb = np.linalg.norm(X0 - Bc, axis=1)
    k = H.smooth(H.smooth(S.bw, 20) * _ss(((X0 - Bc) @ du) / 0.08) * _ss((rb - 0.03) / 0.04), 10)
    k = k / max(k.max(), 1e-9)
    Pp = X0 + p["pull"] * k[:, None] * (du[None, :] - (N0 @ du)[:, None] * N0)
    out = S.phi < 1e-4

    def fill(Pin, anchors=None, its=2):
        X = Pin.copy()
        for _ in range(its):
            N = ph.vn(X, F)
            dn = (dR * N).sum(1, keepdims=True) * N
            delta = (dR - (1 - S.kap[:, None]) * dn) * (1 - S.core[:, None])
            delta[out] = (H.L @ Pin)[out]
            X = _solve(H, Pin, S.phi, delta, anchors)
        return X
    Xf = fill(Pp)
    Nf = ph.vn(Xf, F)
    anc = []
    for pth, amp in ((S.faf, p["ridge"]), (S.baf, p["back"])):
        sl = np.linspace(0, 1, len(pth))
        a = amp * np.sin(np.pi * np.clip(sl * 1.15 - 0.05, 0, 1)) ** 0.7
        anc.append((pth, Xf[pth] + a[:, None] * Nf[pth], p["cr"]))
    C = Xf[S.apex]
    ax = _unit(Nf[np.linalg.norm(Xf - C, axis=1) < 0.02].mean(0))
    hu = _unit(h - (h @ ax) * ax)
    q = Xf - C
    rho = np.sqrt(((q @ hu) / p["dRu"]) ** 2 + ((q - (q @ hu)[:, None] * hu - (q @ ax)[:, None] * ax) ** 2).sum(1) / p["dRv"] ** 2)
    core = np.nonzero((rho < 1.0) & (S.phi > 0.5))[0]
    anc.append((core, Xf[core] - (p["dome"] * (1 - rho[core] ** 2) ** 2)[:, None] * ax, p["cd"]))
    up = _unit(np.array([0, 1.0, 0]) - h[1] * h)
    c = np.cross(up, h)
    dt = _unit(np.cos(np.radians(25)) * up + np.sin(np.radians(25)) * (c if c[2] > 0 else -c))
    v = Xf - J
    ta = v @ h
    rr = v - ta[:, None] * h
    ca = (rr @ dt) / np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
    wdl = _ss((ta + 0.015) / 0.04) * (1 - _ss((ta - 0.06) / 0.065)) * _ss(ca / 0.6) * (S.aw > 0.3) * (S.phi > 0.05)
    dl = np.nonzero(wdl > 0.02)[0]
    if p["delt"] > 0:
        anc.append((dl, Xf[dl] + (p["delt"] * wdl[dl])[:, None] * Nf[dl], p["cl"]))
    X = fill(Xf, anchors=anc, its=1)
    # last, the pit's core relaxed (plain passes: Taubin left it): the A-pose fold's leftover nick where the arm's underside
    # meets the torso wall (3-pass crease 1.9 mm at the reaver_show key, a dark nick in Godot) eased out
    wr = p["relax"] * H.smooth(np.minimum(S.core * 1.5, 1) * S.phi, 6)
    for _ in range(p["relaxIt"]):
        X = X + 0.5 * wr[:, None] * b.lap(X)
    if info is not None:
        info.update(X0=X0, Xf=Xf, X=X)
    return X - X0, B


def _rest(B, D):
    return np.einsum("nab,nb->na", np.linalg.inv(B[:, :3, :3]), D)


def build(G, log=print):
    """{group_side: rest delta} and {group_side: (N0, N1, L, Li, moved)} for the normals"""
    H = Her(G)
    b = H.b
    poses = json.load(open(POSES))
    S = {s: Side(H, s) for s in "lr"}
    samp = {}
    for key, side in (("show", "r"), ("cast", "l"), ("cast", "r"), ("cast150", "l"), ("cast150", "r")):
        D, B = author(H, S[side], poses[key], side)
        _, _, X0, _ = b.pose(poses[key])
        Mg = np.stack([np.eye(4)] * len(b.names))
        for i, n in enumerate(b.names):
            v = poses[key][n]
            Mg[i, :3, 0], Mg[i, :3, 1], Mg[i, :3, 2], Mg[i, :3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
        A, az = sp.arm_angles(Mg, b.I, side)
        wts = sp.psd_weights(A, az, sp.clavicle_rise(Mg, H.M0, b.I, side))
        samp[key + "_" + side] = (_rest(B, D), wts, (ph.vn(X0, b.F), ph.vn(X0 + D, b.F), B[:, :3, :3], np.linalg.norm(D, axis=1) > 1e-6))
        log("SCULPT %s %s: A %.1f az %.1f, posed move max %.1f mm, %d points" % (
            key, side, A, az, 1000 * np.linalg.norm(D, axis=1).max(), int((np.linalg.norm(D, axis=1) > 1e-4).sum())))
    # normals: the posed normal turned as the sculpt turned it, back to rest through the same matrix
    nU = ph.vn(b.U, b.F)
    dN = {}
    for k, (_, _, (N0, N1, L, moved)) in samp.items():
        g0 = _unit(np.einsum("nab,nb->na", L, nU))
        nr = _unit(np.einsum("nab,nb->na", np.linalg.inv(L), ph._rot(N0, N1, g0)))
        dN[k] = np.where(moved[:, None], nr - nU, 0)
    samp["show_l"] = (ph.mirror(b, samp["show_r"][0]), {"shoulder_abd117": samp["show_r"][1]["shoulder_abd117"],
                                                         "shoulder_flex117": samp["show_r"][1]["shoulder_flex117"]}, None)
    dN["show_l"] = ph.mirror(b, dN["show_r"])
    rest, nrm = {}, {}
    for side in "lr":
        # the A 117 pair: per point abd/flex so each key's weights give back its sculpt (2 x 2, the same for all points)
        (Ds, ws, _), (Dc, wc, _) = samp["show_" + side], samp["cast_" + side]
        Wm = np.array([[ws["shoulder_abd117"], ws["shoulder_flex117"]], [wc["shoulder_abd117"], wc["shoulder_flex117"]]])
        Wi = np.linalg.inv(Wm)
        rest["abd117_" + side] = Wi[0, 0] * Ds + Wi[0, 1] * Dc
        rest["flex117_" + side] = Wi[1, 0] * Ds + Wi[1, 1] * Dc
        nrm["abd117_" + side] = Wi[0, 0] * dN["show_" + side] + Wi[0, 1] * dN["cast_" + side]
        nrm["flex117_" + side] = Wi[1, 0] * dN["show_" + side] + Wi[1, 1] * dN["cast_" + side]
        log("SCULPT 117 %s: key weights abd/flex show %.2f/%.2f cast %.2f/%.2f" % (side, *Wm.ravel()))
        D150, w150, _ = samp["cast150_" + side]
        tot = sum(w150[k] for k in SLOTS150)
        rest["150_" + side] = D150 / max(tot, 1e-6)
        nrm["150_" + side] = dN["cast150_" + side] / max(tot, 1e-6)
    return b, rest, nrm


def run(src, dst):
    G = _Gl(src)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names0 = list((mesh.get("extras") or {}).get("targetNames", []))
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    assert len(prims) == len(mesh["primitives"])
    # pit_hollow_post's shapes in these slots off first (the sculpt replaces them; accessors left unreferenced)
    keep = [i for i, n in enumerate(names0) if not n.startswith("shoulder_")]
    if len(keep) < len(names0):
        print("SCULPT: replacing", len(names0) - len(keep), "shoulder shapes")
    for p in prims:
        p["targets"] = [p["targets"][i] for i in keep] if p.get("targets") else []
    w0 = list(mesh.get("weights", [0] * len(names0)))
    names = [names0[i] for i in keep]
    weights = [w0[i] for i in keep]
    b, rest, nrm = build(G)
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    acc = {}
    for key, d in rest.items():
        o = 0
        acc[key] = []
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = b.wid[o:o + n]
            o += n
            Dp, dn = d[w], nrm[key][w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dn
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dn).max(1) > 1e-6)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 1e-7)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 1e-6)[0]
            acc[key].append((_sparse(g, binb, n, ip, Dp[ip]), _sparse(g, binb, n, inn, dNp[inn])))
    added = []
    for nm, grp in [(n, n.replace("shoulder_", "")) for n in SLOTS117] + [(n, "150") for n in SLOTS150]:
        for side in "lr":
            for pi, p in enumerate(prims):
                pa, na = acc[grp + "_" + side][pi]
                p.setdefault("targets", []).append({"POSITION": pa, "NORMAL": na})
            added.append(nm + "_" + side)
    for p in prims:
        assert len(p["targets"]) == len(names) + len(added)
    mesh.setdefault("extras", {})["targetNames"] = names + added
    mesh["weights"] = weights + [0] * len(added)
    g["asset"].setdefault("extras", {}).pop("pit_hollow", None)
    g["asset"]["extras"]["shoulder_sculpt"] = {"keys": ["show r", "cast l", "cast r", "cast150 l", "cast150 r"],
                                               "params": {k: v for k, v in P.items()}}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("SCULPT shapes", len(added), "->", dst)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if os.environ.get("SHOULDER_SCULPT", "0") != "1":
        shutil.copyfile(a[0], a[1])
        print("SCULPT off (SHOULDER_SCULPT=1 builds it): copied")
    else:
        run(a[0], a[1])
