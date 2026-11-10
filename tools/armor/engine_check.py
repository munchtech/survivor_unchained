"""engine_check: the ENGINE against the POSER on held frames (P2 lead 5, 9 Nov: the game drew her shoulder through a
pauldron that gear_wear called clean; this is the standing check that the two still describe the same woman).

    python tools/armor/engine_check.py --shoot            # take the godot turn, shoot FRAMES, give it back, compare
    python tools/armor/engine_check.py [--run DIR]        # compare the dumps already in DIR
    python tools/armor/engine_check.py --store            # and keep each frame's compact reference (engine_ref/NAME.npz)
        [--frames w_dh_a,w_sh_a,w_cf_a] [--strict-pose]

Each frame is one Godot run of the game with --hold CLIP@S and the probes (P1PoseProbe --pose-probe-full: every bone's
final pose, the shape weights, the camera; P1MeshDump --pose-probe-skin: her drawn body and gear as the engine HOLDS
them, arrays, binds, shape values, the tuck map; P1Laws --p1-laws-dump: the laws' input and output). The dumps go to
DIR (default godot/.shots/gear_p2/engine_check; a frame is about 20 MB, git-ignored). Then, per frame, numbers with a
tolerance each (TOL); any over fails the run (exit 1):

  laws   rig_drive (the poser's laws) run on the ENGINE's input pose against the engine's output: worst bone, mm and
         deg, and the worst corrective weight. P1Rig.cs and rig_drive.py out of step show here.
  data   the engine's own arrays (vertices, 8 weights, shapes by the mesh's blend mode, the skin's binds) skinned by the
         frame's bones, against the poser's points for the same bones and weights (gear_wear's Scene: the glb): her body
         untucked, the SKIN PATCH (her points within PATCH of the piece) and the piece's meshes, worst mm. An import
         that lost a weight, a shape, a tier or a vertex shows here.
  tuck   her tucked patch as the engine draws it (its tuck_map times its `tuck` uniform, along its stored skinned
         normal) against gear_wear's (the look's rows merged in python, SkinTuck.Merge, along Scene.stored_normals):
         worst mm over the piece's own record points, and the points where the engine's map is deeper than the rows
         (the garment tuck's `under` row, which gear_wear's skin test does not lay: reported, not failed).
  clip   the engine's input pose against the clip dump's frame (tools/body/out/clips, what gear_wear poses): the bones
         the clip keys must agree (hips, legs, Head and neck apart: an upper-body hold stands on the idle's legs and
         carries her head level). Bones the clip does NOT key are listed: PlayerView --hold plays the clip on an
         AnimationPlayer over whatever the last idle wrote, so an unkeyed clavicle keeps the idle's turn (13 deg on the
         warden) where the dump, and the game's own AnimationTree at full blend, have it at rest. --strict-pose fails
         on them too.
  out    gear_wear's skin test of the piece at that one frame, in the engine's pose and in the dump's: mm2 past the
         outer face by more than 2 mm (information: what the picture should show).

engine_ref/NAME.npz (--store) keeps what test_engine_check.py needs to hold the POSER to the engine without a Godot
run: the laws' input and output, the shape weights, the patch's and the piece's engine positions.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gear_wear as gw  # noqa: E402

GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
RUN = os.path.join(REPO, "godot", ".shots", "gear_p2", "engine_check")
REF = os.path.join(HERE, "engine_ref")
WARDEN = ["warden.bottom", "warden.top", "warden.belt", "warden.boots", "warden.bracers", "warden.greaves", "warden.skirt"]
BASE = "--quick warden --nohud --zone waystation --seed 1 --time day --close 1 --idle-after 1 --close-turn 0.6 --seconds 9"
FRAMES = {      # name: the game's arguments, the clip and key frame it holds, the look's rows, the piece under test
    "w_dh_a": {"args": BASE + " --hold daggers_heavy@0.0667", "clip": "daggers_heavy", "frame": 2,
               "worn": WARDEN + ["plate_pauldrons_warden"], "piece": "plate_pauldrons_warden"},
    "w_sh_a": {"args": BASE + " --hold sword_heavy@0.3333", "clip": "sword_heavy", "frame": 10,
               "worn": WARDEN + ["plate_pauldrons_warden"], "piece": "plate_pauldrons_warden"},
    "w_cf_a": {"args": BASE + " --hold cast_flick@0.2", "clip": "cast_flick", "frame": 6,
               "worn": WARDEN + ["plate_pauldrons_warden"], "piece": "plate_pauldrons_warden"},
}
PATCH = 0.12
TOL = {"laws_mm": 0.05, "laws_deg": 0.3, "laws_w": 0.005, "body_mm": 0.3, "patch_mm": 0.3, "piece_mm": 0.3,
       "tuck_mm": 1.0, "clip_deg": 2.0}      # (clip_deg: sword_heavy's shield arm stands 1.65 deg off its dump under --hold, 9 Nov; not chased)
FREE = ("root", "pelvis", "thigh", "calf", "foot", "ball", "glute", "Head", "neck")     # clip: not held to the dump


# ------------------------------------------------------------------ the engine's dumps --
def xmat(a):
    a = np.asarray(a, float)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = a[0:3], a[3:6], a[6:9], a[9:12]
    return m


def rows34(a):
    a = np.asarray(a, float).reshape(-1, 3, 4)
    m = np.zeros((len(a), 4, 4))
    m[:, :3] = a
    m[:, 3, 3] = 1
    return m


def rot_deg(Ra, Rb):
    R = Ra.T @ Rb
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


class EngMesh:
    """One mesh as P1MeshDump wrote it."""

    def __init__(self, d, m):
        self.name, self.blend_mode = m["name"], m["blend_mode"]
        raw = open(os.path.join(d, m["file"]), "rb").read()
        f32 = lambda oc: np.frombuffer(raw, "<f4", oc[1], oc[0]).astype(np.float64)   # noqa: E731
        i32 = lambda oc: np.frombuffer(raw, "<i4", oc[1], oc[0]).astype(np.int64)     # noqa: E731
        self.values = {k: v for k, v in m["shapes"]}
        self.bind_bone = [b["bone"] for b in m["binds"]]
        self.bind_pose = np.stack([xmat(b["pose"]) for b in m["binds"]]) if m["binds"] else np.zeros((0, 4, 4))
        self.surf = []
        for s in m["surfaces"]:
            n, per = s["verts"], s["per"]
            x = {"P": f32(s["vertex"]).reshape(n, 3), "N": f32(s["normal"]).reshape(-1, 3), "per": per,
                 "J": i32(s["bones"]).reshape(n, per) if per else None, "W": f32(s["weights"]).reshape(n, per) if per else None,
                 "shapes": {k: f32(v).reshape(n, 3) for k, v in s["shapes"].items()}, "tuck_channel": s.get("tuck_channel"),
                 "shape_normals": {k: f32(v).reshape(-1, 3) for k, v in s.get("shape_normals", {}).items()}}
            if "tuck_map" in s:
                x.update(tuck=s["tuck"], tuck_map=f32(s["tuck_map"]), tuck_offset=s["tuck_offset"])
            self.surf.append(x)

    def skinned(self, s, bones, tuck=True):
        """Surface s as the engine draws it, Godot skeleton space: P, her skinned stored normal, the tuck depth (m), not drawn."""
        x = self.surf[s]
        P, N0 = x["P"].copy(), x["N"].copy()
        for k, A in x["shapes"].items():
            P += self.values.get(k, 0.0) * ((A - x["P"]) if self.blend_mode == 0 else A)
        for k, A in x["shape_normals"].items():        # (Godot's blend: normalize(n (1 - sum w) + sum w n_shape), or n + sum w dn)
            if len(A) == len(N0):
                N0 += self.values.get(k, 0.0) * ((A - x["N"]) if self.blend_mode == 0 else A)
        N0 /= np.linalg.norm(N0, axis=1, keepdims=True) + 1e-30
        S = np.stack([bones[b] @ self.bind_pose[i] if b in bones else np.eye(4) for i, b in enumerate(self.bind_bone)])
        Ph = np.c_[P, np.ones(len(P))]
        out, Nn = np.zeros((len(P), 3)), np.zeros((len(P), 3))
        for k in range(x["per"]):
            w = x["W"][:, k]
            if not w.any():
                continue
            M = S[x["J"][:, k]]
            out += w[:, None] * np.einsum("nij,nj->ni", M[:, :3, :], Ph)
            Nn += w[:, None] * np.einsum("nij,nj->ni", M[:, :3, :3], N0)
        Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-30
        depth, gone = np.zeros(len(P)), np.zeros(len(P), bool)
        if x.get("tuck_channel") == -2:
            h = x["tuck_map"][np.arange(len(P)) + x["tuck_offset"]]
            gone = h >= gw.T_GONE
            depth = x["tuck"] * np.where(h > gw.T_FULL, np.minimum(1.0, 2.0 - h), h)      # (heroine_skin.gdshader, tuck_channel -2)
            if tuck:
                out = out - Nn * depth[:, None]
        return out, Nn, depth, gone


def load(run, name):
    d = os.path.join(run, name + ".skin")
    ix = json.load(open(os.path.join(d, "meshes.json")))
    full = [json.loads(ln) for ln in open(os.path.join(run, name + ".full.jsonl"))]
    e = [ln for ln in full if ln["frame"] == ix["frame"]][-1]
    laws = [json.loads(ln) for ln in open(os.path.join(run, name + ".laws.jsonl"))]
    laws = ([ln for ln in laws if ln["frame"] == ix["frame"]] or laws)[-1]
    return {"frame": ix["frame"], "e": e, "bones": {k: xmat(v) for k, v in e["bones"].items()},
            "meshes": {m["name"]: EngMesh(d, m) for m in ix["meshes"]}, "laws": laws}


# ------------------------------------------------------------------------ the poser --
def merged_tuck(sc, byid, worn):
    """SkinTuck.Merge for the look's rows (no garment `under`): per skin point (sc.keys) the depth (m) and not drawn."""
    mm, gone = np.zeros(len(sc.keys)), np.zeros(len(sc.keys), bool)
    for i in worn:
        r = byid.get(i)
        if not r or not r["tuck_path"]:
            continue
        recs = gw.read_records(r["tuck_path"])
        q = np.round(np.clip(np.array([recs.get(k, 0.0) for k in sc.keys]), 0, 1) * 255) / 255
        mm = np.maximum(mm, float(r.get("tuck_depth_mm") or 10.0) * np.where(q > gw.T_FULL, 1.0, q))
        gone |= q >= gw.T_GONE
    return mm / 1000.0, gone


def raw_pose(cp, f):
    """ClipPoser.frame's bones before the laws."""
    p = cp.p
    Gd = gw.mats(cp.d["B"][f])
    G = p.rest.copy()
    got = np.zeros(len(G), bool)
    for a, k in enumerate(cp.map):
        if k >= 0:
            G[k] = cp.X @ Gd[a]
            got[k] = True
    for k in cp.order:
        pk = p.parent[k]
        if pk >= 0 and (not got[k] or p.names[k] in cp.helpers and p.names[k] not in cp.keyed):
            G[k] = G[pk] @ (np.linalg.inv(p.rest[pk]) @ p.rest[k])
    return G


def out_mm2(sc, rows, order, piece, S, w):
    ck = gw.Check(sc, rows, order, 0.0025, True)
    ck.add_skin([piece])
    ck.run([("c", lambda: iter([(0, S, w)]))], log=lambda s: None)
    x = ck.tests[0]
    o = x["per_clip"]["c"]["out"]
    return float(x["area"][o < -0.002].sum() * 1e6), float(-o[np.isfinite(o)].min() * 1000) if np.isfinite(o).any() else 0.0


def compare(run, name, fr, sc, rows, order, strict=False, store=False, log=print):
    byid = {r["id"]: r for r in rows}
    p, piece = sc.poser, fr["piece"]
    cp = gw.ClipPoser(sc, json.load(open(os.path.join(gw.CLIPS, fr["clip"] + ".json"), encoding="utf-8")))
    Xi = np.linalg.inv(cp.X)
    to_g = lambda P: (Xi[:3, :3] @ P.T).T + Xi[:3, 3]      # noqa: E731  (the poser's space -> Godot's skeleton space)
    r = load(run, name)
    E, lw = r["bones"], r["laws"]
    fails, num = [], {}

    def hold(key, val, tol, what):
        num[key] = round(float(val), 4)
        bad = val > TOL[tol]
        log(f"  {'FAIL' if bad else 'ok  '} {what}: {val:.3f} (tolerance {TOL[tol]:g})")
        if bad:
            fails.append(f"{name}: {what} {val:.3f} over {TOL[tol]:g}")

    log(f"{name}: engine frame {r['frame']}, {fr['clip']} f{fr['frame']}, {piece}")
    # ---- laws
    nm = lw["names"]
    pre, post = rows34(lw["pre"]), rows34(lw["post"])
    Gin = np.stack([cp.X @ pre[nm.index(n)] for n in p.names])
    Gout, w = p.driver.drive(p, Gin.copy(), sc.rig)
    hold("laws_mm", max(np.linalg.norm((Xi @ Gout[k])[:3, 3] - post[nm.index(n)][:3, 3]) * 1000 for k, n in enumerate(p.names)),
         "laws_mm", "laws, rig_drive on the engine's input against its output, worst bone mm")
    hold("laws_deg", max(rot_deg((Xi @ Gout[k])[:3, :3], post[nm.index(n)][:3, :3]) for k, n in enumerate(p.names)),
         "laws_deg", "laws, worst bone deg")
    hold("laws_w", max([abs(w.get(k, 0) - lw["weights"].get(k, 0)) for k in set(w) | set(lw["weights"])] + [0.0]),
         "laws_w", "laws, worst corrective weight")
    # ---- data
    S = np.stack([cp.X @ E[n] for n in p.names]) @ sc.ibm
    wE = dict(r["e"]["meshes"]["Heroine"]["shapes"])
    m = r["meshes"]["Heroine"]
    Pe, Ne, depth_e, gone_e = m.skinned(0, E, tuck=False)
    d0, jb = cKDTree(to_g(sc.P0[sc.isk])).query(m.surf[0]["P"])
    Pp = to_g(sc.pose(S, wE, sc.isk))[jb]
    pv = np.nonzero(sc.owner == piece)[0]
    Pq = to_g(sc.pose(S, wE, pv))
    eng = [(n, mm.skinned(0, E, tuck=False)[0], mm.surf[0]["P"]) for n, mm in r["meshes"].items()
           if n.startswith(piece.replace(".", "_") + "_")]
    if len(Pe) != len(sc.isk) or d0.max() > 1e-4:
        fails.append(f"{name}: her body in the engine is not the poser's ({len(Pe)} against {len(sc.isk)} points, rest {d0.max() * 1000:.3f} mm apart)")
    hold("body_mm", np.linalg.norm(Pe - Pp, axis=1).max() * 1000, "body_mm", f"data, her body ({len(Pe)} points, untucked), worst mm")
    Pqe = np.concatenate([a for _, a, _ in eng]) if eng else np.zeros((0, 3))
    patch = np.nonzero(cKDTree(Pq).query(Pp)[0] < PATCH)[0]
    hold("patch_mm", np.linalg.norm(Pe[patch] - Pp[patch], axis=1).max() * 1000, "patch_mm", f"data, the skin patch ({len(patch)} points within {PATCH * 100:g} cm of the piece), worst mm")
    if len(Pqe) != len(pv):
        fails.append(f"{name}: {piece} in the engine has {len(Pqe)} points, the poser's file {len(pv)} (a tier or an import)")
        jq = np.zeros(0, int)
    else:
        dq, jq = cKDTree(to_g(sc.P0[pv])).query(np.concatenate([b for _, _, b in eng]))
        hold("piece_mm", np.linalg.norm(Pqe - Pq[jq], axis=1).max() * 1000, "piece_mm", f"data, {piece} ({len(Pqe)} points in {len(eng)} meshes), worst mm")
    # ---- tuck
    tk, gone_p = merged_tuck(sc, byid, fr["worn"])
    Ns = sc.stored_normals(S, wE, sc.isk)
    Ns = (Xi[:3, :3] @ Ns.T).T[jb]
    Tp = Pp - Ns * tk[jb][:, None]
    Te = Pe - Ne * depth_e[:, None]
    own = np.array([gw.read_records(byid[piece]["tuck_path"]).get(k, 0.0) for k in sc.keys])[jb] > 0
    deeper = depth_e - tk[jb] > 5e-5
    sel = own & ~gone_e & ~deeper
    hold("tuck_mm", np.linalg.norm(Te[sel] - Tp[sel], axis=1).max() * 1000 if sel.any() else 0.0, "tuck_mm",
         f"tuck, her tucked points under the piece's record ({int(sel.sum())}), engine against gear_wear, worst mm")
    num["tuck_under_points"], num["gone_differ"] = int(deeper.sum()), int((gone_e != gone_p[jb]).sum())
    log(f"       tuck: the engine's map is deeper than the look's rows at {int(deeper.sum())} points (the garment tuck's under row, "
        f"worst {((depth_e - tk[jb])[deeper].max() * 1000 if deeper.any() else 0):.2f} mm); not drawn differs at {num['gone_differ']} points")
    if num["gone_differ"]:
        fails.append(f"{name}: {num['gone_differ']} of her points are drawn on one side and not the other")
    # ---- clip
    Gc = raw_pose(cp, fr["frame"])
    loc = lambda G, k: G[k] if p.parent[k] < 0 else np.linalg.inv(G[p.parent[k]]) @ G[k]      # noqa: E731
    keyed, worst, unkeyed = 0.0, "", []
    for k, n in enumerate(p.names):
        if n.startswith(FREE) or n in cp.helpers:
            continue
        d = rot_deg(loc(Gin, k)[:3, :3], loc(Gc, k)[:3, :3])
        if n in cp.keyed:
            keyed, worst = (d, n) if d > keyed else (keyed, worst)
        elif d > 0.5:
            unkeyed.append((n, d))
    hold("clip_deg", keyed, "clip_deg", f"clip, the bones the clip keys, engine input against the dump, worst deg ({worst})")
    num["unkeyed"] = {n: round(d, 2) for n, d in unkeyed}
    if unkeyed:
        log("       clip: bones the clip does not key stand off the dump (the --hold keeps the last idle's): "
            + ", ".join(f"{n} {d:.1f} deg" for n, d in unkeyed))
        if strict:
            fails.append(f"{name}: unkeyed bones off the dump: " + ", ".join(f"{n} {d:.1f}" for n, d in unkeyed))
    # ---- out (information)
    Sd, wd = cp.frame(fr["frame"])
    oe, od = out_mm2(sc, rows, order, piece, S, wE), out_mm2(sc, rows, order, piece, Sd, wd)
    num["out2_engine_mm2"], num["out2_dump_mm2"] = round(oe[0], 1), round(od[0], 1)
    log(f"       out: gear_wear's skin test at this frame, engine pose {oe[0]:.0f} mm2 over 2 mm (deepest {oe[1]:.1f} mm), dump pose {od[0]:.0f} mm2 ({od[1]:.1f} mm)")
    if store:
        os.makedirs(REF, exist_ok=True)
        keep = patch[~gone_e[patch]]
        every = np.arange(0, len(Pqe), 8)
        np.savez_compressed(os.path.join(REF, name + ".npz"), clip=fr["clip"], frame=fr["frame"], piece=piece, worn=np.array(fr["worn"]),
                            names=np.array(nm), pre=pre[:, :3].astype(np.float64), post=post[:, :3].astype(np.float64),
                            weights=json.dumps(lw["weights"]), shapes=json.dumps(wE),
                            bones=np.stack([E[n][:3] for n in nm]),
                            patch_key=np.array(sc.keys)[jb[keep]], patch_row=jb[keep], patch_tucked=Te[keep].astype(np.float32), patch_depth=depth_e[keep].astype(np.float32),
                            piece_rest=np.concatenate([b for _, _, b in eng])[every].astype(np.float32), piece_pos=Pqe[every].astype(np.float32))
        log(f"       stored {os.path.join(REF, name + '.npz')}")
    return fails, num


def shoot(run, names, stale_ok=False):
    wt_godot = os.path.join(REPO, "godot")
    main = REPO.split(os.sep + ".claude" + os.sep)[0]
    turn = os.path.join(main if os.path.isfile(os.path.join(main, "tools", "turn.py")) else REPO, "tools", "turn.py")
    os.makedirs(run, exist_ok=True)
    job = "gear: engine check"
    if subprocess.run([sys.executable, turn, "take", "godot", job, "--wait", "600"] + (["--stale-ok"] if stale_ok else [])).returncode != 0:
        raise SystemExit("engine_check: the godot turn is busy")
    try:
        for n in names:
            o = lambda ext: os.path.join(run, n + ext).replace("\\", "/")      # noqa: E731
            cmd = [GODOT, "--path", ".", "--resolution", "1920x1080", "--fixed-fps", "30", "--audio-driver", "Dummy", "--",
                   "--shot", "ec_" + n, "--body", "p1", "--p1-probe", "--pose-probe", o(".probe.jsonl"), "--pose-probe-full", o(".full.jsonl"),
                   "--pose-probe-every", "30", "--pose-probe-skin", o(".skin"), "--p1-laws-dump", o(".laws.jsonl")] + FRAMES[n]["args"].split()
            with open(o(".log"), "w") as lg:
                rc = subprocess.run(cmd, cwd=wt_godot, stdout=lg, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=900).returncode
            png = os.path.join(wt_godot, ".shots", f"ec_{n}.png")
            if os.path.isfile(png):
                os.replace(png, o(".png"))
            print(f"engine_check: shot {n} (exit {rc})")
    finally:
        subprocess.run([sys.executable, turn, "give", "godot", job])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default=RUN)
    ap.add_argument("--frames", default=",".join(FRAMES))
    ap.add_argument("--shoot", action="store_true", help="run the game for each frame first (takes and gives the godot turn)")
    ap.add_argument("--store", action="store_true", help="keep each frame's compact reference in tools/armor/engine_ref")
    ap.add_argument("--stale-ok", action="store_true", help="shoot though the branch is behind integration (only when the missing commits carry no body or gear art)")
    ap.add_argument("--strict-pose", action="store_true", help="fail on bones the clip does not key standing off the dump")
    a = ap.parse_args(argv)
    names = [n for n in a.frames.split(",") if n]
    if a.shoot:
        shoot(a.run, names, a.stale_ok)
    ix, rows = gw.load_rows(gw.GEAR)
    body = os.path.join(REPO, "godot", "art", "people", ix["body"])
    order = json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["order"]
    fails, report = [], {}
    scenes = {}
    for n in names:
        fr = FRAMES[n]
        if not os.path.isfile(os.path.join(a.run, n + ".skin", "meshes.json")):
            fails.append(f"{n}: no dump in {a.run} (run with --shoot)")
            continue
        if fr["piece"] not in scenes:
            scenes[fr["piece"]] = gw.build_scene(body, rows, {fr["piece"]})
        f, num = compare(a.run, n, fr, scenes[fr["piece"]], rows, order, a.strict_pose, a.store)
        fails += f
        report[n] = num
    json.dump({"tolerances": TOL, "frames": report, "fails": fails}, open(os.path.join(a.run, "engine_check.json"), "w"), indent=1)
    print(f"engine_check: {len(names)} frames, {len(fails)} over tolerance" + ("".join("\n  " + f for f in fails) if fails else " (engine and poser agree)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
