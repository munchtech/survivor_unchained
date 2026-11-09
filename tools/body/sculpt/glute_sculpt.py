"""P1 R1 glute route (b): her glutes SCULPTED ONCE on our topology (a stored per-vertex move, sliders rule "target",
like the hand and foot templates), made by this generator from the numbers in tools/body/designed/glutes.json
("glute_sculpt" -> "sculpt"):

  1. her body without glutes: her spec (default tools/body/specs/r1_glute_b.json) with glute_sculpt 0, close tier,
     through OurSliders (the frame the sliders' moves live in);
  2. each cheek a designed solid (a superellipse in the side plane per half-axis, tilted, its size across x a
     superellipse; the two cheeks joined at the midline by a cubic smooth max: a designed soft cleft valley), placed
     from her hip joints (the skeleton's landmarks); the region is PROJECTED onto it in each side plane (radially from
     the solid's axis: the solid moves nothing in x; the fairing's x is mirrored); where the solid stands out of her, her
     surface is carried out onto it (a union: the solid's ends stay inside her);
  3. the sculpted surface faired once over the moved region (Taubin lambda|mu, no shrink; a sculptor's smooth
     brush): the union's rim, her cleft's V and the base's small lumps go, the lumbar curve, the outer hip and the
     gluteal fold become fair blends, the quads even out;
  4. mirror-symmetric (each vertex's mirror on the reference by nearest point), x as route (a) left it;
  5. written: tools/body/base/targets/glute_sculpt_close.npz (D [n, 3] glTF m at v = 1, "topology"), the play tier
     by sliders.carry_to_tier, and glute_sculpt_close.obj (the sculpted region on her body: an artist can open and
     refine it; --from-obj reads an edited OBJ back into the target).

    python tools/body/sculpt/glute_sculpt.py [--spec SPEC] [--from-obj OBJ]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(BODY))
sys.path.insert(0, BODY)
import sliders  # noqa: E402
import glute_form as gf  # noqa: E402

OUT = os.path.join(BODY, "base", "targets")
NAME = "glute_sculpt"


def solid_rho(c, x, dy, dz):
    """The designed solid's radius along each point's side-plane direction from its axis, and that direction."""
    r = np.maximum(np.hypot(dy, dz), 1e-9)
    t = np.radians(float(c.get("tilt_deg", 0.0)))
    qb, qu = -dz / r, dy / r
    ca = qb * np.cos(t) + qu * np.sin(t)
    sa = -qb * np.sin(t) + qu * np.cos(t)
    e = float(c.get("eps", 0.25))
    Rb = gf.switch(c["r_front"], c["r_back"], ca, e)
    Rv = gf.switch(c["r_down"], c["r_up"], sa, e)
    n = float(c.get("n", 2.0))
    rho0 = (np.abs(ca / Rb) ** n + np.abs(sa / Rv) ** n) ** (-1.0 / n)

    def size(ex):
        R = gf.switch(c["r_med"], c["r_lat"], ex, float(c.get("eps_x", 0.01)))
        u = np.clip(np.abs(ex) / R, 0.0, 1.0)
        m = float(c.get("m", 2.0))
        return (1.0 - u ** m) ** (1.0 / m)
    ax = np.abs(x)
    rho = gf.smax(size(ax - c["x"]) * rho0, size(-ax - c["x"]) * rho0, float(c["kc"]))
    return rho, r


def mirror_map(V0):
    """Each of our vertices' mirror (x -> -x) on the reference V0, by nearest point (the topology npz's mirror_of
    holds one side only: -1 on the other); a vertex with no mirror within 0.1 mm keeps its own move."""
    from scipy.spatial import cKDTree
    d, i = cKDTree(V0).query(V0 * np.array([-1.0, 1.0, 1.0]))
    return np.where(d < 1e-4, i, np.arange(len(V0)))


def laplacian(Q, n):
    import scipy.sparse as sp
    e = np.unique(np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1), axis=0)
    A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    return (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()


def sculpt_from_field(c, sl, B, vals):
    """Mode "from_field" (the target as made, 5 Nov): route (a)'s designed glute ("glute_form", its numbers as they
    stand when this runs) laid once on her body, then refined offline as a live rule cannot afford: a long Taubin
    fairing of the sculpted surface in the side planes (x locked) under a broad C2 region weight (the base's small lumps and the cleft's V go, a
    cleaner cel terminator), the moved quads evened; stored, so an artist can open the OBJ and refine it."""
    t = sl.topo()
    H = gf.hip_frame(sl, B)
    A = sl.evaluate({k: v for k, v in dict(vals, **{c.get("field", "glute_form"): 1.0}).items() if v})
    f = c["fair"]
    w = gf.region(sl, f["mask"], B, H) * gf.parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))
    P = gf.fair(sl, A, w, f["iters"], f.get("lambda", 0.5), f.get("mu", -0.53), lock_x=True)
    D = P - B
    mo = mirror_map(sl.V0)
    D = 0.5 * (D + D[mo] * np.array([-1.0, 1.0, 1.0]))
    D[np.linalg.norm(D, axis=1) < 2e-5] = 0.0
    return D, {"mode": "from_field", "field": c.get("field", "glute_form"), "max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 1),
               "x_max_mm": round(float(np.abs(D[:, 0]).max()) * 1e3, 2)}


def sculpt(c, sl, B):
    """Mode "solid" (tried 5 Nov, NOT the target as made): each cheek a designed solid the region is projected onto.
    Measured: the union's crease at the solid's outline survives a broad 60-step fairing as a rim around each cheek
    (a soft union instead shows the solid's ends: its size across x falls as a square root). Kept for the record."""
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    t = sl.topo()
    Q = t["Q"]
    H = gf.hip_frame(sl, B)
    yA, zA = H[1] + float(c["y"]), H[2] + float(c["z"])
    dy, dz = B[:, 1] - yA, B[:, 2] - zA
    rho, r = solid_rho(c, B[:, 0], dy, dz)
    w = gf.region(sl, c["region"], B, H) * gf.parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))
    out = np.maximum(rho - r, 0.0) * w                                # the union (its crease: the fairing below)
    Dt = np.zeros_like(B)
    Dt[:, 1] = out * dy / r
    Dt[:, 2] = out * dz / r
    # the union's crease (where the solid meets her), her cleft's V and the base's small lumps: the sculpted surface
    # faired once (Taubin lambda|mu: no shrink), a sculptor's smooth brush, under a broad C2 region weight (a
    # narrow one leaves its own edge as a rim); a soft union instead shows the solid's ends (measured, 5 Nov)
    f = c.get("fair")
    P = B + Dt
    if f:
        P = gf.fair(sl, P, gf.region(sl, f["mask"], B, H) * gf.parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"])),
                    f["iters"], f.get("lambda", 0.5), f.get("mu", -0.53))
    D = P - B
    mo = mirror_map(sl.V0)
    D = 0.5 * (D + D[mo] * np.array([-1.0, 1.0, 1.0]))
    D[np.linalg.norm(D, axis=1) < 2e-5] = 0.0
    ev = c.get("even")
    if ev:
        m = gf.smoother(np.clip(np.linalg.norm(D, axis=1) / float(ev.get("full_m", 0.008)), 0.0, 1.0))
        V = gf.relax_region(sl, B + D, m, ev.get("iters", 10), ev.get("step", 0.5))
        D = V - B
        D = 0.5 * (D + D[mo] * np.array([-1.0, 1.0, 1.0]))
    info = {"projected": int((out > 0).sum()), "crown_mm": round(float(np.linalg.norm(Dt, axis=1).max()) * 1e3, 1),
            "max_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 1), "hip_frame_mm": [round(float(v) * 1e3, 1) for v in H]}
    return D, info


def write_obj(path, B, D, Q, ids):
    idx = -np.ones(len(B), np.int64)
    idx[ids] = np.arange(len(ids))
    qs = Q[(idx[Q] >= 0).all(1)]
    with open(path, "w") as f:
        f.write(f"# {NAME}: her sculpted glute region on our topology (close tier, sliders frame, glTF m). Vertex k is our\n")
        f.write(f"# vertex ids[k] of {NAME}_close.npz. Edit freely (keep the vertex count and order), then\n")
        f.write(f"# python tools/body/sculpt/glute_sculpt.py --from-obj THIS.obj\n")
        for p in (B + D)[ids]:
            f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for q in idx[qs] + 1:
            f.write(f"f {q[0]} {q[1]} {q[2]} {q[3]}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="tools/body/specs/r1_glute_b.json")
    ap.add_argument("--from-obj")
    a = ap.parse_args()
    import build_topo as bt
    sl = sliders.OurSliders(os.path.join(BODY, "base", "sliders_close.npz"))
    c = sl.designed[NAME]["sculpt"]
    spec = sliders.load_spec(os.path.join(REPO, a.spec))
    vals = dict(spec["sliders"], **{NAME: 0.0, c.get("field", "glute_form"): 0.0})
    B = sl.evaluate({k: v for k, v in vals.items() if v})
    if a.from_obj:
        ids = np.load(os.path.join(OUT, f"{NAME}_close.npz"))["ids"]
        P = np.array([[float(x) for x in l.split()[1:4]] for l in open(a.from_obj) if l.startswith("v ")])
        assert len(P) == len(ids), ("the OBJ's vertex count is not the sculpt's", len(P), len(ids))
        D = np.zeros_like(B)
        D[ids] = P - B[ids]
        info = {"from_obj": a.from_obj}
    elif c.get("mode", "from_field") == "from_field":
        D, info = sculpt_from_field(c, sl, B, vals)
    else:
        D, info = sculpt(c, sl, B)
    ids = np.where(np.linalg.norm(D, axis=1) > 1e-5)[0]
    z = dict(np.load(os.path.join(BODY, "out", "topo", "close.npz")))
    sha = bt.topo_sha(z)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, f"{NAME}_close.npz"), D=D.astype(np.float32), ids=ids, topology=sha,
                        made_by="tools/body/sculpt/glute_sculpt.py", spec=a.spec)
    Dp = sliders.carry_to_tier(D, "close", "play")
    zp = dict(np.load(os.path.join(BODY, "out", "topo", "play.npz")))
    np.savez_compressed(os.path.join(OUT, f"{NAME}_play.npz"), D=Dp.astype(np.float32), topology=bt.topo_sha(zp),
                        made_by="tools/body/sculpt/glute_sculpt.py (sliders.carry_to_tier from close)", spec=a.spec)
    write_obj(os.path.join(OUT, f"{NAME}_close.obj"), B, D, z["Q"], ids)
    info.update({"vertices_moved": int(len(ids)), "spec": a.spec})
    print(json.dumps(info))


if __name__ == "__main__":
    main()