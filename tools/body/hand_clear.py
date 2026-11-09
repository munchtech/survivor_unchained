"""hand_clear: the hand-clearance law's data for one body (rig.json "hand_clear", rig_drive.hand_clear; P1 R1 sliders).

    python tools/body/hand_clear.py BUILD_OUT [--json OUT]

The clips are A's, laid on every body by its skeleton, so where a body's thigh and hip surface stands further out than
the ref body's (hips, thighs, weight sliders), a hand that rested by or on her thigh goes into it by that much (the hips
variant's idle_reaver_look: 6.2 mm, the left little finger in the thigh). The law opens the arm by that CHANGE only, so
the hand keeps its place relative to the thigh surface the clip was made against; on the ref body itself it is zero.

Data (per side, from the build's stage: its rest body and skeleton, close.npz / close_skeleton.json, against the ref
body the build was laid from, ref_rest_close.npy / ref_skeleton.json (build_topo target_joints_ref); same topology):
  frame     the thigh's rest frame: points q = inverse(thigh rest) p; axis = the thigh's line (head -> calf head) in it,
            e1, e2 across it; t = q . axis / length (0 hip joint, 1 knee), theta = atan2(rho . e2, rho . e1), rho the
            part of q across the axis.
  r         [t][theta] this body's surface radius from the thigh's line (m), the outer layer of the outward-facing
            skin within 15 mm of the bin's outermost (hip, buttock, thigh and the belly's side above the joint).
  dr        [t][theta] how much further out the surface stands than on the ref body, read relative to the same side's
            SHOULDER (the hand hangs from it): per vertex ((V - S) - (V_ref - S_ref)) . rho_hat, so a body that only
            grows taller or shorter, or whose shoulders move out with its hips, reads what the hand meets. The bins'
            means, empty bins filled from their neighbours, one 3x3 smoothing pass, the first and last t rows 0 (the
            law fades out past the table).
A body with no ref (the ref body itself, her_b) gets no data: the law is absent and nothing changes.
Derivation: (b) measured: hips 0.6's idle_reaver_look (clipcheck "inside L 104/6.2mm", the gate body 0); (c) the
clip's contact is the ref body's (A's clips on her_b), so only the change against it is the body's to fix.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

T_LO, T_HI, T_STEP = -0.4, 1.1, 0.1
N_THETA = 24
LAYER_M = 0.015
NEAR_M, FAR_M, SOFT_M = 0.03, 0.10, 0.01
POINTS = ["hand_{s}", "thumb_04_leaf_{s}", "index_04_leaf_{s}", "middle_04_leaf_{s}", "ring_04_leaf_{s}", "pinky_04_leaf_{s}"]
PALM = ["hand_{s}", "middle_01_{s}"]
ANCHOR = "upperarm_{s}"
ARM_SKIP = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky", "clavicle", "scap", "delt")


def _n(v):
    return v / max(np.linalg.norm(v), 1e-12)


def vnormals(V, T):
    n = np.zeros_like(V)
    f = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def unit(M):
    R = M[:3, :3]
    return R / np.linalg.norm(R, axis=0)


def frame(W, names, s):
    """The thigh's rest frame (rotation part orthonormal, origin its head), its line and length in that frame."""
    th, ca = names.index(f"thigh_{s}"), names.index(f"calf_{s}")
    F = np.eye(4)
    F[:3, :3] = unit(W[th])
    F[:3, 3] = W[th][:3, 3]
    Fi = np.linalg.inv(F)
    k = (Fi @ np.append(W[ca][:3, 3], 1.0))[:3]
    L = float(np.linalg.norm(k))
    ax = k / L
    e1 = _n(np.cross(ax, [0.0, 0.0, 1.0]) if abs(ax[2]) < 0.9 else np.cross(ax, [1.0, 0.0, 0.0]))
    e2 = np.cross(ax, e1)
    return Fi, ax, e1, e2, L


def table(V, Vr, T, src, J, W8, Wb, Wr, names, s, anchor=ANCHOR):
    Fi, ax, e1, e2, L = frame(Wb, names, s)
    sh, shr = Wb[names.index(anchor.replace("{s}", s))][:3, 3], Wr[names.index(anchor.replace("{s}", s))][:3, 3]
    q = (Fi[:3, :3] @ V.T).T + Fi[:3, 3]
    t = q @ ax / L
    rho = q - np.outer(q @ ax, ax)
    r = np.linalg.norm(rho, axis=1)
    rh = rho / np.maximum(r[:, None], 1e-12)
    th = np.arctan2(rho @ e2, rho @ e1)
    N = np.zeros_like(V)                                           # (T indexes the split mesh: src maps it to V)
    np.add.at(N, src, vnormals(V[src], T))
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    Nl = (Fi[:3, :3] @ N.T).T
    rw = (np.linalg.inv(Fi[:3, :3]) @ rh.T).T                      # the radial direction, world (rest)
    dr = np.einsum("ij,ij->i", (V - sh) - (Vr - shr), rw)
    dom = np.array([names[j] for j in J[np.arange(len(J)), np.argmax(W8, 1)]])
    side = np.sign(V[:, 0]) == (1.0 if s == "l" else -1.0)
    keep = (side & (t > T_LO - 0.05) & (t < T_HI + 0.05) & (r < 0.25) & (np.einsum("ij,ij->i", Nl, rh) > 0.2)
            & ~np.array([d.startswith(ARM_SKIP) for d in dom]))
    nt = int(round((T_HI - T_LO) / T_STEP)) + 1
    ti = np.clip(np.rint((t - T_LO) / T_STEP).astype(int), 0, nt - 1)
    ci = np.floor((th + np.pi) / (2 * np.pi) * N_THETA).astype(int) % N_THETA
    R = np.full((nt, N_THETA), np.nan)
    D = np.full((nt, N_THETA), np.nan)
    for a in range(nt):
        for c in range(N_THETA):
            m = keep & (ti == a) & (ci == c)
            if not m.any():
                continue
            o = m & (r >= r[m].max() - LAYER_M)
            R[a, c], D[a, c] = float(r[o].mean()), float(dr[o].mean())
    for X in (R, D):
        for _ in range(50):                    # empty bins from their neighbours (theta periodic)
            bad = np.isnan(X)
            if not bad.any():
                break
            P = np.pad(X, ((1, 1), (0, 0)), constant_values=np.nan)
            nb = np.stack([P[:-2], P[2:], np.roll(X, 1, 1), np.roll(X, -1, 1)])
            fill = np.nanmean(np.where(np.isnan(nb), np.nan, nb), 0) if (~np.isnan(nb)).any() else nb[0]
            X[bad] = fill[bad]
        X[np.isnan(X)] = 0.0
    P = np.pad(D, ((1, 1), (0, 0)), mode="edge")
    D = sum(np.roll(P, k, 1)[1 + i:1 + i + nt] for i in (-1, 0, 1) for k in (-1, 0, 1)) / 9.0
    D[0] = 0.0
    D[-1] = 0.0
    return {"axis": ax.round(6).tolist(), "e1": e1.round(6).tolist(), "e2": e2.round(6).tolist(), "length_m": round(L, 6),
            "r": np.round(R, 5).tolist(), "dr": np.round(D, 5).tolist(),
            "_dr_max_mm": round(float(np.abs(D).max() * 1000), 2), "_kept": int(keep.sum())}


def build(src):
    """The rig.json "hand_clear" block for the build at src, or None (no ref body: the ref itself)."""
    st = os.path.join(src, "stage")
    need = [os.path.join(st, f) for f in ("close.npz", "close_skeleton.json", "ref_rest_close.npy", "ref_skeleton.json")]
    if not all(os.path.exists(p) for p in need):
        return None
    z = np.load(need[0])
    sb, sr = json.load(open(need[1])), json.load(open(need[3]))
    Vr = np.load(need[2])
    if sb["names"] != sr["names"] or Vr.shape != z["V"].shape:
        print(f"hand_clear: {src}: the ref body is not this topology/skeleton; no data")
        return None
    names = sb["names"]
    Wb, Wr = np.asarray(sb["worlds"], float), np.asarray(sr["worlds"], float)
    out = {"why": "rig_drive.hand_clear (tools/body/hand_clear.py): the arm opened by the change of the thigh surface against "
                  "the ref body, by the hand's proximity to it",
           "thigh": "thigh_{s}", "arm": "upperarm_{s}", "points": POINTS, "palm": PALM,
           "t0": T_LO, "dt": T_STEP, "near_m": NEAR_M, "far_m": FAR_M, "soft_m": SOFT_M, "sides": {}}
    for s in "lr":
        out["sides"][s] = table(z["V"].astype(float), Vr.astype(float), z["T"], z["src"], z["J"], z["W"], Wb, Wr, names, s)
    if max(out["sides"][s]["_dr_max_mm"] for s in "lr") < 1e-3:
        return None
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = build(os.path.abspath(args[0]))
    if d is None:
        print("no data (no ref body, or no change)")
    else:
        for s, v in d["sides"].items():
            D = np.asarray(v["dr"]) * 1000
            print(s, "dr mm max", v["_dr_max_mm"], "kept", v["_kept"], "by t (max over theta):", np.round(np.abs(D).max(1), 1).tolist())
        if "--json" in sys.argv:
            json.dump(d, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
