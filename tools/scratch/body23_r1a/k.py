"""Body 23 r1a kit: the looped body's frames (cached), a candidate = rest move + new shapes, posed geometry, outlines."""
import os, sys, pickle, time, json, struct
import numpy as np

SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\ee2b9848-690d-4b1a-8af0-4c7c5717800a\scratchpad"
B20, B22, B23 = SCR + r"\body20", SCR + r"\body22", SCR + r"\body23"
HERE = B23 + r"\r1a"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7"
LOOPS = B23 + r"\loops\heroine_loops.glb"
DUMP = B23 + r"\loops\dump_loops"
FRAMES = ["w_p45", "w_m45", "w_p80", "w_m80", "s_p45", "r132_p45", "r132_m45", "rL90_m45", "look_f"]
sys.path.insert(0, B20)
sys.path.insert(0, WT + r"\tools\assets")
sys.path.insert(0, WT + r"\tools\anim")
import harness as h  # noqa
import flex  # noqa
from heroine_neck import _Gl  # noqa
import pit_hollow_post as ph  # noqa

CACHE = HERE + r"\cache"
os.makedirs(CACHE, exist_ok=True)


class Base:
    """the looped body welded: U rest, F faces, wid (prim vertex -> welded), dense weights, rig, shapes (welded)"""

    def __init__(s, path=LOOPS):
        G = _Gl(path)
        s.G = G
        b = ph.Body(G)
        s.b = b
        s.U, s.F, s.wid, s.Wd, s.names, s.ibm = b.U, b.F, b.wid, b.Wd, b.names, b.ibm
        s.J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
        s.gb = h.GlbBody(path)
        s.kidx = [k for k, p in enumerate(s.gb.prims) if p["mat"] != "skin_head"]
        s.offs = np.cumsum([0] + [len(s.gb.prims[k]["P"]) for k in s.kidx])
        s.nU = len(s.U)


_BASE = [None]


def base():
    if _BASE[0] is None:
        _BASE[0] = Base()
    return _BASE[0]


class Body(h.GlbBody):
    """a GlbBody-like candidate: the base's prims with a welded rest move dU and extra/replaced shapes {name: welded}"""

    def __init__(s, dU=None, shapes=None, bs=None):
        bs = bs or base()
        s.bs = bs
        s.dU = np.zeros((bs.nU, 3)) if dU is None else dU
        s.shapes = shapes or {}
        s.prims = []
        for k, p in enumerate(bs.gb.prims):
            if k in bs.kidx:
                i = bs.kidx.index(k)
                w = bs.wid[bs.offs[i]:bs.offs[i + 1]]
                T = dict(p["T"])
                for n, D in s.shapes.items():
                    T[n] = D[w]
                s.prims.append(dict(mat=p["mat"], P=p["P"] + s.dU[w], T=T))
            else:
                s.prims.append(p)

    def bind(s, k, shapes):
        p = s.prims[k]
        X = p["P"].copy()
        for n, w in shapes.items():
            if w and n in p["T"]:
                X += w * p["T"][n]
        return X


def frame(name):
    """h.Frame on the looped dump, with the elbow_psd weights the game would give (flex) and bone globals; cached"""
    pk = os.path.join(CACHE, name + ".pkl")
    bs = base()
    if os.path.exists(pk):
        fr = pickle.load(open(pk, "rb"))
        fr.gb0 = bs.gb
        return fr
    labp = os.path.join(CACHE, "lab.pkl")
    lab = None
    if os.path.exists(labp):
        lab = pickle.load(open(labp, "rb"))
    fr = h.Frame(DUMP, name, LOOPS, lab)
    if lab is None:
        wid, side, tt, pp, b = fr.lab
        pickle.dump((wid, side, tt, pp, None), open(labp, "wb"))
    fr.name = name
    fl, _ = flex.flexions(fr, LOOPS)
    fr.flex = fl
    fr.psdw = flex.weights(fl)
    rig, Gs, res = flex.bones(fr, LOOPS)
    fr.Gs, fr.bnames, fr.bres = Gs, list(rig.names), res
    # per dump vertex: welded id; blended matrices
    A = np.vstack([sf["A"] for sf in fr.dump["surfs"]])
    d2u = []
    for i, (k, j, _) in enumerate(fr.mp):
        n = len(fr.dump["surfs"][i]["A"])
        if k is None or k not in bs.kidx:
            d2u.append(np.full(n, -1))
        else:
            d2u.append(bs.wid[bs.offs[bs.kidx.index(k)] + j])
    fr.d2u = np.concatenate(d2u)
    fr.Bm = np.stack([A[:, 17:20], A[:, 20:23], A[:, 23:26]], 2)   # (n, 3, 3) columns Bx By Bz
    fr.Of = A[:, 26:29]
    fr.lab = None
    gb0 = fr.gb0
    fr.gb0 = None
    pickle.dump(fr, open(pk, "wb"))
    fr.gb0 = gb0
    return fr


def shapes_of(fr, extra=True):
    """the frame's shape weights for her body (dump's + the elbow_psd weights the game would set)"""
    sh = dict(fr.dump["surfs"][-1]["shapes"])
    if extra:
        sh.update(fr.psdw)
    return sh


def geom(fr, body, psd=True):
    """posed geometry (harness dict) of a Body at a frame; psd: apply elbow_psd weights"""
    for sf in fr.dump["surfs"]:
        if psd:
            sf["shapes"].update(fr.psdw)
        else:
            for n in fr.psdw:
                sf["shapes"].pop(n, None)
    return fr.geom(body)


def joint(fr, name):
    return fr.Gs[fr.bnames.index(name)][:3, 3]


def per_u(fr, vals):
    """dump-row values -> welded (first copy wins)"""
    bs = base()
    out = np.full((bs.nU,) + vals.shape[1:], np.nan)
    ok = fr.d2u >= 0
    out[fr.d2u[ok]] = vals[ok]
    return out


def welded_B(fr):
    """per welded vertex: the frame's blended 3x3 and offset (nan where not dumped)"""
    if getattr(fr, "_wB", None) is None:
        fr._wB = (per_u(fr, fr.Bm), per_u(fr, fr.Of))
    return fr._wB


def posed_welded(fr, body):
    """per welded vertex: its posed place at the frame (with the frame's shapes incl. elbow_psd)"""
    Bm, Of = welded_B(fr)
    sh = shapes_of(fr)
    bs = base()
    X = bs.U + body.dU
    for n, w in sh.items():
        if not w:
            continue
        if n in body.shapes:
            X = X + w * body.shapes[n]
        elif n in bs_shapes():
            X = X + w * bs_shapes()[n]
    return np.einsum("nij,nj->ni", Bm, X) + Of


_BSH = [None]


def bs_shapes():
    """the base body's shapes welded {name: (nU,3)}"""
    if _BSH[0] is None:
        bs = base()
        out = {}
        for i, k in enumerate(bs.kidx):
            p = bs.gb.prims[k]
            w = bs.wid[bs.offs[i]:bs.offs[i + 1]]
            for n, D in p["T"].items():
                out.setdefault(n, np.zeros((bs.nU, 3)))[w] = D
        _BSH[0] = out
    return _BSH[0]


def vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


if __name__ == "__main__":
    t0 = time.time()
    bs = base()
    print("base", bs.nU, len(bs.F), "%.1fs" % (time.time() - t0))
    for n in sys.argv[1:] or FRAMES:
        t0 = time.time()
        fr = frame(n)
        print("%-9s flex l %.1f r %.1f  psd %s  proj %.3f match %.1e bres %.1e  %.1fs" % (
            n, fr.flex["l"], fr.flex["r"], {k: round(v, 2) for k, v in fr.psdw.items() if v}, fr.proj_err, fr.match_err,
            fr.bres, time.time() - t0))
