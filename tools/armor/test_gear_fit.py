"""Unit tests for the gear fit engine's bind/evaluate core on a tiny synthetic body (pytest, or python this file)."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gear_fit as gf  # noqa: E402


def cylinder(r=0.05, L=0.3, n=32, m=24):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    y = np.linspace(0, L, m)
    P = np.array([[r * math.cos(t), yy, r * math.sin(t)] for yy in y for t in a])
    T = []
    for i in range(m - 1):
        for k in range(n):
            p, q = i * n + k, i * n + (k + 1) % n
            T += [[p, p + n, q], [q, p + n, q + n]]
    return P, np.array(T)


def body(P, T):
    n = len(P)
    J = np.zeros((n, 8), np.int64)
    J[:, 1] = 1
    W = np.zeros((n, 8))
    W[:, 0] = 1 - P[:, 1] / P[:, 1].max()
    W[:, 1] = 1 - W[:, 0]
    head = np.array([[0, 5.0, 0], [0.01, 5.0, 0], [0, 5.0, 0.01]])
    return gf.Body(P, T, J, W, {"s": np.tile([0, 0.001, 0], (n, 1))}, head, np.array([[0, 1, 2]]),
                   np.zeros((3, 4), np.int64), np.c_[np.ones(3), np.zeros((3, 3))], ["a", "b"])


def sleeve(r=0.058, n=24, m=10):
    P, T = cylinder(r, 0.2, n, m)
    return P + [0, 0.05, 0], T


def test_bind_eval_identity():
    P, T = cylinder()
    b = body(P, T)
    X, _ = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    Xe, _ = gf.eval_points(b, tri, bq, off)
    assert np.abs(Xe - X).max() < 1e-8          # 0.01 micron: the bind body gives back the bind geometry


def test_follows_and_rigid_preserved():
    P, T = cylinder()
    b = body(P, T)
    X, Ts = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    # a second body: +8% girth fading along y, the sleeve follows it
    s = 1 + 0.08 * np.clip(P[:, 1] / 0.3, 0, 1)
    b2 = b.with_points(np.vstack([P * np.c_[s, np.ones(len(P)), s], b.V[b.nt:]]), "fat")
    X2, _ = gf.eval_points(b2, tri, bq, off)
    assert not np.isnan(X2).any()
    r1 = np.hypot(X[:, 0], X[:, 2])
    r2 = np.hypot(X2[:, 0], X2[:, 2])
    assert (r2 > r1 + 1e-4).mean() > 0.9          # grew with the body
    # rigid: Procrustes of the bendy evaluation onto the bind points, every pairwise distance kept
    R, ca, cb = gf.kabsch(X, X2)
    Xr = (X - ca) @ R.T + cb
    d0 = np.linalg.norm(X[:, None] - X[None], axis=2)
    d1 = np.linalg.norm(Xr[:, None] - Xr[None], axis=2)
    assert np.abs(d1 - d0).max() < 5e-8
    # smoothing a zero displacement is the identity
    E = gf.edges_of(Ts)
    D = gf.smooth_field(np.zeros_like(X), E, len(X), np.ones(len(X)), 8)
    assert np.abs(D).max() == 0


def test_weights_at_bound_point():
    P, T = cylinder()
    b = body(P, T)
    X, _ = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    J, W = gf.body_weights(b, tri.astype(np.int64), gf.unq(bq))
    assert np.allclose(W.sum(1), 1, atol=1e-6)
    wb = np.where(J == 1, W, 0).sum(1)
    yb = (X[:, 1]) / 0.3
    assert np.abs(wb - np.clip(yb, 0, 1)).max() < 0.05


def test_field_two_cylinders():
    """The follow field: a sleeve bound across two cylinders (2 cm stand-off) follows one cylinder's +10% girth as one
    smooth surface (the per-triangle evaluation tears it where the binding switches cylinders), clear of the new skin,
    and the bind body gives back the bind geometry exactly."""
    import gear_field as gfl
    P, T = cylinder(0.05, 0.3, 48, 30)
    n = len(P)
    P2 = np.vstack([P + [-0.055, 0, 0], P + [0.055, 0, 0]])
    T2 = np.vstack([T, T + n])
    b = body(P2, T2)
    a = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    X = np.array([[0.125 * math.cos(t), y, 0.07 * math.sin(t)] for y in np.linspace(0.05, 0.25, 21) for t in a])
    Ts = []
    for i in range(20):
        for k in range(96):
            p_, q = i * 96 + k, i * 96 + (k + 1) % 96
            Ts += [[p_, p_ + 96, q], [q, p_ + 96, q + 96]]
    E = gf.edges_of(np.array(Ts))
    tri, bq, off = gf.bind_points(b, X)[:3]
    c0 = np.linalg.norm(off.astype(np.float64), axis=1)
    V = b.V.copy()
    r = V[n:2 * n] - [0.055, 0, 0]
    V[n:2 * n] += 0.10 * r * [1, 0, 1]                     # the right cylinder grows 10% in girth
    b2 = b.with_points(V, "grown")
    Xb, Fb = gf.eval_points(b, tri, bq, off)
    X2, F2 = gf.eval_points(b2, tri, bq, off)
    Xe, _ = gfl.exact_follow(X2, F2, Xb, Fb, off)
    Xf, G = gfl.field_for(b2, b)(Xb)
    bt = gfl.beta(c0)
    n0 = gfl.signed_clear(b, Xb, k=16)[1]
    Xn, _ = gfl.follow_solve(b2, Xe + bt[:, None] * (Xf - Xe), Xb, np.array(Ts), G, gfl.field_for(b2, b).gradient(Xb), c0,
                             n0, np.ones(len(X), bool))
    l0 = np.linalg.norm(Xb[E[:, 0]] - Xb[E[:, 1]], axis=1)
    st = lambda Y: np.abs(np.linalg.norm(Y[E[:, 0]] - Y[E[:, 1]], axis=1) / l0 - 1)  # noqa: E731
    assert not np.isnan(Xn).any()
    assert st(Xe).max() > 0.18                              # bound triangle by triangle: torn where the binding switches
    assert st(Xn).max() < 0.16                              # the field: one surface (the cylinder itself grew 10%)
    assert st(Xn).max() < 0.8 * st(Xe).max()
    c, _ = gfl.signed_clear(b2, Xn, k=16)
    assert (c > gfl.push_req(c0) - 5e-4).all()              # clear of the grown body (a stand-off keeps 60%)
    grew = Xn[:, 0] > 0.08
    assert (np.hypot(Xn[grew, 0] - 0.055, Xn[grew, 2]) > np.hypot(Xb[grew, 0] - 0.055, Xb[grew, 2]) + 2e-3).all()
    gfl._CACHE.clear()
    Xi, _ = gfl.field_for(b.with_points(b.V.copy(), "same"), b)(Xb)
    assert np.abs(Xi - Xb).max() < 1e-12                    # no move: the bind geometry


def test_similarity_fit_scales():
    """A rigid component made to measure: a known rotation + translation + per-axis scale (along its own principal
    axes) comes back, the clamp holds, and the identity is exact."""
    import gear_field as gfl
    g = np.linspace(-1, 1, 7)
    A = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * [0.15, 0.08, 0.03]  # principal axes x, y, z
    M, ca, cb, s, P = gfl.similarity_fit(A, A)
    assert np.abs((A - ca) @ M.T + cb - A).max() < 1e-12 and np.abs(s - 1).max() < 1e-12
    th = 0.3
    R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    B = (A * [1.1, 0.95, 1.0]) @ R.T + [0.01, 0.02, -0.03]
    M, ca, cb, s, P = gfl.similarity_fit(A, B)
    assert np.abs((A - ca) @ M.T + cb - B).max() < 1e-3
    assert np.abs(np.sort(s) - np.sort([1.1, 0.95, 1.0])).max() < 0.005
    _, _, _, s2, _ = gfl.similarity_fit(A, A * [1.5, 1, 1])
    assert s2.max() <= 1.25 + 1e-12                        # clamped


def test_rigid_fit_clear_wrapping_plate():
    """A half-shell plate around a cylinder that grows 8% in girth: no single translation clears both its sides; the
    made-to-measure clear (translation + scales) does, and on the same body nothing moves."""
    import gear_field as gfl
    P, T = cylinder(0.05, 0.3, 64, 30)
    b = body(P, T)
    a = np.linspace(-0.6 * math.pi, 0.6 * math.pi, 40)
    A = np.array([[0.053 * math.sin(t), y, 0.053 * math.cos(t)] for y in np.linspace(0.08, 0.22, 12) for t in a])
    c_req, _ = gfl.signed_clear(b, A, k=16)
    M, ca, cb, info = gfl.rigid_fit_clear(b, A, A, A, c_req)
    assert np.abs((A - ca) @ M.T + cb - A).max() < 1e-12 and info["clear_mm"] == 0.0
    b2 = b.with_points(b.V * [1.08, 1, 1.08], "grown")
    t = gfl.rigid_clear(b2, A, c_req)
    c_t, _ = gfl.signed_clear(b2, A + t, k=16)
    M, ca, cb, info = gfl.rigid_fit_clear(b2, A, A, A, c_req)
    c, _ = gfl.signed_clear(b2, (A - ca) @ M.T + cb, k=16)
    assert c_t.min() < -1e-3                                # one translation leaves a side inside
    assert c.min() > -5e-5, (c.min(), info)
    assert max(info["scale"]) <= 1.25 and min(info["scale"]) >= 0.85


def ring_sleeve(rx, rz, x0, ys, na):
    a = np.linspace(0, 2 * math.pi, na, endpoint=False)
    X = np.array([[x0 + rx * math.cos(t), y, rz * math.sin(t)] for y in ys for t in a])
    Ts = []
    for i in range(len(ys) - 1):
        for k in range(na):
            p_, q = i * na + k, i * na + (k + 1) % na
            Ts += [[p_, p_ + na, q], [q, p_ + na, q + na]]
    return X, np.array(Ts)


def test_follow_solve_shrunk_cylinder():
    """The follow solve on the two-cylinder body with the right cylinder 12% thinner: a tight sleeve on it (2 mm) and a
    stand-off sleeve over both (2 cm) are solved together (one tier): the tight one keeps its clearance (p95 within
    0.5 mm), nothing is nearer the new skin than push_req, the stretch beyond the field's own stays under the gates; a
    dent (to 5 mm off the skin, 12 mm asked) comes out as one smooth bump (no edge over 25%); the bind body gives Y back exactly."""
    import gear_field as gfl
    P, T = cylinder(0.05, 0.3, 48, 30)
    n = len(P)
    b = body(np.vstack([P + [-0.055, 0, 0], P + [0.055, 0, 0]]), np.vstack([T, T + n]))
    ys = np.linspace(0.05, 0.25, 21)
    Xt, Tt = ring_sleeve(0.052, 0.052, 0.055, ys, 64)
    Xs, Ts = ring_sleeve(0.125, 0.07, 0.0, ys, 96)
    Xb = np.vstack([Xt, Xs])
    Tb = np.vstack([Tt, Ts + len(Xt)])
    V = b.V.copy()
    r = V[n:2 * n] - [0.055, 0, 0]
    V[n:2 * n] -= 0.12 * r * [1, 0, 1]
    b2 = b.with_points(V, "shrunk")
    gfl._CACHE.clear()
    c0, n0 = gfl.signed_clear(b, Xb, k=16)
    fld = gfl.field_for(b2, b)
    Y, G = fld(Xb)
    Gk = fld.gradient(Xb)
    sel = np.ones(len(Xb), bool)
    X, st = gfl.follow_solve(b2, Y, Xb, Tb, G, Gk, c0, n0, sel)
    assert not np.isnan(X).any()
    c, _ = gfl.signed_clear(b2, X, k=16)
    tight = np.abs(c0) < gfl.HOLD["in_m"]
    assert tight.sum() == len(Xt)
    assert np.percentile(np.abs(c - c0)[tight], 95) < 5e-4, st
    assert (c[~tight] > gfl.push_req(c0[~tight]) - 5e-4).all(), st
    E = gfl._tri_edges(Tb)
    e0 = Xb[E[:, 1]] - Xb[E[:, 0]]
    le = np.linalg.norm(0.5 * np.einsum("nij,nj->ni", G[E[:, 0]] + G[E[:, 1]], e0), axis=1)
    ex = np.abs(np.linalg.norm(X[E[:, 1]] - X[E[:, 0]], axis=1) / le - 1)
    assert np.percentile(ex, 99) < 0.08 and ex.max() < 0.25, (np.percentile(ex, 99), ex.max())
    # a dent: the stand-off sleeve on the same body with a 6 cm patch pushed to 5 mm off the left cylinder (12 asked)
    gfl._CACHE.clear()
    same = b.with_points(b.V.copy(), "same")
    Xs, Ts = ring_sleeve(0.125, 0.07, 0.0, np.linspace(0.05, 0.25, 51), 192)      # finer: ~4 mm edges
    Xd = Xs.copy()
    rr = np.linalg.norm(Xs - [-0.125, 0.15, 0.0], axis=1)
    hit = rr < 0.03
    Xd[hit, 0] += 0.015 * np.cos(rr[hit] / 0.03 * math.pi / 2) ** 2
    c0s, n0s = gfl.signed_clear(b, Xs, k=16)
    I = np.tile(np.eye(3), (len(Xs), 1, 1))
    Xo, st = gfl.follow_solve(same, Xd, Xs, Ts, I, I, c0s, n0s, np.ones(len(Xs), bool))
    cd, _ = gfl.signed_clear(same, Xd, k=16)
    co, _ = gfl.signed_clear(same, Xo, k=16)
    assert cd.min() < 0.0055 and co.min() > gfl.push_req(c0s).min() - 5e-4, (cd.min(), co.min(), st)
    E = gfl._tri_edges(Ts)
    l0 = np.linalg.norm(Xs[E[:, 1]] - Xs[E[:, 0]], axis=1)
    ld = np.linalg.norm(Xd[E[:, 1]] - Xd[E[:, 0]], axis=1)
    lo = np.linalg.norm(Xo[E[:, 1]] - Xo[E[:, 0]], axis=1)
    assert np.abs(lo / l0 - 1).max() < 0.25 and np.abs(lo / l0 - 1).max() < np.abs(ld / l0 - 1).max()
    # the bind body: Y back exactly
    Xi, _ = gfl.follow_solve(same, Xs, Xs, Ts, I, I, c0s, n0s, np.ones(len(Xs), bool))
    assert np.abs(Xi - Xs).max() == 0.0


def test_fit_verdict():
    m = {"a": {"fail": [], "nan": 0}, "b": {"fail": ["inside"], "why": {"inside": 3, "inside_mm_max": 1.2}}}
    assert gf.fit_verdict(m) == ("flagged", {"b": {"inside": 3, "inside_mm_max": 1.2}})
    assert gf.fit_verdict({"a": {"fail": []}}) == ("ok", None)


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print(k, "ok")


def test_stale_detection(tmp_path, monkeypatch):
    import json as _json
    src = tmp_path / "a.gltf"
    src.write_text("x")
    monkeypatch.setattr(gf, "REPO", str(tmp_path))
    class B:
        hash = "h"
    bodies = {t: B() for t in gf.TIERS}
    us = [{"id": "u1", "src": "a.gltf"}, {"id": "u2", "src": "a.gltf"}]
    bd = tmp_path / "bind"
    bd.mkdir()

    def write(uid, **kw):
        meta = {"bind_version": gf.BIND_VERSION, "src_sha1": gf.sha1(str(src)), "bind_hash": {t: "h" for t in gf.TIERS}}
        meta.update(kw)
        np.savez(bd / f"{uid}.npz", meta=np.frombuffer(_json.dumps(meta).encode(), np.uint8))

    write("u1")
    write("orph")
    bad, orph = gf.stale_units(bodies, str(bd), us)
    assert [b[0] for b in bad] == ["u2"] and orph == ["orph"]  # u2 missing, u1 current
    write("u2", src_sha1="0" * 40)
    assert dict(gf.stale_units(bodies, str(bd), us)[0]) == {"u2": "source changed"}
    write("u2", bind_version=0)
    assert "bind_version" in gf.stale_units(bodies, str(bd), us)[0][0][1]


def test_standoff_floor_law(tmp_path):
    """The stand-off law: a plate whose lower edge must stand 12 mm off (measured targets) moves out there, its top
    (no target) stays seated within a few mm; a target over the law's cap is held at the cap; the tuck reach follows."""
    import json as _json
    import gear_field as gfl
    import gear_tuck as gt
    P, T = cylinder(0.05, 0.3, 64, 30)
    b = body(P, T)
    a = np.linspace(-0.25 * math.pi, 0.25 * math.pi, 16)
    ys = np.linspace(0.05, 0.25, 14)
    A = np.array([[0.054 * math.sin(t), y, 0.054 * math.cos(t)] for y in ys for t in a])
    c_req, _ = gfl.signed_clear(b, A, k=16)
    low = A[:, 1] < 0.08
    floor = np.where(low, 0.012, np.nan)
    M, ca, cb, info = gfl.rigid_fit_clear(b, A, A, A, c_req, floor)
    c, _ = gfl.signed_clear(b, (A - ca) @ M.T + cb, k=16)
    assert c[low].min() > 0.012 - 2e-4, (c[low].min(), info)
    lift = c - c_req
    assert np.median(lift[A[:, 1] > 0.22]) < 0.5 * np.median(lift[low]), info   # the top stays nearer her (a turn)
    assert max(info["scale"]) <= 1.25 and min(info["scale"]) >= 0.85
    # the law: rigid_roles slots "standoff"; targets per node, capped
    roles = {"slots": {"pauldrons": {"standoff": {"cap_mm": 10, "tuck_full_mm": 12, "tuck_zero_mm": 18, "tuck_step": 0.5}}}}
    assert gf.standoff_law("pauldrons", roles)["cap_mm"] == 10 and gf.standoff_law("top", roles) is None

    class _Bd:
        id, meta = "u", {"row": {"slot": "pauldrons"}}
    fp = tmp_path / "u.json"
    fp.write_text(_json.dumps({"targets": {"n0": [[0, 0.03], [2, 0.005]]}}))
    ev = {0: {"X": np.zeros((4, 3)), "comp": np.array([0, 0, 0, -1])}}
    old = gf.rigid_roles
    gf.rigid_roles = lambda path=None: roles
    try:
        f = gf.standoff_floor(_Bd, [{"i": 0, "node": "n0"}], ev, path=str(fp))
        assert abs(f[0] - 0.010) < 1e-9 and np.isnan(f[1]) and abs(f[2] - 0.005) < 1e-9 and np.isnan(f[3])
        assert [gt.rigid_tuck_law("pauldrons")[k] for k in ("full", "zero", "step")] == [0.012, 0.018, 0.5]
        assert [gt.rigid_tuck_law("top")[k] for k in ("full", "zero", "step", "depth")] == [gt.RIGID_FULL, gt.RIGID_ZERO, gt.STEP, gt.BASE]
    finally:
        gf.rigid_roles = old


def test_seat_cap_and_roles_override(tmp_path, monkeypatch):
    """The law's "seat_cap_mm" caps the topmost plates of each side (the cop and what rides it) while the lames below
    keep "cap_mm"; "cap_mm" 0 is no stand-off; GEAR_ROLES names the roles file every tool reads."""
    import json as _json
    # two sides, each a cop (two groups at one height: steel, a trim) over a lame; comps 0..5, each its own leader
    def blk(x, y0, y1):
        return np.array([[x, y0, 0.0], [x, y1, 0.0], [x + 0.01, 0.5 * (y0 + y1), 0.0]])
    X = np.vstack([blk(0.20, 1.47, 1.53), blk(0.21, 1.48, 1.52), blk(0.23, 1.44, 1.48),
                   blk(-0.20, 1.47, 1.53), blk(-0.21, 1.48, 1.52), blk(-0.23, 1.44, 1.48), [[0.0, 2.0, 0.0]]])
    comp = np.r_[np.repeat(np.arange(6), 3), -1]
    lead = np.arange(6)
    top = gf.top_groups(X, comp, lead)
    assert top.tolist() == [True] * 6 + [False] * 3 + [True] * 6 + [False] * 3 + [False]
    roles = {"slots": {"pauldrons": {"standoff": {"cap_mm": 10, "seat_cap_mm": 3}}}}
    rp = tmp_path / "roles.json"
    rp.write_text(_json.dumps(roles))
    monkeypatch.setenv("GEAR_ROLES", str(rp))
    assert gf.roles_path() == str(rp) and gf.standoff_law("pauldrons")["seat_cap_mm"] == 3
    import gear_tuck as gt
    assert [gt.rigid_tuck_law("pauldrons")[k] for k in ("full", "zero", "step", "depth")] == [gt.RIGID_FULL, gt.RIGID_ZERO, gt.STEP, gt.BASE]

    class _Bd:
        id, meta, z = "u", {"row": {"slot": "pauldrons"}}, {"lead_close": lead}
    fp = tmp_path / "u.json"
    fp.write_text(_json.dumps({"targets": {"n0": [[0, 0.03], [1, 0.002], [6, 0.03], [7, 0.004]]}}))
    ev = {0: {"X": X, "Xbind": X, "comp": comp}}
    ms = [{"i": 0, "node": "n0", "tier": "close"}]
    f = gf.standoff_floor(_Bd, ms, ev, path=str(fp))
    assert abs(f[0] - 0.003) < 1e-9 and abs(f[1] - 0.002) < 1e-9      # the cop: held at the seat cap
    assert abs(f[6] - 0.010) < 1e-9 and abs(f[7] - 0.004) < 1e-9      # the lame: the law's cap
    rp2 = tmp_path / "roles0.json"
    rp2.write_text(_json.dumps({"slots": {"pauldrons": {"standoff": {"cap_mm": 0, "tuck_step": 1.0}}}}))
    monkeypatch.setenv("GEAR_ROLES", str(rp2))
    assert gf.standoff_floor(_Bd, ms, ev, path=str(fp)) is None
    assert gt.rigid_tuck_law("pauldrons")["step"] == 1.0
    monkeypatch.delenv("GEAR_ROLES")
    assert gf.roles_path() == gf.ROLES_PATH


def test_standoff_floor_rest_min(tmp_path, monkeypatch):
    """rest_min_mm: every rigid point gets at least the rest floor (a point without a target included, a loose point
    not); without the key the law is as it was (no target, no floor)."""
    import json as _json
    from types import SimpleNamespace as _NS
    import gear_fit as _gf
    fp = tmp_path / "x.json"
    fp.write_text(_json.dumps({"targets": {"n": [[0, 0.02], [1, 0.0005]]}}))
    bd = _NS(meta={"row": {"slot": "pauldrons"}}, id="x")
    ms = [{"i": 0, "node": "n", "tier": "close"}]
    ev = {0: {"X": np.zeros((4, 3)), "comp": np.array([0, 0, -1, 0])}}
    monkeypatch.setattr(_gf, "standoff_law", lambda slot, roles=None: {"cap_mm": 8})
    f = _gf.standoff_floor(bd, ms, ev, str(fp))
    assert np.allclose(f[:2], [0.008, 0.0005]) and np.isnan(f[2]) and np.isnan(f[3])
    monkeypatch.setattr(_gf, "standoff_law", lambda slot, roles=None: {"cap_mm": 8, "rest_min_mm": 1})
    f = _gf.standoff_floor(bd, ms, ev, str(fp))
    assert np.allclose(f[[0, 1, 3]], [0.008, 0.001, 0.001]) and np.isnan(f[2])


def test_rim_rides_its_plate(tmp_path, monkeypatch):
    """A small rigid group lying along a larger one (a plate's rim) pairs with it by geometry at the authored rest and
    joins its group; a plate hanging below does not; the roles file's keys switch a slot off or name / free a pair."""
    import json as _json

    def grid(x0, x1, z0, z1, y, n):
        xs, zs = np.meshgrid(np.linspace(x0, x1, n), np.linspace(z0, z1, n), indexing="ij")
        P = np.c_[xs.ravel(), np.full(n * n, y), zs.ravel()]
        q = np.array([[i * n + j, (i + 1) * n + j, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)]
                     + [[(i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)])
        return P, q
    parts = [grid(0.0, 0.10, 0.0, 0.10, 1.50, 11),      # 0: the plate, 100 x 100 mm
             grid(0.0, 0.10, 0.0, 0.02, 1.499, 11),     # 1: its rim, a strip 1 mm under one edge (area x0.2)
             grid(0.0, 0.07, 0.0, 0.07, 1.485, 11)]     # 2: a lame 15 mm below (area x0.49, far)
    X = np.vstack([p for p, _ in parts])
    T = np.vstack([q + 121 * k for k, (_, q) in enumerate(parts)])
    comp = np.repeat(np.arange(3), 121)
    lead = np.arange(3)
    pairs = gf.rim_pairs(X, T, comp)
    assert list(pairs) == [1] and pairs[1][0] == 0 and abs(pairs[1][2] - 1.0) < 0.01 and abs(pairs[1][4] - 0.2) < 1e-6
    assert gf.rim_pairs(X, T, comp, ratio=0.1) == {} and gf.rim_pairs(X, T, comp, near_m=0.0005) == {}
    assert gf.rim_leads(lead, pairs).tolist() == [0, 0, 2] and gf.rim_leads(lead, {}) is lead

    class _Bd:
        id, meta, z = "u", {"row": {"slot": "pauldrons"}}, {}
    ms = [{"i": 0, "node": "n0", "tier": "close"}]
    for roles, want in (({}, {1: 0}), ({"slots": {"pauldrons": {"rims": False}}}, {}),
                        ({"rims": {"ratio": 0.1}}, {}), ({"rim_of": {"u": {"close/1": None, "close/2": 0}}}, {2: 0}),
                        ({"slots": {"pauldrons": {"rims": {"near_mm": 20, "share": 0.5}}}}, {1: 0, 2: 0})):
        rp = tmp_path / f"roles{len(_json.dumps(roles))}.json"
        rp.write_text(_json.dumps(roles))
        monkeypatch.setenv("GEAR_ROLES", str(rp))
        got = gf.rim_hosts(_Bd, ms, X, comp, lead, T=T)
        assert {a: v[0] for a, v in got.items()} == want, roles

    class _Native:
        id, meta, z = "u", {"kind": "native", "row": {"slot": "pauldrons"}}, {}
    assert gf.rim_hosts(_Native, ms, X, comp, lead, T=T) == {}


def test_built_outputs_stamped():
    """Every built gear .gltf carries its .bin's sha1 (asset.extras.build). Godot reimports a .gltf only when the .gltf's
    own bytes change, so a .bin rewritten without the stamp leaves a stale imported scene on screen (lane G lead 6, 17 Nov)."""
    root = Path(__file__).resolve().parents[2] / "godot" / "art" / "gear" / "out"
    paths = [p for p in root.rglob("*.gltf") if p.with_suffix(".bin").exists()]
    assert paths, root
    bad = {str(p.relative_to(root)): r for p in paths for ok, r in [gf.gltf_stamp_state(str(p))] if not ok}
    assert not bad, bad


def test_import_stale_and_stamp(tmp_path):
    import hashlib
    import json
    godot = tmp_path / "godot"
    imp = godot / ".godot" / "imported"
    imp.mkdir(parents=True)
    folder = godot / "art" / "gear"
    folder.mkdir(parents=True)

    def piece(name, scn="ok", stamp="ok", md5="ok"):
        b = b"binbytes"
        (folder / f"{name}.bin").write_bytes(b)
        js = {"asset": {"version": "2.0"}}
        if stamp == "ok":
            gf.stamp_build(js, b)
        elif stamp == "wrong":
            js["asset"]["extras"] = {"build": "0" * 40}
        g = folder / f"{name}.gltf"
        g.write_text(json.dumps(js, separators=(",", ":")))
        if scn == "noimport":
            return g
        line = f'path="res://.godot/imported/{name}.gltf-abc.scn"\n' if scn != "nopath" else "valid=true\n"
        (folder / f"{name}.gltf.import").write_text("[remap]\n" + line)
        if scn == "ok":
            (imp / f"{name}.gltf-abc.scn").write_bytes(b"s")
            if md5 != "none":
                m = hashlib.md5(g.read_bytes()).hexdigest() if md5 == "ok" else "f" * 32
                (imp / f"{name}.gltf-abc.md5").write_text(f'source_md5="{m}"\ndest_md5="x"\n')
        return g

    st = lambda n, **k: gf.import_stale(str(piece(n, **k)), str(godot))
    assert st("fresh") is None
    assert "no .import" in st("a", scn="noimport")[0]
    assert "no path=" in st("b", scn="nopath")[0]
    assert "scene missing" in st("c", scn="missing")[0]
    assert "no .md5" in st("d", md5="none")[0]
    assert "changed since import" in st("e", md5="bad")[0]
    assert "no build stamp" in st("f", stamp="none")[0]
    assert "does not match" in st("g", stamp="wrong")[0]
    js = gf.stamp_build({"asset": {"version": "2.0"}}, b"abc")
    assert js["asset"]["extras"]["build"] == hashlib.sha1(b"abc").hexdigest()
    # --stamp: fix an unstamped gltf in place; the import then reads as changed until Godot reimports
    g = piece("h", stamp="none")
    assert not gf.gltf_stamp_state(str(g))[0]
    gf.stamp_file(str(g))
    assert gf.gltf_stamp_state(str(g))[0]
    assert "changed since import" in gf.import_stale(str(g), str(godot))[0]


def test_native_rows_replace_bound_and_skip_stale(tmp_path, monkeypatch):
    import json as _json
    import struct
    import types
    import piece_ship
    arm, out = tmp_path / "armor", tmp_path / "out"
    nd = arm / "body_x"
    (nd / "armor_tuck").mkdir(parents=True)
    (nd / "armor_cover").mkdir()
    for pid in ("kit_a", "kit_b"):
        (nd / "armor_tuck" / f"{pid}.bin").write_bytes(struct.pack("<I", 3) + b"\0" * 48)
        (nd / "armor_cover" / f"{pid}.bin").write_bytes(struct.pack("<I", 2) + b"\0" * 32)
    (nd / "kit_a.sockets.json").write_text("{}")
    rows = [{"id": "kit_a", "slot": "top", "tuck": "armor_tuck/kit_a.bin", "body_glb": "good"},
            {"id": "kit_b", "slot": "head", "body_glb": "old"}]
    (nd / "armor_index.json").write_text(_json.dumps(rows))
    monkeypatch.setattr(gf, "ARMOR", str(arm))
    monkeypatch.setattr(piece_ship, "glb_body_hash", lambda p: "good")
    bodies = {"close": types.SimpleNamespace(glb=str(tmp_path / "people" / "body_x" / "body.glb"), hash="hc"),
              "play": types.SimpleNamespace(glb="p", hash="hp")}
    said = []
    got = gf.native_rows(bodies, str(out), say=said.append)
    assert list(got) == ["kit_a"] and len(said) == 1 and "kit_b" in said[0] and "bound row is used" in said[0]
    r = got["kit_a"]
    assert r["native"] is True and r["fit"] == "ok" and r["body_hash"] == "hc" and r["play_hash"] == "hp"
    assert r["file"].startswith("res://") and r["file"].endswith("body_x/kit_a.gltf")
    assert r["sockets"].endswith("kit_a.sockets.json") and r["tuck_count"] == 3 and r["cover_count"] == 2
    assert (out / "armor_tuck" / "kit_a.bin").exists() and (out / "armor_cover" / "kit_a.bin").exists()
    # no native folder for the body: nothing, nothing written
    bodies["close"].glb = str(tmp_path / "people" / "body_y" / "body.glb")
    assert gf.native_rows(bodies, str(out)) == {}

def test_ornaments_ride_as_one():
    """ORNAMENT: an outfit metal part A skins with one blend (and small) is rigid; one A bends is not; a gem touching a
    boss rides it, a stud far from both rides itself; leather never."""
    def quad(c, s):
        P = np.array([[c[0] - s, c[1] - s, c[2]], [c[0] + s, c[1] - s, c[2]], [c[0] + s, c[1] + s, c[2]], [c[0] - s, c[1] + s, c[2]]])
        return P, np.array([[0, 1, 2], [0, 2, 3]])
    parts = [quad((0, 0, 0), 0.018), quad((0, 0, 0.001), 0.0175), quad((0.2, 0, 0), 0.003), quad((0, 0.3, 0), 0.06)]
    X = np.vstack([p for p, _ in parts])
    T = np.vstack([t + 4 * k for k, (_, t) in enumerate(parts)])
    J = np.tile([[0, 1]], (16, 1))
    W = np.tile([[0.6, 0.4]], (16, 1)).astype(float)
    W[12] = [0.1, 0.9]    # the last part: A bends it
    inv = np.arange(16)
    m = gf.ornament_mask("piece.gold", X, T, inv, J, W)
    assert m[:12].all() and not m[12:].any()
    assert not gf.ornament_mask("piece.darkleather", X, T, inv, J, W).any()
    comp_of, lead, _ = gf.rigid_groups([X], [T], [16], [m], reach=gf.ORNAMENT["ride_mm"] / 1000.0)
    c = comp_of[0]
    assert (c[12:] == -1).all() and len(lead) == 3
    assert lead[c[4]] == c[0] and lead[c[8]] == c[8] and lead[c[0]] == c[0]


def test_plates_ride_as_a_rides_them():
    """ORNAMENT "plates": a metal part over max_mm that A skins with one blend is rigid too and keeps A's blend by joint
    name (the plain mean only when the body lacks a joint of it); a small one keeps none (the plain mean)."""
    def quad(c, s):
        P = np.array([[c[0] - s, c[1] - s, c[2]], [c[0] + s, c[1] - s, c[2]], [c[0] + s, c[1] + s, c[2]], [c[0] - s, c[1] + s, c[2]]])
        return P, np.array([[0, 1, 2], [0, 2, 3]])
    parts = [quad((0, 0, 0), 0.018), quad((0, 0.3, 0), 0.06)]
    X = np.vstack([p for p, _ in parts])
    T = np.vstack([t + 4 * k for k, (_, t) in enumerate(parts)])
    J = np.tile([[0, 1]], (8, 1))
    W = np.tile([[0.25, 0.75]], (8, 1)).astype(float)
    inv = np.arange(8)
    assert gf.ornament_mask("boots.steel", X, T, inv, J, W).all()
    pid, bl = gf.plate_blends("boots.steel", X, T, inv, J, W, ["thigh_l", "calf_l"])
    assert (pid[:4] == -1).all() and (pid[4:] == 0).all() and bl == [{"thigh_l": 0.25, "calf_l": 0.75}]

    class B:
        joint_names = ["root", "calf_l", "thigh_l"]
    Jb, Wb = gf.a_blend(B, bl[0])
    assert Jb[0] == 1 and abs(Wb[0] - 0.75) < 1e-9 and Jb[1] == 2 and abs(Wb[1] - 0.25) < 1e-9
    B.joint_names = ["root", "calf_l"]
    assert gf.a_blend(B, bl[0]) is None


def test_a_leads_gives_a_trim_to_the_plate_A_skins_it_with():
    # plates 0 and 1 (own leaders), trim 2 led by plate 1 but skinned on A with plate 0's blend: it moves to 0;
    # trim 3 led by plate 1 with plate 1's blend stays; trim 4 with a blend no plate has keeps its leader
    import numpy as np
    import gear_fit as gf
    B = np.array([[1, 0, 0], [0, 1, 0], [1, 0, 0], [0, 1, 0], [0.5, 0, 0.5]], float)
    X = np.array([[0, 0, 0], [1, 0, 0], [0.9, 0, 0], [1, 0.1, 0], [1, 0, 0.1]], float)
    comp = np.arange(5)
    lead, moved = gf.a_leads(np.array([0, 1, 1, 1, 1]), B, X, comp)
    assert list(lead) == [0, 1, 0, 1, 1] and moved == {2: (1, 0)}


def test_trim_rides_its_steel():
    """TRIM_RIDE: a gold component lying on the piece's steel takes the steel's weights and every shape delta at its
    nearest steel point (a shape the steel lacks is 0 there), full within near_mm, a cosine fade to its own by fade_mm;
    rest positions untouched; a strap far off the steel and a rigid group shared with another mesh keep their own. Posed
    (bones that translate, a shape on), the riding trim keeps its rest offset off the steel exactly, where its own values
    let it drift (B's warden top: the cup-edge gold out through the steel, lane G rim2, 17 Nov)."""
    import json as _json

    def grid(x0, x1, z0, z1, y, n):
        xs, zs = np.meshgrid(np.linspace(x0, x1, n), np.linspace(z0, z1, n), indexing="ij")
        P = np.c_[xs.ravel(), np.full(n * n, y), zs.ravel()]
        q = np.array([[i * n + j, (i + 1) * n + j, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)]
                     + [[(i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)])
        return P, q

    def unit(parts, J, W, shapes, comp):
        X = np.vstack([p for p, _ in parts])
        T = np.vstack([q + sum(len(p) for p, _ in parts[:k]) for k, (_, q) in enumerate(parts)])
        n = len(X)
        J, W = np.pad(J, ((0, 0), (0, 8 - J.shape[1]))), np.pad(W, ((0, 0), (0, 8 - W.shape[1])))   # (8 a vertex, as built)
        return T, {"Xu": X.copy(), "inv": np.arange(n), "J": J.astype(np.uint16), "W": W.astype(np.float32),
                   "shapes": {k: v.astype(float) for k, v in shapes.items()}, "comp": comp, "lead": None}

    sx, sT = grid(0.0, 0.1, 0.0, 0.1, 1.5, 11)          # the steel: a 100 mm plate, weights and its lift shape vary
    sJ = np.tile([[0, 1]], (len(sx), 1))
    sW = np.c_[1 - sx[:, 0] / 0.1, sx[:, 0] / 0.1]
    S_T, st_ev = unit([(sx, sT)], sJ, sW, {"lift": np.c_[0 * sx[:, 0], 0.002 * sx[:, 2] / 0.1, 0 * sx[:, 0]]},
                      np.full(len(sx), -1))
    parts = [grid(0.02, 0.08, 0.02, 0.04, 1.5005, 5),   # A: a trim 0.5 mm on it: rides
             grid(0.02, 0.08, 0.20, 0.22, 1.5005, 5),   # B: a strap trim 100 mm off: keeps its own
             grid(0.048, 0.052, 0.07, 0.074, 1.501, 2),  # C: a rivet (rigid, its own group): rides per point
             grid(0.048, 0.052, 0.09, 0.094, 1.501, 2),  # D: a rivet whose group is shared with the leather: keeps its own
             grid(0.090, 0.106, 0.05, 0.06, 1.5005, 9)]  # E: a trim past the plate's edge: rides, fading out by 8 mm
    n = sum(len(p) for p, _ in parts)
    comp = np.full(n, -1)
    comp[50:54], comp[54:58] = 0, 1
    gJ = np.tile([[0, 1]], (n, 1))
    gW = np.tile([[0.5, 0.5]], (n, 1))
    G_T, g_ev = unit(parts, gJ, gW, {"lift": np.tile([0, 0.0005, 0], (n, 1)), "hang": np.tile([0, 0, 0.003], (n, 1))}, comp)
    lx, lT = grid(0.3, 0.32, 0.0, 0.02, 1.5, 3)          # the leather, sharing rivet D's group
    L_T, l_ev = unit([(lx, lT)], np.tile([[0, 1]], (9, 1)), np.tile([[1.0, 0.0]], (9, 1)), {}, np.full(9, 2))
    lead = np.array([0, 2, 2])
    for v in (st_ev, g_ev, l_ev):
        v["lead"] = lead

    class _Bd:
        id, meta = "test.trim_ride", {"meshes": [{"i": 0, "node": "p.steel", "tier": "close"},
                                                 {"i": 1, "node": "p.gold", "tier": "close"},
                                                 {"i": 2, "node": "p.darkleather", "tier": "close"}]}
    for i, T in enumerate((S_T, G_T, L_T)):
        gf._TRIS[(_Bd.id, i)] = T
    ev = {"p.steel": st_ev, "p.gold": g_ev, "p.darkleather": l_ev}
    X0, W0 = g_ev["Xu"].copy(), g_ev["W"].copy()
    hang0 = g_ev["shapes"]["hang"].copy()
    roles = _json.loads((Path(__file__).resolve().parent / "rigid_roles.json").read_text())
    tr = roles["slots"]["top"]["trim_ride"]
    assert set(tr) <= set(gf.TRIM_RIDE), tr           # (a key the rule does not read would be a silent no-op)
    law = dict(gf.TRIM_RIDE, host_n=50)

    def posed(v, t=np.array([0.0, 0.01, 0.004])):     # bone 0 still, bone 1 moved by t, lift on: LBS = P + S + W1 t
        D = np.zeros((len(v["Xu"]), 2))
        np.add.at(D, (np.repeat(np.arange(len(D)), v["J"].shape[1]), v["J"].astype(int).ravel()), v["W"].astype(float).ravel())
        return v["Xu"] + v["shapes"]["lift"] + D[:, 1:2] * t
    surf = gf.Surface(sx, sT)
    q, _, tq, d = surf.closest(X0, k=16)
    b = gf.bary(q, sx[sT[tq, 0]], sx[sT[tq, 1]], sx[sT[tq, 2]])
    drift = lambda: np.linalg.norm((posed(g_ev) - np.einsum("nc,ncx->nx", b, posed(st_ev)[sT[tq]])) - (X0 - q), axis=1)  # noqa: E731
    assert drift()[:25].max() > 1e-3                  # own values: the trim drifts off the steel (here 1 mm and up)
    st = gf.trim_ride_rule(_Bd, ev, law, "close")
    try:
        assert st["trims"] == 2 and st["rivets"] == 1, st
        assert np.array_equal(g_ev["Xu"], X0)
        A, B, C, D, E = (np.arange(0, 25), np.arange(25, 50), np.arange(50, 54), np.arange(54, 58), np.arange(58, 139))
        ride = np.r_[A, C]
        assert np.allclose(g_ev["W"][ride, 1], 1 - g_ev["W"][ride, 0], atol=1e-6)
        # (J is [0, 1] here; W at the nearest steel point is the steel's, interpolated: x / 0.1 on bone 1)
        k1 = (g_ev["J"][ride] == 1)
        w1 = np.where(k1, g_ev["W"][ride], 0).sum(1)
        assert np.allclose(w1, np.clip(q[ride, 0] / 0.1, 0, 1), atol=1e-5)
        assert np.allclose(g_ev["shapes"]["lift"][ride], np.c_[0 * ride, 0.002 * q[ride, 2] / 0.1, 0 * ride], atol=1e-9)
        assert np.abs(g_ev["shapes"]["hang"][ride]).max() == 0
        for keep in (B, D):
            assert np.array_equal(g_ev["W"][keep], W0[keep]) and np.array_equal(g_ev["shapes"]["hang"][keep], hang0[keep])
            assert np.allclose(g_ev["shapes"]["lift"][keep], [0, 0.0005, 0])
        assert drift()[ride].max() < 1e-9             # riding: the rest offset held exactly, posed
        # E past the plate's edge: the column 6 mm off is half its own (cosine fade from near_mm 4 to fade_mm 8)
        far = E[np.abs(X0[E, 0] - 0.106) < 1e-9]
        g = 0.5 * (1 + np.cos(np.pi * np.clip((d[far] - 0.004) / 0.004, 0, 1)))
        assert 0.4 < g.min() and g.max() < 0.6
        assert np.allclose(g_ev["shapes"]["hang"][far, 2], (1 - g) * 0.003, atol=1e-9)
        near = E[X0[E, 0] <= 0.1 + 1e-9]
        assert np.abs(g_ev["shapes"]["hang"][near]).max() == 0 and drift()[near].max() < 1e-9
    finally:
        for i in range(3):
            gf._TRIS.pop((_Bd.id, i), None)
    assert gf.trim_ride_rule(_Bd, {"p.gold": g_ev}, law, "close") == {}    # a tier missing a mesh's eval: nothing


def test_units_import_as_their_a_source():
    """Every built unit on B imports with its A source's mesh settings (no generated LODs: Godot's LOD simplified the
    steel and its riding gold trim apart at the Look camera, body lead 9, 17 Nov). Written by gear_fit build and
    `gear_fit.py imports`; a unit Godot has not imported yet has no .import to hold it."""
    import json
    import os
    sys.path.insert(0, os.path.join(gf.REPO, "tools", "body"))
    import publish_p1
    folder = os.path.join(gf.OUT, "body_p1")
    if not os.path.isdir(folder):
        return
    bad = []
    for f in sorted(os.listdir(folder)):
        imp = os.path.join(folder, f + ".import")
        if not f.endswith(".gltf") or not os.path.exists(imp):
            continue
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            src = json.loads(fh.read())["asset"]["extras"]["gear_fit"]["a_source"]
        want = publish_p1.import_params(a_import=os.path.join(gf.REPO, src) + ".import")
        have = dict(ln.rstrip("\n").partition("=")[::2] for ln in open(imp, encoding="utf-8") if "=" in ln)
        bad += [f"{f} {k}={have.get(k)} (A {v})" for k, v in want.items() if have.get(k) != v]
    assert not bad, bad


def test_each_cup_rides_one_blend():
    """CUP_BLEND: each big bendy steel component takes one blend, the mean of its points' weights (top 8), on every
    point; shapes and rest positions untouched; a small steel part, a rigid one and the gold keep their own. Posed (a
    bone that turns), the cup keeps its shape (its edge does not bend against its middle), where per point weights bent
    it (B's warden top: the cup's lower inner rim, lane G lead 9, 17 Nov)."""
    import json as _json

    def grid(x0, x1, z0, z1, y, n):
        xs, zs = np.meshgrid(np.linspace(x0, x1, n), np.linspace(z0, z1, n), indexing="ij")
        P = np.c_[xs.ravel(), np.full(n * n, y), zs.ravel()]
        q = np.array([[i * n + j, (i + 1) * n + j, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)]
                     + [[(i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)])
        return P, q
    cups = [grid(0.0, 0.1, 0.0, 0.1, 1.5, 11), grid(-0.1, 0.0, 0.2, 0.3, 1.5, 11), grid(0.3, 0.31, 0.0, 0.01, 1.5, 3)]
    X = np.vstack([p for p, _ in cups])
    T = np.vstack([q + sum(len(p) for p, _ in cups[:k]) for k, (_, q) in enumerate(cups)])
    n = len(X)
    w1 = np.clip(np.abs(X[:, 0]) / 0.1, 0, 1)                    # bone 1's share rises across each cup (its rim: 1)
    J = np.pad(np.tile([[0, 1]], (n, 1)), ((0, 0), (0, 6))).astype(np.uint16)
    W = np.pad(np.c_[1 - w1, w1], ((0, 0), (0, 6))).astype(np.float32)
    comp = np.full(n, -1)
    comp[-3:] = 0                                               # a rigid part of the steel keeps its own
    lift = np.c_[0 * X[:, 0], 0.002 * X[:, 2], 0 * X[:, 0]]
    st_ev = {"Xu": X.copy(), "inv": np.arange(n), "J": J.copy(), "W": W.copy(), "shapes": {"lift": lift.copy()},
             "comp": comp, "lead": np.array([0])}
    gx, gT = grid(0.02, 0.08, 0.02, 0.04, 1.5005, 5)
    g_ev = {"Xu": gx, "inv": np.arange(len(gx)), "J": J[:len(gx)].copy(), "W": W[:len(gx)].copy(), "shapes": {},
            "comp": np.full(len(gx), -1), "lead": None}

    class _Bd:
        id, meta = "test.cup_blend", {"meshes": [{"i": 0, "node": "p.steel", "tier": "close"},
                                                 {"i": 1, "node": "p.gold", "tier": "close"}]}
    gf._TRIS[(_Bd.id, 0)], gf._TRIS[(_Bd.id, 1)] = T, gT
    roles = _json.loads((Path(__file__).resolve().parent / "rigid_roles.json").read_text(encoding="utf-8"))
    cb = roles["slots"]["top"].get("cup_blend") or dict(gf.CUP_BLEND)   # (PARKED: no slot has it)
    assert set(cb) <= set(gf.CUP_BLEND), cb             # (a key the rule does not read would be a silent no-op)
    gJ, gW = g_ev["J"].copy(), g_ev["W"].copy()
    st = gf.cup_blend_rule(_Bd, {"p.steel": st_ev, "p.gold": g_ev}, dict(gf.CUP_BLEND, host_n=100))
    assert st["cups"] == 2 and st["vertices"] == 242, st
    for a in (slice(0, 121), slice(121, 242)):                  # one blend over each cup: the mean of its points'
        assert (st_ev["J"][a] == st_ev["J"][a][0]).all() and np.allclose(st_ev["W"][a], st_ev["W"][a][0])
        assert np.isclose(st_ev["W"][a][0][list(st_ev["J"][a][0]).index(1)], w1[a].mean(), atol=1e-6)
    assert (st_ev["J"][-3:] == J[-3:]).all() and (st_ev["W"][-3:] == W[-3:]).all()          # the small/rigid part: own
    assert (g_ev["J"] == gJ).all() and (g_ev["W"] == gW).all()                                # the gold: its own
    assert np.array_equal(st_ev["Xu"], X) and np.array_equal(st_ev["shapes"]["lift"], lift)  # rest and shapes untouched
    assert gf.cup_blend_rule(_Bd, {"p.steel": st_ev, "p.gold": g_ev}, dict(gf.CUP_BLEND, host_n=200)) == {}

    def posed(v, W_):                                           # bone 1 turned 20 deg about z at the origin
        c, s = np.cos(np.radians(20)), np.sin(np.radians(20))
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        w = W_[:, 1].astype(float)
        return (1 - w)[:, None] * v + w[:, None] * (v @ R.T)
    a = slice(0, 121)
    bent = posed(X[a], W[a])
    one = posed(X[a], st_ev["W"][a])
    flat = lambda P: np.linalg.svd(P - P.mean(0))[1][-1]       # noqa: E731  (off its plane: a flat cup stays flat)
    assert flat(one) < 1e-9 < 1e-4 < flat(bent), (flat(one), flat(bent))


def test_each_cup_takes_a_smooth_field():
    """CUP_BLEND "mode" "smooth": each big bendy steel component's weights diffused over its own surface (Laplacian
    rounds over its edges between unique points: welded at its seams): a weight change packed at its rim is spread
    over the cup, the crown keeps most of its own (not the one mean), the weights stay a partition of 1; shapes, rest
    positions, a small or rigid steel part and the gold keep their own; the rule reads the slot's law from rigid_roles
    (B's warden top: the cups' lower inner rims, lane G lead 9 solver 3, 17 Nov)."""
    import json as _json
    n = 21
    xs, zs = np.meshgrid(np.linspace(0, 0.1, n), np.linspace(0, 0.1, n), indexing="ij")
    X = np.c_[xs.ravel(), np.full(n * n, 1.5), zs.ravel()]
    T = np.array([[i * n + j, (i + 1) * n + j, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)]
                 + [[(i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1] for i in range(n - 1) for j in range(n - 1)])
    X = np.vstack([X, [[0.3, 1.5, 0.0], [0.31, 1.5, 0.0], [0.3, 1.5, 0.01]]])
    T = np.vstack([T, [[n * n, n * n + 1, n * n + 2]]])
    m = len(X)
    w1 = np.clip(X[:, 0] / 0.1, 0, 1)                           # bone 1 (the breast) rises across the cup to its crown
    w1 = np.where(X[:, 0] < 0.012, 0.6 - w1, w1)                # and a wiggle packed at its rim (x 0)
    w1[n * n:] = 0.5
    J = np.pad(np.tile([[0, 1]], (m, 1)), ((0, 0), (0, 6))).astype(np.uint16)
    W = np.pad(np.c_[1 - w1, w1], ((0, 0), (0, 6))).astype(np.float32)
    comp = np.full(m, -1)
    lift = np.c_[0 * X[:, 0], 0.002 * X[:, 2], 0 * X[:, 0]]
    inv = np.r_[np.arange(m), np.arange(n)]                     # a UV seam: the cup's first row twice, one unique each
    st_ev = {"Xu": X.copy(), "inv": inv, "J": J[inv].copy(), "W": W[inv].copy(), "shapes": {"lift": lift[inv].copy()},
             "comp": comp, "lead": None}
    gx = X[:4] + [0, 0.0005, 0]
    g_ev = {"Xu": gx, "inv": np.arange(4), "J": J[:4].copy(), "W": W[:4].copy(), "shapes": {},
            "comp": np.full(4, -1), "lead": None}

    class _Bd:
        id, meta = "test.cup_smooth", {"meshes": [{"i": 0, "node": "p.steel", "tier": "close"},
                                                  {"i": 1, "node": "p.gold", "tier": "close"}]}
    gf._TRIS[(_Bd.id, 0)], gf._TRIS[(_Bd.id, 1)] = T, np.array([[0, 1, 2], [1, 3, 2]])
    roles = _json.loads((Path(__file__).resolve().parent / "rigid_roles.json").read_text(encoding="utf-8"))
    cb = roles["slots"]["top"]["cup_blend"]
    assert cb["mode"] == "smooth" and set(cb) <= set(gf.CUP_BLEND) and cb["rounds"] > 0, cb
    gJ, gW = g_ev["J"].copy(), g_ev["W"].copy()
    st = gf.cup_blend_rule(_Bd, {"p.steel": st_ev, "p.gold": g_ev}, dict(cb, host_n=100))
    assert st["cups"] == 1 and st["vertices"] == n * n + n, st
    D = gf.dense_w(st_ev["J"], st_ev["W"], 2)
    assert np.allclose(D.sum(1), 1, atol=1e-5) and np.allclose(D[n * n + 3:][:n], D[:n], atol=1e-6)   # seam welded
    grad = lambda w: np.abs(np.diff(w[:n * n].reshape(n, n), axis=0)).max()   # noqa: E731  (along x, per row step)
    assert grad(D[:m, 1]) < 0.5 * grad(w1), (grad(D[:m, 1]), grad(w1))             # the rim's packed change spread
    crown = X[:m, 0] > 0.095
    assert D[:m, 1][crown].mean() > w1[:n * n].mean() + 0.1                         # the crown keeps most of its own
    assert (st_ev["J"][n * n:m] == J[n * n:]).all() and (st_ev["W"][n * n:m] == W[n * n:]).all()   # small part: own
    assert (g_ev["J"] == gJ).all() and (g_ev["W"] == gW).all()                       # the gold: its own (TRIM_RIDE's)
    assert np.array_equal(st_ev["Xu"], X) and np.array_equal(st_ev["shapes"]["lift"], lift[inv])
