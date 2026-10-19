"""The plate top's gore over her skin in each calling's idle (armor 4 r3, F7): her body and the piece posed as the game
poses them (tools/anim/skin.py: Godot's skinning, her springs at the top's hold), her skin tucked as the game tucks it
(the piece's armor_tuck records, 10 mm x the mark, all of it past 0.973, along her posed normal), and over the gore's
footprint (her points whose ray out along the normal meets the gore at rest) the clearance from her tucked skin out
to the gore's inner face, mm (negative: her skin through it). Minimum over every frame of each idle.

    python tools/armor/gore_idle.py [<id>] [--step 2]
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAIN = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))     # (the main checkout: the built clips, tools/anim/out)
sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
os.environ.setdefault("ANIM_OUT", os.path.join(MAIN if os.path.isdir(os.path.join(MAIN, "tools", "anim", "out")) else ROOT, "tools", "anim", "out"))
import skin  # noqa: E402

IDLES = ("idle_warden", "idle_stalker", "idle_arcanist", "idle_reaver")


def ray_t(O, D, tri, reach):
    """Each ray's nearest hit distance along it within (-reach, reach) (nan: none), Moller-Trumbore."""
    out = np.full(len(O), np.nan)
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    for a in range(0, len(O), 128):
        o, d = O[a:a + 128], D[a:a + 128]
        p = np.cross(d[:, None], e2[None])
        det = (e1[None] * p).sum(2)
        ok = np.abs(det) > 1e-14
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = o[:, None] - v0[None]
        u = (s * p).sum(2) * inv
        q = np.cross(s, e1[None])
        v = (d[:, None] * q).sum(2) * inv
        t = (e2[None] * q).sum(2) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (np.abs(t) < reach)
        tt = np.where(h, t, np.nan)
        # (the nearest hit in front if any, else the nearest behind)
        front = np.where(tt >= 0, tt, np.inf).min(1)
        back = np.where(tt < 0, tt, -np.inf).max(1)
        out[a:a + 128] = np.where(np.isfinite(front), front, np.where(np.isfinite(back), back, np.nan))
    return out


def tuck_of(pid, P):
    raw = open(os.path.join(ROOT, "godot", "art", "armor", "armor_tuck", f"{pid}.bin"), "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    d = {(int(r["x"]), int(r["y"]), int(r["z"])): float(r["t"]) for r in rec}
    q = np.round(P.astype(np.float64) * 1e5).astype(np.int64)
    t = np.array([d.get(tuple(k), 0.0) for k in q])
    # (as her skin's shader reads it: eight bits, all of it past 0.973)
    t = np.round(np.clip(t, 0, 1) * 255) / 255
    return 0.010 * np.where(t > 0.973, 1.0, t)


def main(argv):
    pid = next((a for a in argv if not a.startswith("--") and not a.isdigit()), "plate_top_plain")
    step = int(argv[argv.index("--step") + 1]) if "--step" in argv else 1
    sk = skin.Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
    gl = os.path.join(ROOT, "godot", "art", "armor", f"{pid}.gltf")
    files = [(skin.PEOPLE / "heroine.glb", lambda n: n == "Heroine", "skin"),
             (skin.Path(gl), lambda n, p=pid: n == f"{p}.top.steel", "garment")]
    row = next(r for r in json.load(open(os.path.join(ROOT, "godot", "art", "armor", "armor_index.json"), encoding="utf-8")) if r["id"] == pid)
    hold = row.get("hold") or {"amount": 1, "squash": 1}
    body = skin.Body(sk, files, skin.Jiggle(sk, amount=hold["amount"], squash=hold["squash"]), label="her", helpers=True)
    isk, ig = np.nonzero(body.kind == "skin")[0], np.nonzero(body.kind == "garment")[0]
    # (the gore: the piece's points on the gore's one blend, near its socket)
    sock = json.load(open(os.path.join(ROOT, "godot", "art", "armor", f"{pid}.sockets.json"), encoding="utf-8"))
    gs = next(v for k, v in (sock.get("sockets") or sock).items() if k == "gore")
    gp = np.array(gs["point"], float)
    near = ig[np.linalg.norm(body.P[ig] - gp, axis=1) < 0.012]
    rows = np.round(np.c_[body.J[near], body.W[near]], 3)
    vals, cnt = np.unique(rows, axis=0, return_counts=True)
    gore_row = vals[cnt.argmax()]
    allrows = np.round(np.c_[body.J[ig], body.W[ig]], 3)
    gv = ig[(allrows == gore_row).all(1) & (np.linalg.norm(body.P[ig] - gp, axis=1) < 0.06)]
    gset = set(gv.tolist())
    GT = body.T[np.isin(body.T, list(gset)).all(1)]
    ST = body.T[(body.kind[body.T] == "skin").all(1)]
    tk = np.zeros(len(body.P))
    tk[isk] = tuck_of(pid, body.P[isk])
    # (the footprint: her points near the gore whose ray out meets it at rest)
    N0 = skin._normals(body.P, ST)
    cand = isk[np.linalg.norm(body.P[isk] - gp, axis=1) < 0.06]
    t0 = ray_t(body.P[cand] + N0[cand] * 1e-4, N0[cand], body.P[GT], 0.02)
    foot = cand[np.isfinite(t0) & (t0 >= 0)]
    out = {"gore_points": int(len(gv)), "footprint_points": int(len(foot)),
           "tuck_mm_footprint": [round(float(tk[foot].min() * 1000), 2), round(float(np.median(tk[foot]) * 1000), 2)],
           "rest_clearance_mm": round(float(np.nanmin(t0[np.isfinite(t0) & (t0 >= 0)] - tk[foot] * 0) * 1000), 2)}
    for name in IDLES:
        clip = body.clip(name)
        worst, where = np.inf, None
        frames = body.frames(clip)
        for f in range(0, len(frames), step):
            Pp = body.pose(frames[f])
            Np = skin._normals(Pp, ST)
            o = Pp[foot] - Np[foot] * tk[foot][:, None]
            t = ray_t(o + Np[foot] * 1e-5, Np[foot], Pp[GT], 0.03)
            ok = np.isfinite(t)
            if ok.any() and t[ok].min() < worst:
                worst, where = float(t[ok].min()), (f, int(foot[ok][t[ok].argmin()]), int((t[ok] < 0.0015).sum()), int((~ok).sum()))
        out[name] = {"min_clearance_mm": round(worst * 1000, 2), "frame": where[0], "point": where[1],
                     "points_under_1_5mm": where[2], "footprint_points_off_the_gore": where[3]}
    print("GORE IDLE", pid, json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1:])
