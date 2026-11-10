"""Flex and lap opening per part of a built piece, posed PER VERTEX the way the game poses it: a REPORT.

    python tools/armor/flex_check.py --pieces plate_spaulders_plain,plate_cuisses_plain --out <dir>   -> flex.json, flex.md

Each part (reach_table.plates(bent=True) components matched to their piece.json part by ride rule, a bent part's by
its mode row; rims and rivets ride with their plate, so they join it) is posed per vertex from its own glTF weights
(top 8) on its formed rest (its carried shapes at the game's form) over her clips (native_travel.frames(): every clip
but Jog_Fwd, under a held top its worn carry, as reach_table).

FLEX: per frame the Kabsch residual of the posed part against its rest (the best rigid fit's per-vertex distance:
max and p95 over the part's vertices), then the max over frames: separately over the idle clips (idle_*) and over all
clips, with the worst clip@frame. A rigid part reads ~0 (its blend of bone matrices is near rigid); a bent one reads
how far it bends.

LAP OPENING (a piece with lames: cop / plate = 0, lameN = N, per side): for each adjacent pair (k above, k+1 below)
and each theta bin round the limb (a point's bin is its theta at rest round the rest axis upperarm -> lowerarm, or
thigh -> calf, theta 0 = her front; bins inside both plates' spans only, their side edges' bins left out), overlap = how far k's edge nearest k+1 runs past k+1's edge nearest k, along the
posed axis (the bin's points only). Negative = an opening onto what is under. Reported: the smallest over bins and
frames, where (theta, clip@frame), the rest value, and the frames with any opening.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reach_table as rt  # noqa: E402

MM, BINS, CHUNK = 0.001, 24, 96
LIMBS = {"upperarm": "lowerarm", "thigh": "calf"}


def kabsch_residual(A, B):
    """[F, n]: per frame each point's distance from B [F, n, 3] to the best rigid motion of A [n, 3] onto it."""
    a = A - A.mean(0)
    b = B - B.mean(1, keepdims=True)
    H = np.einsum("ni,fnj->fij", a, b)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(np.einsum("fij,fjk->fik", U, Vt)))
    Vt[:, 2] *= d[:, None]
    R = np.einsum("fij,fjk->fik", U, Vt)          # a @ R ~ b
    return np.linalg.norm(b - np.einsum("ni,fij->fnj", a, R), axis=2)


def lbs(S, X, J, W, D=None):
    """[F, n, 3]: points X posed by per-point weights over the frames' skin matrices S [F, B, 4, 4]. D [F, n, 3]: the
    frames' carried shapes (sum_k w_k dP_k) added in rest space first, as the game does."""
    if D is None:
        Xh = np.c_[X, np.ones(len(X))]
        out = np.zeros((len(S), len(X), 3))
        for k in range(J.shape[1]):
            if W[:, k].any():
                out += W[None, :, k, None] * np.einsum("fnij,nj->fni", S[:, J[:, k], :3, :], Xh)
        return out
    R = X[None] + D
    out = np.zeros((len(S), len(X), 3))
    for k in range(J.shape[1]):
        if W[:, k].any():
            Sk = S[:, J[:, k]]
            out += W[None, :, k, None] * (np.einsum("fnij,fnj->fni", Sk[:, :, :3, :3], R) + Sk[:, :, :3, 3])
    return out


def carried(Fs, cw, i, n, X):
    """[n, 3, ..] -> [frames i..i+n, points, 3]: a part's carried shapes Fs {shape: [p, 3]} at the frames' weights cw
    ({shape: [F]}, native_travel.frames()["cw"]); None when it carries none (or cw is None: no shapes)."""
    ks = [k for k in (Fs or {}) if cw is not None and k in cw]
    if not ks:
        return None
    return sum(np.asarray(cw[k][i:i + n])[:, None, None] * Fs[k][None] for k in ks)


def flex(X, J, W, S, chunk=CHUNK, Fs=None, cw=None):
    """(max [F], p95 [F]) mm: the part's Kabsch residual per frame (Fs, cw: its carried shapes at the frames' weights)."""
    mx, p95 = [], []
    for i in range(0, len(S), chunk):
        r = kabsch_residual(X, lbs(S[i:i + chunk], X, J, W, carried(Fs, cw, i, len(S[i:i + chunk]), X))) / MM
        mx.append(r.max(1))
        p95.append(np.percentile(r, 95, axis=1))
    return np.concatenate(mx), np.concatenate(p95)


def limb_frame(S, heads, up, low, ref=(0.0, 0.0, 1.0)):
    """(c [F, 3], a [F, 3], r [F, 3], t [F, 3]): the limb's posed root, axis, theta-0 direction and the third axis."""
    h = np.c_[heads[[up, low]], np.ones(2)]
    c = np.einsum("fij,j->fi", S[:, up, :3, :], h[0])
    a = np.einsum("fij,j->fi", S[:, low, :3, :], h[1]) - c
    a /= np.linalg.norm(a, axis=1, keepdims=True)
    a0 = heads[low] - heads[up]
    a0 /= np.linalg.norm(a0)
    r0 = np.asarray(ref) - np.dot(ref, a0) * a0
    r = np.einsum("fij,j->fi", S[:, up, :3, :3], r0 / np.linalg.norm(r0))
    r -= (r * a).sum(1, keepdims=True) * a
    r /= np.linalg.norm(r, axis=1, keepdims=True)
    return c, a, r, np.cross(a, r)


def lap(upper, lower, S, heads, up, low, bins=BINS, chunk=CHUNK, cw=None):
    """Per frame and theta bin the overlap (mm) of the plate `upper` (X, J, W) over `lower` along the limb axis:
    [F, bins] (nan where a bin lacks either plate), and the sign used (+1: k+1 lies further down the axis)."""
    rest = np.broadcast_to(np.eye(4), S.shape[1:])[None]
    c, a, r, t = limb_frame(rest, heads, up, low)
    sgn = 1.0 if ((lower[0] - c[0]) @ a[0]).mean() > ((upper[0] - c[0]) @ a[0]).mean() else -1.0
    rb = []                                        # each point's bin by its REST theta (fixed on the plate)
    for X, *_ in (upper, lower):
        th = np.arctan2((X - c[0]) @ t[0], (X - c[0]) @ r[0])
        rb.append(np.minimum(((th + np.pi) / (2 * np.pi) * bins).astype(int), bins - 1))
    cnt = np.stack([np.bincount(b, minlength=bins) >= 3 for b in rb]).all(0)
    ok = cnt & np.roll(cnt, 1) & np.roll(cnt, -1)  # inside both plates' spans (their side edges' bins left out)
    out = []
    for i in range(0, len(S), chunk):
        Sc = S[i:i + chunk]
        c, a, r, t = limb_frame(Sc, heads, up, low)
        F = len(Sc)
        edge = []
        for (X, J, W, *Fs), red, b in ((upper, np.maximum, rb[0]), (lower, np.minimum, rb[1])):
            P = lbs(Sc, X, J, W, carried(Fs[0] if Fs else None, cw, i, F, X)) - c[:, None]
            s = sgn * np.einsum("fni,fi->fn", P, a)
            e = np.full((F, bins), -np.inf if red is np.maximum else np.inf)
            red.at(e, (np.repeat(np.arange(F), P.shape[1]), np.tile(b, F)), s.reshape(-1))
            edge.append(e)
        o = (edge[0] - edge[1]) / MM
        out.append(np.where(np.isfinite(o) & ok, o, np.nan))
    return np.concatenate(out), sgn


def lame_index(part):
    w = rt.role_word(part) or ""
    return 0 if w in ("cop", "plate") else int(w[4:]) if w.startswith("lame") and w[4:].isdigit() else None


def parts_of(sc, row, pid, wgt, min_cm2, shapes=()):
    """{name: (X [n, 3], J, W, bones {name: share}, bent, Fs {shape: [n, 3]})}: the piece's parts, their components
    joined (Fs: the glTF targets named in `shapes`, her correctives, that each part carries)."""
    from gl import Glb
    names = list(sc.poser.names)
    g = Glb(row["path"])
    col = np.array([sc.poser.index[g.nodes[j]["name"]] for j in g.js["skins"][0]["joints"]])
    ms = [(m.P, m.T, col[m.J], m.W.astype(float), rt.formed(m, wgt), {k: m.targets[k]["POSITION"].astype(float) for k in shapes if k in m.targets}) for m in g.meshes if m.node in row["meshes"] and m.J is not None]
    side = lambda k: "l" if "_l_" in k else "r" if "_r_" in k else ""  # noqa: E731
    expand = lambda d: {k: {b.replace("{s}", side(k)): v for b, v in r.items()} for k, r in d.items()}  # noqa: E731
    roles, bends = expand(rt.part_roles(pid)), expand(rt.part_bends(pid))
    out = {}
    for q in rt.plates(ms, min_cm2, bent=True):
        rule = {names[b]: v for b, v in q["rule"].items()}
        cand = bends if q["bent"] else roles
        tol = 0.01 if q["bent"] else 0.003
        hit = [k for k in cand if rt.role_of(rule, {k: cand[k]}, tol) == k]
        if not hit and q["bent"]:
            continue                                # a skinned (cloth) component, not a plate
        c = q["Xf"].mean(0)
        # one part per rule (its rims and rivets join it); a rule several parts share: each component on its own
        key = hit[0] if len(hit) == 1 else f"{'|'.join(rt.role_word(h) for h in hit) or max(rule, key=rule.get)}_{'l' if c[0] > 0 else 'r'}_y{c[1] * 100:.0f}"
        J = np.pad(q["J"], ((0, 0), (0, 8 - q["J"].shape[1])))
        W = np.pad(q["W"], ((0, 0), (0, 8 - q["W"].shape[1])))
        Fs = q.get("Fs", {})
        if key in out:
            X0, J0, W0, b0, bt, F0 = out[key]
            ks = set(F0) | set(Fs)
            Fj = {k: np.r_[F0.get(k, np.zeros_like(X0)), Fs.get(k, np.zeros_like(q["Xf"]))] for k in ks}
            out[key] = (np.r_[X0, q["Xf"]], np.r_[J0, J], np.r_[W0, W], b0, bt or q["bent"], Fj)
        else:
            out[key] = (q["Xf"], J, W, {k: round(v, 3) for k, v in rule.items()}, q["bent"], Fs)
    return out


def run(gear, ids, min_cm2=1.0, log=print, shapes=True):
    import gear_wear as gw
    import native_travel as nt
    ix, rows = gw.load_rows(gear)
    byid = {r["id"]: r for r in rows}
    sc = gw.build_scene(os.path.join(gw.REPO, "godot", "art", "people", ix["body"]), [])
    z = nt.frames()
    cw = z["cw"] if shapes else None                # (her correctives per frame: what the plates' carried shapes answer)
    names = list(sc.poser.names)
    assert z["index"] == {n: i for i, n in enumerate(names)}, "the clip cache is not on the body's skeleton"
    assert list(sc.poser.skel.names) == names
    heads = sc.poser.skel.rest[:, :3, 3]
    idle = np.char.startswith(z["clip"].astype(str), "idle_")
    wf = lambda k: f"{z['clip'][k]}@{int(z['frame'][k])}"  # noqa: E731
    out = []
    for pid in ids:
        row = byid.get(pid)
        if row is None:
            log(f"{pid}: no such row in {gear}")
            continue
        wt = gw.worn_top(sc, row)
        wgt = gw.support_weights(gw.support_of(row)) if wt is not None else None
        S = np.stack([wt.carry(s) for s in z["S"]]) if wt is not None else z["S"]
        parts = parts_of(sc, row, pid, wgt, min_cm2, tuple(cw) if cw is not None else ())
        rec = {"piece": pid, "file_mtime": os.path.getmtime(row["path"]), "frames": len(S), "idle_frames": int(idle.sum()),
               "clips": int(z["clips"]), "parts": [], "laps": []}
        for name, (X, J, W, bones, bent, Fs) in parts.items():
            mx, p95 = flex(X, J, W, S, Fs=Fs, cw=cw)
            e = {"part": name, "bent": bent, "points": len(X), "bones": bones}
            for tag, m in (("idle", idle), ("all", np.ones(len(S), bool))):
                k = np.flatnonzero(m)
                i, j = k[np.argmax(mx[k])], k[np.argmax(p95[k])]
                e[tag] = {"max": round(float(mx[i]), 3), "max_at": wf(i), "p95": round(float(p95[j]), 3), "p95_at": wf(j)}
            rec["parts"].append(e)
            log(f"{pid} {name}: flex max {e['all']['max']:.2f} mm ({e['all']['max_at']}), p95 {e['all']['p95']:.2f}; idle {e['idle']['max']:.2f} / {e['idle']['p95']:.2f}")
        for side in ("l", "r"):
            # the stack: the side's plates on a limb (>= 100 points), in order down its rest axis
            on = {n: next((u for u in LIMBS if any(b.startswith(u) and b.endswith("_" + side) for b in p[3])), None) for n, p in parts.items() if len(p[0]) >= 100}
            on = {n: u for n, u in on.items() if u}
            if not on:
                continue
            limb = max(set(on.values()), key=list(on.values()).count)
            up, low = names.index(f"{limb}_{side}"), names.index(f"{LIMBS[limb]}_{side}")
            ax = heads[low] - heads[up]
            stack = sorted((float(((parts[n][0] - heads[up]) @ ax).mean()), n) for n, u in on.items() if u == limb)
            for (_, n0), (_, n1) in zip(stack, stack[1:]):
                main = max(parts[n0][3], key=parts[n0][3].get)
                o, sgn = lap(parts[n0][:3] + (parts[n0][5],), parts[n1][:3] + (parts[n1][5],), S, heads, up, low, cw=cw)
                o0, _ = lap(parts[n0][:3], parts[n1][:3], np.broadcast_to(np.eye(4), S.shape[1:])[None], heads, up, low)
                f, b = np.unravel_index(np.nanargmin(o), o.shape)
                L = {"upper": n0, "lower": n1, "limb": f"{limb}_{side}->{LIMBS[limb]}_{side}", "main_bone": main, "axis_sign": sgn,
                     "min_overlap": round(float(o[f, b]), 2), "at": wf(f), "theta_deg": round((b + 0.5) * 360 / BINS - 180, 1),
                     "rest_min": round(float(np.nanmin(o0)), 2), "rest_theta_deg": round((int(np.nanargmin(o0[0])) + 0.5) * 360 / BINS - 180, 1),
                     "frames_open": int((np.nanmin(o, axis=1) < 0).sum()), "bins_shared": int(np.isfinite(o0[0]).sum()),
                     "idle_min": round(float(np.nanmin(o[idle])), 2)}
                rec["laps"].append(L)
                log(f"{pid} {n0}/{n1}: lap min {L['min_overlap']:.1f} mm at th {L['theta_deg']} {L['at']} (rest {L['rest_min']:.1f}, open frames {L['frames_open']})")
        out.append(rec)
    return out


def markdown(recs):
    L = ["# flex check", "", "flex = Kabsch residual of the part posed per vertex vs its rest (mm; max / p95 over its vertices, "
         "then the max over frames). lap = overlap of plate k's edge past k+1's along the posed limb axis per theta bin (mm; < 0 = open).", ""]
    for r in recs:
        L += [f"## {r['piece']} ({r['frames']} frames, {r['clips']} clips, {r['idle_frames']} idle frames; built file mtime {r['file_mtime']:.0f})", "",
              "| part | bent | points | idle max | idle p95 | all max | all p95 | worst (max) |", "|---|---|---|---|---|---|---|---|"]
        for e in r["parts"]:
            L.append(f"| {e['part']} | {'yes' if e['bent'] else ''} | {e['points']} | {e['idle']['max']:.2f} | {e['idle']['p95']:.2f} | "
                     f"{e['all']['max']:.2f} | {e['all']['p95']:.2f} | {e['all']['max_at']} |")
        if r["laps"]:
            L += ["", "| upper / lower | limb | min overlap | theta | clip@frame | idle min | rest min (theta) | frames open | bins |", "|---|---|---|---|---|---|---|---|---|"]
            for x in r["laps"]:
                L.append(f"| {x['upper']} / {x['lower']} | {x['limb']} | {x['min_overlap']:.1f} | {x['theta_deg']} | {x['at']} | {x['idle_min']:.1f} | "
                         f"{x['rest_min']:.1f} ({x['rest_theta_deg']}) | {x['frames_open']} | {x['bins_shared']} |")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gear", default=os.path.join(os.path.dirname(os.path.dirname(HERE)), "godot", "art", "gear", "out", "body_p1"))
    ap.add_argument("--pieces", default="plate_spaulders_plain,plate_cuisses_plain")
    ap.add_argument("--min-cm2", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-shapes", action="store_true", help="no corrective shapes carried on the plates")
    a = ap.parse_args(argv)
    recs = run(a.gear, [i for i in a.pieces.split(",") if i], a.min_cm2, shapes=not a.no_shapes)
    os.makedirs(a.out, exist_ok=True)
    json.dump(recs, open(os.path.join(a.out, "flex.json"), "w"), indent=1, default=str)
    open(os.path.join(a.out, "flex.md"), "w", encoding="utf-8").write(markdown(recs))
    print(f"flex_check: {len(recs)} pieces -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
