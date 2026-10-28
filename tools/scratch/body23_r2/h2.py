"""Body 23 r2: the FINAL-POSE dump. Godot's --dump-her reads her bones in _Process, after Godot 4.3+ has restored the
pre-modifier pose, so its skin matrices miss every SkeletonModifier3D (HerJoints' elbow point/share/twists, HerCarriage,
HerJiggle, HerScap, ...): at a bent elbow the B20 harness sat ~10 px inside the game's picture. HerRaise's --pose-dump
writes every bone's pose at SkeletonUpdated (the final pose). This rewrites a --dump-her dump's skin columns (and the
world/normal/screen/depth columns that follow from them) from that final pose and the body's own weights, so the B20
harness poses bodies as the game draws them.
    python h2.py DUMPDIR OUTDIR BODY.glb [frames...]"""
import os, sys, json, shutil, re, numpy as np
import r2lib as c
h = c.h
from shoulder_psd_post import Rig
from heroine_neck import _Gl

STILL = ("root", "pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r")


def pose_json(path):
    d = json.load(open(path))
    out = {}
    for n, v in d.items():
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
        out[n] = M
    return out


def synth(ddir, odir, glb, frame, log=print):
    fr = h.Frame(ddir, frame, glb, c._LAB[0])
    if c._LAB[0] is None:
        c._LAB[0] = fr.lab
    rig, Gs, res = c.flex.bones(fr, glb)
    T = pose_json(os.path.join(ddir, "pose_%s.json" % frame))
    # her skeleton node's transform: from bones no modifier touches
    Ss = [Gs[rig.index[n]] @ np.linalg.inv(T[n]) for n in STILL if n in rig.index and n in T]
    S = np.mean(Ss, 0)
    spread = max(np.abs(x - S).max() for x in Ss)
    Gf = np.stack([S @ T[n] if n in T else Gs[i] for i, n in enumerate(rig.names)])
    K = Gf @ rig.ibm                                         # per bone skin matrix
    moved = {n: float(np.linalg.norm(Gf[i][:3, 3] - Gs[i][:3, 3]) * 1000) for i, n in enumerate(rig.names)}
    G = _Gl(glb); g = G.g
    mi = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]
    prims = g["meshes"][mi]["primitives"]
    os.makedirs(odir, exist_ok=True)
    logtxt = open(os.path.join(ddir, "log_%s.txt" % frame), encoding="utf-8", errors="replace").read()
    open(os.path.join(odir, "log_%s.txt" % frame), "w", encoding="utf-8").write(logtxt)
    for ext in (".png", ):
        src = os.path.join(ddir, frame + ext)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(odir, frame + ext))
    for k, (s, (pk, j, _)) in enumerate(zip(fr.dump["surfs"], fr.mp)):
        A = s["A"].copy()
        if pk is not None:
            p = prims[pk]
            Jt = np.hstack([G.get(p["attributes"]["JOINTS_0"]), G.get(p["attributes"]["JOINTS_1"])])[j].astype(int)
            Wt = np.hstack([G.get(p["attributes"]["WEIGHTS_0"]), G.get(p["attributes"]["WEIGHTS_1"])])[j].astype(float)
            M = np.einsum("vk,vkij->vij", Wt, K[Jt])
            bind, bn = A[:, 11:14], A[:, 14:17]
            P = np.einsum("vij,vj->vi", M[:, :3, :3], bind) + M[:, :3, 3]
            N = np.einsum("vij,vj->vi", M[:, :3, :3], bn)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            A[:, 0:3], A[:, 3:6] = P, N
            A[:, 17:20], A[:, 20:23], A[:, 23:26], A[:, 26:29] = M[:, :3, 0], M[:, :3, 1], M[:, :3, 2], M[:, :3, 3]
            A[:, 6:8] = h.project(fr.Pm, P)
            A[:, 8] = np.linalg.norm(P - fr.campos, axis=1)
        nv, I = len(A), s["I"]
        with open(os.path.join(odir, "%s_s%d.bin" % (frame, k)), "wb") as f:
            f.write(np.array([nv, I.size], "<i4").tobytes())
            f.write(A.astype("<f4").tobytes())
            f.write(I.astype("<i4").tobytes())
    top = sorted(moved.items(), key=lambda kv: -kv[1])[:8]
    log("%-9s skeleton node from %d still bones (spread %.2e); bones moved by her modifiers (mm): %s"
        % (frame, len(Ss), spread, " ".join("%s %.1f" % kv for kv in top)))
    return moved


if __name__ == "__main__":
    ddir, odir, glb = sys.argv[1:4]
    frames = sys.argv[4:] or c.LIST9
    for f in frames:
        synth(ddir, odir, glb, f)
