"""The reach rule for every rigid plate of a set, on today's weights: a REPORT (it never fails a build, never
changes a recipe).

    python tools/armor/reach_table.py --gear godot/art/gear/out/body_p1 --set plate --out <dir>   -> reach.json, reach.md

The reading (P2 lead 11, spaulder): a plate point may come toward her as far as its OWN REST STANDOFF minus the
leather (2.4 mm): limit = rest height - leather, so past = leather - its least height over her skin in motion. Her
skin is the skin the engine shows under that piece: linear blend (native_travel's frames, no corrective shapes),
each vertex pulled in along its posed stored normal by the piece's tuck record (gear_wear.skin_tuck), and under a
held top her springs at their worn equilibrium in every frame with the hold's form_support shapes (gear_wear.WornTop).
Heights are nearest-vertex along that vertex's normal (the rule's, native_travel.on_skin), her skin within REACH of
the plate at rest. The points are the BUILT mesh's vertices, its rolled rims' walls included (they hang up to 4 mm
nearer her than the plate's design face): a design sheet read on a grid (lead 11's room.py) under-reads the spaulder
cop by 2.3 / 1.2 mm (test_spaulder_row_is_lead_11s has the trace). A native piece's plates are named by their part
(piece.json "parts", matched by ride rule): cop, lame1.., else their main bone.

A plate = a connected component of the piece's meshes whose vertices all carry ONE bone blend (gear_wear's "rigid
component") of at least --min-cm2 of surface; its inner face (the vertices facing her) is what is measured. The row's
worst is the past-line at least STRAY+1 points reach; a deeper reading carried by 1-STRAY points is given in the note
as a stray with its place (near_mm: how far the nearest skin vertex was, a sideways reading shows as near >> past).
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MM, LEATHER_MM, REACH, STRAY, EPS_MM = 0.001, 2.4, 0.07, 3, 0.005


def height(P, V, N):
    """(h [n], near [n]): each point's height over the skin vertex nearest it, along that vertex's normal, and how far
    that vertex is."""
    d, j = cKDTree(V).query(P)
    return ((P - V[j]) * N[j]).sum(1), d


def measure(X0, frames, V0, N0, skin, leather=LEATHER_MM * MM):
    """The rule on one plate. X0 [n, 3]: its points at rest; frames: an iterable of (X [n, 3], key) (the points in a
    frame, any key naming it); (V0, N0): her skin at rest; skin(key) -> (V, N) in that frame. Returns per point:
    standoff (rest height), limit (standoff - leather), past (leather - least height: > 0 is past the line), at (the
    key of its worst frame), near (its nearest skin vertex's distance there), and hits {key: points past in it}."""
    s0, _ = height(X0, V0, N0)
    low, near, at, hits = np.full(len(X0), np.inf), np.zeros(len(X0)), np.full(len(X0), -1, object), {}
    for X, key in frames:
        h, d = height(X, *skin(key))
        m = h < low
        low, near, at[m] = np.where(m, h, low), np.where(m, d, near), key
        n = int((leather - h > EPS_MM * MM).sum())
        if n:
            hits[key] = n
    return {"standoff": s0, "limit": s0 - leather, "past": leather - low, "travel": s0 - low, "at": at, "near": near, "hits": hits}


def mark(past_mm):
    return "INSIDE" if past_mm <= EPS_MM else ("PAST <3" if past_mm < 3.0 else "PAST >=3")


def summary(r, stray=STRAY):
    """One row's numbers (mm) from measure()'s result: the worst at least stray+1 points reach, the strays above it."""
    p = r["past"] / MM
    order = np.argsort(-p)
    k = int(order[min(stray, len(p) - 1)])           # the (stray+1)th deepest point
    top = int(order[0])
    held = float(p[k]) if p[top] - p[k] > max(1.0, 0.3 * abs(p[top])) or int((p > EPS_MM).sum()) <= stray else float(p[top])
    w = top if held == float(p[top]) else k
    out = {"standoff_min": float(r["standoff"].min() / MM), "standoff_med": float(np.median(r["standoff"]) / MM),
           "limit_min": float(r["limit"].min() / MM), "limit_med": float(np.median(r["limit"]) / MM),
           "past": held, "travel": float(r["travel"][w] / MM), "at": r["at"][w], "near": float(r["near"][w] / MM), "worst_point": w,
           "points_past": int((p > EPS_MM).sum()), "points": len(p), "rest_past": float(max(0.0, -r["limit"].min() / MM)),
           "rest_points_past": int((r["limit"] < -EPS_MM * MM).sum()), "samples_past": int(sum(r["hits"].values())), "frames_past": len(r["hits"])}
    out["mark"] = mark(held)
    if held != float(p[top]):
        out["stray"] = {"past": float(p[top]), "points": int((p > held + 1.0).sum()), "at": r["at"][top], "near": float(r["near"][top] / MM), "point": top}
    return out


def plates(meshes, min_cm2=10.0, bent=False, top=8):
    """The rigid components of a piece. meshes: [(P [n, 3], T [m, 3], J [n, k] bone columns, W [n, k][, F [n, 3]])]
    (F: the mesh's carried shapes at the game's form, summed; zeros when absent). Returns [{"X": its welded points,
    "T": its triangles (rows of X), "rule": {bone column: share}, "cm2"}], by size.
    bent: every component (blend varying or not) also carries per point "Xf" (X + F, the formed rest), "J" / "W"
    [n, k] (its own glTF weights, top `top`, summing to 1) and "bent" (its blend varies); a varying one's "rule" is its
    MODE row (the ride its unbent points keep). Without bent the rows are exactly as before."""
    P = np.concatenate([m[0] for m in meshes]).astype(float)
    F = np.concatenate([m[4] if len(m) > 4 else np.zeros((len(m[0]), 3)) for m in meshes]).astype(float) if bent else None
    base = np.cumsum([0] + [len(m[0]) for m in meshes])
    T = np.concatenate([m[1] + b for m, b in zip(meshes, base)])
    nb = 1 + max(int(m[2].max()) for m in meshes)
    D = np.zeros((len(P), nb))
    for m, b in zip(meshes, base):
        W = m[3] / np.maximum(m[3].sum(1, keepdims=True), 1e-12)
        for k in range(m[2].shape[1]):
            np.add.at(D, (b + np.arange(len(W)), m[2][:, k]), W[:, k])
    _, first, weld = np.unique(np.round(P * 1e5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    weld = weld.reshape(-1)
    Tw = weld[T]
    n = len(first)
    e = np.concatenate([Tw[:, [0, 1]], Tw[:, [1, 2]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    out = []
    for c in np.unique(lab[Tw[:, 0]]):
        tri = Tw[lab[Tw[:, 0]] == c]
        vs = np.flatnonzero(lab == c)
        Dc = D[np.flatnonzero(lab[weld] == c)]
        X = P[first[vs]]
        a = 0.5 * np.linalg.norm(np.cross(P[first[tri[:, 1]]] - P[first[tri[:, 0]]], P[first[tri[:, 2]]] - P[first[tri[:, 0]]]), axis=1).sum()
        varies = np.abs(Dc - Dc[0]).max() > 2e-3
        if (varies and not bent) or a * 1e4 < min_cm2:
            continue
        at = np.full(n, -1)
        at[vs] = np.arange(len(vs))
        row = Dc[0]
        if varies:
            u, inv, cnt = np.unique(np.round(Dc * 1e3).astype(np.int64), axis=0, return_inverse=True, return_counts=True)
            row = Dc[np.flatnonzero(inv.reshape(-1) == int(np.argmax(cnt)))[0]]
        q = {"X": X, "T": at[tri], "rule": {int(b): float(row[b]) for b in np.flatnonzero(row > 1e-4)}, "cm2": float(a * 1e4)}
        if bent:
            Dv = D[first[vs]]
            Jv = np.argsort(-Dv, axis=1)[:, :top]
            Wv = np.take_along_axis(Dv, Jv, 1)
            q.update(Xf=X + F[first[vs]], J=Jv, W=Wv / np.maximum(Wv.sum(1, keepdims=True), 1e-12), bent=bool(varies))
        out.append(q)
    return sorted(out, key=lambda q: -q["cm2"])


def inner_face(X, T, V0, N0):
    """(the rows of X that face her, those of them on that face's border): by the plate's own vertex normals against
    the normal of the skin nearest each. A sheet with no face toward her (one-sided): every row."""
    fn = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    vn = np.zeros_like(X)
    for k in range(3):
        np.add.at(vn, T[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-20)
    inn = (vn * N0[cKDTree(V0).query(X)[1]]).sum(1) < -0.3
    if inn.sum() < 0.1 * len(X):
        return np.arange(len(X)), np.zeros(0, int)
    ti = T[inn[T].all(1)]
    e = np.sort(np.concatenate([ti[:, [0, 1]], ti[:, [1, 2]], ti[:, [2, 0]]]), axis=1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    return np.flatnonzero(inn), np.unique(u[cnt == 1])


def place(X, i, border, edge=0.008):
    """A coarse name for point i of the plate X (B's axes: +x her left, +y up, +z front)."""
    c, half = 0.5 * (X.max(0) + X.min(0)), np.maximum(0.5 * (X.max(0) - X.min(0)), 1e-6)
    d = (X[i] - c) / half
    side = ("medial" if abs(X[i][0]) < abs(c[0]) else "lateral", "upper" if d[1] > 0 else "lower", "front" if d[2] > 0 else "back")
    words = [w for w, v in zip(side, d) if abs(v) > 0.5] or ["middle"]
    on_edge = len(border) and np.linalg.norm(X[border] - X[i], axis=1).min() < edge
    return " ".join(words) + (" edge" if on_edge else "")


def part_roles(pid):
    """{part name: {bone: share}}: the native build's rigid parts and their ride rules (godot/art/gear/native/<id>/
    piece.json "parts"; {} when the piece is not native). The built gear merges its parts by material, so a plate's
    role is read back by its ride."""
    path = os.path.join(os.path.dirname(os.path.dirname(HERE)), "godot", "art", "gear", "native", pid, "piece.json")
    if not os.path.isfile(path):
        return {}
    parts = json.load(open(path, encoding="utf-8")).get("parts") or {}
    return {k: v["bones"] for k, v in parts.items() if isinstance(v, dict) and v.get("bones")}


def part_bends(pid):
    """{part name: {bone: share}} of the native parts whose rule has "bend" (their plates bend: per vertex the weights
    lerp from that ride toward her skin; the plate keeps the ride where it does not bend)."""
    path = os.path.join(os.path.dirname(os.path.dirname(HERE)), "godot", "art", "gear", "native", pid, "piece.json")
    if not os.path.isfile(path):
        return {}
    parts = json.load(open(path, encoding="utf-8")).get("parts") or {}
    return {k: v["bones"] for k, v in parts.items() if isinstance(v, dict) and v.get("bones") and v.get("bend")}


def formed(m, weights):
    """[n, 3]: a glTF mesh's carried shapes at the game's form (`weights` {shape: w}, the worn top's support), summed."""
    F = np.zeros((len(m.P), 3))
    for k, w in (weights or {}).items():
        if w and k in m.targets:
            F += w * m.targets[k]["POSITION"].astype(float)
    return F


def role_of(rule, roles, tol=0.003):
    """The part (cop_l_rigid, lame1_l_rigid, ..) whose ride rule is the plate's {bone name: share}, or None."""
    best, err = None, tol
    for k, b in roles.items():
        tot = sum(b.values()) or 1.0
        e = max(abs(rule.get(n, 0.0) - b.get(n, 0.0) / tot) for n in set(rule) | set(b))
        if e < err:
            best, err = k, e
    return best


def role_word(part):
    """cop_l_rigid -> cop, lame2_r_rigid -> lame2, arming_l_cap -> arming."""
    return part.split("_")[0] if part else None


def piece_ids(rows, name, also=()):
    return [r["id"] for r in rows if r["id"].startswith(name + "_") or r["id"] in also]


def run(gear, ids, clips="all", min_cm2=10.0, leather_mm=LEATHER_MM, log=print):
    """[row ..] for the pieces `ids` of `gear`, sorted by worst past-line; (rows, notes)."""
    import gear_wear as gw
    import native_travel as nt
    from gl import Glb
    ix, rows = gw.load_rows(gear)
    byid = {r["id"]: r for r in rows}
    sc = gw.build_scene(os.path.join(gw.REPO, "godot", "art", "people", ix["body"]), [])
    z = nt.frames()
    on = np.flatnonzero(nt.clip_frames(clips))
    names = list(sc.poser.names)
    assert z["index"] == {n: i for i, n in enumerate(names)}, "the clip cache is not on the body's skeleton"
    kd_skin, eye = cKDTree(sc.P0[sc.isk]), np.broadcast_to(np.eye(4), (len(names), 4, 4))
    out, notes, seen, worn_S = [], [], {}, {}
    for pid in ids:
        row = byid.get(pid)
        if row is None:
            notes.append(f"{pid}: no such row in {gear}")
            continue
        g = Glb(row["path"])
        col = np.array([sc.poser.index[g.nodes[j]["name"]] for j in g.js["skins"][0]["joints"]])
        bends = part_bends(pid)
        wt = gw.worn_top(sc, row)
        wgt = gw.support_weights(gw.support_of(row)) if wt is not None else None
        ms = [(m.P, m.T, col[m.J], m.W.astype(float)) + ((formed(m, wgt),) if bends else ()) for m in g.meshes if m.node in row["meshes"] and m.J is not None]
        pl = plates(ms, min_cm2, bent=bool(bends))
        for q in [q for q in pl if q.get("bent")]:      # a varying blend reads only as a plate whose part bends
            part = role_of({names[b]: v for b, v in q["rule"].items()}, bends, tol=0.01)
            if part is None:
                pl.remove(q)
            else:
                q["part"] = part
        sig = json.dumps([[np.round(q["X"].mean(0), 4).tolist(), len(q["X"]), sorted(q["rule"])] for q in pl])
        if not pl or sig in seen:
            notes.append(f"{pid}: " + ("no rigid plate (every component is skinned or under the size floor)" if not pl else f"shares {seen[sig]}'s plates (same shapes, same rides): skipped"))
            continue
        seen[sig] = pid
        if wt is not None and wt.key not in worn_S:
            worn_S[wt.key] = np.stack([wt.carry(z["S"][f]) for f in on])
        S_all = worn_S[wt.key] if wt is not None else z["S"][on]
        S0 = wt.S if wt is not None else eye
        recs = gw.read_records(row["tuck_path"]) if row.get("tuck_path") else {}
        roles = part_roles(pid)
        for n_pl, q in enumerate(pl):
            vs = np.unique(np.concatenate(kd_skin.query_ball_point(q["X"], REACH)).astype(int))   # (isk is the first rows)
            if not len(vs):
                continue
            tk = gw.skin_tuck(recs, [sc.keys[i] for i in vs], row.get("tuck_depth_mm"))[0]
            sub, nsub = sc.restrict(vs), sc.restrict(vs, sc.ntargets)

            def skin(S, vs=vs, tk=tk, sub=sub, nsub=nsub):
                V = sc.lbs(S, sc.rest(vs, wgt, sub), sc.J[vs], sc.W[vs])
                N = sc.stored_normals(S, wgt, vs, nsub)
                return V - N * tk[:, None], N
            bones, share = np.array(sorted(q["rule"])), np.array([q["rule"][b] for b in sorted(q["rule"])])
            share = share / share.sum()
            ride = lambda S, X: np.einsum("b,bij,nj->ni", share, S[bones][:, :3, :], np.c_[X, np.ones(len(X))])  # noqa: E731
            X = q["X"]
            if q.get("bent"):                           # per vertex: its own weights and shapes, the game's form
                X = q["Xf"]
                ride = lambda S, X, q=q: gw.Scene.lbs(S, X, q["J"], q["W"])  # noqa: E731
            V0, N0 = skin(S0)
            Xr = ride(S0, X)
            inn, border = inner_face(Xr, q["T"], V0, N0)
            at = np.full(len(Xr), -1)
            at[inn] = np.arange(len(inn))
            r = measure(Xr[inn], ((ride(S_all[k], X)[inn], k) for k in range(len(on))), V0, N0, lambda k: skin(S_all[k]))
            s = summary(r)
            wf = lambda k: f"{z['clip'][on[k]]}@{int(z['frame'][on[k]])}" if k is not None and k != -1 else "-"  # noqa: E731
            cl = {str(z["clip"][on[k]]) for k in r["hits"]}
            c = Xr[inn].mean(0)
            rule = {names[b]: round(float(v), 3) for b, v in zip(bones, share)}
            part = q.get("part") or role_of({names[b]: float(v) for b, v in zip(bones, share)}, roles)
            name = f"{pid} #{n_pl + 1} {role_word(part) or max(rule, key=rule.get)} " + ("mid" if abs(c[0]) < 0.02 else "l" if c[0] > 0 else "r") + f" y{c[1] * 100:.0f} {q['cm2']:.0f}cm2"
            s.update(piece=pid, plate=name + (" bent" if q.get("bent") else ""), **({"bent": True} if q.get("bent") else {}), part=part, bones=rule, cm2=round(q["cm2"], 1), leather=leather_mm, worn=wt is not None, at=wf(s["at"]),
                     place=place(Xr[inn], s.pop("worst_point"), at[border]), clips_past=len(cl), clips=len(set(z["clip"][on])), frames=len(on),
                     clips_past_names=sorted(cl))
            if "stray" in s:
                s["stray"].update(at=wf(s["stray"]["at"]), place=place(Xr[inn], s["stray"].pop("point"), at[border]))
            out.append(s)
            log(f"{name}: {s['mark']} {s['past']:.1f} mm {s['at']} {s['place']}")
    return sorted(out, key=lambda s: -s["past"]), notes


def markdown(rows, notes, head=""):
    L = [f"# reach table {head}", "", "limit = rest standoff - leather; past = leather - least height over her tucked / worn skin (mm). "
         "share = clips with any sample past. rest = already inside the leather line at rest (mm, points).", "",
         "| plate | bones | standoff min/med | limit min/med | worst past | travel | clip@frame | place | near | share | points | samples | rest | mark | note |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in rows:
        st = s.get("stray")
        note = f"stray: {st['points']} pt to {st['past']:.1f} at {st['at']}, {st['place']}, near {st['near']:.0f}" if st else ""
        L.append(f"| {s['plate']} | {' '.join(f'{b} {v:g}' for b, v in s['bones'].items())} | {s['standoff_min']:.1f} / {s['standoff_med']:.1f} | "
                 f"{s['limit_min']:.1f} / {s['limit_med']:.1f} | {s['past']:.1f} | {s['travel']:.1f} | {s['at']} | {s['place']} | {s['near']:.0f} | "
                 f"{s['clips_past']}/{s['clips']} | {s['points_past']}/{s['points']} | {s['samples_past']} | {s['rest_past']:.1f} ({s['rest_points_past']}) | "
                 f"{s['mark']}{' (worn)' if s['worn'] else ''} | {note} |")
    return "\n".join(L + [""] + [f"- {n}" for n in notes]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gear", default=os.path.join(os.path.dirname(os.path.dirname(HERE)), "godot", "art", "gear", "out", "body_p1"))
    ap.add_argument("--set", default="plate", help="every row whose id starts with <set>_")
    ap.add_argument("--also", default="", help="more row ids, comma separated")
    ap.add_argument("--only", default="", help="just these row ids")
    ap.add_argument("--clips", default="all", help='"all", "four" (the fight clips) or names, comma separated')
    ap.add_argument("--min-cm2", type=float, default=10.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        import gear_wear as gw
        ids = [i for i in a.only.split(",") if i] or piece_ids(gw.load_rows(a.gear)[1], a.set, [i for i in a.also.split(",") if i])
        clips = a.clips if a.clips in ("all", "four") else a.clips.split(",")
        rows, notes = run(a.gear, ids, clips, a.min_cm2)
        os.makedirs(a.out, exist_ok=True)
        json.dump({"set": a.set, "clips": a.clips, "leather_mm": LEATHER_MM, "rows": rows, "notes": notes}, open(os.path.join(a.out, "reach.json"), "w"), indent=1, default=str)
        open(os.path.join(a.out, "reach.md"), "w", encoding="utf-8").write(markdown(rows, notes, f"({a.set}, clips {a.clips}, {len(rows)} plates)"))
        print(f"reach_table: {len(rows)} plates, {sum(s['mark'] != 'INSIDE' for s in rows)} past their line -> {a.out}")
    except (Exception, SystemExit) as e:                      # a report: it never fails a build
        print(f"reach_table: no table ({type(e).__name__}: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
