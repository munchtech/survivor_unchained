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
        assert gt.rigid_tuck_law("pauldrons") == (0.012, 0.018, 0.5)
        assert gt.rigid_tuck_law("top") == (gt.RIGID_FULL, gt.RIGID_ZERO, gt.STEP)
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
    assert gt.rigid_tuck_law("pauldrons") == (gt.RIGID_FULL, gt.RIGID_ZERO, gt.STEP)

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
    assert gt.rigid_tuck_law("pauldrons")[2] == 1.0
    monkeypatch.delenv("GEAR_ROLES")
    assert gf.roles_path() == gf.ROLES_PATH
