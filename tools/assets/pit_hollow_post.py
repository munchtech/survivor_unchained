"""Her armpit as an arm rises: the hollow, the front axillary fold and the biceps/triceps groove (Body 6 S2c, 24 Oct 2026).

The S1 judge on the helper-joint rig (scap + delt/trap/pec/lat): "the arms read as tubes plugged into the corners of a
box"; the filled, square armpit corner the biggest single read. Helpers make folds, not hollows, so these are
pose-space shapes, authored in BONE SPACE on the helper-deformed body: at each sample her body is skinned with all 8
weights at a pose Godot dumped (tools/assets/pit_hollow_poses.json: cast_raise at A 148/155, reaver_show's right arm at
A 114), the wanted move sculpted there in her chest's frame, and carried back to the bind shape through the inverse of
each point's blended skin matrix (normals likewise, as the rotation of the posed normal), so at the sample it lands
exactly under the deformation and between samples it rides with the skin.

The sculpt (per side, at each sample):
  relax   the junction's skinning slot, shelf and pinch (Taubin, a soft mask about the pit) and the leftover S2 folds
          (the lat's front edge, the acromion's top), Taubin too
  hollow  an elliptic dome pushed in along the pit's own axis, long along the arm: DEPTH at A 150, DEPTH_115 at A 114
  fold    the front axillary fold: a soft ridge from the pec's border on the chest into the arm's front, 75 mm down
          (OFF by default since 24 Oct, PIT_FOLD=0.010 restores S2d: in Godot it IS the owner's "really strange crease at
          shoulder" at reaver_show A 114; a softer, wider fold (0.005, 45 mm) still creased)
  pull    the breast's upper-outer edge drawn toward that fold (along her skin)
  seam    the valley over the shoulder's top where scap_rig_post's arm ramp meets the clavicle, smoothed out (OFF by
          default, PIT_SEAM=1 on: measured in Godot it darkened the junction a little, not the owner's crease)
  groove  the biceps/triceps groove up the arm's face toward the pit, shallow with a wide falloff

Driven by the existing machinery: the shapes take Play/ShoulderPsd's names (HerRaise finds them by name; Python twin
shoulder_psd_post.psd_weights), the A 114 sample in the 117 slots, the A 150 one in the 140 and 175 slots and their
shrug twins (shared accessors), so they are 0 up to A 90 (the Look and the idles move 0.00 mm), eased in to A 117, all
A 150 from A 140. The hero and NPCs carry no such shapes: untouched. The left's A 114 sample is the right's, mirrored.

    PIT_HOLLOW=1 python tools/assets/pit_hollow_post.py <src.glb> <dst.glb> [--npz rest_deltas.npz]
Run after shoulder_rig_post.py (its JOINTS_1/WEIGHTS_1 are read and kept). Without PIT_HOLLOW=1 it copies unchanged.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from wrap_post import skin_union  # noqa: E402
from worn_reaver_post import _sparse  # noqa: E402

POSES = os.path.join(HERE, "pit_hollow_poses.json")
DEPTH, DEPTH_115 = float(os.environ.get("PIT_DEPTH", 0.009)), float(os.environ.get("PIT_DEPTH_115", 0.007))
P = dict(Ru=0.050, Rv=0.032, Ra=0.06, drop=0.012, relaxR=float(os.environ.get("PIT_RELAX_R", 0.055)), relaxK=0.8, relaxIt=int(os.environ.get("PIT_RELAX_IT", 30)), leftR=0.028, leftIt=12,
         fold=float(os.environ.get("PIT_FOLD", 0.0)), foldW=float(os.environ.get("PIT_FOLD_W", 0.026)), foldIt=int(os.environ.get("PIT_FOLD_SMOOTH", 10)), pull=float(os.environ.get("PIT_PULL", 0.023)),
         groove=float(os.environ.get("PIT_GROOVE", 0.0035)), grooveW=float(os.environ.get("PIT_GROOVE_W", 0.018)), smoothIt=int(os.environ.get("PIT_SMOOTH", 40)),
         grooveIt=int(os.environ.get("PIT_GROOVE_SMOOTH", 4)), tilt=float(os.environ.get("PIT_TILT", 20.0)),
         shift=float(os.environ.get("PIT_SHIFT", 0.006)),
         seam=float(os.environ.get("PIT_SEAM", 0.0)), seamR=float(os.environ.get("PIT_SEAM_R", 0.035)),
         seamIt=int(os.environ.get("PIT_SEAM_IT", 100)), seamFill=int(os.environ.get("PIT_SEAM_FILL", 60)), seamA=[0.228, 1.505, -0.05],
         seamB=[float(v) for v in os.environ.get("PIT_SEAM_B", "0.20,1.465,0.045").split(",")])
SAMPLES = (("150_l", "cast", "l", DEPTH), ("150_r", "cast", "r", DEPTH), ("115_r", "over", "r", DEPTH_115))
SLOTS = {"115": ("shoulder_abd117", "shoulder_flex117"),
         "150": ("shoulder_abd140", "shoulder_flex140", "shoulder_up175", "shoulder_abd140s", "shoulder_flex140s",
                 "shoulder_up175s")}


def _unit(v):
    return v / np.linalg.norm(v)


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _bump(r, k=2):
    r = np.clip(r, 0, 1)
    return (1 - r * r) ** k


def _segd(U, a, b):
    v = b - a
    t = np.clip(((U - a) @ v) / (v @ v), 0, 1)
    return np.linalg.norm(U - (a + t[:, None] * v), axis=1)


def vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


class Body:
    """Her welded body (both primitives), dense 8-bone weights, rig names and inverse binds."""

    def __init__(s, G):
        g = G.g
        s.G = G
        s.U, s.F, J, W, s.wid = skin_union(G)
        sk = g["skins"][0]
        s.names = [g["nodes"][j].get("name") for j in sk["joints"]]
        s.ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        s.Wd = np.zeros((len(s.U), len(s.names)))
        np.add.at(s.Wd, (np.repeat(np.arange(len(s.U)), J.shape[1]), J.ravel()), W.ravel())
        s.I = {n: i for i, n in enumerate(s.names)}
        E = np.unique(np.sort(np.r_[s.F[:, [0, 1]], s.F[:, [1, 2]], s.F[:, [2, 0]]], axis=1), axis=0)
        n = len(s.U)
        s.A = coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
        s.deg = np.asarray(s.A.sum(1)).ravel()

    def lap(s, X):
        return (s.A @ X) / s.deg[:, None] - X

    def arm_w(s, side):
        return s.Wd[:, [i for i, n in enumerate(s.names) if n.endswith("_" + side)
                        and n.split("_")[0] in ("upperarm", "lowerarm", "hand")]].sum(1)

    def pose(s, d):
        """bone globals {name: 4x4} from a dump entry; the chest frame T; points posed in it; blended matrices"""
        M = {}
        for n, v in d.items():
            m = np.eye(4)
            m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
            M[n] = m
        T = np.linalg.inv(M["spine_03"] @ s.ibm[s.I["spine_03"]])
        S = np.stack([T @ M[n] @ s.ibm[j] if n in M else T for j, n in enumerate(s.names)])
        B = np.einsum("nj,jab->nab", s.Wd, S)
        X = np.einsum("nab,nb->na", B[:, :3, :3], s.U) + B[:, :3, 3]
        return M, T, X, B


def _near(X, p, mask=None):
    d = np.linalg.norm(X - p, axis=1)
    if mask is not None:
        d = np.where(mask, d, 1e9)
    return int(np.argmin(d))


def apex(b, X, side):
    sg = 1 if side == "l" else -1
    U = b.U
    m = ((U[:, 0] * sg > 0.12) & (U[:, 0] * sg < 0.20) & (U[:, 1] < 1.45) & (U[:, 1] > 1.30)
         & (np.abs(U[:, 2] + 0.02) < 0.035) & (b.arm_w(side) < 0.5))
    return int(np.nonzero(m)[0][X[m, 1].argmax()])


def author(b, d, side, depth, p=P, info=None):
    """(D posed move in her chest frame, B blended chest-frame skin matrices) for one side at one pose"""
    U, F = b.U, b.F
    sg = 1 if side == "l" else -1
    M, T, X0, B = b.pose(d)
    J = (T @ M["upperarm_" + side])[:3, 3]
    h = _unit((T @ M["lowerarm_" + side])[:3, 3] - J)
    aw = b.arm_w(side)
    sd = (U[:, 0] * sg > 0.06) & (U[:, 1] > 1.2)
    ia = apex(b, X0, side)
    C = X0[_near(X0, X0[ia] - np.array([0, p["drop"], 0]), sd & (U[:, 0] * sg > 0.12))]
    # relax: the junction (Taubin, tangential too: the pinch is a stretched fan), then the leftover folds (normal-only)
    wr = p["relaxK"] * _bump(np.linalg.norm(X0 - C, axis=1) / p["relaxR"], 3) * sd
    Xr = X0.copy()
    for _ in range(p["relaxIt"]):
        Xr = Xr + 0.5 * wr[:, None] * b.lap(Xr)
        Xr = Xr - 0.53 * wr[:, None] * b.lap(Xr)
    # (the slot where the arm's lower mass meets the torso wall holds folded triangles: plain Laplacian there, close in)
    wu = float(os.environ.get("PIT_UNTANGLE", 1.0)) * _bump(np.linalg.norm(X0 - C, axis=1) / 0.035, 2) * sd
    for _ in range(int(os.environ.get("PIT_UNTANGLE_IT", 40))):
        Xr = Xr + 0.5 * wu[:, None] * b.lap(Xr)
    wl = np.zeros(len(U))
    for q in ((0.13, 1.36, -0.04), (0.22, 1.49, -0.04)):
        wl = np.maximum(wl, _bump(np.linalg.norm(U - np.array((q[0] * sg,) + q[1:]), axis=1) / p["leftR"], 3))
    for _ in range(p["leftIt"]):
        Xr = Xr + 0.5 * wl[:, None] * b.lap(Xr)
        Xr = Xr - 0.53 * wl[:, None] * b.lap(Xr)
    # seam: the valley over the shoulder's top and down the deltoid's front, where scap_rig_post's arm ramp (x 0.19 to
    # 0.25) blends the clavicle and the raised arm half and half (linear skinning's crease, the owner's 24 Oct note)
    # smoothed out along a rest-space line, eased over seamR: plain Laplacian steps (the A 114 valley holds folded
    # triangles), then outward-only ones (fill, no ridge shrinks). Crease (concave bends within 20 mm of the line, deg*m)
    # A 114 right 18.5 -> 11.3, A 150 r/l 16.6/20.8 -> 8.8/11.7 (the resting side 5.3); PIT_SEAM=0 turns it off
    ws = p["seam"] * _bump(_segd(U, np.array([p["seamA"][0] * sg] + p["seamA"][1:]),
                                    np.array([p["seamB"][0] * sg] + p["seamB"][1:])) / p["seamR"], 2) * sd
    if ws.any():
        for _ in range(p["seamIt"]):       # (plain first: the sharpest stretch holds folded triangles)
            Xr = Xr + 0.5 * ws[:, None] * b.lap(Xr)
        for _ in range(p["seamFill"]):
            n = vn(Xr, F)
            Xr = Xr + 0.5 * ws[:, None] * np.maximum((b.lap(Xr) * n).sum(1), 0)[:, None] * n
    Nr = vn(Xr, F)
    # hollow: the dome along the pit's own axis (its mean normal about the centre), long along the arm
    wa = _bump(np.linalg.norm(Xr - C, axis=1) / 0.02) * sd
    a = _unit((wa[:, None] * Nr).sum(0))
    # (tilted toward the camera side, forward-down, so a front camera sees its shadow; its centre slid that way too)
    fd = _unit(np.array([0, -1.0, 1.0]))
    ft = _unit(fd - (fd @ a) * a)
    fk = _ss((0.75 - a[2]) / 0.25)   # (the overhead A 114 pit already faces the camera: left as it is)
    tr = np.radians(p["tilt"]) * fk
    a = _unit(np.cos(tr) * a + np.sin(tr) * ft)
    C = C + p["shift"] * fk * ft
    hu = _unit(h - (h @ a) * a)
    hv = np.cross(a, hu)
    q = Xr - C
    rho = np.sqrt(((q @ hu) / p["Ru"]) ** 2 + ((q @ hv) / p["Rv"]) ** 2 + ((q @ a) / p["Ra"]) ** 2)
    Dh = -depth * (_bump(rho) * sd)[:, None] * a
    # front fold: a soft ridge from the pec's border into the arm's front, 75 mm down the humerus
    fa = _unit(np.array([0, 0, 1.0]) - h[2] * h)
    P1 = Xr[_near(Xr, J + 0.075 * h + 0.045 * fa, aw > 0.5)]
    P0 = Xr[_near(U, np.array([0.13 * sg, 1.46, 0.075]))]
    sv = P1 - P0
    t = np.clip(((Xr - P0) @ sv) / (sv @ sv), -0.5, 1.5)
    dd = np.linalg.norm(Xr - (P0 + t[:, None] * sv), axis=1)
    taper = _ss((t + 0.35) / 0.5) * _ss((1.35 - t) / 0.5)
    Df = p["fold"] * (_bump(dd / p["foldW"], 3) * taper * sd)[:, None] * Nr
    # the breast's upper-outer edge drawn toward the fold, along her skin
    bw = b.Wd[:, b.I["breast_" + side]]
    Bm = bw > 0.3
    Bc = (Xr[Bm] * bw[Bm, None]).sum(0) / bw[Bm].sum()
    du = _unit(P1 - Bc)
    rb = np.linalg.norm(Xr - Bc, axis=1)
    k = bw * _ss(((Xr - Bc) @ du) / 0.07) * _ss((rb - 0.035) / 0.03) * (1 - _ss((rb - 0.09) / 0.04))   # (the edge, not the areola)
    Dp = p["pull"] * k[:, None] * (du[None, :] - (Nr @ du)[:, None] * Nr)
    # the biceps/triceps groove: up the arm's face toward the pit (its normal nearest the pit's axis)
    ta = (Xr - J) @ h
    face = Nr @ a
    line = []
    for tt in np.arange(-0.01, 0.23, 0.01):
        m = (aw > 0.6) & (np.abs(ta - tt) < 0.005)
        if m.any():
            line.append(Xr[np.nonzero(m)[0][np.argmax(face[m])]])
    dl, _ = cKDTree(np.array(line)).query(Xr)
    tw = _ss((ta + 0.01) / 0.04) * _ss((0.22 - ta) / 0.06)
    Dg = -p["groove"] * (_bump(dl / p["grooveW"], 3) * tw * (aw > 0.2))[:, None] * Nr
    # the sculpt's move smoothed along her skin (no thin triangle folds where the pit's fan is stretched)
    S = Dh
    for _ in range(p["smoothIt"]):
        S = S + 0.5 * b.lap(S)
    # (the fold and the pull on their own pass: the hollow's 40 steps took a 2.5 mm ridge down to 0.6)
    Sf = Df + Dp
    for _ in range(p["foldIt"]):
        Sf = Sf + 0.5 * b.lap(Sf)
    S = S + Sf
    # (the groove after that pass, its own light smoothing only: 40 steps flattened it out of sight)
    for _ in range(p["grooveIt"]):
        Dg = Dg + 0.5 * b.lap(Dg)
    S = S + Dg
    D = Xr + S - X0
    if info is not None:
        info.update(C=C, a=a, J=J, h=h, P0=P0, P1=P1, Dh=Dh, Dg=Dg, Df=Df, Dp=Dp, relax=Xr - X0, X0=X0, Nr=Nr, S=S)
    return D, B


def mirror(b, d):
    """a rest-space delta field mirrored to the other side (x -> -x), 4 nearest, inverse-distance weighted"""
    Um = b.U * np.array([-1, 1, 1])
    dist, ix = cKDTree(b.U).query(Um, k=4)
    w = 1 / np.maximum(dist, 1e-5)
    w /= w.sum(1, keepdims=True)
    return (d[ix] * w[:, :, None]).sum(1) * np.array([-1, 1, 1])


def build(G):
    b = Body(G)
    poses = json.load(open(POSES))
    rest, posedN = {}, {}
    for key, pose, side, depth in SAMPLES:
        D, B = author(b, poses[pose], side, depth)
        L = B[:, :3, :3]
        Li = np.linalg.inv(L)
        rest[key] = np.einsum("nab,nb->na", Li, D)
        _, _, X0, _ = b.pose(poses[pose])
        posedN[key] = (vn(X0, b.F), vn(X0 + D, b.F), L, Li, np.linalg.norm(D, axis=1) > 1e-6)
        print("PIT %s (%s %s): posed move max %.1f mm, %d points" % (
            key, pose, side, 1000 * np.linalg.norm(D, axis=1).max(), int((np.linalg.norm(D, axis=1) > 1e-4).sum())))
    rest["115_l"] = mirror(b, rest["115_r"])
    return b, rest, posedN


def _rot(a, c, x):
    """rotate x by the turn taking unit a to unit c (rows)"""
    v = np.cross(a, c)
    k = (a * c).sum(1, keepdims=True)
    return x * k + np.cross(v, x) + v * (v * x).sum(1, keepdims=True) / np.maximum(1 + k, 1e-6)


def run(src, dst, npz=None):
    G = _Gl(src)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names0 = (mesh.get("extras") or {}).get("targetNames", [])
    assert "shoulder_abd117_l" not in names0, "the shoulder shapes are on the glb already"
    b, rest, posedN = build(G)
    if npz:
        np.savez(npz, **rest)
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    assert len(prims) == len(mesh["primitives"])
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    # normals: the posed normal turned as the sculpt turned it, carried back to rest through the same matrix (a union
    # field; the mirrored side's mirrored), then put on each primitive's own normals
    nU = vn(b.U, b.F)
    dNu = {}
    for key, (N0, N1, L, Li, moved) in posedN.items():
        g0 = np.einsum("nab,nb->na", L, nU)
        g0 /= np.linalg.norm(g0, axis=1, keepdims=True)
        nr = np.einsum("nab,nb->na", Li, _rot(N0, N1, g0))
        nr /= np.linalg.norm(nr, axis=1, keepdims=True)
        dNu[key] = np.where(moved[:, None], nr - nU, 0)
    dNu["115_l"] = mirror(b, dNu["115_r"])
    acc = {}
    for key, d in rest.items():
        o = 0
        acc[key] = []
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = b.wid[o:o + n]
            o += n
            Dp, dn = d[w], dNu[key][w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dn
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dn).max(1) > 1e-6)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 1e-7)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 1e-6)[0]
            acc[key].append((_sparse(g, binb, n, ip, Dp[ip]), _sparse(g, binb, n, inn, dNp[inn])))
    added = []
    for grp, slots in (("115", SLOTS["115"]), ("150", SLOTS["150"])):
        for nm in slots:
            for side in "lr":
                for pi, p in enumerate(prims):
                    pa, na = acc[grp + "_" + side][pi]
                    p.setdefault("targets", []).append({"POSITION": pa, "NORMAL": na})
                added.append(nm + "_" + side)
    for p in prims:
        assert len(p["targets"]) == len(names0) + len(added)
    mesh.setdefault("extras", {})["targetNames"] = list(names0) + added
    mesh["weights"] = list(mesh.get("weights", [0] * len(names0))) + [0] * len(added)
    g["asset"].setdefault("extras", {})["pit_hollow"] = {
        "samples": [[k, ps, s, dp] for k, ps, s, dp in SAMPLES], "depth_mm": DEPTH * 1000, "depth_115_mm": DEPTH_115 * 1000,
        "fold_mm": P["fold"] * 1000, "pull_mm": P["pull"] * 1000, "groove_mm": P["groove"] * 1000, "slots": SLOTS}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("PIT shapes", len(added), "->", dst)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    npz = sys.argv[sys.argv.index("--npz") + 1] if "--npz" in sys.argv else None
    if npz in a:
        a.remove(npz)
    if os.environ.get("PIT_HOLLOW", "0") != "1":
        shutil.copyfile(a[0], a[1])
        print("PIT off (PIT_HOLLOW=1 builds it): copied")
    else:
        run(a[0], a[1], npz)
