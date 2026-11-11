"""p4_parity: the game against the Python side, for a built P4 clip played in the game.

    python tools/anim/p4_parity.py <full.jsonl> <clip> [--json OUT]

<full.jsonl> is the game's --pose-probe-full dump (godot/src/Actors/P1PoseProbe.cs, with --pose-probe-every N): per probed
frame every bone's skeleton-space pose (12 numbers: basis columns, origin) and each held piece's sample points ("pts":
vertex indices range(0, n, max(1, n // 64)) of its meshes in tools_scenes/ArmsDump.cs's order). <clip> is the built clip
godot/art/people/body_p1/p4/<clip>.json (or a path to one).

Per probed frame:
  1. the time fit: the clip time t (in frames, continuous) whose Python pose (the clip's keys: slerp between the two
     neighbouring frames, pelvis/root translation lerped, the loop wrapping, other bones at rest local; rig FK) turns the
     bones the laws keep (pelvis, spine_01..05, thighs, upper arms, hands) as the game's do: the summed world-rotation
     angle, coarse over every clip frame then golden-section within +-1 frame. Each probed frame fits on its own (the
     overlay may play at another speed).
  2. B's laws as the game runs them (tools/body/rig_drive.drive on the lbs poser, built as clipcheck.Body, without
     skinning): the post-law globals at the fitted t.
  3. pieces: the sword (mount_hand_r/*) and the shield (mount_lowerarm_l/*): the game's "pts" against Python's
     (p4.pieces() points at the same indices, in the bone's space, carried by the POST-LAW bone global): the max distance
     (mm) and the Kabsch best-fit rotation between the two sets (deg). Tolerance 1 mm and 0.5 deg.
  4. the blend-base test: every bone in the clip's "rot": the game's local rotation (parent^-1 * bone, from the dump)
     against Python's post-law local: the worst angle per bone over the frames, tolerance 0.1 deg. Bones that carry a
     runtime look layer (neck, head) are listed apart, not hidden.
Prints the table; exits 1 over tolerance (pieces and blend-base bones, the look bones excluded from the exit code).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402  (Marionette's core on the path)
from motion import quat as Q  # noqa: E402
from motion.rig import Rig  # noqa: E402

REPO = p4.REPO
TOL_MM, TOL_DEG, TOL_BASE = 1.0, 0.5, 0.1
RUN_IN_MM = 0.5       # (and a pelvis more than this far off the fitted clip pose: the overlay is still blending in from the stance before)
NOT_PLAYING = 1.0     # a probed frame whose best time fit still turns the fit bones this many deg (summed) is not the clip
                      # playing (the first frame, before the overlay starts): left out, and counted
FIT_BONES = ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "thigh_l", "thigh_r",
             "upperarm_l", "upperarm_r", "hand_l", "hand_r")
LOOK = ("neck", "head")          # (runtime look layers ride these: listed apart)
PIECES = {"sword": ("mount_hand_r/", "hand_r"), "shield": ("mount_lowerarm_l/", "lowerarm_l")}


def mat(v):
    a = np.asarray(v, float)
    M = np.eye(4)
    M[:3, :3] = a[:9].reshape(3, 3).T      # (basis columns)
    M[:3, 3] = a[9:12]
    return M


def ang_deg(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


class Py:
    """The clip's pose at a continuous time, before and after B's laws."""

    def __init__(self, clip, rig=None, glb=None, rigj=None):
        self.c = clip
        self.rig = rig or Rig(p4.RIG)
        self.n, self.loop = clip["frames"], bool(clip.get("loop"))
        rig = self.rig
        self.Q = {b: np.array(q, float) for b, q in clip["rot"].items()}
        self.T = {b: np.array(p, float) for b, p in clip["pos"].items()}
        sys.path.insert(0, str(REPO / "tools/body"))
        import clipcheck as CC
        P1 = REPO / "godot/art/people/body_p1"
        self.body = CC.Body(glb or str(P1 / "body.glb"), rigj or json.loads((P1 / "rig.json").read_text()), rig.names,
                            p4.m44(rig.R0, rig.head), True)
        self.keyed = set(self.Q)
        self.Xi = np.linalg.inv(self.body.X)
        self.cache = {}

    def locals_at(self, t):
        n = self.n
        # (a loop's last frame is its first again: the game's length is (n - 1) / fps, as p4_blend.locals_at)
        t = t % (n - 1) if self.loop else min(max(t, 0.0), n - 1)
        a = min(int(np.floor(t)), n - 2)
        f = t - a
        b = a + 1
        rig = self.rig
        Lr, Lt = rig.rest_locals(1)
        for k, q in self.Q.items():
            Lr[0, rig.index[k]] = Q.to_mat(Q.slerp(q[a], q[b], f)[None])[0]
        for k, p in self.T.items():
            Lt[0, rig.index[k]] = (1 - f) * p[a] + f * p[b]
        return Lr, Lt

    def pre(self, t):
        Lr, Lt = self.locals_at(t)
        G, P = self.rig.fk(Lr, Lt)
        return G[0], P[0]

    def post(self, t):
        """Post-law globals in the game's skeleton space (names of the rig), as 4x4 (J,4,4)."""
        key = round(float(t), 6)
        if key in self.cache:
            return self.cache[key]
        G, P = self.pre(t)
        Gd = p4.m44(G, P)
        B = self.body
        p = B.p
        Gb = p.rest.copy()
        got = np.zeros(len(Gb), bool)
        for a, k in enumerate(B.map):
            if k >= 0:
                Gb[k] = B.X @ Gd[a]
                got[k] = True
        for k in B.order:      # (clipcheck.Body.pose: bones the clip lacks, and unkeyed helpers, at rest local)
            pk = p.parent[k]
            if pk >= 0 and (not got[k] or p.names[k] in B.helpers and p.names[k] not in self.keyed):
                Gb[k] = Gb[pk] @ (np.linalg.inv(p.rest[pk]) @ p.rest[k])
        Gb, _ = p.driver.drive(p, Gb, B.rig)
        out = {n: self.Xi @ Gb[p.index[n]] for n in p.names}
        self.cache[key] = out
        return out


def fit_time(py, game, names=FIT_BONES, step_tol=1e-3):
    """The clip time (frames) whose pre-law world turns of `names` best match the game's (sum of angles, deg)."""
    rig = py.rig
    idx = [rig.index[b] for b in names]
    Rg = [game[b][:3, :3] for b in names]

    def cost(t):
        G, _ = py.pre(t)
        return sum(ang_deg(G[j], R) for j, R in zip(idx, Rg))
    m = py.n - 1
    ts = np.arange(m, dtype=float)
    cs = [cost(t) for t in ts]
    k = int(np.argmin(cs))
    lo, hi = ts[k] - 1, ts[k] + 1
    gr = (np.sqrt(5) - 1) / 2
    a, b = hi - gr * (hi - lo), lo + gr * (hi - lo)
    ca, cb = cost(a), cost(b)
    while hi - lo > step_tol:
        if ca < cb:
            hi, b, cb = b, a, ca
            a = hi - gr * (hi - lo)
            ca = cost(a)
        else:
            lo, a, ca = a, b, cb
            b = lo + gr * (hi - lo)
            cb = cost(b)
    t = (lo + hi) / 2
    return (t % m if py.loop else t), cost(t)


def kabsch_deg(A, B):
    """Angle of the best-fit rotation taking point set A onto B (both centered)."""
    A = A - A.mean(0)
    B = B - B.mean(0)
    U, _, Vt = np.linalg.svd(A.T @ B)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1, 1, d]) @ Vt
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def piece_of(frame, prefix):
    for k, v in frame.get("pieces", {}).items():
        if k.startswith(prefix):
            return v
    return None


def run(lines, clip, py=None, pc=None):
    py = py or Py(clip)
    pc = pc or p4.pieces()
    rig = py.rig
    rows, base = [], {}
    for fr in lines:
        game = {n: mat(v) for n, v in fr["bones"].items()}
        t, cost = fit_time(py, game)
        post = py.post(t)
        row = {"frame": fr["frame"], "t": round(t, 3), "fit_deg_sum": round(cost, 3)}
        off = (game["pelvis"][:3, 3] - post["pelvis"][:3, 3]) * 1000
        row["pelvis_off_mm"] = off
        if cost > NOT_PLAYING or np.linalg.norm(off) > RUN_IN_MM:
            row["skipped"] = True
            rows.append(row)
            continue
        for k, (prefix, bone) in PIECES.items():
            pie = piece_of(fr, prefix)
            if pie is None:
                continue
            v = pc[k]
            n = pie["n"]
            idx = np.arange(0, n, max(1, n // 64))
            if len(v) != n:
                row[f"{k}_n"] = f"game {n} vs python {len(v)}"
                continue
            gp = np.array(pie["pts"], float)
            M = post[bone]
            pp = v[idx] @ M[:3, :3].T + M[:3, 3]
            row[f"{k}_mm"] = float(np.linalg.norm(gp - pp, axis=1).max() * 1000)
            row[f"{k}_deg"] = kabsch_deg(pp, gp)
            row[f"{k}_off_mm"] = (gp.mean(0) - pp.mean(0)) * 1000
        for b in py.keyed & set(rig.names):
            j = rig.index[b]
            p = rig.parent[j]
            if p < 0 or b not in game or rig.names[p] not in game or rig.names[p] not in post:
                continue
            gl = game[rig.names[p]][:3, :3].T @ game[b][:3, :3]
            pl = post[rig.names[p]][:3, :3].T @ post[b][:3, :3]
            base[b] = max(base.get(b, 0.0), ang_deg(gl, pl))
        rows.append(row)
    return rows, base


def report(rows, base, name):
    skipped = [r for r in rows if r.get("skipped")]
    rows = [r for r in rows if not r.get("skipped")]
    print(f"{name}: {len(rows)} probed frames compared, {len(skipped)} not the clip playing (fit > {NOT_PLAYING} deg or pelvis > {RUN_IN_MM} mm off: run-in): "
          f"{[(r['frame'], r['fit_deg_sum'], round(float(np.linalg.norm(r['pelvis_off_mm'])), 1)) for r in skipped]}")
    po = np.array([r["pelvis_off_mm"] for r in rows]) if rows else np.zeros((1, 3))
    print(f"  pelvis position game - python (mm), compared frames: max {np.abs(po).max():.3f}, mean {np.round(po.mean(0), 3).tolist()} (a ground offset would show here)")
    print("  frame      t   fit_sum_deg   sword mm / deg      shield mm / deg")
    for r in rows:
        s = f"  {r['frame']:5d} {r['t']:7.2f} {r['fit_deg_sum']:10.3f}"
        for k in PIECES:
            s += f"   {r[f'{k}_mm']:7.3f} / {r[f'{k}_deg']:6.3f}" if f"{k}_mm" in r else f"   {r.get(k + '_n', 'no piece')}"
        print(s)
    bad = False
    mx = {}
    for k in PIECES:
        e = [(r[f"{k}_mm"], r[f"{k}_deg"], r["frame"]) for r in rows if f"{k}_mm" in r]
        if e:
            w = max(e)
            mx[k] = {"mm": w[0], "deg": max(x[1] for x in e), "worst_frame": w[2]}
            print(f"  {k}: max {w[0]:.3f} mm (frame {w[2]}), max {mx[k]['deg']:.3f} deg  (tolerance {TOL_MM} mm, {TOL_DEG} deg)")
            bad |= w[0] > TOL_MM or mx[k]["deg"] > TOL_DEG
            offs = np.array([r[f"{k}_off_mm"] for r in rows if f"{k}_off_mm" in r])
            print(f"      mean centroid offset game-python (mm): {np.round(offs.mean(0), 3).tolist()}")
    over = {b: a for b, a in base.items() if a > TOL_BASE}
    look = {b: round(a, 3) for b, a in over.items() if any(b.lower().startswith(p) for p in LOOK)}
    rest = {b: round(a, 3) for b, a in over.items() if b not in look}
    print(f"  blend-base: {len(base)} bones, max {max(base.values()) if base else 0:.3f} deg; over {TOL_BASE} deg: {len(rest)} "
          f"{dict(sorted(rest.items(), key=lambda kv: -kv[1]))}")
    print(f"  look-layer bones over {TOL_BASE} deg (listed apart): {look}")
    bad |= bool(rest)
    mxf = max((r["fit_deg_sum"] for r in rows), default=0)
    print(f"  time fit: worst summed world turn of the {len(FIT_BONES)} fit bones {mxf:.3f} deg; time step between probes "
          f"{np.round(np.median(np.diff([r['t'] for r in rows])), 3) if len(rows) > 1 else '-'} frames (median)")
    return bad, mx, rest, look


def load_lines(path):
    import gzip
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(x) for x in f if x.strip()]


def main(argv):
    path, name = argv[0], argv[1]
    cp = Path(name)
    clip = json.loads((cp if cp.exists() else p4.OUT / f"{name}.json").read_text())
    lines = [l for l in load_lines(path) if "bones" in l]
    rows, base = run(lines, clip)
    bad, mx, rest, look = report(rows, base, cp.stem)
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(
            {"clip": cp.stem, "frames": len(rows), "pieces": mx, "base_over": rest, "look_over": look,
             "base_max": base, "rows": [{k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in r.items()} for r in rows]}))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main([a for a in sys.argv[1:]]))
