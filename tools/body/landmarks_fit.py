#!/usr/bin/env python
"""P1 B1 step 3: our skeleton's landmarks as sparse weighted combinations of OUR vertices (tools/body/base/landmarks.json).

    python tools/body/landmarks_fit.py        # needs tools/body/out/slider_bake/hm.npz (slider_bake.py) and the corr

Derived from: (b) MakeHuman's joint cubes, bone ends and weight boundaries (CC0, MPFB rig.default.json's rules) read
as the TARGET positions on the reference and on every sampled slider body (skeleton.py `Landmarks`); (c) skeleton.json's
landmark rules inherited as they are (each atomic point: cube / mh / skin_out / weights_base; mean, lerp and origin
compose them); (a) the game's need: our skeleton placed from OUR vertices alone (skeleton.py `place_skeleton_ours`),
so a body from our sliders, or one the app has reshaped, gets its bones without MakeHuman at placement time.

Method: per atomic landmark (cube / mh / weights_base) and tier, the candidates are the vertices it sees all round
(`candidates_rays`: per one of DIRS directions, the nearest vertex within CONE degrees of it: an inside joint gets its
whole cross-section ring; a one-sided patch (the nearest vertices) could not follow the spine as the belly grows: 50 mm
off); weights w (sum 1: the point moves with the whole body) by ridge least squares fitted JOINTLY over the training
bodies (the reference + every stored slider sample: our vertices = the correspondence of the MPFB body; the target =
the MakeHuman point on that same body, placed as the build places it), the ridge per atom the largest that fits the
training bodies within FIT_MM (the least noise gain). The midpoints and the random 6-slider mixes are held out.
skin_out is not fitted: its rule (the skin's furthest point out from an inner point, in a 2 cm tube) runs on OUR skin,
because MakeHuman's own answer jumps (onto the jaw when the shoulders narrow: 17 cm; no skin in the tube on tall
bodies); it is checked against MakeHuman's apart. Composites (mean, lerp) are taken in our frame (glTF).
Check: our landmarks vs MakeHuman's on every sampled body: p95 <= 2 mm, max <= 4 mm.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out", "slider_bake")
BASE_DIR = os.path.join(HERE, "base")
DIRS = 256            # (a) the directions a joint looks out along for its candidates (256: 64 left the knee and
CONE = 12.0           #     spine at 8-10 mm off on the height ends; measured 64 / 128 / 256 / 400)
TUBE_M = 0.02         # (c) skin_out's tube, skeleton.py's rule as it is
LAMBDAS = (1e-6, 3e-7, 1e-7, 3e-8, 1e-8, 3e-9, 1e-9, 3e-10, 1e-10)    # the ridge, tried largest first
FIT_MM = (1.0, 2.0)   # (a) a training fit's p95 / max that stops the search (half the check's 2 / 4 mm)
M, SHELL = 48, 1.6    # (the shell candidates: kept for comparison, not used)


def key(p):
    return json.dumps(p, sort_keys=True, separators=(",", ":"))


def atoms_of(skel):
    import skeleton as sk
    out = {}

    def walk(p):
        if p is None or "origin" in p:
            return
        if "mean" in p:
            for q in p["mean"]:
                walk(q)
            return
        if "lerp" in p:
            walk(p["lerp"][0])
            walk(p["lerp"][1])
            return
        out[key(p)] = p
    for d in skel["bones"]:
        if d.get("leaf"):
            continue
        e = sk.expand(d, "l", "l", "L")
        walk(e["head"])
        walk(e["tail"])
    return out


def fib_dirs(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def candidates_rays(V, x, n=64, cone_deg=12.0, reach=0.35):
    """The vertices the point sees all round: per direction (n, Fibonacci), the nearest vertex within `cone_deg`
    of it (the first surface a ray meets, roughly): an inside joint gets its whole cross-section ring."""
    r = V - x
    d = np.linalg.norm(r, axis=1)
    near = np.where(d < reach)[0]
    u = r[near] / np.maximum(d[near, None], 1e-12)
    cosc = np.cos(np.radians(cone_deg))
    out = set()
    for D in fib_dirs(n):
        m = (u @ D) > cosc
        if m.any():
            out.add(int(near[m][np.argmin(d[near][m])]))
    return np.array(sorted(out))


def candidates(V, x):
    d = np.linalg.norm(V - x, axis=1)
    order = np.argsort(d)
    r = SHELL * d[order[0]]
    pool = order[: max(2 * M, int((d < r).sum()))]
    pick = [pool[0]]
    dm = np.linalg.norm(V[pool] - V[pool[0]], axis=1)
    while len(pick) < min(M, len(pool)):
        j = int(np.argmax(dm))
        pick.append(pool[j])
        dm = np.minimum(dm, np.linalg.norm(V[pool] - V[pool[j]], axis=1))
    return np.array(sorted(pick))


def fit(X, L, lam):
    """X [S, M, 3] candidates on each body, L [S, 3] targets: min sum |X w - L|^2 + lam |w|^2 st sum w = 1."""
    S, m, _ = X.shape
    A0 = X.transpose(0, 2, 1).reshape(S * 3, m)
    b0 = L.reshape(S * 3)
    H = A0.T @ A0
    lam_abs = lam * np.trace(H) / m
    K = np.zeros((m + 1, m + 1))
    K[:m, :m] = 2 * (H + lam_abs * np.eye(m))
    K[:m, m] = K[m, :m] = 1.0
    rhs = np.append(2 * A0.T @ b0, 1.0)
    return np.linalg.solve(K, rhs)[:m]


def bodies():
    import slider_bake as sb
    import skeleton as sk
    import stages
    import topo_corr as tc
    z = np.load(os.path.join(OUT, "hm.npz"))
    HV, ids = z["V"], [str(i) for i in z["ids"]]
    js = {j["id"]: j for j in sb.jobs()}
    ref = tc.Reference()
    rig, wts = stages.load_mh("rig.default.json"), stages.load_mh("weights.default.json")["weights"]
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    atoms = atoms_of(skel)
    corr = {t: tc.load(t) for t in ("close", "play")}
    ours = {t: [] for t in corr}
    targ = []
    t0 = time.time()
    for k, i in enumerate(ids):
        b, to_world = ref.world(None if i == "ref" else HV[k])
        P = ref.close(None if i == "ref" else HV[k])
        lm = sk.Landmarks(b, rig, wts)
        row = []
        for a in atoms.values():
            try:
                row.append(to_world(lm.point(a)[None])[0])
            except ValueError:            # (MakeHuman's own rule finds no skin: skin_out's 2 cm tube on an extreme body)
                row.append(np.full(3, np.nan))
                print("  no MakeHuman point:", i, key(a)[:70])
        targ.append(np.stack(row))
        for t in corr:
            ours[t].append(tc.evaluate(corr[t], P).astype(np.float64))
    print("bodies", len(ids), round(time.time() - t0, 1), "s")
    kinds = np.array(["ref" if i == "ref" else js[i]["kind"] for i in ids])
    return skel, atoms, ids, kinds, np.stack(targ), {t: np.stack(v) for t, v in ours.items()}, ref, rig, wts, z


def stats_mm(e):
    e = np.asarray(e).ravel() * 1000
    return {"p95": round(float(np.percentile(e, 95)), 3), "max": round(float(e.max()), 3)}


def skin_out_ours(V, o, way):
    """skeleton.json's skin_out rule on OUR skin (glTF: up +y, front +z, back -z, lateral +x on her left)."""
    d = {"lateral": np.array([1.0, 0, 0]), "up": np.array([0.0, 1, 0]), "front": np.array([0.0, 0, 1]),
         "back": np.array([0.0, 0, -1])}[way].copy()
    if way == "lateral" and o[0] < 0:
        d = -d
    rel = V - o
    along = rel @ d
    off = np.linalg.norm(rel - along[:, None] * d, axis=1)
    m = (off < TUBE_M) & (along > 0)
    return o + d * along[m].max()


def fit_atom(X, L, c, train):
    """Per atom: the largest ridge (the smallest noise gain) whose fit on the training bodies is within FIT_MM."""
    ok = train & ~np.isnan(L[:, 0])
    for lam in LAMBDAS:
        w = fit(X[ok][:, c], L[ok], lam)
        e = np.linalg.norm(np.einsum("smx,m->sx", X[ok][:, c], w) - L[ok], axis=1) * 1000
        if np.percentile(e, 95) <= FIT_MM[0] and e.max() <= FIT_MM[1]:
            break
    return w, lam


def main():
    skel, atoms, ids, kinds, LT, OV, ref, rig, wts, z = bodies()
    train = np.isin(kinds, ["ref", "sample"])
    names = list(atoms)
    fitted = [a for a, n in enumerate(names) if "skin_out" not in atoms[n]]
    rules = [a for a, n in enumerate(names) if "skin_out" in atoms[n]]
    out = {"about": "P1 B1 step 3 (landmarks_fit.py): each atomic skeleton.json landmark (key: its rule as canonical "
                    "json), per tier: {ids, w}, a weighted sum of OUR vertices (w sums to 1), or {rule: skin_out}: "
                    "the rule itself on our skin (tube_m), its inner point from the table. skeleton.py "
                    "place_skeleton_ours reads it. 'gain' = |w|_2: a joint's move per unit of independent vertex noise.",
           "directions": DIRS, "cone_deg": CONE, "tube_m": TUBE_M, "fit_mm": FIT_MM, "tiers": {}, "check": {}}
    import skeleton as sk
    for tier, X in OV.items():
        table, lams, gains = {}, [], []
        for a in fitted:
            c = candidates_rays(X[0], LT[0, a], n=DIRS, cone_deg=CONE)
            w, lam = fit_atom(X, LT[:, a], c, train)
            table[names[a]] = {"ids": [int(i) for i in c], "w": [round(float(x), 10) for x in w]}
            lams.append(lam)
            gains.append(float(np.linalg.norm(w)))
        for a in rules:
            table[names[a]] = {"rule": "skin_out"}
        # every body: our landmarks (from our vertices alone) vs MakeHuman's on the same body
        E = np.full((len(ids), len(names)), np.nan)
        for k in range(len(ids)):
            lm = sk.OurLandmarks(X[k], table)
            for a in range(len(names)):
                if not np.isnan(LT[k, a, 0]):
                    E[k, a] = np.linalg.norm(lm.point(atoms[names[a]]) - LT[k, a])
        Ef, Er = E[:, fitted], E[:, rules]
        held = ~train
        per = {names[a]: stats_mm(E[:, a][~np.isnan(E[:, a])]) for a in fitted}
        worst = dict(sorted(per.items(), key=lambda kv: -kv[1]["max"])[:4])
        ok = ~np.isnan(Ef)
        rule_rep = {}
        for j, a in enumerate(rules):
            e = Er[:, j]
            m = ~np.isnan(e)
            big = [ids[k] for k in np.where(m & (e > 0.004))[0]]
            rule_rep[names[a]] = {**stats_mm(e[m]), "no_MH_point": int((~m).sum()), "over_4mm": len(big),
                                  "over_4mm_bodies": big[:6]}
        out["tiers"][tier] = table
        out["check"][tier] = {
            "fitted_atoms": len(fitted), "bodies": len(ids),
            "all": stats_mm(Ef[ok]), "train": stats_mm(Ef[train][ok[train]]), "held_out": stats_mm(Ef[held][ok[held]]),
            "mix": stats_mm(Ef[kinds == "mix"][ok[kinds == "mix"]]),
            "pass": bool(np.percentile(Ef[ok], 95) * 1000 <= 2 and Ef[ok].max() * 1000 <= 4),
            "worst_atoms": worst, "lambda_used": {str(l): lams.count(l) for l in sorted(set(lams))},
            "gain_p50": round(float(np.median(gains)), 2), "gain_max": round(float(max(gains)), 2),
            "ids_per_atom_p50": int(np.median([len(table[names[a]]["ids"]) for a in fitted])),
            "skin_out_rule_vs_MH": rule_rep}
        print(tier, json.dumps({k: v for k, v in out["check"][tier].items() if k != "skin_out_rule_vs_MH"}))
        for k, v in rule_rep.items():
            print("  ", k[:70], v)
    # through OUR slider evaluator (no MPFB at all): the held-out bodies from sliders_{tier}.npz
    import sliders
    import slider_bake as sb
    js = {j["id"]: j for j in sb.jobs()}
    for tier in OV:
        ev = sliders.OurSliders(os.path.join(BASE_DIR, f"sliders_{tier}.npz"))
        e = []
        for k, i in enumerate(ids):
            if kinds[k] in ("mix", "check"):
                lm = sk.OurLandmarks(ev.evaluate(js[i]["sliders"]), out["tiers"][tier])
                e += [np.linalg.norm(lm.point(atoms[names[a]]) - LT[k, a]) for a in fitted if not np.isnan(LT[k, a, 0])]
        out["check"][tier]["via_our_sliders_held_out"] = stats_mm(np.array(e))
        print(tier, "via our sliders (held-out bodies):", out["check"][tier]["via_our_sliders_held_out"])
    with open(os.path.join(BASE_DIR, "landmarks.json"), "w") as f:
        json.dump(out, f, indent=0)
    compare(skel, ref, rig, wts, out)


def compare(skel, ref, rig, wts, lmj):
    """Bone by bone: place_skeleton_ours on our reference vertices vs today's place_skeleton (MakeHuman's)."""
    import skeleton as sk
    import topo_corr as tc
    b, to_world = ref.world(None)
    names, par, Wm, ends_m, _ = sk.place_skeleton(skel, b, rig, wts, to_world)
    P = ref.close(None)
    for tier in ("close", "play"):
        V = tc.evaluate(tc.load(tier), P)
        n2, _, Wo, ends_o, _ = sk.place_skeleton_ours(skel, V, lmj["tiers"][tier])
        assert n2 == names
        dh = {n: max(np.linalg.norm(ends_m[n][0] - ends_o[n][0]), np.linalg.norm(ends_m[n][1] - ends_o[n][1])) * 1000
              for n in names}
        ang = {n: float(np.degrees(np.arccos(np.clip((np.einsum("ij,ij->j", Wm[i][:3, :3], Wo[i][:3, :3]).min()),
                                                            -1, 1)))) for i, n in enumerate(names)}
        top = sorted(dh.items(), key=lambda kv: -kv[1])[:6]
        topa = sorted(ang.items(), key=lambda kv: -kv[1])[:4]
        r = {"bones": len(names), "end_mm_p50": round(float(np.median(list(dh.values()))), 3),
             "end_mm_max": round(max(dh.values()), 3), "worst": {k: round(v, 3) for k, v in top},
             "axis_deg_max": round(max(ang.values()), 3), "worst_axis_deg": {k: round(v, 3) for k, v in topa}}
        lmj["check"][tier]["vs_today_on_reference"] = r
        print(tier, "vs today's placement:", json.dumps(r))
    with open(os.path.join(BASE_DIR, "landmarks.json"), "w") as f:
        json.dump(lmj, f, indent=0)


if __name__ == "__main__":
    main()
