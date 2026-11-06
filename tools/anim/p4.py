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
    allp = sorted((P4 / "specs").glob("*.json"))
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


def run_post(src, spec, name):
    """The core on one source with the spec's post steps (loop, in place, whole cycles, the gait lock)."""
    po = spec.get("post", {})
    cyc = po.get("cycle_s")
    return MC.run(src, RIG, loop=po.get("loop", spec.get("loop", False)), inplace=po.get("inplace", spec.get("inplace", False)),
                  name=name, gait=po.get("gait", False), duty=po.get("duty"),
                  cycle=(int(round(cyc[0] * KFPS)), int(round(cyc[1] * KFPS))) if cyc else None,
                  crop=tuple(po["crop"]) if po.get("crop") else None)


def build_one(p):
    spec = json.loads(p.read_text())
    return run_post(P4 / spec["source"], spec, p.stem)


def measure(r, spec):
    """The bible's numbers on a core result (B's side), per the spec's kind."""
    fps = r.src.fps
    if spec.get("kind") == "gait":
        return measures.gait(r.P, r.rig, fps, r.clip.get("speed_mps"), loop=r.clip["loop"])
    return measures.idle(r.P, r.rig, fps, loop=r.clip["loop"])


def gen_specs(names):
    return [(p, json.loads(p.read_text())) for p in specs(names) if json.loads(p.read_text()).get("gen")]


def jobs_of(names):
    jobs = []
    for p, sp in gen_specs(names):
        g = sp["gen"]
        for i, pr in enumerate(g["prompts"]):
            j = {"name": f"{p.stem}__p{i}", "prompt": pr, "seconds": g["seconds"], "seed": g["seeds"][i % len(g["seeds"])],
                 "takes": g["takes"]}
            if not g.get("root2d"):
                jobs.append(j)
                continue
            # root2d_scales: the path's amplitude scaled per variant (Kimodo's hips swing past its smooth root)
            for v, sc in enumerate(g.get("root2d_scales", [1.0])):
                r = dict(g["root2d"])
                for k in ("travel", "overshoot"):
                    if k in r:
                        r[k] = r[k] * sc
                jv = dict(j, name=j["name"] + (f"v{v}" if "root2d_scales" in g else ""))
                jv["root2d"] = {"xz": paths.make(r, g["seconds"], KFPS).round(5).tolist(), "every": r.get("every", 1)}
                jobs.append(jv)
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
        log.sort(key=lambda x: x["score"])
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
    a = ap.parse_args()
    {"import": cmd_import, "build": cmd_build, "check": cmd_check, "gen": cmd_gen, "takes": cmd_takes}[a.cmd](a)


if __name__ == "__main__":
    main()
