"""gear_gap.py: how far a built rigid piece stands off her at REST, band by band, and what its tuck does to her skin.

    python tools/armor/gear_gap.py --gear godot/art/gear/out/body_p1 --body godot/art/people/body_p1 \
        --pieces plate_pauldrons_plain,plate_pauldrons_warden [--json out.json]

Per piece, per side (x- / x+) and per BAND (the binding's rigid groups stacked by height: band 0 = the topmost, a
pauldron's cop; band 1, 2 = its lames, going down), in mm:
  clear   the band's clearance to the RENDERED skin (her skin tucked as the shader lays it under this piece): min / median
  raw     the same against her untucked skin
  edge    the clearance to the rendered skin along the band's leading edge (the rim furthest along the stack, the last
          EDGE_MM of the band in each direction around it): the gap a camera sees under the plate; min / median
  top     band 0 only: its least clearance where her skin faces up (the shoulder top), rendered / untucked
and per piece the tuck's dent: the deepest tuck of her skin within RING_MM OUTSIDE the piece's footprint next to a rigid
plate (the dent that shows), and the deepest under the rigid plates.
The bands are read off the binding evaluated under the current roles (GEAR_ROLES as the build had it), laid on the
built meshes by nearest point: a build under other roles is said."""
import argparse
import json
import os
import sys
from types import SimpleNamespace

import numpy as np
from scipy.spatial import cKDTree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BAND_MM = 8.0      # a rigid group joins the band above it when their mean heights lie this close
EDGE_MM = 3.0      # a band's leading edge: its points this close to the furthest point of their direction
BINS = 24          # directions around the stack
RING_MM = 15.0     # the visible dent: her skin this far outside the footprint, beside a rigid plate
UP = 0.5           # her skin faces up: its normal's Y above this


def bands_of(bd, ev, tier="close"):
    """(X, side, band) of the binding's rigid points on this body: side -1 / +1 by x, band 0 = topmost of its side."""
    ms = [m for m in bd.meta["meshes"] if m["tier"] == tier]
    lead = bd.z[f"lead_{tier}"]
    comp = np.concatenate([ev[m["node"]]["comp"] for m in ms])
    X = np.vstack([ev[m["node"]]["Xu"] for m in ms])
    g = np.where(comp >= 0, lead[np.maximum(comp, 0)], -1)
    side, band = np.zeros(len(X), int), np.full(len(X), -1)
    ids = np.unique(g[g >= 0])
    gs = np.array([1 if X[g == k, 0].mean() >= 0 else -1 for k in ids])
    gy = np.array([X[g == k, 1].mean() for k in ids])
    for s in (-1, 1):
        b, last = -1, None
        for i in [i for i in np.argsort(-gy) if gs[i] == s]:
            if last is None or last - gy[i] > BAND_MM / 1000.0:
                b += 1
            last = gy[i]
            side[g == ids[i]], band[g == ids[i]] = s, b
    return X[band >= 0], side[band >= 0], band[band >= 0]


def edge_of(X, d):
    """The band's leading edge along d: per direction around d, its points within EDGE_MM of the furthest one."""
    c = X.mean(0)
    u = np.cross(d, [0.0, 0.0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    r = X - c
    s = r @ d
    b = np.floor((np.arctan2(r @ v, r @ u) + np.pi) / (2 * np.pi) * BINS).astype(int) % BINS
    top = np.full(BINS, -np.inf)
    np.maximum.at(top, b, s)
    return s >= top[b] - EDGE_MM / 1000.0


def gap(out_dir, bodies, row):
    import gear_fit as gf
    import gear_field
    import gear_tuck as gt
    import gear_wear as gw
    B = bodies["close"]
    P, T, R = gt.piece_of(out_dir, row, flags=True)
    rv = np.zeros(len(P), bool)
    rv[T[R].ravel()] = True
    bd = gf.Binding(os.path.join(gf.BIND, row["id"] + ".npz"))
    Xe, se, be = bands_of(bd, gf.eval_unit(bd, bodies, None if gf.is_bind_body(bodies, bd) else
                                           gf.load_bodies(os.path.join(REPO, bd.meta["bind_body"]))))
    dn, nn = cKDTree(Xe).query(P[rv])
    X, side, band = P[rv], se[nn], be[nn]
    tk, gone = gw.skin_tuck(gw.read_records(os.path.join(out_dir, "armor_tuck", row["id"] + ".bin")), gw.keys_of(B.V))
    wet = SimpleNamespace(V=B.V - B.N * tk[:, None], T=B.T, N=B.N)
    wet.surf = gf.Surface(wet.V, wet.T)
    c1 = gear_field.signed_clear(wet, X, k=16)[0] * 1000
    c0, n0 = gear_field.signed_clear(B, X, k=16)
    c0 = c0 * 1000
    res = {"id": row["id"], "rigid_points": int(rv.sum()), "band_fit_mm": round(float(dn.max() * 1000), 2),
           "tucked_points": int((tk > 0).sum()), "gone_points": int(gone.sum()), "bands": []}
    mm = lambda a: [round(float(a.min()), 1), round(float(np.median(a)), 1)] if len(a) else [None, None]
    for s in (-1, 1):
        nb = int(band[side == s].max()) + 1 if (side == s).any() else 0
        cs = [X[(side == s) & (band == b)].mean(0) for b in range(nb)]
        d = cs[-1] - cs[0] if nb > 1 else np.array([0.0, -1.0, 0.0])
        d = d / np.linalg.norm(d)
        for b in range(nb):
            m = (side == s) & (band == b)
            e = edge_of(X[m], d)
            r = {"side": "x-" if s < 0 else "x+", "band": b, "points": int(m.sum()), "clear": mm(c1[m]), "raw": mm(c0[m]),
                 "edge": mm(c1[m][e]), "edge_raw": mm(c0[m][e]), "edge_points": int(e.sum())}
            if b == 0:
                up = n0[m][:, 1] > UP
                up = up if up.any() else np.ones(int(m.sum()), bool)
                r["top"] = [round(float(c1[m][up].min()), 1), round(float(c0[m][up].min()), 1)]
            res["bands"].append(r)
    sk = SimpleNamespace(P=B.V, N=B.N)
    under = gt.under_rigid_of(sk, P, T, R)
    foot = gt.under_rigid_of(sk, P, T, np.ones(len(T), bool)) | under
    ring = np.zeros(len(B.V), bool)
    if under.any():
        ring = ~foot & (cKDTree(B.V[under]).query(B.V)[0] <= RING_MM / 1000.0)
    res["dent_out_mm"] = round(float(tk[ring].max() * 1000), 1) if ring.any() else 0.0
    res["dent_out_points"] = int((tk[ring] > 0.001).sum())
    res["dent_under_mm"] = round(float(tk[under].max() * 1000), 1) if under.any() else 0.0
    return res


def table(res):
    L = [f"{res['id']}: {res['rigid_points']} rigid points (bands laid within {res['band_fit_mm']} mm), "
         f"{res['tucked_points']} skin points tucked, {res['gone_points']} gone; dent outside the footprint "
         f"{res['dent_out_mm']} mm ({res['dent_out_points']} points over 1 mm), under the plates {res['dent_under_mm']} mm",
         "  side band  points | clear min  med | raw min  med | edge min  med | top (rendered / raw)"]
    f = lambda v: "    -" if v is None else f"{v:5.1f}"
    for r in res["bands"]:
        L.append(f"  {r['side']}   {r['band']}   {r['points']:6d} |     {f(r['clear'][0])} {f(r['clear'][1])} |   {f(r['raw'][0])} "
                 f"{f(r['raw'][1])} |    {f(r['edge'][0])} {f(r['edge'][1])} |"
                 + (f" {f(r['top'][0])} / {f(r['top'][1])}" if "top" in r else ""))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gear", default=os.path.join("godot", "art", "gear", "out", "body_p1"))
    ap.add_argument("--body", default=None, help="the body folder (default: godot/art/people/<gear_index body>)")
    ap.add_argument("--pieces", default="", help="row ids (default: every rigid row)")
    ap.add_argument("--json")
    a = ap.parse_args()
    import gear_fit as gf
    out = a.gear if os.path.isabs(a.gear) else os.path.join(REPO, a.gear)
    ix = json.load(open(os.path.join(out, "gear_index.json")))
    body = a.body or os.path.join("godot", "art", "people", ix["body"])
    bodies = gf.load_bodies(body if os.path.isabs(body) else os.path.join(REPO, body))
    want = set(a.pieces.split(",")) if a.pieces else None
    rows = [r for r in ix["rows"] if (r["id"] in want if want else
                                      bool(r.get("rigid")) or r["id"].startswith(("plate_", "mar_her_"))) and not r.get("lod")]
    allr = {}
    for r in rows:
        allr[r["id"]] = gap(out, bodies, r)
        print(table(allr[r["id"]]))
    if a.json:
        json.dump({"gear": a.gear, "body": bodies["close"].name, "roles": gf.roles_path(), "pieces": allr},
                  open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
