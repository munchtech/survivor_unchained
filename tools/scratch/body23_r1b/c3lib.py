"""Body 23 r1b (C3, outline-first): shared helpers on the LOOPED body (frames cached, posed geometry, outlines)."""
import os, sys, pickle, numpy as np
SP = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\ee2b9848-690d-4b1a-8af0-4c7c5717800a\scratchpad"
B20 = os.path.join(SP, "body20"); B22 = os.path.join(SP, "body22"); B23 = os.path.join(SP, "body23")
HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7"
sys.path.insert(0, B20); sys.path.insert(0, os.path.join(B22, "shoulder"))
import harness as h, flex  # noqa
import sh  # noqa  (B22's helpers; we re-point its globals)
A_GLB = os.path.join(B23, "loops", "heroine_loops.glb")
DUMP = os.path.join(B23, "loops", "dump_loops")
sh.GIT = A_GLB; sh.DUMP = DUMP
_LAB = [None]
_FR = {}
HANG = ["w_p45", "w_m45", "look_f"]
BEND = ["w_m80", "rL90_m45", "s_p45"]
RAISE = ["r132_p45", "r132_m45"]
ALL = HANG + BEND + RAISE + ["w_p80"]


def frame(name):
    if name in _FR:
        return _FR[name]
    lab_p = os.path.join(HERE, "cache_lab.pkl")
    if _LAB[0] is None and os.path.exists(lab_p):
        _LAB[0] = tuple(pickle.load(open(lab_p, "rb"))) + (None,)
    fr = h.Frame(DUMP, name, A_GLB, _LAB[0]); fr.name = name
    if _LAB[0] is None:
        _LAB[0] = fr.lab
        pickle.dump(fr.lab[:4], open(lab_p, "wb"))
    fl, _ = flex.flexions(fr, A_GLB)
    w = flex.weights(fl)
    fr.flex = fl
    for s in fr.dump["surfs"]:
        s["shapes"].update(w)
    rig, Gs, res = flex.bones(fr, A_GLB)
    fr.rig, fr.Gs, fr.bone_res = rig, Gs, res
    _FR[name] = fr
    return fr


def joint(fr, name):
    return fr.Gs[fr.rig.names.index(name)][:3, 3]


def jscreen(fr, name):
    return h.project(fr.Pm, joint(fr, name)[None])[0]


# ---------------------------------------------------------------- bodies in memory --
from heroine_neck import _Gl  # noqa
import pit_hollow_post as ph  # noqa
_B = [None]


def body():
    """A's welded body (ph.Body) with smoothed rest normals b.N"""
    if _B[0] is None:
        b = ph.Body(_Gl(A_GLB))
        N = ph.vn(b.U, b.F)
        for _ in range(3):
            N = N + b.lap(N) * 0.5
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        b.N = N
        _B[0] = b
    return _B[0]


_GBA = [None]


def gbA():
    if _GBA[0] is None:
        _GBA[0] = h.GlbBody(A_GLB)
    return _GBA[0]


class MemBody(h.GlbBody):
    """a GlbBody-like body: A's prims with a welded rest move dU (n,3 m) and extra welded targets {name: (n,3)}"""

    def __init__(s, dU=None, shapes=None):
        b, g0 = body(), gbA()
        s.names = list(g0.names) + list((shapes or {}).keys())
        s.prims = []
        o = 0
        for p in g0.prims:
            n = len(p["P"])
            w = b.wid[o:o + n]; o += n
            P = p["P"] + (dU[w] if dU is not None else 0)
            T = dict(p["T"])
            for k, D in (shapes or {}).items():
                T[k] = D[w]
            s.prims.append(dict(mat=p["mat"], P=P, T=T))

    def bind(s, k, shapes):
        p = s.prims[k]
        X = p["P"].copy()
        for n, w in shapes.items():
            if w and n in p["T"]:
                X += w * p["T"][n]
        return X


def d2u(fr):
    return sh.dump_to_u(fr, body().wid)


def skin3(fr):
    """per concatenated dump vertex: the blended skin's 3x3 (columns Bx By Bz)"""
    if getattr(fr, "_S3", None) is None:
        A = np.vstack([x["A"] for x in fr.dump["surfs"]])
        fr._S3 = np.stack([A[:, 17:20], A[:, 20:23], A[:, 23:26]], -1)
    return fr._S3


def jac(fr, X):
    """(n,2,3) projection Jacobians at world points X"""
    Pm = fr.Pm
    q = np.c_[X, np.ones(len(X))] @ Pm.T
    uv = q[:, :2] / q[:, 2:]
    J = (Pm[None, :2, :3] - uv[:, :, None] * Pm[None, 2:3, :3]) / q[:, 2, None, None]
    return J


def box_of(fr, pad=(220, 170, 220, 330)):
    """a box round both arms' joints"""
    P = np.array([jscreen(fr, n) for n in ("upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r")])
    x0, y0 = P.min(0); x1, y1 = P.max(0)
    return (int(max(x0 - 140, 0)), int(max(y0 - 140, 0)), int(min(x1 + 140, 1920)), int(min(y1 + 60, 1080)))


def grid(tiles, out, cols=2, gap=6):
    from PIL import Image
    w = max(t.width for t in tiles); hh = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    s = Image.new("RGB", (cols * w + (cols - 1) * gap, rows * hh + (rows - 1) * gap), (20, 20, 20))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * (w + gap), (i // cols) * (hh + gap)))
    s.save(out)
    return s
