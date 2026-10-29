"""Her shoulder join reweighted so a raised arm doesn't look plugged in (Body 8, 24 Oct 2026; the judge's fix 1):

    SHOULDER_REWEIGHT=1 python tools/assets/shoulder_reweight_post.py <in heroine.glb> <out heroine.glb>

Run LAST, after pit_hollow_post.py (its shapes and the 8 weights a point, JOINTS_1/WEIGHTS_1, kept). Weights only:
positions, normals, shapes and the bind pose untouched. Without SHOULDER_REWEIGHT=1 it copies the body unchanged.

Measured on the body of record (Body 8): the arm-ness of her join's skin (below, e) stepped across the front-shoulder
pocket and the pec's upper-outer edge into the arm's underside (front line: the clavicle 0.43 -> 0.05 and the share 0.18
-> 0.55 in ~70 mm, with kinks; the chest's edge onto twist_01/02 in ~40 mm), so a raised arm creased there (the
owner's front-shoulder crease, the pinched pit); over the cap's top the clavicle plateaued at 0.5-0.65 for 40 mm,
then fell to 0.07 in 44 mm. Per side, in her rest space, within REACH of the shoulder joint, in front of BACK_Z (her
shoulder blade's skin, which creased nothing, kept), on the welded body:

1. arm-ness e = (her humerus bones: the upper arm, its twist chain, delt + half the share bone) / all, the point's
   place between her girdle/torso and her humerus. Eased over her surface (SMOOTH passes of half toward the mean of
   its neighbours, ~3 mm a pass), so no step is sharper than the passes' span: fix (a)'s spread and (b)'s band in one.
2. the cap's top on the delt (fix (a)): on the cap's top-outer side (DELT_C: the cosine to it about the humerus,
   from, full; as shoulder_rig_post's delt mask) and along the humerus (DELT_T, m from the joint: in, full, full, out),
   the delt helper takes at least DELT of the humerus' weight there, from the twist chain (the same motion below the
   helpers' A 60: her idles and the Look don't move). At A 110+ its bulge then lifts the cap's top instead of only the
   belly below it: the cap's sink (-4 mm over ~70 mm of the top line, the notch) next to the bulge (+4-5 mm, the mound)
   becomes one rise from the acromion onto the deltoid.
3. the share kept as it was (capped at 2 min(e, 1 - e), so the humerus never goes negative); the humerus e - share/2
   over its bones (twist chain, delt) in the proportions it had (twist_01 if none); the rest 1 - e - share/2 back to
   her clavicle/trap and torso bones (spine_03 with the pit's dome, pec, lat, scap, breast) in their proportions.
Then eight bones a point (shoulder_rig_post.merge_cap), all eight summing to 1. The sides are mirror twins (each
side's masks the left's, x mirrored). Her bind pose is unchanged; an idle or the Look (arms 20-55 deg from her A 38
rest) moves up to ~2-3 mm where e moved (measured on Godot pose dumps).
(Tried: a clavicle -> share -> humerus "ladder" on the cap, the share 2 min(e, 1 - e): every crease got worse; e itself
raised on the cap's top, e^(1/2): the sink moved toward the neck and doubled. DELT 1.0 grew the mound.)"""
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
sys.path.insert(0, HERE)
from scap_rig_post import Glb, _S  # noqa: E402
from shoulder_rig_post import merge_cap, rest_globals, smoother  # noqa: E402
from wrap_post import skin_union  # noqa: E402
import helpers as hp  # noqa: E402

_E = os.environ.get
REACH = [float(v) for v in _E("REWEIGHT_REACH", "0.10,0.15").split(",")]   # m from the joint: full, none past
SMOOTH = int(_E("REWEIGHT_SMOOTH", 12))                                     # passes easing e over her surface
DELT = float(_E("REWEIGHT_DELT", 0.8))                                      # the delt's least share of the humerus' on the cap
DELT_C = [float(v) for v in _E("REWEIGHT_DELT_C", "0.0,0.6").split(",")]    # the cap's top-outer side: cosine from, full
DELT_T = [float(v) for v in _E("REWEIGHT_DELT_T", "-0.06,0.0,0.12,0.16").split(",")]   # m along the humerus: in, full, full, out
BACK_Z = [float(v) for v in _E("REWEIGHT_BACK_Z", "-0.09,-0.06").split(",")]  # z: none behind, full in front (her blade kept)


def _groups(names, s):
    """column ids per side: humerus H (upper arm, its twist chain, delt), share S, the rest of the join O"""
    H = [i for i, n in enumerate(names) if n in (f"upperarm_{s}", f"delt_{s}") or n.startswith("upperarm_twist_") and n.endswith("_" + s)]
    S = names.index(f"upperarm_share_{s}")
    tw1 = names.index(f"upperarm_twist_01_{s}")
    return H, S, tw1


def masks(U, Grest, s):
    """(zone [V], cap [V]: the delt's least share of the humerus' weight) for side s at her welded rest points U."""
    sg = 1.0 if s == "l" else -1.0
    J, E = Grest["upperarm_" + s][:3, 3], Grest["lowerarm_" + s][:3, 3]
    h = (E - J) / np.linalg.norm(E - J)
    top = np.array([abs(h[1]) * sg, abs(h[0]), 0.0])          # square to the humerus, up and out (as the delt's mask)
    v = U - J
    r = v - (v @ h)[:, None] * h
    cc = (r @ top) / np.maximum(np.linalg.norm(r, axis=1), 1e-9)
    d = np.linalg.norm(v, axis=1)
    zone = (1 - _S((d - REACH[0]) / (REACH[1] - REACH[0]))) * (U[:, 0] * sg > 0.02) * _S((U[:, 2] - BACK_Z[0]) / (BACK_Z[1] - BACK_Z[0]))
    t = v @ h
    cap = DELT * _S((cc - DELT_C[0]) / (DELT_C[1] - DELT_C[0])) * _S((t - DELT_T[0]) / (DELT_T[1] - DELT_T[0]))         * (1 - _S((t - DELT_T[2]) / (DELT_T[3] - DELT_T[2])))
    return zone, cap


def reweight(U, F, D, names, Grest, sm=None):
    """Dense weights D [V, J] on her welded points U (faces F) with each side's join rewritten."""
    D = D.copy()
    sm = sm or smoother(F, SMOOTH)
    for s in "lr":
        H, S, tw1 = _groups(names, s)
        dl = names.index(f"delt_{s}")
        hd = [i for i in H if i != dl]
        zone, cap = masks(U, Grest, s)
        tot = D.sum(1)
        h, sh = D[:, H].sum(1), D[:, S]
        e0 = (h + 0.5 * sh) / np.maximum(tot, 1e-9)
        k = zone > 1e-4
        e = e0 + zone * (sm(e0) - e0)                           # (smoothed over the whole body, used in the zone)
        e = np.clip(e, 0, 1)
        s1 = np.minimum(sh / np.maximum(tot, 1e-9), 2 * np.minimum(e, 1 - e))
        h1 = e - 0.5 * s1
        o1 = 1 - h1 - s1
        for v in np.nonzero(k)[0]:
            w = D[v] / tot[v]
            oc = np.ones(len(names), bool)
            oc[H] = False
            oc[S] = False
            wo, wh = w[oc], w[H]
            new = np.zeros(len(names))
            new[S] = s1[v]
            if wh.sum() > 1e-6:
                new[H] = h1[v] * wh / wh.sum()
            else:
                new[tw1] = h1[v]
            c = cap[v] * zone[v] * h1[v]                        # (the cap's top on the delt: its bulge fills the dip)
            if new[dl] < c and new[hd].sum() > 1e-9:
                new[hd] *= max(new[hd].sum() - (c - new[dl]), 0) / new[hd].sum()
                new[dl] = h1[v] - new[hd].sum()
            if wo.sum() > 1e-6:
                new[oc] = o1[v] * wo / wo.sum()
            else:                                               # (all arm before: the rest to the clavicle)
                new[names.index(f"clavicle_{s}")] = o1[v]
            D[v] = tot[v] * new                                 # (e is eased in by the zone: at its edge new = w)
    return D


def run(src, dst):
    G = Glb(src)
    g = G.g
    U, F, J8, W8, wid = skin_union(G)
    names, _, Grest = rest_globals(G)
    D = np.zeros((len(U), len(names)))
    np.add.at(D, (np.repeat(np.arange(len(U)), J8.shape[1]), J8.ravel()), W8.ravel())
    D2 = reweight(U, F, D, names, Grest)
    frames = hp.shoulder_rest(Grest)
    D2 = merge_cap(D2, names, frames, cap=8)
    ch = np.abs(D2 - D).max(1)
    print("REWEIGHT points changed > 0.01:", int((ch > 0.01).sum()), "max", round(float(ch.max()), 3))
    hn = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    prims = [p for p in g["meshes"][hn["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        at = p["attributes"]
        n = g["accessors"][at["POSITION"]]["count"]
        Dp = D2[wid[o:o + n]]
        o += n
        top = np.argsort(-Dp, 1, kind="stable")[:, :8]
        tw = np.clip(np.take_along_axis(Dp, top, 1), 0, None)
        tw[tw < 1e-5] = 0
        tw /= tw.sum(1, keepdims=True)
        top[tw == 0] = 0
        G.put(at["JOINTS_0"], top[:, :4])
        G.put(at["WEIGHTS_0"], tw[:, :4].astype(np.float32))
        G.put(at["JOINTS_1"], top[:, 4:])
        G.put(at["WEIGHTS_1"], tw[:, 4:].astype(np.float32))
    g["asset"].setdefault("extras", {})["shoulder_reweight"] = {"reach": REACH, "smooth": SMOOTH, "delt": DELT, "delt_c": DELT_C, "delt_t": DELT_T, "back_z": BACK_Z}
    G.save(dst)
    print("REWEIGHT ->", dst)


if __name__ == "__main__":
    if _E("SHOULDER_REWEIGHT", "0") != "1":
        shutil.copyfile(sys.argv[1], sys.argv[2])
        print("REWEIGHT off (SHOULDER_REWEIGHT=1 builds it): copied")
    else:
        run(sys.argv[1], sys.argv[2])
