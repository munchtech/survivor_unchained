"""Her body AS WORN under a piece (P2 gear, the plate top's cups): the rest a rigid plate is made to measure for.

A top's hold gives her support (HerWear -> P1Jiggle.SetSupport: ArmorHold.support, else (1 - amount) / 0.45), and the
support moves her at REST whenever the piece is on: her form_support_lift / _press / _fill shapes, and her springs'
equilibrium (godot/logic/Play/P1Springs.cs Integrate + Finish: sag, press and tilt at the support; a push-up, support 1,
rests each breast's tip about 20 mm above the bare bind). A bendy vertex rides her skin's weights and shapes and follows
by itself. A rigid component rides its slot's roles only (rigid_roles.json: a top's plates ride the spine), so a cup
fitted to the bare bind sat where her breast is NOT while the piece is worn, and her skin came through it at rest.
The rule (rigid_roles.json slots.<slot>.worn_rest, a spring group; "worn_rest" names the springs file and body row):
gear_fit eval_unit fits such a slot's rigid components to the worn body (its points, and the move of each bound point by
its own skin blend), and stores them so the engine's own pose of them (their blend, their mean shape deltas) lands them
there. No support, no springs row, or bones the body lacks: None (the build is what it was).

THE JOINS (JOIN; all read off the authored mesh and the body, nothing per piece). The worn fit moves plates, so what
was authored joined must stay joined:
- weld: rigid components that touch (points within JOIN "weld_m") are one group (a cup, its rim, its rivets): one fit.
  A group that holds a component big enough to lead (gear_fit SMALL_SHARE) is a PLATE; any other is a FITTING (a
  buckle, a clasp, a strap's rivet).
- a plate is fitted to her worn skin, the largest first; a plate within JOIN "link_m" of plates already fitted is a
  bridge (a gore between two cups) and is fitted to THEIR moves instead (each of its points to the nearer plate's).
  A bridge keeps its JOINTS on its plates (its points within "link_m" of them) and its span rests ON her worn skin
  between them, as a gore does on a pushed-up bust (it does not tack to the sternum: it floats on the tissue the cups
  press together). Its span clears her worn skin by the plates' own stand-off (gear_field RIGID "clear_m") with the
  least motion: first a rigid HINGE about the line through its joints (bridge_hinge: the smallest turn, within JOIN
  "turn", that leaves nothing a lift cannot finish), then, for what a hinge cannot clear, a smooth LIFT off her that is
  zero at the joints and never steeper than JOIN "strain" (bridge_lift; the steel is shaped to her at the build and
  rides one blend, it never bends in motion). What is still under after both (a point too near a joint) is the tuck's.
  (Not cleared at all, her pressed-in breasts stood 8 mm through the gore's ends and the tuck left 4 to 6 mm; cleared
  as one rigid part by one translation it went 16 mm forward, 19 mm proud of its cups.)
- a fitting rides what it sits on: the plain mean of her skin's weights over its own footprint (no slot roles: a
  buckle over the clavicle follows the clavicle as the strap under it does), placed by the join field below.
- the join field: a bendy vertex (or a fitting's point) at a fitted plate takes that plate's move and its blend of
  weights, fading to her skin's own by a STRAIGHT ramp over the plate's fade length (its largest mismatch with the
  bendy the fade reaches, over JOIN "strain", kept in JOIN "fade_m"), so a strap's end stays on its cup at rest and
  in motion and the strap runs taut from the plate to where it lies on her: its stretch even along it, no more than
  JOIN "strain", wherever a fitting sits on it. (An eased ramp sized by the seam's mismatch alone put up to 19 %
  squeeze and a bend at the ramp's middle, at the shoulder buckle: the strap zigzagged there seen edge on.) Where
  plates' fields overlap each counts by g / (1 - g): a point at a plate is on that plate alone.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for d in ("body", "anim"):
    if os.path.join(REPO, "tools", d) not in sys.path:
        sys.path.insert(0, os.path.join(REPO, "tools", d))
DOWN = np.array([0.0, -1.0, 0.0])
JOIN = {"weld_m": 0.002, "weld_n": 3, "link_m": 0.010, "strain": 0.25, "fade_m": (0.03, 0.12), "host": 0.5,
        "turn": 0.5, "turn_n": 50, "lift_rounds": 8, "lift_cos": 0.5, "lift_k": 12}
SHAPES = ("form_support_lift", "form_support_press", "form_support_fill")


def support_of(row):
    """(springs' support, (lift, press, fill)) of a row's hold, as ArmorHold gives them; None without a hold."""
    h = (row or {}).get("hold")
    if not h:
        return None
    s = h.get("support")
    s = float(np.clip((1 - float(h.get("amount", 1))) / 0.45, 0, 1)) if s is None else float(s)
    return s, tuple(float(h[k]) if h.get(k) is not None else s for k in ("lift", "press", "fill"))


def _ortho(m):
    u, _, vt = np.linalg.svd(m)
    return u @ vt


def _between(a, b):
    la, lb = np.linalg.norm(a), np.linalg.norm(b)
    if la < 1e-9 or lb < 1e-9:
        return np.eye(3)
    u, v = a / la, b / lb
    ax = np.cross(u, v)
    s, c = np.linalg.norm(ax), u @ v
    if s < 1e-12:
        return np.eye(3)
    k = ax / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + K * s + K @ K * (1 - c)


def spring_rest(names, parent, rest, support, group, doc, posed=None):
    """The skeleton-space globals with the group's springs at their equilibrium (upright, squash 0): rest [B, 4, 4]
    in, the posed globals out, and {spring: its tip's offset, m}. `posed` [B, 4, 4]: a clip frame's globals instead of
    the rest's (P1Springs: each spring's input is its posed local under its parent's new global, its frame the
    parent's turn from rest, down the skeleton's): the equilibrium the springs hold in that pose, no swing."""
    P = rest if posed is None else posed
    pinv = None if posed is None else np.linalg.inv(posed)
    G = P.copy()
    idx = {n: i for i, n in enumerate(names)}
    sf = doc.get("support", {}).get(group, {})
    F = lambda k: 1 + support * (sf[k] - 1) if k in sf else 1.0  # noqa: E731
    rinv = np.linalg.inv(rest)
    rows = [(r, s) for r in doc["springs"] if r["group"] == group for s in "lr"]
    rows = [x for x in rows if x[0]["mode"] != "shift"] + [x for x in rows if x[0]["mode"] == "shift"]
    new, lens, eqs = {}, {}, {}
    for r, s in rows:
        N = lambda k: r[k].replace("{s}", s)  # noqa: E731
        if N("bone") not in idx:
            continue
        b = idx[N("bone")]
        par, shift = parent[b], r["mode"] == "shift"
        side = 1.0 if rest[b][0, 3] >= 0 else -1.0
        if shift:
            tip, ln = np.zeros(3), 0.0
        elif "tip" in r and N("tip") in idx:
            tip = (rinv[b] @ rest[idx[N("tip")]])[:3, 3]
            ln = np.linalg.norm(tip)
        else:
            ln = r["len_m"]
            tip = np.array([0, ln, 0.0])
        lens[N("name")] = ln
        sl = lens.get(r["size_of"].replace("{s}", s), ln) if "size_of" in r else ln
        q = sl / r["size_ref_m"] if sl > 0 else 1.0
        sag, press, tilt = r["sag"] * q, r["press"] * q, r["tilt"] * q
        rs = r.get("rest_shows", 0.0)
        rd = np.array(r.get("rest_down", [0, -1, 0]), float)
        rd /= np.linalg.norm(rd)
        Gp = new.get(par, G[par])
        In = new[par] @ ((rinv if pinv is None else pinv)[par] @ P[b]) if par in new else G[b]
        Fm = _ortho(Gp[:3, :3] @ rinv[par][:3, :3])
        eq = (Fm @ np.array([-side, 0, 0])) * (press * F("press")) + DOWN * (sag * F("sag")) \
            + (DOWN - Fm @ rd) * (tilt * F("reach")) - Fm @ (np.array([-side * press * rs, 0, 0]) + rd * (sag * rs))
        o = In.copy()
        if shift:
            o[:3, 3] += eq
        else:
            frm = In[:3, :3] @ tip
            o[:3, :3] = _between(frm, frm + eq) @ In[:3, :3]
        new[b], eqs[N("name")] = o, eq
    depth = lambda k: 0 if parent[k] < 0 else 1 + depth(parent[k])  # noqa: E731
    for k in sorted(range(len(names)), key=depth):       # (bones under a sprung bone ride its new pose)
        if k not in new and parent[k] in new:
            new[k] = new[parent[k]] @ ((rinv if pinv is None else pinv)[parent[k]] @ P[k])
    for k, g in new.items():
        G[k] = g
    return G, eqs


class Worn:
    """body: the worn Body; A [nv, 3, 4]: each body vertex's skin blend of the worn pose; weights: the shapes' values."""

    def __init__(self, base, S, weights, eqs):
        self.S, self.weights, self.eqs, self.base = S, weights, eqs, base
        self.A = np.einsum("nk,nkij->nij", base.W, S[base.J][:, :, :3, :])
        V = base.V.copy()
        for nm, w in weights.items():
            V += w * base.shapes[nm]
        self.body = base.with_points(np.einsum("nij,nj->ni", self.A[:, :, :3], V) + self.A[:, :, 3], base.name + "+worn")

    def move(self, tri, w, X):
        """Points X bound at (triangle, barycentrics): each moved as its bound skin point moves into the worn rest."""
        Tv = self.base.T[tri]
        M = (w[:, :, None, None] * self.A[Tv]).sum(1)
        d = np.zeros_like(X)
        for nm, k in self.weights.items():
            d += k * (w[:, :, None] * self.base.shapes[nm][Tv]).sum(1)
        return np.einsum("nij,nj->ni", M[:, :, :3], X + d) + M[:, :, 3]

    def mats(self, tri, w):
        """[n, 3, 4]: each bound point's own skin blend of the worn pose."""
        return (w[:, :, None, None] * self.A[self.base.T[tri]]).sum(1)

    def unpose_each(self, Y, J, W, deltas):
        """Worn points Y as STORED under per-point blends (J, W [n, 8]) and shape deltas {shape: [n, 3]}; also each
        point's inverse linear part [n, 3, 3] (its normal's way back)."""
        M = np.einsum("nk,nkij->nij", np.asarray(W, np.float64), self.S[np.asarray(J, np.int64)][:, :, :3, :])
        Li = np.linalg.inv(M[:, :, :3])
        X0 = np.einsum("nij,nj->ni", Li, Y - M[:, :, 3])
        for nm, d in deltas.items():
            X0 = X0 - self.weights.get(nm, 0.0) * d
        return X0, Li

    def unpose(self, X, N, J, W, deltas):
        """A rigid component's worn points X (normals N) as STORED: the engine poses them by the component's own blend
        (J, W [8]) and its mean shape deltas {shape: [3]}, and they land at X."""
        M = np.einsum("k,kij->ij", W, self.S[J][:, :3, :])
        Li = np.linalg.inv(M[:, :3])
        X0 = (X - M[:, 3]) @ Li.T
        for nm, d in deltas.items():
            X0 = X0 - self.weights.get(nm, 0.0) * d
        return X0, N @ Li.T


def law(row, roles, names=None):
    """What a row's piece does to her springs: (support_of(row), the slot's spring group, the springs file's body row),
    or None (no switch on the slot, no hold or support, no springs row; with `names`, a body with none of the group's
    spring bones). roles: rigid_roles.json."""
    grp = (roles.get("slots", {}).get((row or {}).get("slot"), {}) or {}).get("worn_rest")
    cfg, sup = roles.get("worn_rest"), support_of(row)
    if not grp or not cfg or sup is None or not (sup[0] or any(sup[1])):
        return None
    doc = json.load(open(os.path.join(REPO, cfg["file"]), encoding="utf-8"))["bodies"].get(cfg["body"])
    if doc is None:
        return None
    if names is not None and not any(r["bone"].replace("{s}", s) in names for r in doc["springs"]
                                     if r["group"] == grp for s in "lr"):
        return None
    return sup, grp, doc


def state(glb_path, joint_names, shape_names, row, roles):
    """(S [B, 4, 4] the worn pose's skin matrices, {shape: weight}, the springs' offsets) of a body glb under the row's
    piece, or None (see the module doc). roles: rigid_roles.json."""
    if not glb_path or law(row, roles) is None:
        return None
    from gl import Glb
    g = Glb(glb_path)
    joints = g.js["skins"][0]["joints"]
    at = {j: k for k, j in enumerate(joints)}
    parent = np.full(len(joints), -1)
    for j in joints:
        for c in g.js["nodes"][j].get("children", []):
            if c in at:
                parent[at[c]] = at[j]
    names = list(joint_names) if joint_names is not None else [g.nodes[j].get("name") for j in joints]
    lw = law(row, roles, names)
    if lw is None:
        return None
    sup, grp, doc = lw
    ibm = np.asarray(g.skeleton(0).ibm, np.float64)
    G, eqs = spring_rest(names, parent, np.linalg.inv(ibm), sup[0], grp, doc)
    weights = {nm: v for nm, v in zip(SHAPES, sup[1]) if v and nm in shape_names}
    return G @ ibm, weights, eqs


def worn(body, row, roles):
    """The Worn of `body` under the row's piece, or None (see the module doc). roles: rigid_roles.json."""
    st = state(getattr(body, "glb", None), body.joint_names, body.shapes, row, roles)
    return None if st is None else Worn(body, *st)


def pose(S, weights, P, J, W, targets, N=None):
    """A glb mesh's own vertices in the worn pose (the engine's order: shapes, then the skin): points, and normals
    when given. targets: {shape: [n, 3]}."""
    J, W = np.asarray(J, np.int64), np.asarray(W, np.float64)
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-12)
    M = np.einsum("nk,nkij->nij", W, S[J][:, :, :3, :])
    V = np.asarray(P, np.float64).copy()
    for nm, k in weights.items():
        if nm in targets:
            V += k * targets[nm]
    Pw = np.einsum("nij,nj->ni", M[:, :, :3], V) + M[:, :, 3]
    if N is None:
        return Pw
    Nw = np.einsum("nij,nj->ni", M[:, :, :3], N)
    return Pw, Nw / np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)


# ---------------------------------------------------------------- the joins

def clusters(X, comp, lead0):
    """Rigid components welded by touch (JOIN "weld_m", at least "weld_n" points of one within it of the other). X: the
    tier's authored points, comp: each point's component (-1 bendy), lead0: the bind's leaders. Returns (lead: each
    component's group, named by its largest member; plate: per component, its group holds a bind-time leader)."""
    from scipy.spatial import cKDTree
    nc = int(comp.max()) + 1
    rg = comp >= 0
    cr = comp[rg]
    par = np.arange(nc)

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    pairs = cKDTree(X[rg]).query_pairs(JOIN["weld_m"], output_type="ndarray")
    if len(pairs):
        a, b = cr[pairs[:, 0]], cr[pairs[:, 1]]
        m = a != b
        # (a touch counts by the points of the lower-numbered side that are in it)
        lo, hi = np.minimum(a[m], b[m]), np.maximum(a[m], b[m])
        pt = np.where(a[m] < b[m], pairs[m][:, 0], pairs[m][:, 1])
        key = np.unique(np.c_[lo, hi, pt], axis=0)
        uq, cnt = np.unique(key[:, :2], axis=0, return_counts=True)
        for (i, j), n in zip(uq, cnt):
            if n >= JOIN["weld_n"]:
                par[find(i)] = find(j)
    root = np.array([find(c) for c in range(nc)])
    size = np.bincount(cr, minlength=nc)
    lead, plate = np.arange(nc), np.zeros(nc, bool)
    big = np.asarray(lead0)[:nc] == np.arange(nc)
    for r in np.unique(root):
        mem = np.nonzero(root == r)[0]
        lead[mem] = mem[np.argmax(size[mem])]
        plate[mem] = big[mem].any()
    return lead, plate


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


class Joins:
    """The plates fitted so far and the field they give what is joined to them. Xb, Yb: the tier's bendy points as
    authored and as her skin alone carries them into the worn rest (a seam's mismatch is measured on them)."""

    def __init__(self, Xb, Yb):
        self.Xb, self.Yb, self.rows = Xb, Yb, {}

    def add(self, c, Xg, M, ca, cb):
        """A fitted plate: its group's authored points Xg and its move X -> (X - ca) M^T + cb."""
        from scipy.spatial import cKDTree
        tree = cKDTree(Xg)
        lo, hi = JOIN["fade_m"]
        fade, gap = lo, 0.0
        if len(self.Xb):
            d = tree.query(self.Xb)[0]
            seam = d <= JOIN["weld_m"] if (d <= JOIN["weld_m"]).any() else d <= JOIN["link_m"]
            if seam.any():
                # (the mismatch is the largest over the bendy the fade reaches, not the seam's alone: at the seam her
                # skin still goes with the plate, further along a strap it does not, and the strap takes it all)
                mis = np.linalg.norm((self.Xb - ca) @ M.T + cb - self.Yb, axis=1)
                for _ in range(8):
                    gap = float(mis[d <= JOIN["weld_m"] + fade].max())
                    f = float(np.clip(gap / JOIN["strain"], lo, hi))
                    if f <= fade:
                        break
                    fade = f
        self.rows[int(c)] = dict(tree=tree, M=M, ca=ca, cb=cb, fade=fade, gap=gap)

    def bridge(self, X):
        """Targets of a plate's points X from the fitted plates it is linked to (within JOIN "link_m"), each point by
        the inverse square of its distance to them; None when it is linked to none."""
        ds = {c: r["tree"].query(X)[0] for c, r in self.rows.items()}
        ds = {c: d for c, d in ds.items() if d.min() <= JOIN["link_m"]}
        if not ds:
            return None
        Y, wsum = np.zeros_like(X), np.zeros(len(X))
        for c, d in ds.items():
            r = self.rows[c]
            w = 1.0 / (d * d + 1e-8)
            Y += w[:, None] * ((X - r["ca"]) @ r["M"].T + r["cb"])
            wsum += w
        return Y / wsum[:, None]

    def reach(self, X, skip=None):
        """Each point's distance to the nearest fitted plate it is linked to (as bridge links them; `skip`: the row
        that is these points' own); None when none."""
        ds = [r["tree"].query(X)[0] for c, r in self.rows.items() if c != skip]
        ds = [d for d in ds if d.min() <= JOIN["link_m"]]
        return np.min(ds, axis=0) if ds else None

    def field(self, X, Ys):
        """Points X (authored; Ys as her skin alone carries them) -> (their worn targets, each one's share of a plate's
        move 0..1, the plate it is nearest by that share or -1)."""
        Y, G, gs = np.zeros_like(X), np.zeros(len(X)), np.zeros(len(X))
        near = np.full(len(X), -1)
        for c, r in self.rows.items():
            # (a straight ramp: a strap between a plate and where it lies on her is taut, its stretch even along it;
            # an eased ramp put half as much again at its middle, where a buckle sits, and the strap zigzagged there)
            g = np.clip(1.0 - np.maximum(0.0, r["tree"].query(X)[0] - JOIN["weld_m"]) / r["fade"], 0.0, 1.0)
            # (where plates' fields overlap each counts by g / (1 - g): a point at a plate is on that plate alone)
            w = g / (1.0 - g + 1e-6)
            Y += w[:, None] * ((X - r["ca"]) @ r["M"].T + r["cb"])
            gs += w
            near = np.where(g > G, c, near)
            G = np.maximum(G, g)
        on = gs > 0
        out = Ys.copy()
        out[on] = (1 - G[on])[:, None] * Ys[on] + G[on][:, None] * Y[on] / gs[on][:, None]
        return out, G, near


# ---------------------------------------------------------------- a bridge on her worn skin

def _lift_cap(d):
    """What a bridge point may lift: JOIN "strain" of its distance to the plate it is joined to (none at the plate)."""
    return JOIN["strain"] * np.maximum(0.0, d)


def bridge_hinge(body, Y, d, tgt, ok):
    """The smallest turn of a bridge about the line through its joints that rests its span on her worn skin.
    Y: the bridge's points as its plates carry them; d: each one's authored distance to the nearest plate it is linked
    to (its joints: d <= JOIN "link_m"); tgt: the clearance each must reach on `body` (her worn skin); ok: the points
    held to it (those clear on the bind). A turn is as good as the best one when the root mean square of what it leaves
    short is within 0.1 mm of the best's; the smallest such is taken (the lift, bridge_lift, is for what is left).
    Returns (Q [3, 3], p0 [3]: Y -> (Y - p0) Q^T + p0, info)."""
    import gear_field
    info = {"turn_deg": 0.0}
    jt = d <= JOIN["link_m"]
    if jt.sum() < 3 or not ok.any():
        return np.eye(3), Y.mean(0), info
    p0 = Y[jt].mean(0)
    ax = np.linalg.svd(Y[jt] - p0, full_matrices=False)[2][0]
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    n = max(1, int(ok.sum()))

    def at(a):
        Q = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
        c = gear_field.signed_clear(body, (Y - p0) @ Q.T + p0, k=16)[0]
        e = np.maximum(0.0, tgt - c)[ok]
        return Q, float(np.sqrt((e * e).sum() / n))
    angs = np.linspace(-JOIN["turn"], JOIN["turn"], 2 * JOIN["turn_n"] + 1)
    cost = np.array([at(a)[1] for a in angs])
    if os.environ.get("GEAR_BRIDGE_DEBUG"):
        print("bridge_hinge rms mm by deg:", " ".join(f"{np.degrees(a):+.0f}:{c * 1000:.2f}" for a, c in list(zip(angs, cost))[::5]))
    lim = cost.min() + 1e-4
    good = np.nonzero(cost <= lim)[0]
    k = good[np.argmin(np.abs(angs[good]))]
    a = angs[k]
    if abs(a) > 1e-9:
        lo = angs[k - 1] if a > 0 else angs[k + 1]      # (the grid step toward no turn: not as good)
        for _ in range(8):
            mid = 0.5 * (lo + a)
            if at(mid)[1] <= lim:
                a = mid
            else:
                lo = mid
    info.update(turn_deg=round(float(np.degrees(a)), 2), hinge_rms_mm=[round(float(cost[len(angs) // 2]) * 1000, 2), round(at(a)[1] * 1000, 2)])
    return at(a)[0], p0, info


def bridge_lift(body, Y, d, tgt, ok):
    """The smooth lift that finishes a hinged bridge: each point still short of its clearance is raised along the one
    way off her under the bridge (her worn skin's mean normal there), as a smooth bump that takes its neighbours with it
    (never steeper than JOIN "strain"), nothing at the joints (_lift_cap), in rounds until clear or at the cap.
    Returns (L [n, 3] the lift, R [n, 3, 3] each point's turn for its normal, info); (None, None, info) for no lift."""
    import gear_field
    from scipy.spatial import cKDTree
    from scipy.spatial.distance import cdist
    c, fn = gear_field.signed_clear(body, Y, k=16)
    need = np.where(ok, tgt - c, 0.0)
    info = {"under_hinged": int((ok & (c < 0)).sum()), "deep_hinged_mm": round(float(max(0.0, -c[ok].min() if ok.any() else 0.0)) * 1000, 2)}
    cap = _lift_cap(d)
    if not ((need > 1e-5) & (cap > 1e-6)).any():
        return None, None, info
    n = fn[ok].mean(0)
    n = n / max(np.linalg.norm(n), 1e-12)
    D = cdist(Y, Y)
    h = np.zeros(len(Y))
    for _ in range(JOIN["lift_rounds"]):
        c, fn = gear_field.signed_clear(body, Y + h[:, None] * n, k=16)
        need = np.where(ok, tgt - c, 0.0)
        up = (need > 1e-5) & (h < cap - 1e-6)
        if not up.any():
            break
        h = h + np.where(up, need / np.maximum(fn @ n, JOIN["lift_cos"]), 0.0)
        r = np.maximum(1.5 * h / JOIN["strain"], JOIN["link_m"])
        h = np.minimum(cap, (h[None, :] * _smooth(1.0 - D / r[None, :])).max(1))
    L = h[:, None] * n
    c = gear_field.signed_clear(body, Y + L, k=16)[0]
    # (each point's normal turns as its neighbourhood did)
    nb = cKDTree(Y).query(Y, k=min(JOIN["lift_k"], len(Y)))[1]
    A, B = Y[nb], (Y + L)[nb]
    A, B = A - A.mean(1, keepdims=True), B - B.mean(1, keepdims=True)
    u, _, vt = np.linalg.svd(np.einsum("nki,nkj->nij", A, B))
    R = np.einsum("nji,nkj->nik", vt, u)
    flip = np.linalg.det(R) < 0
    if flip.any():
        vt[flip, 2] *= -1
        R = np.einsum("nji,nkj->nik", vt, u)
    info.update(lift_mm=round(float(h.max()) * 1000, 2), lifted=int((h > 1e-5).sum()), under=int((ok & (c < 0)).sum()),
                deep_mm=round(float(max(0.0, -c[ok].min() if ok.any() else 0.0)) * 1000, 2))
    return L, R, info
