"""The stand-off law's measure (P2 gear): how far each rigid plate must stand off her skin where she moves under it.

A rigid plate never bends, and B's skin under it does not move rigidly with the bone the plate rides (the share law
spreads an arm's lift over the shoulder; the arm correctives swell the deltoid): it rises 14-19 mm toward a pauldron's
lames as the arm lifts, so a plate fit at A's 4 mm clearance is gone through. This measures it: her skin under each
piece over the clips (gear_wear's skin test, the tuck as the game draws it), and for every sample through the plate's
outer face by more than gear_wear's 2 mm (OUT_MM) the plate's hit vertices get a target clearance: their clearance now
+ that shortfall + the law's "margin_mm". Targets only grow (each round's max with the last). The play tier's plates
(lod1, shadow) take the close tier's extra need from its nearest targeted vertex on the body.

gear_fit build reads the targets (godot/art/gear/standoff/<id>.json) where the slot has a "standoff" law in
tools/armor/rigid_roles.json and clears each rigid component to them (gear_field.rigid_fit_clear floor: translation +
per-axis scales, each target held at the law's "cap_mm"); gear_tuck's rule under a rigid plate takes the law's tuck
reach. The targets are clearances, so a slider body re-solves the same law on its own skin.
Loop: build, tuck, measure, rebuild (two or three rounds).

    python tools/armor/gear_standoff.py measure --gear godot/art/gear/out/body_p1 --pieces id,id --clips a,b [--jobs 3]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
OUT_MM = 2.0          # gear_wear's out2: through the outer face by more than this
NEAR_PLAY = 0.015     # a play-tier vertex takes the extra need of the close tier's nearest targeted vertex this close


def _work(args):
    gear, pieces, clips, step = args
    import gear_wear as gw
    ix, rows = gw.load_rows(gear)
    sc = gw.build_scene(os.path.join(REPO, "godot", "art", "people", ix["body"]), rows, set(pieces))
    order = json.load(open(os.path.join(HERE, "slot_map.json")))["order"]
    ck = gw.Check(sc, [r for r in rows if r["id"] in pieces], order, 0.0025, True)
    ck.add_skin(pieces)
    ck.run(gw.dump_sources(sc, gw.clip_files(",".join(clips)), step), log=lambda *a: None)
    return {x["B"]: dict(hitv=x["hitv"], minout=x["min_out"], area=x["area"]) for x in ck.tests}


def scene_nodes(gear, pieces):
    """gear_wear.build_scene's piece vertex ranges, [(piece, node, start, n)], and the scene."""
    import gear_wear as gw
    from gl import Glb
    ix, rows = gw.load_rows(gear)
    body_dir = os.path.join(REPO, "godot", "art", "people", ix["body"])
    sc = gw.build_scene(body_dir, rows, set(pieces))
    out, at = [], int((sc.kind != "piece").sum())
    for r in rows:
        if r["id"] not in pieces:
            continue
        for m in Glb(r["path"]).meshes:
            if m.node not in r["meshes"] or m.J is None:
                continue
            out.append((r["id"], m.node, at, len(m.P)))
            at += len(m.P)
    assert at == len(sc.P0), "gear_standoff: scene order differs from gear_wear's"
    return out, sc


def measure(gear, pieces, clips, jobs=3, step=2, say=print):
    import gear_fit as gf
    from multiprocessing import Pool
    from scipy.spatial import cKDTree
    parts = [clips[k::jobs] for k in range(jobs) if clips[k::jobs]]
    with Pool(len(parts)) as pool:
        rs = pool.map(_work, [(gear, pieces, p, step) for p in parts])
    ranges, sc = scene_nodes(gear, pieces)
    ix = json.load(open(os.path.join(gear, "gear_index.json")))
    bodies = gf.load_bodies(os.path.join(REPO, "godot", "art", "people", ix["body"]))
    os.makedirs(gf.STANDOFF, exist_ok=True)
    res = {}
    for pc in pieces:
        if pc not in rs[0]:
            continue
        bd = gf.Binding(os.path.join(gf.BIND, f"{pc}.npz"))
        law = gf.standoff_law(bd.meta["row"].get("slot")) or {}
        mg = float(law.get("margin_mm", 1.0)) / 1000.0
        mo = np.min([r[pc]["minout"] for r in rs], 0)
        hitv, area = rs[0][pc]["hitv"], rs[0][pc]["area"]
        short = -mo - OUT_MM / 1000.0
        bad = short > 0
        fp = os.path.join(gf.STANDOFF, f"{pc}.json")
        old = json.load(open(fp)).get("targets", {}) if os.path.isfile(fp) else {}
        tg = {n: {int(u): float(c) for u, c in v} for n, v in old.items()}
        node_of = {m["node"]: m for m in bd.meta["meshes"]}
        z = bd.z
        for (pid, node, st, n) in ranges:
            if pid != pc or node not in node_of:
                continue
            inv = z[f"inv{node_of[node]['i']}"]
            sel = bad[:, None] & (hitv >= st) & (hitv < st + n)
            if not sel.any():
                continue
            rows_, cols = np.nonzero(sel)
            c_now, _ = gf.signed_clear(bodies["close"], sc.P0[hitv[rows_, cols]])
            want = c_now + short[rows_] + mg
            d = tg.setdefault(node, {})
            for u, w in zip(inv[hitv[rows_, cols] - st], want):
                d[int(u)] = max(d.get(int(u), -1.0), float(w))
        # the play tier: the close tier's extra need (target less its clearance as bound), by the nearest targeted vertex
        cl = [(m, tg[m["node"]]) for m in bd.meta["meshes"] if m["tier"] == "close" and m["node"] in tg]
        if cl:
            Pc, Ec = [], []
            for m, d in cl:
                X, _ = gf.eval_points(bodies["close"], z[f"tri{m['i']}"], z[f"bw{m['i']}"], z[f"off{m['i']}"])
                us = np.array(sorted(d))
                c0, _ = gf.signed_clear(bodies["close"], X[us])
                Pc.append(X[us])
                Ec.append(np.array([d[u] for u in us]) - c0)
            Pc, Ec = np.vstack(Pc), np.concatenate(Ec)
            kd = cKDTree(Pc)
            for m in bd.meta["meshes"]:
                cm = z[f"comp{m['i']}"]
                if m["tier"] != "play" or not (cm >= 0).any():
                    continue
                X, _ = gf.eval_points(bodies["play"], z[f"tri{m['i']}"], z[f"bw{m['i']}"], z[f"off{m['i']}"])
                dd, kk = kd.query(X)
                ok = (dd < NEAR_PLAY) & (cm >= 0) & (Ec[kk] > 0)
                if ok.any():
                    c0, _ = gf.signed_clear(bodies["play"], X[ok])
                    d = tg.setdefault(m["node"], {})
                    for u, w in zip(np.nonzero(ok)[0], c0 + Ec[kk[ok]]):
                        d[int(u)] = max(d.get(int(u), -1.0), float(w))
        out = {"id": pc, "body": ix["body"], "clips": clips, "out_mm": OUT_MM, "margin_mm": mg * 1000,
               "targets": {n: [[u, round(c, 5)] for u, c in sorted(d.items())] for n, d in tg.items()}}
        with open(fp, "w") as f:
            json.dump(out, f)
        res[pc] = {"out2_mm2": round(float(area[bad].sum() * 1e6), 1), "worst_mm": round(float(-mo.min() * 1000), 1),
                   "targets": sum(len(v) for v in tg.values())}
        say(f"gear_standoff {pc}: out2 {res[pc]['out2_mm2']} mm2, worst {res[pc]['worst_mm']} mm, "
            f"{res[pc]['targets']} targeted vertices -> {os.path.relpath(fp, REPO)}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("measure",))
    ap.add_argument("--gear", required=True)
    ap.add_argument("--pieces", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--step", type=int, default=2)
    a = ap.parse_args()
    gear = a.gear if os.path.isabs(a.gear) else os.path.join(REPO, a.gear)
    measure(gear, a.pieces.split(","), a.clips.split(","), a.jobs, a.step)


if __name__ == "__main__":
    main()
