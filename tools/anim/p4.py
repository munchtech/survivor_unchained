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
import datetime
import hashlib
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


PLAYS = ("name", "fps", "frames", "loop", "rot", "pos", "beats", "speed_mps")   # what P4Pack reads: all that plays


def clip_hash(built):
    """The pack gate's fingerprint of a built clip: sha256 (first 16 hex) of what plays (not notes, not `judged`)."""
    obj = {k: built[k] for k in PLAYS[:6] if k in built}
    for k in PLAYS[6:]:
        if built.get(k) is not None:
            obj[k] = built[k]
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def judged_state(spec, built):
    """"judged" (spec flag matches the build), "stale" (flag present, build changed) or "not judged" (no flag)."""
    j = spec.get("judged")
    if not j:
        return "not judged"
    return "judged" if j.get("build") == clip_hash(built) else "stale"


def judged_note(name, spec, built):
    """Writes (or strips) the top-level `judged` in `built` by the state; returns the printed line."""
    st = judged_state(spec, built)
    built.pop("judged", None)
    if st == "judged":
        j = spec["judged"]
        built["judged"] = j
        return f"p4: {name}: judged ({j.get('by')}, {j.get('on')}), build matches"
    if st == "stale":
        return (f"p4: {name}: JUDGED FLAG STALE: the build changed since its judge ({spec['judged'].get('build')} -> "
                f"{clip_hash(built)}); the pack will skip it")
    return f"p4: {name}: not judged (the pack skips it; review packs only)"


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
    """B's held pieces in their bones' spaces, as the game seats them on B: the sword's and the shield's points are
    tools/anim/data/arms_local_b.json's (ArmsDump with Arms.Seat isB: the game's own seat on B's fist pocket, WeaponSockets
    BladeAtRB / BladeDirRB). Only when that file is missing: the old model, A's dump (arms_local.json) with the sword moved
    onto B's pocket by the least turn. And the pockets the fit aims by: the blade's axis and grip, the shield's boss (its
    points' centroid) and face (its thin axis, out of the arm)."""
    if "_pc" in globals():
        return _pc
    from motion import quat as Q
    atB, dirB = np.array(_cs_vec("BladeAtRB")), np.array(_cs_vec("BladeDirRB"))
    dirB = dirB / np.linalg.norm(dirB)
    fb = REPO / "tools/anim/data/arms_local_b.json"
    if fb.exists():
        arms = json.loads(fb.read_text())
        sw = np.array(arms["chevalier_sword@hand_r"]["v"], float)
    else:
        arms = json.loads((REPO / "tools/anim/data/arms_local.json").read_text())
        atA, dirA = np.array(_cs_vec("BladeAtR")), np.array(_cs_vec("BladeDirR"))
        dirA = dirA / np.linalg.norm(dirA)
        sw = np.array(arms["chevalier_sword@hand_r"]["v"], float)
        sw = atB + (sw - atA) @ Q.arc(dirA, dirB).T
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
    if "end" in f:
        # (an action's blend out: the built clip it ends in (fit.end.clip, at fit.end.frame), its locals, its pelvis's
        # world turn and height on B)
        f["end"]["pose"] = end_pose(f["end"]["clip"], f["end"].get("frame", 0))
        if f.get("shield", {}).get("hand") == "end":    # (the shield hand held at the end pose's local all through)
            f["shield"]["hand_rot"] = f["end"]["pose"]["rot"]["hand_l"]
    if "start" in f:                # (an action's blend in from a built clip's frame (fit.start: the mirror of end))
        f["start"]["pose"] = end_pose(f["start"]["clip"], f["start"].get("frame", 0))
    if "clear" in f:
        # (the game's mount on B: the pieces' points in their bones' spaces, a fixed sample)
        pc, bones = pieces(), {"sword": ("hand_r", "r"), "shield": ("lowerarm_l", "l")}
        rng = np.random.default_rng(1)
        f["clear"]["pieces"] = {k: {"bone": bones[k][0], "side": bones[k][1],
                                    "pts": pc[k][rng.choice(len(pc[k]), min(len(pc[k]), 800), replace=False)].tolist()}
                                for k in f["clear"].get("held", spec.get("held", []))}
    return f


def end_pose(clip, frame=0):
    """A built clip's pose at one frame (OUT/<clip>.json): {rot: {bone: [x, y, z, w] local}, pelvis_rot: its world turn,
    pelvis_y: its world height, spot: {pelvis, heel_l, ball_l, heel_r, ball_r: [x, z]} where it stands in the node's
    frame, m (fit.end.spot: an action ends there)}."""
    from motion import fit as FIT
    from motion.rig import Rig
    c = MC.read(OUT / f"{clip}.json")
    G, P = MC.globals_of(c, Rig(RIG))
    pv = Rig(RIG).index["pelvis"]
    return {"rot": {b: q[frame] for b, q in c["rot"].items()}, "pelvis_rot": G[frame, pv].tolist(),
            "pelvis_y": float(P[frame, pv, 1]),
            "spot": {k: [float(v[frame][0]), float(v[frame][2])] for k, v in FIT.ground_points(Rig(RIG), G, P).items()}}


def action_of(spec):
    """An action's post (Marionette motion/action.py) with its named moments resolved to clip seconds: post.action
    {seconds, retime, derotate_tps, travel: [a, b], planted: {foot_l|foot_r: [[a, b, "ball"|"ankle"], ...]}}, where a
    and b are seconds, "start", "end" or a beats event."""
    if spec.get("kind") != "action":
        return None, None
    beats = spec.get("beats", {})
    act = json.loads(json.dumps(spec.get("post", {}).get("action", {})))
    T = float(act.setdefault("seconds", spec.get("seconds", 1.0)))
    ev = beats.get("events", {})

    def sec(x):
        return 0.0 if x == "start" else T if x == "end" else float(ev[x]) if isinstance(x, str) else float(x)
    act["planted"] = {k: [[sec(w[0]), sec(w[1])] + list(w[2:]) for w in ws] for k, ws in act.get("planted", {}).items()}
    return act, beats


def run_post(src, spec, name):
    """The core on one source with the spec's post steps (loop, in place, whole cycles, the gait lock, an action's
    post) and its fit."""
    po = spec.get("post", {})
    act, beats = action_of(spec)
    cyc = po.get("cycle_s")
    return MC.run(src, RIG, loop=po.get("loop", spec.get("loop", False)), inplace=po.get("inplace", spec.get("inplace", False)),
                  name=name, gait=po.get("gait", False), duty=po.get("duty"),
                  cycle=(int(round(cyc[0] * KFPS)), int(round(cyc[1] * KFPS))) if cyc else None,
                  crop=tuple(po["crop"]) if po.get("crop") else None, fit=fit_of(spec),
                  body=body_field() if "clear" in spec.get("fit", {}) else None, action=act, beats=beats)


def build_one(p):
    spec = json.loads(p.read_text())
    return run_post(P4 / spec["source"], spec, p.stem)


def measure(r, spec):
    """The bible's numbers on a core result (B's side), per the spec's kind."""
    fps = r.src.fps
    if spec.get("kind") == "action":
        m = measures.action(r.P, r.G, r.rig, fps, spec.get("bands", {}), r.clip.get("beats", {}),
                            extra=action_held(r, spec), head_top=head_top())
        m.update(steps(r))
        return m
    if spec.get("kind") == "gait":
        m = measures.gait(r.P, r.rig, fps, r.clip.get("speed_mps"), loop=r.clip["loop"])
        m.update(held(r, spec))
        m.update(steps(r))
        return m
    m = measures.idle(r.P, r.rig, fps, loop=r.clip["loop"])
    m.update(hand_targets(r, spec))
    m.update(held(r, spec))
    m.update(steps(r))
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
        # (the face tipped down = the top edge leaning out from her, deg)
        out["shield_tilt_deg"] = round(float(np.degrees(np.arctan2(-f[:, 1], np.hypot(f[:, 0], f[:, 2]))).mean()), 1)
    return out


def action_held(r, spec):
    """Per-frame series of the held pieces for an action's bands (measures.at): blade_below_deg (the blade's angle
    below the horizontal), tip_cm (its tip's height), tip_ahead_cm (the tip ahead of the pelvis along her heading),
    shield_top_cm (its top edge's height), shield_face_deg (its face's heading off hers, + open), boss_sternum_cm
    (the boss from the chest, spine_05's head)."""
    out = {}
    rig, G, P = r.rig, r.G, r.P
    pv = rig.index["pelvis"]
    Rp = G[:, pv] @ rig.R0[pv].T
    fwd = Rp @ np.array([0, 0, 1.0])
    hd = np.stack([fwd[:, 0], np.zeros(len(fwd)), fwd[:, 2]], 1)
    hd /= np.linalg.norm(hd, axis=1, keepdims=True) + 1e-12
    pc = pieces()
    if "sword" in spec.get("held", []):
        h = rig.index["hand_r"]
        d = np.einsum("fij,j->fi", G[:, h], pc["blade"]["dir"])
        out["blade_below_deg"] = np.degrees(np.arctan2(-d[:, 1], np.hypot(d[:, 0], d[:, 2])))
        grip = P[:, h] + np.einsum("fij,j->fi", G[:, h], pc["blade"]["at"])
        tip = grip + d * pc["blade"]["tip"]
        out["tip_cm"] = 100 * tip[:, 1]
        out["tip_ahead_cm"] = 100 * np.einsum("fi,fi->f", tip - P[:, pv], hd)
        out["grip_cm"] = 100 * grip[:, 1]                                       # (the grip's height)
        out["grip_ahead_cm"] = 100 * np.einsum("fi,fi->f", grip - P[:, pv], hd)
    # (her look: the face's forward (Head's rest +Z) below the horizontal, deg, + down)
    hz = np.einsum("fij,j->fi", G[:, rig.index["Head"]] @ rig.R0[rig.index["Head"]].T, [0, 0, 1.0])
    out["head_down_deg"] = np.degrees(np.arctan2(-hz[:, 1], np.hypot(hz[:, 0], hz[:, 2])))
    hold = r.clip.get("beats", {}).get("hold")
    if hold:                           # (the settle: the pelvis below its hold height, % of the hold's drop from frame 0)
        y = P[:, pv, 1]
        yh = y[int(round(hold[0] * r.src.fps))]
        out["settle_pct"] = 100 * (yh - y) / max(y[0] - yh, 1e-6)
    if spec.get("fit", {}).get("end"):  # (each frame's largest keyed-bone turn off the clip it ends in, deg; its pelvis
        e = spec["fit"]["end"]          # by its world turn)
        tg = end_pose(e["clip"], e.get("frame", 0))
        from motion import quat as Q
        dd = []
        for b, q in tg["rot"].items():
            if b in ("root", "pelvis") or b not in rig.index:
                continue
            j = rig.index[b]
            L = np.swapaxes(G[:, rig.parent[j]], -1, -2) @ G[:, j]
            dd.append(np.degrees(Q.angle(L, Q.to_mat(np.asarray(q, float)[None]))))
        dd.append(np.degrees(Q.angle(G[:, pv], np.asarray(tg["pelvis_rot"])[None])))
        out["end_deg"] = np.max(dd, 0)
    if "shield" in spec.get("held", []):
        la = rig.index["lowerarm_l"]
        boss = P[:, la] + np.einsum("fij,j->fi", G[:, la], pc["shieldp"]["at"])
        pts = np.einsum("fij,kj->fki", G[:, la], pc["shield"]) + P[:, la][:, None]
        out["shield_top_cm"] = 100 * pts[:, :, 1].max(1)
        f = np.einsum("fji,fj->fi", Rp, np.einsum("fij,j->fi", G[:, la], pc["shieldp"]["face"]))
        out["shield_face_deg"] = np.degrees(np.arctan2(f[:, 0], f[:, 2]))
        out["boss_sternum_cm"] = 100 * np.linalg.norm(boss - P[:, rig.index["spine_05"]], axis=1)
        out["boss_cm"] = 100 * boss[:, 1]                                       # (the shield's centre height)
        out["boss_ahead_cm"] = 100 * np.einsum("fi,fi->f", boss - P[:, pv], hd)  # (ahead of the pelvis, her heading)
        # (a block's cover: the shield's top edge over her eyes (EYE_BELOW_TOP under the head's top, along the Head's
        # up), and its face ahead of the head's top along her heading (+ = the head tucked behind it))
        hj = rig.index["Head"]
        top = P[:, hj] + np.einsum("fij,j->fi", G[:, hj] @ rig.R0[hj].T, [0, 1.0, 0]) * head_top()
        eye = top - np.einsum("fij,j->fi", G[:, hj] @ rig.R0[hj].T, [0, 1.0, 0]) * EYE_BELOW_TOP
        out["shield_over_eyes_cm"] = out["shield_top_cm"] - 100 * eye[:, 1]
        out["head_behind_cm"] = 100 * np.einsum("fi,fi->f", boss - top, hd)
    if "sword" in spec.get("held", []) or "shield" in spec.get("held", []):
        for sd in "lr":                # (the hands ahead of the pelvis along her heading: a shove's reach)
            out[f"hand_{sd}_ahead_cm"] = 100 * np.einsum("fi,fi->f", P[:, rig.index[f"hand_{sd}"]] - P[:, pv], hd)
    return out


EYE_BELOW_TOP = 0.11     # m: an adult's eyes under the top of the head (vertex to pupil, ~11-12 cm)


def head_top():
    """The top of her head over the Head bone's head at rest (m): the skin's highest point, B's rest."""
    if "_ht" not in globals():
        body_field()
        B = globals()["_bfB"]
        from motion.rig import Rig
        rig = Rig(RIG)
        V = (np.c_[B.p.P0, np.ones(len(B.p.P0))] @ np.linalg.inv(B.X).T)[:, :3]
        globals()["_ht"] = float(V[:, 1].max() - rig.head[rig.index["Head"]][1])
    return _ht


def hand_targets(r, spec):
    """The keyed hands' distance from their targets on B (cm; mean and worst over the clip): each target rides the
    pelvis at its rest offset (gen.keys.hands, B meters from the pelvis head, her left/up/forward)."""
    K = spec.get("gen", {}).get("keys")
    if not K:
        return {}
    rig, out = r.rig, {}
    pv = rig.index["pelvis"]
    Rrel = r.G[:, pv] @ rig.R0[pv].T
    for h, off in K.get("hands", {}).items():
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
    # (heading_tps: a heading track at that rate, turns a second, + to her left: a spin's turn, Kimodo's heading)
    # (orbit [x, z]: the root circles a pivot at the origin, at that offset when the heading is 0 and turning with it:
    # a spin over a planted foot)
    tps, h0, orb = r.pop("heading_tps", None), r.pop("heading_deg0", 0.0), r.pop("orbit", None)
    out = {"xz": paths.make(r, g["seconds"], KFPS).round(5).tolist(), "every": r.get("every", 1)}
    if tps:
        h = np.radians(h0) + 2 * np.pi * tps * np.arange(len(out["xz"])) / KFPS
        out["heading"] = h.round(6).tolist()
        if orb:
            c, s_ = np.cos(h), np.sin(h)
            out["xz"] = (np.array(out["xz"]) + np.stack([c * orb[0] + s_ * orb[1], -s_ * orb[0] + c * orb[1]], 1)
                         ).round(5).tolist()
    return out


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

        def pz(d):
            d = dict(d)
            if isinstance(d.get("prompt"), int):
                d["prompt"] = g["prompts"][d["prompt"]]
            d.setdefault("seconds", g["seconds"])
            d.setdefault("takes", g["takes"])
            if d.get("keys", {}).get("poses"):          # (a source that is itself a keyed take)
                d["keys"] = dict(d["keys"], poses=[dict(q, src=pz(q["src"])) for q in d["keys"]["poses"]])
            return d
        if g.get("keys") and g["keys"].get("poses") and not g["keys"].get("src"):
            # (keyed beats: FullBody key poses from native takes {src: {prompt: index | text, seed, seconds, takes},
            # pick, frame (the source take's), at (this job's frame), xz, yaw, lift} (kimodo_run.pose_keys); Kimodo
            # makes only the in-betweens, per keys.prompts x keys.seeds as __q<tag><i>s<seed>)
            K = g["keys"]
            poses = [dict(q, src=pz(q["src"])) for q in K["poses"]]
            for i in K.get("prompts", range(len(g["prompts"]))):
                for sd in K.get("seeds", [g["seeds"][i % len(g["seeds"])]]):
                    j = job(i, 1.0, f"{p.stem}__q{K.get('tag', '')}{i}s{sd}")
                    j.update(seed=sd, keys={"poses": poses})
                    if K.get("seconds"):
                        j["seconds"] = K["seconds"]
                    if K.get("takes"):
                        j["takes"] = K["takes"]
                    jobs.append(j)
        elif g.get("keys"):
            K = g["keys"]
            k = soma_k(sp)
            src = job(K["src"]["prompt"], K["src"].get("scale", 1.0), "src")
            src = {kk: src[kk] for kk in ("prompt", "seconds", "seed", "takes", "root2d") if kk in src}
            src["pick"] = K["src"].get("pick", 0)
            # (a source made by its own seed, length and keys: a keyed take, the hands then keyed on it)
            src.update({kk: K["src"][kk] for kk in ("seed", "seconds", "takes") if kk in K["src"]})
            if K["src"].get("keys"):
                src["keys"] = pz({"prompt": "", "keys": K["src"]["keys"]})["keys"]
            # (aim: what is sent = the target minus the take's measured mean miss on B, in the pelvis frame: the
            # retarget's arm calibration lands Kimodo's wrist a few cm from where it put SOMA's)
            aim = K.get("aim", {})
            hands = {h: [(x + a) / k for x, a in zip(off, aim.get(h, [0, 0, 0]))] for h, off in K.get("hands", {}).items()}
            # (an action's keys: end effectors at given take frames {joint: {frame: [l, u, f] B m from the pelvis}},
            # and FullBody key poses at given take frames (the take's pose there, after those edits))
            tgts = {jn: {f: [(x + a) / k for x, a in zip(off, aim.get(jn, [0, 0, 0]))] for f, off in d.items()}
                    for jn, d in K.get("targets", {}).items()}
            for i in K.get("prompts", [K["src"]["prompt"]]):
                for sc in K.get("scales", [K["src"].get("scale", 1.0)]):
                    for sd in K.get("seeds", [None]):     # (seeds: more takes of the keyed job, __k<tag><i>s<pct>r<seed>)
                        j = job(i, sc, f"{p.stem}__k{K.get('tag', '')}{i}s{round(sc * 100)}" + (f"r{sd}" if sd else ""))
                        j["keys"] = {"src": src, "hands": hands, "targets": tgts, "fullbody": K.get("fullbody", []),
                                     "start": K.get("start", 15), "every": K.get("every", 30)}
                        if sd:
                            j["seed"] = sd
                        for kk in ("seconds", "takes"):
                            if K.get(kk):
                                j[kk] = K[kk]
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
        sp = json.loads(p.read_text())
        line = judged_note(p.stem, sp, r.clip)
        MC.write(r.clip, OUT / f"{p.stem}.json")
        print(line)
        if sp.get("bands"):
            m = measure(r, sp)
            ok = measures.passes(m, sp["bands"])
            print(f"  {p.stem}: " + ", ".join(f"{k} {m.get(k)}{'' if ok[k] else ' MISS'}" for k in sp["bands"]))
            print(f"  {p.stem} more: " + ", ".join(f"{k} {v}" for k, v in m.items() if k not in sp["bands"] and
                                                     k.startswith(("step_", "wrist_", "blade_", "shield_", "boss_"))))
        for L in r.fitlog or []:
            print(f"  fit {L['layer']}: " + ", ".join(f"{k} {v}" for k, v in L.items() if k != "layer"))
        if r.clip.get("beats"):
            print(f"  {p.stem} beats: {json.dumps(r.clip['beats'])}")
        for nt in r.prep.notes:
            print(f"  note: {nt}")
        print(f"{p.stem}: {r.clip['frames']} frames, source crop {r.prep.crop}, yaw {r.prep.yaw_deg:.1f} deg, "
              f"windows L {len(r.wins[0])} R {len(r.wins[1])} -> {OUT.relative_to(REPO).as_posix()}/{p.stem}.json")


def clearance(G, P, held, target_mm=10.0, n=None, pts=800):
    """Each held piece against her skin (body_field: the winding number's sign) on every frame of a clip: the closest
    gap (mm, + outside), the deepest in (mm, 0 if never), the frames inside and the frames under target_mm."""
    from motion import fit as FIT
    bones = {"sword": "hand_r", "shield": "lowerarm_l"}
    pc, rng = pieces(), np.random.default_rng(1)
    sel = {k: pc[k][rng.choice(len(pc[k]), min(len(pc[k]), pts), replace=False)] for k in held}
    from motion.rig import Rig
    rig = Rig(RIG)
    out = {k: {"gap_mm": 1e9, "in_mm": 0.0, "inside": [], "under": []} for k in held}
    bf = body_field()
    for f in range(n or len(G)):
        field = bf(G[f], P[f])
        for k in held:
            j = rig.index[bones[k]]
            sd = float(field(sel[k] @ G[f, j].T + P[f, j])[0].min()) * 1000
            o = out[k]
            o["gap_mm"] = min(o["gap_mm"], sd)
            if sd < 0:
                o["in_mm"] = max(o["in_mm"], -sd)
                o["inside"].append(f)
            if sd < target_mm:
                o["under"].append(f)
    return {k: {"gap_mm": round(v["gap_mm"], 1), "in_mm": round(v["in_mm"], 1), "inside": FIT._ranges(v["inside"]),
                "under": FIT._ranges(v["under"])} for k, v in out.items()}


GROUND_CM = 2.5          # a foot is on the floor where its ball AND its heel point are within this of their floor heights
SKATE_CM = 1.0           # the fail line: a foot's grounded travel outside its planted windows, cm a clip (see skate())


def _foot_pts(rig, G, P, s, tps=None, fps=30):
    """One foot's ball and heel ground point (F,3) (a de-rotated spin's in the WORLD: the game's turn put back),
    its sole's tilt from flat (deg) and its leg's reach (the hip-ankle distance over the leg's length)."""
    from motion.footlock import heel_local
    th, ca, fo, ba = (rig.index[f"{b}_{s}"] for b in ("thigh", "calf", "foot", "ball"))
    ball, heel = P[:, ba].copy(), P[:, fo] + np.einsum("fij,j->fi", G[:, fo], heel_local(rig, fo))
    if tps:
        w = 2 * np.pi * tps * np.arange(len(P)) / fps
        c, sn = np.cos(w), np.sin(w)
        ball, heel = (np.stack([c * q[:, 0] + sn * q[:, 2], q[:, 1], -sn * q[:, 0] + c * q[:, 2]], 1) for q in (ball, heel))
    tilt = np.degrees(np.arccos(np.clip((G[:, fo] @ rig.R0[fo].T)[:, 1, 1], -1, 1)))
    reach = np.linalg.norm(P[:, fo] - P[:, th], axis=1) / (np.linalg.norm(P[:, ca] - P[:, th], axis=1) +
                                                             np.linalg.norm(P[:, fo] - P[:, ca], axis=1))
    return ball, heel, tilt, reach


def skate(r, spec, G=None, P=None):
    """Skating, per foot: its grounded travel OUTSIDE its planted windows, cm. On each frame step where the foot is on
    the floor at both ends (ball and heel point within GROUND_CM of their floor heights: the ball's rest height, 0)
    the smaller of the ball's and the heel point's horizontal step is summed (the belt out for a gait, in the world
    for a de-rotated spin), so a pivot on the heel or the ball is free and a drag is counted. Over SKATE_CM is a MISS."""
    G, P = (r.G, r.P) if G is None else (G, P)
    rig, fps, n, m = r.rig, r.src.fps, len(P), r.m
    tps = (spec.get("post", {}).get("action") or {}).get("derotate_tps")
    out = {}
    for si, s in enumerate("lr"):
        ball, heel, _, _ = _foot_pts(rig, G, P, s, tps, fps)
        hb = rig.head[rig.index[f"ball_{s}"]][1]
        on = (np.abs(ball[:, 1] - hb) < GROUND_CM / 100) & (np.abs(heel[:, 1]) < GROUND_CM / 100)
        pl = {(ws + k) % m for ws, ln, _ in _contacts(r, si) for k in range(ln)}
        pl |= set((getattr(r, "rides", None) or [[], []])[si])   # (a push-off foot riding the travel strip on the floor
        #                                                          (plant ride): still in the world, the node carries her)
        tot, worst, cnt = 0.0, (0.0, 0), 0
        for f in range(m if r.clip["loop"] else n - 1):
            g = (f + 1) % m if r.clip["loop"] else f + 1
            inw = f in pl and g in pl
            # (a de-rotated spin (solver S1): a window pinned in the clip is not still in the WORLD unless it is on the
            # turn's axis or turned back, so its planted windows are counted too, by the ball's travel in the world)
            if (inw and not tps) or not (inw or (on[f] and on[g])):
                continue
            d = min(np.linalg.norm((q[g] - q[f] - r.belt / fps)[[0, 2]]) for q in ((ball,) if inw else (ball, heel))) * 100
            tot, cnt = tot + d, cnt + 1
            if d > worst[0]:
                worst = (float(d), g)
        out[s] = {"cm": round(tot, 2), "frames": cnt, "worst_cm": round(worst[0], 2), "at": worst[1]}
        if tps:                              # (a spin's floor: the ball over its rest height and the sole's lowest point)
            ba = rig.index[f"ball_{s}"]
            toe = P[:, ba] + np.einsum("fij,j->fi", G[:, ba], rig.R0[ba].T @ np.array([0.0, -hb, 0.11]))
            low = np.minimum(np.minimum(heel[:m, 1], ball[:m, 1] - hb), toe[:m, 1])
            out[s].update(ball_cm=[round(float(x) * 100, 2) for x in (ball[:m, 1].min() - hb, ball[:m, 1].max() - hb)],
                          low_cm=round(float(low.min()) * 100, 2), low_at=int(np.argmin(low)))
    return out


def _contacts(r, si):
    """One foot's planted windows: the lock's, and a spin's world-still steps (fit.axis.steps)."""
    return list(r.wins[si]) + list((getattr(r, "steps", None) or [[], []])[si])


def floors(r, G=None, P=None):
    """Each planted window's floor numbers: the ankle's and the ball's height over rest (cm, the largest either way),
    the sole's tilt from flat (deg, max) and the leg's reach (max)."""
    G, P = (r.G, r.P) if G is None else (G, P)
    rig, out = r.rig, {}
    for si, s in enumerate("lr"):
        ball, _, tilt, reach = _foot_pts(rig, G, P, s)
        fo, ba = rig.index[f"foot_{s}"], rig.index[f"ball_{s}"]
        out[s] = []
        for ws, ln, _ in _contacts(r, si):
            fr = [(ws + k) % r.m for k in range(ln)]
            big = lambda v: round(float(v[np.argmax(np.abs(v))]) * 100, 2)  # noqa: E731
            out[s].append({"frames": [int(fr[0]), int(fr[-1])], "ankle_cm": big(P[fr, fo, 1] - rig.head[fo][1]),
                           "ball_cm": big(ball[fr, 1] - rig.head[ba][1]), "tilt_deg": round(float(tilt[fr].max()), 1),
                           "reach": round(float(reach[fr].max()), 3)})
    return out


def spot_off(rig, G, P, sj):
    """Where an action with an `end` clip stands against that clip's place (the node's frame, cm): its first frame's
    heels and pelvis, and the largest miss of its last frame's pelvis, heels and balls (over 0.5 = a slide when the
    game crossfades to the idle on her node). Explicit fit.end.spot points are the targets where given."""
    from motion import fit as FIT
    e = (sj.get("fit") or {}).get("end") or {}
    if not e.get("clip") or not (OUT / f"{e['clip']}.json").exists():
        return None
    tg = end_pose(e["clip"], e.get("frame", 0))["spot"]
    if isinstance(e.get("spot"), dict):
        tg.update({k: v for k, v in e["spot"].items() if k in FIT.SPOTS})
    pts = FIT.ground_points(rig, G, P)
    off = lambda k, f: round(100 * float(np.hypot(pts[k][f][0] - tg[k][0], pts[k][f][2] - tg[k][1])), 2)  # noqa: E731
    return {"start": [off(k, 0) for k in ("heel_l", "heel_r", "pelvis")], "end": max(off(k, -1) for k in tg)}


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
        print(f"{p.stem}: " + judged_state(json.loads(p.read_text()), c)+ " (pack gate)")
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
        sj = json.loads(p.read_text())
        cl = clearance(G, P, sj.get("held", []), n=n - 1 if c["loop"] else n) if sj.get("held") else {}
        rows.append({"clip": p.stem, "frames": n, "pops": len(sp), "clearance": cl, "worst_step": [round(worst[0], 2), worst[1], worst[2]],
                     "seam_deg": round(seam[0], 4) if c["loop"] else None, "feet": ft, "contact": ct,
                     "slide_mm": [round(x * 1000, 2) for x in sl], "fidelity": fid,
                     "locked_frames": [sum(w[1] for w in ws) for ws in r.wins],
                     "skate": skate(r, sj, G, P), "skate_line_cm": SKATE_CM, "floors": floors(r, G, P),
                     "spot": spot_off(rig, G, P, sj)})
    for R in rows:
        f, b = R["feet"], R["contact"]
        print(f"\n{R['clip']}: {R['frames']} frames, pops {R['pops']} (worst step {R['worst_step'][0]} deg {R['worst_step'][1]} "
              f"@{R['worst_step'][2]}), seam {R['seam_deg']} deg")
        print(f"  feet: locked frames L {R['locked_frames'][0]} R {R['locked_frames'][1]}, planted slide (core) L {R['slide_mm'][0]} "
              f"R {R['slide_mm'][1]} mm; clipcheck drift SOMA/B mm L {f['l']['A']}/{f['l']['B']} R {f['r']['A']}/{f['r']['B']} (belt {f['belt_mps']} m/s)")
        print("  skate (grounded travel outside the planted windows, cm; line %s): " % SKATE_CM + "  ".join(
            f"{s.upper()} {v['cm']}{' MISS' if v['cm'] > SKATE_CM else ''} ({v['frames']} steps, worst {v['worst_cm']} @{v['at']})"
            for s, v in R["skate"].items()))
        if any("low_cm" in v for v in R["skate"].values()):
            print("  floor (a spin; skate counts its planted windows in the world): " + "  ".join(
                f"{s.upper()} ball {v['ball_cm'][0]:+}..{v['ball_cm'][1]:+} cm over rest, lowest sole point {v['low_cm']:+} cm @{v['low_at']}"
                for s, v in R["skate"].items()))
        if R["spot"]:
            so = R["spot"]
            print(f"  spot: start off idle L {so['start'][0]:.1f} R {so['start'][1]:.1f} pelvis {so['start'][2]:.1f} cm; "
                  f"end off idle max {so['end']:.1f} cm{' MISS' if so['end'] > 0.5 else ''}")
        for s, ws in R["floors"].items():
            for w in ws:
                print(f"  planted {s} f{w['frames'][0]}-{w['frames'][1]}: ankle {w['ankle_cm']:+} cm, ball {w['ball_cm']:+} cm over rest, "
                      f"sole {w['tilt_deg']} deg from flat, reach {w['reach']}")
        print("  fidelity deg (mean / max, worst):  " + "  ".join(f"{g} {v['mean']}/{v['max']} {v['worst']}" for g, v in R["fidelity"].items()))
        for k, v in R["clearance"].items():
            print(f"  held {k}: closest gap {v['gap_mm']} mm, deepest in {v['in_mm']} mm (frames in: {v['inside'] or '-'}; "
                  f"under 10 mm: {v['under'] or '-'})")
        for s in "lr":
            v = b[s]
            print(f"  arm {s}: inside {v['inside']} verts, deepest {v['depth_mm']} mm @f{v['frame']} {v.get('where', '')}; "
                  f"axilla {v['axilla']}/{v['axilla_mm']} mm; hand gap {v['hand_gap_mm']} mm")
    out = REPO / "tools/body/out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "p4check.json").write_text(json.dumps(rows, indent=1))


def cmd_judged(a):
    ps = specs(a.clips)
    if a.list or not a.clips:
        for p in ps:
            b = OUT / f"{p.stem}.json"
            st = "not built" if not b.exists() else {"judged": "judged", "not judged": "NOT JUDGED", "stale": "STALE"}[
                judged_state(json.loads(p.read_text()), MC.read(b))]
            print(f"{p.stem}: {st}")
        return
    for p in ps:
        b = OUT / f"{p.stem}.json"
        if not b.exists():
            sys.exit(f"{p.stem}: not built (build it first)")
        sp, built = json.loads(p.read_text()), MC.read(b)
        sp.pop("judged", None)
        built.pop("judged", None)
        if a.clear:
            print(f"{p.stem}: judged flag cleared")
        else:
            if not a.by:
                sys.exit("--by is required")
            sp["judged"] = {"by": a.by, "on": a.on or datetime.date.today().isoformat(), "verdict": a.verdict, "build": clip_hash(built)}
            built["judged"] = sp["judged"]
            print(f"{p.stem}: judged, build {sp['judged']['build']}")
        p.write_text(json.dumps(sp, indent=1) + "\n")
        MC.write(built, b)


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
    j = sub.add_parser("judged")
    j.add_argument("clips", nargs="*")
    j.add_argument("--by", default="")
    j.add_argument("--verdict", default="PASS")
    j.add_argument("--on", default="")
    j.add_argument("--list", action="store_true")
    j.add_argument("--clear", action="store_true")
    a = ap.parse_args()
    {"judged": cmd_judged, "import": cmd_import, "build": cmd_build, "check": cmd_check, "gen": cmd_gen, "takes": cmd_takes}[a.cmd](a)



EDGE = 0.013              # m: a skin vertex's patch for the field (her edges on B: median 6.8 mm, p95 12.7)


def skin_gap(d, pr, inside):
    """The field's signed distance (m, + outside) from the nearest skin vertex's distance d, the point's offset along
    that vertex's normal pr, and the winding's inside: along the normal where that agrees with the sign, but only
    within the vertex's own patch: past EDGE sideways the tangent plane is not her skin, the sideways rest counts (a
    point 40-57 cm off her side in a vertex's tangent plane read 0-8 mm: the leap's raised sword and out-held shield,
    and the clear layer moved arms that touched nothing; solver F3)."""
    t = np.sqrt(np.maximum(d * d - pr * pr, 0.0))
    mag = np.where((pr < 0) == inside, np.hypot(pr, np.maximum(t - EDGE, 0.0)), d)
    return np.where(inside, -mag, mag)


def body_field():
    """Her skin as the fit's `clear` layer and p4_blend read it: body(G, P) -> a field: world points -> (signed
    distance m, + outside; outward normals), B posed by clipcheck's poser (the glb's skin + B's laws).

    The sign is the generalized winding number of her whole closed skin (body + head pieces: Marionette
    motion/winding.py), so it holds deep inside her and far outside (the old nearest-vertex sign read any point over
    8 cm from her skin as outside: idle_warden's shield rim sat in her thigh at that ceiling and read clear). A point
    nearer her arms' skin than the rest is never inside (a held piece's strap in its own forearm, a blade against the
    other arm: the arms are clipcheck's matter). The distance: to the nearest skin vertex but the arms' (torso, legs,
    neck, head), along its normal where that agrees with the sign; the normal is that vertex's."""
    if "_bf" in globals():
        return _bf
    sys.path.insert(0, str(REPO / "tools/body"))
    import clipcheck as CC
    from scipy.spatial import cKDTree
    from motion.rig import Rig
    from motion.winding import Winding
    rig = Rig(RIG)
    P1 = REPO / "godot/art/people/body_p1"
    B = CC.Body(str(P1 / "body.glb"), json.loads((P1 / "rig.json").read_text()), rig.names, m44(rig.R0, rig.head), True)
    Xi = np.linalg.inv(B.X)
    keyed = set(rig.keyed)
    arm = B.arm["l"] | B.arm["r"] | B.hand["l"] | B.hand["r"]
    skin = np.nonzero(~arm)[0]
    armi = np.nonzero(arm)[0]
    # (a point well inside the rest mesh for the winding's orientation: the pelvis head, in glb space)
    pv = rig.index["pelvis"]
    W = Winding(B.p.T, B.p.P0, inside=(B.X @ np.r_[rig.head[pv], 1.0])[:3])

    def body(G, P):
        B.cache.clear()
        V, _, N, _ = B.pose(m44(G, P), keyed, 0)
        ts, ta = cKDTree(V[skin]), cKDTree(V[armi])

        def field(pts):
            Pg = (np.c_[pts, np.ones(len(pts))] @ B.X.T)[:, :3]
            d, i = ts.query(Pg)
            q = skin[i]
            da, _ = ta.query(Pg)
            inside = (W(V, Pg) > 0.5) & (da >= d)
            pr = np.einsum("ij,ij->i", Pg - V[q], N[q])
            s = skin_gap(d, pr, inside)
            nrm = N[q] @ Xi[:3, :3].T
            nrm = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
            return s, nrm
        return field
    globals()["_bf"], globals()["_bfB"] = body, B
    return body


class _Pose:
    """A built result as the fit's measures read it (fit.wrist_of)."""
    def __init__(self, r):
        self.rig, self.G, self.P = r.rig, r.G, r.P

    def j(self, n):
        return self.rig.index[n]


def steps(r):
    """The worst one-frame local turn (deg) of each foot and knee (calf) over the loop, and the wrists' worst bends."""
    from motion import fit as FIT
    from motion import quat as Q
    rig, G = r.rig, r.G
    out = {}
    for b in ("foot_l", "foot_r", "calf_l", "calf_r"):
        j = rig.index[b]
        L = np.swapaxes(G[:, rig.parent[j]], -1, -2) @ G[:, j]
        a = np.degrees(np.arccos(np.clip((np.trace(np.swapaxes(L[:-1], -1, -2) @ L[1:], axis1=1, axis2=2) - 1) / 2, -1, 1)))
        out[f"step_{b}_deg"] = round(float(a.max()), 1)
    F = _Pose(r)
    for s in "lr":
        fl, de = FIT.wrist_of(F, s)
        out[f"wrist_{s}_flex_deg"] = round(float(np.abs(fl[:r.m]).max()), 1)
        out[f"wrist_{s}_dev_deg"] = round(float(np.abs(de[:r.m]).max()), 1)
        # (the hand's roll on the forearm, from B's rest: a candy-wrapper wrist the flex/dev cap cannot see)
        la, ha = rig.index[f"lowerarm_{s}"], rig.index[f"hand_{s}"]
        D = np.swapaxes(rig.Lr0[ha], -1, -2)[None] @ (np.swapaxes(G[:, la], -1, -2) @ G[:, ha])
        q = Q.from_mat(D)
        tw = np.degrees((2 * np.arctan2(q[:, 1], q[:, 3]) + np.pi) % (2 * np.pi) - np.pi)
        out[f"wrist_{s}_twist_deg"] = round(float(np.abs(tw[:r.m]).max()), 1)
    return out

if __name__ == "__main__":
    main()
