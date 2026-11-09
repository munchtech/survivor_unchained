"""P1 R1 form view (the form library's working look): build_topo stages 1-2 (sliders, join, stance, the post-join
fields, the head placed) on the close tier in seconds, then smooth clay and painted-cel tiles plus the neck numbers.
    python tools/body/formview.py SPEC[,SPEC...] OUT.png [--views front,q34,side,back] [--y0 --y1 --x --px] [--both|--cel]
The cel row: two value masses and a soft terminator (what a cel band does to a form: a ledge or a dent shows as a
kinked terminator). Arms at rest (the A-pose); formview_hang.py poses a BUILD with the arms hanging."""
#   [--npz OUT.npz]  (V, T body+head for other tools)   [--pose hang]  (not here: use the build + bust-style poser)
import sys, os, json, math, argparse
import numpy as np
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WT + "/tools/body")
import build_topo as bt, headbake, ray
from gl import Glb
from sliders import load_spec, head_move
from PIL import Image

_A = {}


def body(spec_path, tier="close"):
    spec = load_spec(spec_path)
    if "A" not in _A:
        _A["A"] = Glb(os.path.join(bt.REPO, spec["ref"]))
        _A["baked0"] = headbake.bake(_A["A"], bt.HEADS)
    A = _A["A"]
    g = bt.with_defaults(spec) and bt.ground_offset(bt.with_defaults(spec))     # (P1 R1 sliders: grounded as the build is)
    if g:
        spec = {**spec, "_ground_m": g}
    hm = np.asarray(head_move(spec.get("sliders", {})), float) + np.asarray(g or [0.0, 0.0, 0.0], float)
    baked = {h: dict(v, P=v["P"] + hm[None, :]) for h, v in _A["baked0"].items()}
    rep = {}
    z, V = bt.stage_base(spec, tier, rep)
    V, ring, hv = bt.stage_place(spec, z, V, A, baked, rep)
    V = bt.stage_forms(spec, tier, z, V, ring, rep)
    Q = z["Q"]
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    H = baked["HeroineHead"]["P"]
    HT = A.mesh("HeroineHead").T
    return V, T, H, HT, z, rep


def vnormals(V, T, weld_tol=2e-5):
    """Smooth vertex normals with coincident points welded (UV splits and the head/body ring share one normal, as
    the game's export gives the ring the head's normals)."""
    from gl import weld
    w = np.asarray(weld(V, weld_tol))
    Vw = np.zeros((w.max() + 1, 3))
    Vw[w] = V
    return _vn(Vw, w[T])[w]


def _vn(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def render(V, T, view, cel=False, N=None):
    s = ray.scene(V, T)
    x, y = view.grid()
    org = (view.o + x[..., None] * view.ex + y[..., None] * view.ey + 5.0 * view.cam).reshape(-1, 3)
    d = np.broadcast_to(-view.cam, org.shape)
    pid, tf = ray.hits(s, org, d)
    m = pid >= 0
    img = np.ones(len(pid))
    N = vnormals(V, T) if N is None else N
    t = T[pid[m]]
    P = org[m] + tf[m][:, None] * d[m]
    a, b, c = V[t[:, 0]], V[t[:, 1]], V[t[:, 2]]
    v0, v1, v2 = b - a, c - a, P - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bu = 1 - bv - bw
    n = N[t[:, 0]] * bu[:, None] + N[t[:, 1]] * bv[:, None] + N[t[:, 2]] * bw[:, None]
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    n = np.where((n @ view.cam)[:, None] < 0, -n, n)
    L = 0.62 * view.cam + 0.55 * view.ey - 0.45 * view.ex
    L /= np.linalg.norm(L)
    lam = np.clip(n @ L, 0, 1)
    if cel:
        # painted-cel read: two value masses and a soft terminator, a rim; what a cel band does to the form
        band = 1.0 / (1.0 + np.exp(-(lam - 0.32) / 0.025))
        img[m] = 0.30 + 0.50 * band + 0.10 * np.clip(n @ view.cam, 0, 1) ** 4
    else:
        img[m] = 0.16 + 0.66 * lam + 0.10 * np.clip(n @ view.cam, 0, 1)
    return img.reshape(view.h, view.w)


VIEWS = {"front": 0, "q34": 35, "side": 90, "q34b": 145, "back": 180, "q34r": -35, "sider": -90}


def tiles(V, T, views, y0, y1, xw, px, cel):
    out = []
    N = vnormals(V, T)
    for nm in views:
        yaw = VIEWS[nm] if nm in VIEWS else float(nm)
        a = math.radians(yaw)
        ex = [math.cos(a), 0, -math.sin(a)]
        cam = [math.sin(a), 0, math.cos(a)]
        v = ray.View([0, 0, 0], ex, [0, 1, 0], cam, px, -xw, xw, y0, y1)
        out.append((np.clip(render(V, T, v, cel, N), 0, 1) * 255).astype(np.uint8))
    return np.concatenate(out, 1)


def neck_numbers(V, H, ring=None):
    """R2's neckprof on the built rest: the chin (lowest head point near the front midline), the shoulder top under it
    at x 5..17 cm (both sides averaged), the width 3 cm under the chin; plus the neck's narrowest width between the
    ring and 8 cm under the chin and its depth there, and the trapezius slope 7->13 cm (deg below horizontal)."""
    hz = H[(np.abs(H[:, 0]) < 0.02) & (H[:, 2] > H[:, 2].mean())]
    chin = hz[:, 1].min()
    prof = []
    for x in [0.05, 0.07, 0.09, 0.11, 0.13, 0.15, 0.17]:
        ys = []
        for s in (1, -1):
            sel = V[(np.abs(V[:, 0] * s - x) < 0.004) & (V[:, 1] < chin) & (np.abs(V[:, 2] - V[:, 2].mean()) < 0.2)]
            ys.append(sel[:, 1].max())
        prof.append(round((np.mean(ys) - chin) * 1000))
    def width(y):
        nb = V[(np.abs(V[:, 1] - y) < 0.003) & (np.abs(V[:, 0]) < 0.12)]
        return (nb[:, 0].max() - nb[:, 0].min()) * 1000 if len(nb) else float("nan")
    w3 = width(chin - 0.03)
    ws = [(round(width(chin - k / 100)), k) for k in range(2, 9)]
    slope = math.degrees(math.atan2((prof[1] - prof[4]), 60))
    return {"chin_mm": round(chin * 1000), "top_under_chin_5_17": prof, "w3": round(w3), "widths_2_8cm": ws,
            "trap_slope_7_13_deg": round(slope, 1), "height_mm": round(max(V[:, 1].max(), H[:, 1].max()) * 1000)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--views", default="front,q34,side,back")
    ap.add_argument("--y0", type=float, default=1.10)
    ap.add_argument("--y1", type=float, default=1.88)
    ap.add_argument("--x", type=float, default=0.30)
    ap.add_argument("--px", type=float, default=700)
    ap.add_argument("--cel", action="store_true")
    ap.add_argument("--both", action="store_true", help="a clay row and a cel row")
    ap.add_argument("--npz")
    a = ap.parse_args()
    specs = a.spec.split(",")
    rows = []
    for sp in specs:
        V, T, H, HT, z, rep = body(sp)
        VV = np.concatenate([V, H])
        TT = np.concatenate([T, HT + len(V)])
        print(os.path.basename(sp), json.dumps(neck_numbers(V, H)), "ring_move", rep["place"]["ring_move_max_mm"])
        vs = a.views.split(",")
        if a.both:
            rows.append(tiles(VV, TT, vs, a.y0, a.y1, a.x, a.px, False))
            rows.append(tiles(VV, TT, vs, a.y0, a.y1, a.x, a.px, True))
        else:
            rows.append(tiles(VV, TT, vs, a.y0, a.y1, a.x, a.px, a.cel))
        if a.npz:
            np.savez(a.npz, V=V, T=T, H=H, HT=HT)
    Image.fromarray(np.concatenate(rows, 0)).save(a.out)
    print("wrote", a.out)
