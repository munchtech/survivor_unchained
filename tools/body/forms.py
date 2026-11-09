"""Her forms on the base, at build time (pipeline.run, after stage 2's placement): the slider body joined under the
head, then her residual. Pure numpy.

    compose(base, pl, spec, rep) -> base with V replaced (MakeHuman space, every point: skin and helpers)
1 join      with "sliders" (mh_base made Vs, the slider body): its change from V (the head's human: v1's woman, whose
            head A carries) taken with its mean at the neck under the head ring (the band 0..4 cm under SPLIT) taken
            off, so the slider body hangs from the head as it is; none of it within `HOLD_M` of SPLIT, all of it
            `EASE_M` lower (smoothstep): the head and its ring's neighbours stay v1's to the bit, so the placement and
            the head's correspondence (stage 2) hold and the ring stays exact;
2 stance    with "stance" ({"pitch_deg": a, "move_m": [0, y, z]}, MakeHuman space: z up, her front -y): the body under
            the head turned a degrees about her left-right axis through the neck's middle (the band 0..4 cm under
            SPLIT), then moved, eased in as 1 is (her trunk stands further forward under her head than MakeHuman's:
            a posture, not a form, so it is two numbers and not a residual);
3 residual  with "forms" (an npz in tools/body/forms/, made by wrap.py): D [N,3], a move per base point (MakeHuman
            space; the helpers' too, so the skeleton's landmarks follow it), added; and E [n2,3], its detail per close
            point (the subdivided tier, placed: Blender axes), which stage 3 adds after the ring's snap (0 on the ring,
            so the head ring stays exact; it carries what the base's resolution cannot: the neck under the ring and
            her forms below a few mm; the skeleton reads D's landmarks, not E's);
4 mirror    the change (1 to 3; E is mirrored as made) made exactly symmetric (each point with a mirror: the mean of its change and its
            mirror's, mirrored); V itself is untouched where nothing changed (base_woman.json builds v1 to the bit).
"""
import os

import numpy as np

import headmatch as hm

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HOLD_M = 0.015
EASE_M = 0.06


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def split_depth(V, pl):
    """How far under SPLIT each point is (m, positive below), placed as the head is."""
    return -hm.s_split(hm.place(V, pl["sim"]))


def join_weight(V0, pl):
    return smooth01((split_depth(V0, pl) - HOLD_M) / EASE_M)


def mirror_pairs(P, tol=1e-4):
    from scipy.spatial import cKDTree
    d, k = cKDTree(P).query(P * np.array([-1.0, 1, 1]))
    return np.where(d < tol, k, -1)


def symmetrize(V, pairs):
    out = V.copy()
    ok = pairs >= 0
    out[ok] = 0.5 * (V[ok] + V[pairs[ok]] * np.array([-1.0, 1, 1]))
    return out


def join(V0, Vs, inbody, pl):
    d = Vs - V0
    dep = split_depth(V0, pl)
    neck = inbody & (dep > 0) & (dep < 0.04)
    t = d[neck].mean(0)
    t[0] = 0.0
    return V0 + join_weight(V0, pl)[:, None] * (d - t), t


def neck_mid(V0, inbody, pl):
    dep = split_depth(V0, pl)
    c = V0[inbody & (dep > 0) & (dep < 0.04)].mean(0)
    c[0] = 0.0
    return c


def stance(V, V0, inbody, pl, st):
    a = np.radians(st.get("pitch_deg", 0.0))
    R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    c = neck_mid(V0, inbody, pl)
    to = (V - c) @ R.T + c + np.asarray(st.get("move_m", [0, 0, 0]), float)
    w = join_weight(V0, pl)[:, None]
    return V + w * (to - V)


def compose(base, pl, spec, rep):
    V0 = base["V"]
    V = V0.copy()
    info = {}
    if "Vs" in base:
        V, t = join(V0, base["Vs"], base["inbody"], pl)
        info["sliders"] = spec.get("sliders", {})
        info["neck_shift_m"] = [round(float(x), 5) for x in t]
    if spec.get("stance"):
        V = stance(V, V0, base["inbody"], pl, spec["stance"])
        info["stance"] = spec["stance"]
    if spec.get("forms"):
        z = np.load(os.path.join(REPO, spec["forms"]))
        D = z["D"]
        assert D.shape == V.shape, "the residual is per base point"
        V = V + D
        if "E" in z.files:
            out_E = z["E"]
            info["detail_max_mm"] = round(float(np.linalg.norm(out_E, axis=1).max()) * 1000, 2)
        info["forms"] = spec["forms"]
        info["residual_max_mm"] = round(float(np.linalg.norm(D, axis=1).max()) * 1000, 2)
    pairs = mirror_pairs(V0)
    V = V0 + symmetrize(V - V0, pairs)
    info["mirror_pairs"] = int((pairs >= 0).sum())
    rep["forms"] = info
    out = dict(base)
    out["V"] = V
    if spec.get("forms") and "E" in z.files:
        out["E"] = out_E
    return out
