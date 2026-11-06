"""P4 clips: SOMA motion (Kimodo / MotionBricks) retargeted onto B, the game-side front of Marionette's motion core
(Marionette tools/motion/: one implementation the app and this CLI share).

    python tools/anim/p4.py import <bvh> <clip> [--loop] [--inplace]   source -> tools/anim/p4/src/<clip>.npz (committed:
                                                                      generation is not reproducible) + a stub spec
                                                                      tools/anim/p4/specs/<clip>.json
    python tools/anim/p4.py build [clips]     every spec -> godot/art/people/body_p1/p4/<clip>.json (build output,
                                              git-ignored; bash tools/anim/p4_pack.sh packs them into p4_clips.res)
    python tools/anim/p4.py gen [clips] [--encode-only] the specs' gen blocks -> Kimodo (motion/kimodo_run.py): every prompt
                                              encoded ONCE into the embedding cache (only with 18 GB of RAM free), then
                                              the diffusion model alone makes the takes from the cache (take the gpu
                                              turn first) -> TAKES_DIR/<clip>__p<i>_<k>.bvh
    python tools/anim/p4.py takes [clips]     every take through the core with the spec's post, measured against its bands
                                              (motion/measures.py), logged in specs/<clip>.takes.json; the best is imported
    python tools/anim/p4.py check [clips]     tools/body/clipcheck.py's measures on the built clips (pops, seam, feet,
                                              arm contact, hand gap) plus the core's fidelity and planted slide, a table

The rig is tools/body/rig/{b_skeleton,soma_to_b}.json (tools/body/rig_map.py).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
# Where Marionette lives (its tools/motion is the core). One constant, overridable by env MARIONETTE_DIR; the
# motion-a1 worktree for now, Marionette's main checkout once the core is merged there.
MARIONETTE = os.environ.get("MARIONETTE_DIR", "C:/Users/munch/Desktop/Marionette_motion")
sys.path.insert(0, str(Path(MARIONETTE) / "tools"))
from motion import clip as MC  # noqa: E402
from motion import footlock, measures, paths, retarget, soma  # noqa: E402

P4 = REPO / "tools/anim/p4"
RIG = REPO / "tools/body/rig"
OUT = REPO / "godot/art/people/body_p1/p4"
KIMODO_PY = os.environ.get("KIMODO_PY", "C:/Users/munch/Tools/kimodo/.venv/Scripts/python.exe")
TAKES_DIR = Path(os.environ.get("P4_TAKES", "C:/Users/munch/Tools/mocap/kimodo_p4"))
CACHE = Path(os.environ.get("KIMODO_CACHE", "C:/Users/munch/Tools/mocap/kimodo_cache"))
KFPS = 30


def specs(names):
    allp = sorted(p for p in (P4 / "specs").glob("*.json") if not p.stem.endswith(".takes"))
    return [p for p in allp if not names or p.stem in names]


def cmd_import(a):
    s = soma.read_bvh(a.bvh)
    (P4 / "src").mkdir(parents=True, exist_ok=True)
    (P4 / "specs").mkdir(parents=True, exist_ok=True)
    soma.save_npz(s, P4 / "src" / f"{a.clip}.npz")
    sp = P4 / "specs" / f"{a.clip}.json"
    spec = json.loads(sp.read_text()) if sp.exists() else {"notes": ""}
    spec.update({"loop": a.loop, "inplace": a.inplace, "source": f"src/{a.clip}.npz",
                 "bvh": os.path.basename(a.bvh), "sha1": s.sha1})
    sp.write_text(json.dumps(spec, indent=1) + "\n")
    print(f"{a.clip}: {s.frames} frames from {os.path.basename(a.bvh)} -> src/{a.clip}.npz, specs/{a.clip}.json")


def _cs_vec(name):
    """A Vector3 constant from godot/logic/Play/WeaponSockets.cs (the game's data, one source)."""
    import re
    src = (REPO / "godot/logic/Play/WeaponSockets.cs").read_text(encoding="utf-8")
    m = re.search(name + r"\s*=\s*new\(([^)]*)\)", src)
    return [float(x.strip().rstrip("f")) for x in m.group(1).split(",")]


def pieces():
    """B's held pieces in their bones' spaces, as the game seats them on B: the sword's points (ArmsDump's, A's hand
    space, seated on A's fist pocket) moved onto B's own pocket (WeaponSockets.BladeAtRB / BladeDirRB, the least turn,
    as FistSeat lays it), the shield's as they are (lowerarm_l, the same bone-local mount). And the pockets the fit aims
    by: the blade's axis and grip, the shield's boss (its points' centroid) and face (its thin axis, out of the arm)."""
    if "_pc" in globals():
        return _pc
    from motion import quat as Q
    arms = json.loads((REPO / "tools/anim/data/arms_local.json").read_text())
    atA, dirA = np.array(_cs_vec("BladeAtR")), np.array(_cs_vec("BladeDirR"))
    atB, dirB = np.array(_cs_vec("BladeAtRB")), np.array(_cs_vec("BladeDirRB"))
    dirA, dirB = dirA / np.linalg.norm(dirA), dirB / np.linalg.norm(dirB)
    R = Q.arc(dirA, dirB)
    sw = np.array(arms["chevalier_sword@hand_r"]["v"], float)
    sw = atB + (sw - atA) @ R.T
    tip = float(np.max((sw - atB) @ dirB))
    sh = np.array(arms["shield_round@lowerarm_l"]["v"], float)
    c = sh.mean(0)
    _, _, vt = np.linalg.svd(sh - c)
    face = vt[2] if vt[2] @ np.array([-1.0, 0, 0]) > 0 else -vt[2]
    rad = float(np.max(np.linalg.norm((sh - c) - np.outer((sh - c) @ face, face), axis=1)))
    globals()["_pc"] = {"sword": sw, "shield": sh, "blade": {"dir": dirB.tolist(), "at": atB.tolist(), "tip": tip},
                        "shieldp": {"at": c.tolist(), "face": face.tolist(), "radius": rad}}
    return _pc


def fit_of(spec):
    """The spec's fit block with the game's pocket data filled in."""
    f = spec.get("fit")
    if not f:
        return None
    f = json.loads(json.dumps(f))
    if "blade" in f:
        f["blade"]["pocket"] = pieces()["blade"]
    if "shield" in f:
        f["shield"]["pocket"] = pieces()["shieldp"]
    return f


def run_post(src, spec, name):
    """The core on one source with the spec's post steps (loop, in place, whole cycles, the gait lock) and its fit."""
    po = spec.get("post", {})
    cyc = po.get("cycle_s")
    return MC.run(src, RIG, loop=po.get("loop", spec.get("loop", False)), inplace=po.get("inplace", spec.get("inplace", False)),
                  name=name, gait=po.get("gait", False), duty=po.get("duty"),
                  cycle=(int(round(cyc[0] * KFPS)), int(round(cyc[1] * KFPS))) if cyc else None,
                  crop=tuple(po["crop"]) if po.get("crop") else None, fit=fit_of(spec))


def build_one(p):
    spec = json.loads(p.read_text())
    return run_post(P4 / spec["source"], spec, p.stem)


def measure(r, spec):
    """The bible's numbers on a core result (B's side), per the spec's kind."""
    fps = r.src.fps
    if spec.get("kind") == "gait":
        m = measures.gait(r.P, r.rig, fps, r.clip.get("speed_mps"), loop=r.clip["loop"])
        m.update(held(r, spec))
        return m
    m = measures.idle(r.P, r.rig, fps, loop=r.clip["loop"])
    m.update(hand_targets(r, spec))
    m.update(held(r, spec))
    return m


def held(r, spec):
    """The held pieces' numbers on B (the game's seat on B: pieces()): the blade's angle below the horizontal (mean, and
    its pitch swing peak to peak), its heading off her forward (+ her left), its tip's height; the shield's boss in her
    pelvis frame (cm: left, up, forward of the pelvis head), its top edge's height and its face's heading (+ open)."""
    out = {}
    rig, G, P = r.rig, r.G, r.P
    n = r.m
    pv = rig.index["pelvis"]
    Rp = G[:n, pv] @ rig.R0[pv].T
    pc = pieces()
    def local(v):
        return np.einsum("fji,fj->fi", Rp, v)
    if "sword" in spec.get("held", []):
        h = rig.index["hand_r"]
        d = local(np.einsum("fij,j->fi", G[:n, h], pc["blade"]["dir"]))
        below = np.degrees(np.arctan2(-d[:, 1], np.hypot(d[:, 0], d[:, 2])))
        out["blade_below_deg"] = round(float(below.mean()), 1)
        out["blade_swing_deg"] = round(float(np.ptp(below)), 1)
        out["blade_heading_deg"] = round(float(np.degrees(np.arctan2(d[:, 0], d[:, 2])).mean()), 1)
        grip = P[:n, h] + np.einsum("fij,j->fi", G[:n, h], pc["blade"]["at"])
        tip = grip + np.einsum("fij,j->fi", G[:n, h], pc["blade"]["dir"]) * pc["blade"]["tip"]
        out["blade_tip_cm"] = round(100 * float(tip[:, 1].mean()), 1)
    if "shield" in spec.get("held", []):
        la = rig.index["lowerarm_l"]
        boss = P[:n, la] + np.einsum("fij,j->fi", G[:n, la], pc["shieldp"]["at"])
        b = local(boss - P[:n, pv]).mean(0)
        out["boss_l_cm"], out["boss_up_cm"], out["boss_fwd_cm"] = (round(100 * float(x), 1) for x in b)
        pts = np.einsum("fij,kj->fki", G[:n, la], pc["shield"]) + P[:n, la][:, None]
        out["shield_top_cm"] = round(100 * float(pts[:, :, 1].max(1).mean()), 1)
        f = local(np.einsum("fij,j->fi", G[:n, la], pc["shieldp"]["face"]))
        out["shield_open_deg"] = round(float(np.degrees(np.arctan2(f[:, 0], f[:, 2])).mean()), 1)
    return out


def hand_targets(r, spec):
    """The keyed hands' distance from their targets on B (cm; mean and worst over the clip): each target rides the
    pelvis at its rest offset (gen.keys.hands, B meters from the pelvis head, her left/up/forward)."""
    K = spec.get("gen", {}).get("keys")
    if not K:
        return {}
    rig, out = r.rig, {}
    pv = rig.index["pelvis"]
    Rrel = r.G[:, pv] @ rig.R0[pv].T
    for h, off in K["hands"].items():
        b = rig.index["hand_l" if h.startswith("Left") else "hand_r"]
        t = r.P[:, pv] + Rrel @ np.asarray(off)
        d = np.linalg.norm(r.P[:, b] - t, axis=1) * 100
        s = "l" if h.startswith("Left") else "r"
        out[f"hand_{s}_target_cm"] = round(float(d.mean()), 2)
        out[f"hand_{s}_target_max_cm"] = round(float(d.max()), 2)
    return out


def gen_specs(names):
    return [(p, json.loads(p.read_text())) for p in specs(names) if json.loads(p.read_text()).get("gen")]


def soma_k(spec):
    """B's size over SOMA's (the retarget's scale), from the clip's current source."""
    return float(retarget.scale_of(retarget.Rig(RIG), soma.load_npz(P4 / spec["source"])))


def path_of(g, sc):
    r = dict(g["root2d"])
    for k in ("travel", "overshoot"):
        if k in r:
            r[k] = r[k] * sc
    return {"xz": paths.make(r, g["seconds"], KFPS).round(5).tolist(), "every": r.get("every", 1)}


def jobs_of(names):
    """Each prompt x each path scale (root2d_scales: Kimodo's hips swing past its smooth root, and not linearly, so
    the path's amplitude is searched; the scale is in the job name, s<percent>). gen.keys: hand end-effector keys
    (kimodo_run.hand_keys) taken from our own take {src: {prompt, scale, pick}} at the B offsets (meters from the
    pelvis, her left/up/forward) mapped to SOMA's scale, regenerated per keys.prompts x keys.scales as __k<i>s<pct>."""
    jobs = []
    for p, sp in gen_specs(names):
        g = sp["gen"]
        def job(i, sc, nm):
            j = {"name": nm, "prompt": g["prompts"][i], "seconds": g["seconds"], "seed": g["seeds"][i % len(g["seeds"])],
                 "takes": g["takes"]}
            if g.get("root2d"):
                j["root2d"] = path_of(g, sc)
            return j
        for i in range(len(g["prompts"])):
            if not g.get("root2d") or "root2d_scales" not in g:
                jobs.append(job(i, 1.0, f"{p.stem}__p{i}"))
                continue
            for sc in g["root2d_scales"]:
                jobs.append(job(i, sc, f"{p.stem}__p{i}s{round(sc * 100)}"))
        if g.get("more"):              # (more takes of chosen prompts, new seeds: __m<i>)
            for i in g["more"]["prompts"]:
                j = job(i, 1.0, f"{p.stem}__m{i}")
                j.update(takes=g["more"]["takes"], seed=j["seed"] + g["more"]["seed_add"])
                jobs.append(j)
        if g.get("keys"):
            K = g["keys"]
            k = soma_k(sp)
            src = job(K["src"]["prompt"], K["src"].get("scale", 1.0), "src")
            src = {kk: src[kk] for kk in ("prompt", "seconds", "seed", "takes", "root2d") if kk in src}
            src["pick"] = K["src"].get("pick", 0)
            # (aim: what is sent = the target minus the take's measured mean miss on B, in the pelvis frame: the
            # retarget's arm calibration lands Kimodo's wrist a few cm from where it put SOMA's)
            aim = K.get("aim", {})
            hands = {h: [(x + a) / k for x, a in zip(off, aim.get(h, [0, 0, 0]))] for h, off in K["hands"].items()}
            for i in K.get("prompts", [K["src"]["prompt"]]):
                for sc in K.get("scales", [K["src"].get("scale", 1.0)]):
                    j = job(i, sc, f"{p.stem}__k{K.get('tag', '')}{i}s{round(sc * 100)}")
                    j["keys"] = {"src": src, "hands": hands, "start": K.get("start", 15), "every": K.get("every", 30)}
                    jobs.append(j)
    return jobs


def cmd_gen(a):
    import subprocess
    import tempfile
    jobs = jobs_of(a.clips)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f)
    core = str(Path(MARIONETTE) / "tools/motion/kimodo_run.py")
    env = dict(os.environ, TEXT_ENCODER_DEVICE="cpu", PYTHONUNBUFFERED="1")
    r = subprocess.run([KIMODO_PY, core, "encode", f.name, "--cache", str(CACHE)], env=env)
    if r.returncode or a.encode_only:
        os.unlink(f.name)
        sys.exit(r.returncode)
    r = subprocess.run([KIMODO_PY, core, "generate", f.name, str(TAKES_DIR), "--cache", str(CACHE)], env=env)
    os.unlink(f.name)
    sys.exit(r.returncode)


def cmd_takes(a):
    for p, sp in gen_specs(a.clips):
        bvhs = sorted(TAKES_DIR.glob(f"{p.stem}__*_*.bvh"))
        log = []
        tl = P4 / "specs" / f"{p.stem}.takes.json"
        if a.match and tl.exists():    # (score only the takes matching; the rest keep their logged scores)
            log = [t for t in json.loads(tl.read_text()) if a.match not in t["take"]]
            bvhs = [b for b in bvhs if a.match in b.name]
        for b in bvhs:
            try:
                r = run_post(b, sp, p.stem)
                m = measure(r, sp)
                sl = footlock.slide(r.P, r.rig, r.wins, r.belt, r.src.fps, r.m)
                m["slide_mm"] = round(max(sl) * 1000, 2)
                m["seam_cost"] = round(r.prep.seam_cost, 3) if getattr(r.prep, "seam_cost", None) is not None else None
                sc = measures.score(m, sp["bands"])
                log.append({"take": b.name, "score": sc, "frames": r.clip["frames"], "crop": list(r.prep.crop), **m})
            except Exception as e:  # (a take the core cannot read is logged, not fatal)
                log.append({"take": b.name, "score": 1e9, "error": str(e)})
        for t in log:                  # (logged takes re-scored against the spec's bands as they are now)
            if "error" not in t:
                t["score"] = measures.score(t, sp["bands"])
        # gate: bands a take must pass to be chosen at all (a run's cadence: playback scale cannot fix it)
        gate = {k: sp["bands"][k] for k in sp.get("gate", [])}
        log.sort(key=lambda x: (not all(k in x and lo <= x[k] <= hi for k, (lo, hi) in gate.items()), x["score"]))
        (P4 / "specs" / f"{p.stem}.takes.json").write_text(json.dumps(log, indent=1) + "\n")
        for t in log[:3]:
            print(f"{p.stem}: {t['take']} score {t['score']}")
        if log and log[0]["score"] < 1e9:
            best = TAKES_DIR / log[0]["take"]
            s = soma.read_bvh(str(best))
            soma.save_npz(s, P4 / "src" / f"{p.stem}.npz")
            sp.update({"source": f"src/{p.stem}.npz", "bvh": best.name, "sha1": s.sha1, "take_score": log[0]["score"]})
            p.write_text(json.dumps(sp, indent=1) + "\n")


def cmd_build(a):
    OUT.mkdir(parents=True, exist_ok=True)
    for p in specs(a.clips):
        r = build_one(p)
        MC.write(r.clip, OUT / f"{p.stem}.json")
        sp = json.loads(p.read_text())
        if sp.get("bands"):
            m = measure(r, sp)
            ok = measures.passes(m, sp["bands"])
            print(f"  {p.stem}: " + ", ".join(f"{k} {m.get(k)}{'' if ok[k] else ' MISS'}" for k in sp["bands"]))
        for L in r.fitlog or []:
            print(f"  fit {L['layer']}: " + ", ".join(f"{k} {v}" for k, v in L.items() if k != "layer"))
        print(f"{p.stem}: {r.clip['frames']} frames, source crop {r.prep.crop}, yaw {r.prep.yaw_deg:.1f} deg, "
              f"windows L {len(r.wins[0])} R {len(r.wins[1])} -> {OUT.relative_to(REPO).as_posix()}/{p.stem}.json")


def m44(R, P):
    M = np.zeros(R.shape[:-2] + (4, 4))
    M[..., :3, :3], M[..., :3, 3], M[..., 3, 3] = R, P, 1
    return M


def cmd_check(a):
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    P1 = REPO / "godot/art/people/body_p1"
    rigj = json.loads((P1 / "rig.json").read_text())
    body = None
    rows = []
    for p in specs(a.clips):
        built = OUT / f"{p.stem}.json"
        if not built.exists():
            print(f"{p.stem}: not built"); continue
        c = MC.read(built)
        r = build_one(p)                       # (in memory: SOMA's side, for the contact windows and fidelity)
        rig = r.rig
        G, P = MC.globals_of(c, rig)
        Gb = m44(G, P)
        rest = m44(rig.R0, rig.head)
        # "A" for clipcheck's feet: SOMA's joints (scaled into B's space) under the B names they drive
        an = [n for n in rig.keyed if "joint" in rig.map.get(n, {})]
        Ga = m44(np.stack([r.Gs[:, r.src.index(rig.map[n]["joint"])] for n in an], 1),
                 np.stack([r.Ps[:, r.src.index(rig.map[n]["joint"])] for n in an], 1))
        d = {"name": p.stem, "fps": c["fps"], "loop": c["loop"], "a_names": an, "b_names": rig.names}
        if body is None:
            body = CC.Body(str(P1 / "body.glb"), rigj, rig.names, rest, True)
        body.cache.clear()
        n = len(Gb)
        frames = list(range(0, n, max(1, n // 30)))
        sp, worst, seam = CC.pops(rig.names, list(rig.parent), Gb, c["bones"], c["loop"])
        ft = CC.feet(d, Ga, Gb)
        ct = CC.contact(body, Gb, frames, set(c["bones"]))
        fid = retarget.fidelity_table(retarget.fidelity(rig, r.src, G, P))
        sl = footlock.slide(P, rig, r.wins, r.belt, c["fps"], r.m)
        rows.append({"clip": p.stem, "frames": n, "pops": len(sp), "worst_step": [round(worst[0], 2), worst[1], worst[2]],
                     "seam_deg": round(seam[0], 4) if c["loop"] else None, "feet": ft, "contact": ct,
                     "slide_mm": [round(x * 1000, 2) for x in sl], "fidelity": fid,
                     "locked_frames": [sum(w[1] for w in ws) for ws in r.wins]})
    for R in rows:
        f, b = R["feet"], R["contact"]
        print(f"\n{R['clip']}: {R['frames']} frames, pops {R['pops']} (worst step {R['worst_step'][0]} deg {R['worst_step'][1]} "
              f"@{R['worst_step'][2]}), seam {R['seam_deg']} deg")
        print(f"  feet: locked frames L {R['locked_frames'][0]} R {R['locked_frames'][1]}, planted slide (core) L {R['slide_mm'][0]} "
              f"R {R['slide_mm'][1]} mm; clipcheck drift SOMA/B mm L {f['l']['A']}/{f['l']['B']} R {f['r']['A']}/{f['r']['B']} (belt {f['belt_mps']} m/s)")
        print("  fidelity deg (mean / max, worst):  " + "  ".join(f"{g} {v['mean']}/{v['max']} {v['worst']}" for g, v in R["fidelity"].items()))
        for s in "lr":
            v = b[s]
            print(f"  arm {s}: inside {v['inside']} verts, deepest {v['depth_mm']} mm @f{v['frame']} {v.get('where', '')}; "
                  f"axilla {v['axilla']}/{v['axilla_mm']} mm; hand gap {v['hand_gap_mm']} mm")
    out = REPO / "tools/body/out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "p4check.json").write_text(json.dumps(rows, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("import")
    i.add_argument("bvh")
    i.add_argument("clip")
    i.add_argument("--loop", action="store_true")
    i.add_argument("--inplace", action="store_true")
    g = sub.add_parser("gen")
    g.add_argument("clips", nargs="*")
    g.add_argument("--encode-only", action="store_true")
    for nm in ("build", "check", "takes"):
        s = sub.add_parser(nm)
        s.add_argument("clips", nargs="*")
        if nm == "takes":
            s.add_argument("--match", default="")
    a = ap.parse_args()
    {"import": cmd_import, "build": cmd_build, "check": cmd_check, "gen": cmd_gen, "takes": cmd_takes}[a.cmd](a)


if __name__ == "__main__":
    main()
