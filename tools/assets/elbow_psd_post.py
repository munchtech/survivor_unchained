"""Her elbow as it bends: pose-space correctives (Body 19 solver 2, 27 Oct 2026; the owner on a town close-up of her
bent right arm: "that bend still just dosn't look feminine OR athletic - it just looks clunky", and at elbow 30-40:
the same hard V at the inner crease).

Linear skinning there (tools/anim/elbow_sweep.py): the upper arm's front unmoved to t .85 (no biceps bunching), the
front at t .95 in 5-10 mm (the V), the outer side caved (-9 mm at 90, -29 at 145), the elbow's volume -9% at 90 and
-29% at 145. A bone can't make a crease or a bunching muscle: these are pose-space shapes.

Shapes (morph targets on heroine.glb's body, per side _l/_r, each side authored on its own skin): elbow_psd45,
elbow_psd90, elbow_psd135: the elbow FLEXED that many degrees (helpers.flexion: the forearm's line about its own X,
the hinge her clips bend about; her clips' small "bends" are mostly the forearm swung sideways onto the humerus' line,
not flexion), the forearm swung DEV toward the humerus' line as her clips carry it at that flexion. At each sample:
her rest with that forearm turned there, her helpers driven as HerJoints drives them, elbow_point at its weight. The
target there: the posed skinned mesh made smooth and volume-keeping round the elbow, delta-mush style (the posed mesh
smoothed, the rest's detail put back in each point's local frame; less of it at the back, where the point bone makes
the olecranon), then SCULPTED along the posed normal: the biceps' belly bunched and moved up the arm, the forearm's
masses below the crease, the crease itself (a short soft groove on the bend's bisector, its lips rolled), the
olecranon's point and the epicondyles. The move wanted there is carried back to bind space through the inverse of each
point's blended skin matrix, so at the sample it is exactly that target and between samples it rides with the skin.

HerJoints drives them as in-betweens of the flexion (helpers.SPEC "correctives", keys [lo, at, hi]: 0 at lo, whole at
`at`, 0 again at hi; the last holds past 135), linear between: 0 at flexion 0 and below, so a straight arm is
bit-identical. elbow_point_{s} is KEPT (its drive and its garment copies as before); these shapes are authored on top
of it.

    python tools/assets/elbow_psd_post.py IN.glb [OUT.glb] [--dry]
Idempotent: done-mark elbow_psd (a marked body is copied unchanged). Bare body only (outfits: a follow step, later).
"""
import json
import math
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from wrap_post import skin_union  # noqa: E402
from worn_reaver_post import _sparse, _vn, _ss  # noqa: E402
from shoulder_psd_post import Rig, _q2m, _mq, _blend, _adj, _smooth, delta_mush, untangle, body_morphs  # noqa: E402

MARK = "elbow_psd"
_E = os.environ.get
SAMPLES = (45.0, 90.0, 135.0)
NAMES = ("elbow_psd45", "elbow_psd90", "elbow_psd135")
# her clips' forearm swung toward the humerus' line at that flexion (deg; Body 19's clip census: 15-18 below 70,
# 8-13 at 70-100, 0-5 past 100)
DEV = {45.0: 16.0, 90.0: 10.0, 135.0: 3.0}
DMI = int(_E("EPSD_DM", 40))          # delta mush rounds (her arm's edges ~4.7 mm: about 2 cm of smoothing)
DM_BACK = float(_E("EPSD_BACK", 0.0))  # the delta mush's share at the elbow's back (|phi| past 130: the share and point
#                                       bones' round and the olecranon are the rig's; smoothing them took volume)
REACH_UP, REACH_FORE = 0.11, 0.11      # m from the elbow joint up the humerus / down the forearm: whole, then fading
FADE = 0.04
# the sculpt per sample (mm; t up the humerus from the shoulder in humerus lengths, t2 down the forearm in forearm
# lengths from the elbow; phi deg round the arm: 0 front, 90 out, 180 back, -90 in)
SCULPT = {
    45.0: dict(bic=2.0, bic_t=0.62, bic_lo=0.3, fore=1.0, crease=0.8, lip=0.5, ole=1.5, epi=0.6, vol=0.8),
    90.0: dict(bic=3.5, bic_t=0.58, bic_lo=0.5, fore=2.0, crease=1.6, lip=0.9, ole=3.0, epi=1.0, vol=2.5),
    135.0: dict(bic=3.5, bic_t=0.56, bic_lo=0.3, fore=1.5, crease=2.0, lip=1.0, ole=2.5, epi=1.0, vol=4.0),
}
if _E("EPSD_SCULPT"):
    for k, v in json.loads(_E("EPSD_SCULPT")).items():
        SCULPT[float(k)].update(v)
CREASE_W, LIP_AT, LIP_W, CREASE_ARC = 4.0, 7.5, 3.5, 75.0   # mm, mm, mm, deg either side of the bend's inside


def _bw(x):
    x = np.clip(1 - np.asarray(x, float) ** 2, 0, None)
    return x * x


def _wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def flex_pose(rig, s, flex, dev):
    """Bone globals for her rest with forearm s flexed `flex` deg about its own X and swung `dev` toward the humerus'
    line, her helpers driven as HerJoints drives them; and elbow_point's weight there."""
    import helpers as hp
    from rig import Skeleton, qbetween, qmul
    I = rig.index
    rot, pos, scl = rig.rest_rot.copy(), rig.rest_pos.copy(), rig.rest_scl.copy()
    M0 = rig.fk(rot, pos, scl)
    la, ua = I[f"lowerarm_{s}"], I[f"upperarm_{s}"]
    hum = M0[la, :3, 3] - M0[ua, :3, 3]
    R = M0[la, :3, :3] / np.linalg.norm(M0[la, :3, :3], axis=0)
    sx = math.copysign(1.0, float(hum @ R[:, 0]))
    f, d = math.radians(flex), math.radians(dev)
    want = np.array([sx * math.sin(d), math.cos(d) * math.cos(f), math.cos(d) * math.sin(f)])
    rot[la] = qmul(rig.rest_rot[la], qbetween([0, 1.0, 0], want))
    sk = Skeleton(names=rig.names, parent=rig.parent, rest_rot=rig.rest_rot.copy(), rest_pos=rig.rest_pos.copy())
    sk.index = dict(I)
    hs, hh = np.ones((len(rig.names), 3)), np.zeros((len(rig.names), 3))
    rot = hp.drive(sk, rot, hs, hh)
    for j in range(len(rig.names)):
        if np.any(hs[j] != 1) or np.any(hh[j] != 0):
            scl[j] = scl[j] * hs[j]
            pos[j] = pos[j] + _q2m(rot[j]) @ hh[j]
    w = {k: v for k, v in hp.corrective_weights(sk, rot).items() if k.startswith("elbow_point")}
    return rig.fk(rot, pos, scl), w, hp.flexion(sk, rot, f"lowerarm_{s}")


def charts(U, M0, I, s):
    """Rest charts: upper arm (t from the shoulder joint in humerus lengths, phi), forearm (t2 from the elbow in forearm
    lengths, phi2); phi 0 front, 90 out, 180 back, -90 in."""
    sh, el, wr = (M0[I[n + "_" + s], :3, 3] for n in ("upperarm", "lowerarm", "hand"))
    sd = 1.0 if s == "l" else -1.0
    out = []
    for O, E in ((sh, el), (el, wr)):
        L = np.linalg.norm(E - O)
        ax = (E - O) / L
        f = np.array([0, 0, 1.0]) - ax * ax[2]
        f /= np.linalg.norm(f)
        lat = np.cross(f, ax) * -sd
        lat = lat if lat[0] * sd > 0 else -lat
        rel = U - O
        t = rel @ ax / L
        q = rel - np.outer(rel @ ax, ax)
        out.append((t, np.degrees(np.arctan2(q @ lat, q @ f)), np.linalg.norm(q, axis=1), L))
    return out


def author(G, s, log=print):
    U, F, J, W, wid = skin_union(G)
    rig = Rig(G)
    I = rig.index
    M0 = rig.fk(rig.rest_rot, rig.rest_pos, rig.rest_scl)
    E = np.abs(M0 @ rig.ibm - np.eye(4)).max((1, 2))
    for j in np.nonzero(E > 1e-3)[0]:
        assert rig.names[j] in ("Head",), "the glb's joints don't match its bind"
        rig.ibm[j] = np.linalg.inv(M0[j])
    mor = body_morphs(G, wid, len(U))
    A, deg = _adj(F, len(U))
    nb = A.indices[A.indptr[:-1]]
    sd = 1.0 if s == "l" else -1.0
    wsum = lambda pre: sum((W * (J == j)).sum(1) for n, j in I.items()  # noqa: E731
                           if n.endswith("_" + s) and n.split("_")[0] in pre)
    armw = wsum(("upperarm", "lowerarm", "hand"))
    (t, phi, r, L), (t2, phi2, r2, L2) = charts(U, M0, I, s)
    el0 = M0[I[f"lowerarm_{s}"], :3, 3]
    up_d, fo_d = (1 - t) * L, t2 * L2           # m from the elbow up the humerus / down the forearm
    along = np.where(t2 > 0, fo_d, up_d)
    reach = np.where(t2 > 0, REACH_FORE, REACH_UP)
    reg = (1 - _ss((along - reach) / FADE)) * _ss((armw - 0.5) / 0.4) * (sd * U[:, 0] > 0.05)
    reg *= np.linalg.norm(U - el0, axis=1) < 0.25
    reg = _smooth(reg[:, None], A, deg, 4)[:, 0]
    active = reg > 1e-3
    grow = _smooth(active[:, None].astype(float), A, deg, DMI + 4)[:, 0] > 0
    upper = t2 <= 0.0
    out = {}
    for flex, name in zip(SAMPLES, NAMES):
        M, wep, fl = flex_pose(rig, s, flex, DEV[flex])
        Ur = U + sum(w * mor.get(k, 0) for k, w in wep.items())
        Bm = _blend(J, W, M @ rig.ibm)
        X = np.einsum("nij,nj->ni", Bm, np.c_[Ur, np.ones(len(U))])[:, :3]
        T = delta_mush(Ur, X, F, A, deg, nb, DMI, grow)
        # (the back keeps DM_BACK of it: the point bone's olecranon is the rig's; |phi| past 120 is the back)
        ph = np.where(upper, phi, phi2)
        kdm = 1 - (1 - DM_BACK) * _ss((np.abs(ph) - 90) / 40)
        Dp = (T - X) * (reg * kdm)[:, None]
        # the sculpt, along the posed normal, in the posed elbow's frame
        c = SCULPT[flex]
        Y = X + Dp
        Ny = _vn(Y, F)
        bic = c["bic"] * _bw((t - c["bic_t"]) / 0.2) * _bw(_wrap(phi + 8) / 55) * upper
        bic -= c["bic_lo"] * _bw((t - 0.86) / 0.07) * _bw(phi / 50) * upper
        fore = c["fore"] * _bw((t2 - 0.2) / 0.16) * _bw(_wrap(phi2 - 25) / 65) * (t2 > 0)
        # the crease: on the bend's bisector (the plane through the joint between the humerus and the forearm)
        ce = M[I[f"lowerarm_{s}"], :3, 3]
        uu = M[I[f"upperarm_{s}"], :3, 3] - ce
        uu /= np.linalg.norm(uu)
        ff = M[I[f"hand_{s}"], :3, 3] - ce
        ff /= np.linalg.norm(ff)
        nbis = uu - ff
        nbis /= np.linalg.norm(nbis)
        dlt = (Y - ce) @ nbis * 1000
        inside = uu + ff
        inside = inside / max(np.linalg.norm(inside), 1e-9)
        rel = Y - ce
        rel_p = rel - np.outer(rel @ nbis, nbis)
        cosang = (rel_p @ inside) / np.maximum(np.linalg.norm(rel_p, axis=1), 1e-9)
        arc = _bw(np.degrees(np.arccos(np.clip(cosang, -1, 1))) / CREASE_ARC)
        near = 1 - _ss((np.linalg.norm(rel, axis=1) - 0.055) / 0.02)
        crease = (-c["crease"] * np.exp(-0.5 * (dlt / CREASE_W) ** 2)
                  + c["lip"] * np.exp(-0.5 * ((np.abs(dlt) - LIP_AT) / LIP_W) ** 2)) * arc * near
        # the olecranon's point (the back at the joint's line, up the bend's outside) and the epicondyles
        back = _bw(np.degrees(np.arccos(np.clip(-cosang, -1, 1))) / 35) * _bw(dlt / 14)
        ole = c["ole"] * back * (1 - _ss((np.linalg.norm(rel, axis=1) - 0.045) / 0.02))
        epi = c["epi"] * (_bw(_wrap(phi - 100) / 30) + 1.3 * _bw(_wrap(phi + 100) / 30)) * _bw((t - 0.97) / 0.06) * upper
        # the outer elbow's volume: the corner's sides and back, where the bend presses it in, filled out round the joint
        side = _ss((np.abs(ph) - 60) / 40)
        vol = c["vol"] * side * (1 - _ss((np.linalg.norm(rel, axis=1) - 0.035) / 0.03)) * (1 - 0.6 * back)
        h = (bic + fore + crease + ole + epi + vol) * 1e-3 * reg
        Dp = Dp + Ny * h[:, None]
        Dp = _smooth(Dp, A, deg, 2, grow)
        Dp, nf0, nf1 = untangle(X, Dp, F, A, deg, grow, reg)
        Dp[~active] = 0
        Db = np.einsum("nij,nj->ni", np.linalg.inv(Bm[:, :3, :3]), Dp)
        Db[np.linalg.norm(Db, axis=1) < 1e-6] = 0
        dn = (Dp * _vn(X, F)).sum(1)
        log("ELBOW_PSD %s_%s (flexion %.1f, elbow_point %s): folds %d -> %d; %d points, most %.1f mm, out %.1f in %.1f mm"
            % (name, s, fl, {k: round(v, 2) for k, v in wep.items()}, nf0, nf1, int((np.abs(Db).max(1) > 0).sum()),
               1000 * np.linalg.norm(Dp, axis=1).max(), 1000 * dn.max(), -1000 * dn.min()))
        out[name] = Db
    return out, (U, F, wid)


def main(a):
    args = [x for x in a if not x.startswith("--")]
    src = args[0]
    dst = args[1] if len(args) > 1 else src
    G = _Gl(src)
    g = G.g
    if MARK in ((g.get("asset") or {}).get("extras") or {}):
        print("ELBOW_PSD: already on", src)
        if dst != src:
            shutil.copyfile(src, dst)
        return
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    shapes = []
    per = {s: author(G, s) for s in "lr"}
    U, F, wid = per["l"][1]
    for n in NAMES:
        shapes += [(n + "_l", per["l"][0][n]), (n + "_r", per["r"][0][n])]
    if "--dry" in a:
        np.savez_compressed(dst + ".npz", **{n: D for n, D in shapes})
        return
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    for name, D in shapes:
        dN = _vn(U + D, F) - _vn(U, F)
        o = 0
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = wid[o:o + n]
            Dp = D[w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dN[w]
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dN[w]).max(1) > 1e-5)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 0)[0]
            p.setdefault("targets", []).append({"POSITION": _sparse(g, binb, n, ip, Dp[ip]),
                                                "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            o += n
        mesh.setdefault("extras", {}).setdefault("targetNames", []).append(name)
        mesh["weights"] = list(mesh.get("weights", [])) + [0]
    g.setdefault("asset", {}).setdefault("extras", {})[MARK] = {
        "samples": list(SAMPLES), "dev": {str(k): v for k, v in DEV.items()}, "dm_iters": DMI, "dm_back": DM_BACK,
        "sculpt": {str(k): v for k, v in SCULPT.items()}}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("ELBOW_PSD: written", dst)


if __name__ == "__main__":
    main(sys.argv[1:])
