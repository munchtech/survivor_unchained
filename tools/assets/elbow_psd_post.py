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
REACH_UP, REACH_FORE = 0.15, 0.14      # m from the elbow joint up the humerus / down the forearm: whole, then fading
FADE = 0.04
# The sculpt per sample (r2, after judge 1: r1's 1-4 mm forms didn't read at the town close-up, ~0.9 px per mm), in mm
# along the posed normal, on one chart continuous across the joint (z mm along the arm, - up the humerus, + down the
# forearm; ang deg round it: 0 front, 90 out, 180 back, -90 in):
#   fill  the posed skin's radial shrink round the joint's sides put back (the side caved by the bend), plus this much
#         on the outer side (never caved);
#   bic   the biceps' belly bunched (~5 mm at 90);
#   br    the brachioradialis/extensor mass (the mobile wad), rising 30-40 mm above the joint on the outer side, over the
#         humerus' lower end, its peak ~25 mm below the joint, spiralling to the thumb side;
#   flex  the flexor-pronator mass from the medial epicondyle, bulging into the biceps (4-6 mm at 90-135);
#   epi   the lateral epicondyle's bump (the medial's 0.8 of it);
#   ole   the olecranon: the elbow's back point brought to this PROMINENCE (mm past the triceps' back line carried on,
#         as tools/anim/elbow_sweep.py measures it), whatever the body gives (a function of the input body), and at
#         least ole_min tall (the corner's round tightened to a point: the measure alone left a round corner);
SCULPT = {
    45.0: dict(fill=1.0, bic=3.0, bic_lo=1.5, fs=3.0, br=2.5, flex=1.5, epi=1.8, flat=0.5, ole=6.5, ole_min=2.5),
    90.0: dict(fill=1.5, bic=5.5, bic_lo=3.0, fs=6.0, br=4.0, flex=3.0, epi=3.0, flat=2.0, ole=6.0, ole_min=7.0),
    135.0: dict(fill=1.5, bic=5.5, bic_lo=0.0, fs=4.0, br=4.0, flex=2.5, epi=3.0, flat=2.0, ole=6.0, ole_min=7.0),
}
if _E("EPSD_SCULPT"):
    for k, v in json.loads(_E("EPSD_SCULPT")).items():
        SCULPT[float(k)].update(v)
BIC_T = 0.62                            # the biceps' bunched belly, humerus lengths from the shoulder


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


def elbow_chart(t, phi, L, t2, phi2, L2):
    """One chart continuous across the joint: z (mm along the arm: - up the humerus, + down the forearm), ang (deg
    round it: 0 front, 90 out, 180 back, -90 in), and bf (0 the humerus' chart, 1 the forearm's; blended over the
    joint's +-15 mm)."""
    zu, zf = (t - 1.0) * L * 1000, t2 * L2 * 1000
    bf = _ss((zf + 15.0) / 30.0)
    pu, pf = np.radians(phi), np.radians(phi2)
    ang = np.degrees(np.arctan2((1 - bf) * np.sin(pu) + bf * np.sin(pf), (1 - bf) * np.cos(pu) + bf * np.cos(pf)))
    return (1 - bf) * zu + bf * zf, ang, bf


def apex_z(X, zm, ang, side, sh, el, flex):
    """The rest z (mm) whose back (ang ~180) lands on the posed outer corner's bisector: round the joint, flex/2 from
    the humerus' back line toward the forearm's (the humerus at rest: flex_pose turns the forearm only)."""
    u = (el - sh) / np.linalg.norm(el - sh)
    f = np.array([0, 0, 1.0]) - u * u[2]
    f /= np.linalg.norm(f)
    m = side & (np.abs(_wrap(ang - 180)) < 15) & (np.abs(zm) < 60)
    rel = X[m] - el
    th = np.arctan2(rel @ u, -(rel @ f))
    zs = np.arange(-50.0, 51.0, 5.0)
    med = np.array([np.median(th[np.abs(zm[m] - z0) < 4]) for z0 in zs])
    med = np.degrees(np.unwrap(med))
    k = np.r_[True, np.diff(med) > 0]          # (monotone near the joint; past a fold, cut)
    k = np.cumprod(k).astype(bool)
    return float(np.interp(flex / 2, med[k], zs[k]))


def _line_dist(X, a, b):
    ax = (b - a) / np.linalg.norm(b - a)
    rel = X - a
    return np.linalg.norm(rel - np.outer(rel @ ax, ax), axis=1)


def prominence(Y, sel, sh, el):
    """The elbow's back point (mm), as tools/anim/elbow_sweep.py olecranon() reads it on the posed arm: the back edge
    (|across| < 25 mm) per 7.5 mm along the humerus from the joint, its most past the upper arm's back line (z -60..-30
    mm) carried on, at z -7.5..+22.5 mm. The humerus at rest here (flex_pose turns the forearm only)."""
    u = (el - sh) / np.linalg.norm(el - sh)
    f = np.array([0, 0, 1.0]) - u * u[2]
    f /= np.linalg.norm(f)
    h = np.cross(u, f)
    rel = Y[sel] - el
    y, z, x = rel @ f, rel @ u * 1000, rel @ h
    near = np.abs(x) < 0.025
    rows = []
    for z0 in np.arange(-60, 31, 7.5):
        k = near & (np.abs(z - z0) < 3.75)
        rows.append((z0, -y[k].min() * 1000 if k.any() else np.nan))
    rows = np.array(rows)
    up = rows[(rows[:, 0] >= -60) & (rows[:, 0] <= -30)]
    cf = np.polyfit(up[:, 0], up[:, 1], 1)
    tip = rows[(rows[:, 0] >= -7.5) & (rows[:, 0] <= 22.5)]
    return float(np.nanmax(tip[:, 1] - np.polyval(cf, tip[:, 0])))


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
    zm, ang, bf = elbow_chart(t, phi, L, t2, phi2, L2)
    side = sd * U[:, 0] > 0.05
    out = {}
    for flex, name in zip(SAMPLES, NAMES):
        M, wep, fl = flex_pose(rig, s, flex, DEV[flex])
        Ur = U + sum(w * mor.get(k, 0) for k, w in wep.items())
        Bm = _blend(J, W, M @ rig.ibm)
        X = np.einsum("nij,nj->ni", Bm, np.c_[Ur, np.ones(len(U))])[:, :3]
        T = delta_mush(Ur, X, F, A, deg, nb, DMI, grow)
        # (the back keeps DM_BACK of it: the point bone's olecranon is the rig's; |phi| past 120 is the back)
        kdm = 1 - (1 - DM_BACK) * _ss((np.abs(ang) - 90) / 40)
        Dp = (T - X) * (reg * kdm)[:, None]
        # the sculpt, along the posed normal (mm), on the elbow's chart (z, ang)
        c = SCULPT[flex]
        Y = X + Dp
        Ny = _vn(Y, F)
        P = {n: M[I[f"{n}_{s}"], :3, 3] for n in ("upperarm", "lowerarm", "hand")}
        # fill: the skin's radial shrink round each bone's line (posed against rest; + caved) put back on the joint's
        # sides and back, plus `fill` on the outer side, kept broad
        ru = _line_dist(Y, P["upperarm"], P["lowerarm"])
        rf = _line_dist(Y, P["lowerarm"], P["hand"])
        shrink = ((1 - bf) * (r - ru) + bf * (r2 - rf)) * 1000
        sides = np.clip(_bw(_wrap(ang - 95) / 85) + 0.8 * _bw(_wrap(ang + 100) / 70), 0, 1)
        zone = _ss((zm + 70) / 25) * (1 - _ss((zm - 15) / 30))
        fill = (np.clip(shrink, 0, 12) + c["fill"] * _bw(_wrap(ang - 95) / 70)) * sides * zone
        fill = _smooth(fill[:, None], A, deg, 10, grow)[:, 0]
        # the masses
        bic = (c["bic"] * _bw((zm + (1 - BIC_T) * L * 1000) / 80) * _bw(_wrap(ang + 5) / 70)
               + c["bic_lo"] * _bw((zm + 38) / 32) * _bw(_wrap(ang) / 60)) * (1 - bf)
        # the forearm's front (what faces the biceps as it bends), swelling from a fold that slants: higher on the
        # outer side, lower on the inner (the medial epicondyle's line)
        top = -5.0 - 15.0 * np.sin(np.radians(ang))
        fs = c["fs"] * _bw((zm - 40) / np.where(zm < 40, 40 - top + 5, 110)) * _bw(_wrap(ang - 10) / 85) * (zm > top - 5)
        a0 = np.clip(45 - 0.3 * zm, 5, 60)
        br = c["br"] * _bw((zm - 30) / np.where(zm < 30, 65, 110)) * _bw(_wrap(ang - a0) / 70)
        fx = c["flex"] * _bw((zm - 35) / np.where(zm < 35, 45, 100)) * _bw(_wrap(ang + 45) / 60)
        epi = c["epi"] * _bw((zm + 8) / 22) * (_bw(_wrap(ang - 100) / 35) + 0.8 * _bw(_wrap(ang + 100) / 35))
        # the outer corner: where the bend's outside turns (the rest z landing on its bisector) the olecranon's point;
        # either side of it the triceps' tendon (above) and the ulna's border (below) eased in, so the round reads as a
        # point between two flat planes, not a pipe's bend
        za = apex_z(X, zm, ang, side, P["upperarm"], P["lowerarm"], flex)
        flat = -c["flat"] * (_bw((zm - za + 24) / 14) + 0.8 * _bw((zm - za - 24) / 14)) * _bw(_wrap(ang - 180) / 55)
        h = fill + bic + fs + br + fx + epi + flat
        # the olecranon: tall enough to bring its prominence to c["ole"], at least c["ole_min"]
        olek = _bw((zm - za) / 16) * _bw(_wrap(ang - 180) / 40)
        sel = (armw > 0.6) & (t > -0.1) & (t < 1.6) & (r < 0.08) & (sd * U[:, 0] > 0.05)
        prom = lambda a: prominence(Y + Ny * ((h + a * olek) * 1e-3 * reg)[:, None], sel,  # noqa: E731
                                    P["upperarm"], P["lowerarm"])
        oa, p0 = 0.0, prom(0.0)
        pr = p0
        for _ in range(3):
            oa = float(np.clip(oa + c["ole"] - pr, c["ole_min"], 9.0))
            pr = prom(oa)
        h = (h + oa * olek) * 1e-3 * reg
        log("ELBOW_PSD %s_%s: olecranon %.1f -> %.1f mm (point %.1f mm at rest z %+.1f); fill most %.1f"
            % (name, s, p0, pr, oa, za, fill.max()))
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
        if _E("EPSD_TABLE"):
            log(_table(zm, ang, dn * 1000, reg > 0.05, "%s_%s: the shape's move along the posed normal (mm, mean)"
                       % (name, s)))
        out[name] = Db
    return out, (U, F, wid)


def _table(zm, ang, v, m, title):
    """A (z, ang) table of v's mean over m (a check for the authoring: EPSD_TABLE=1)."""
    rows = [title, "   z / ang  " + " ".join("%5d" % a for a in range(-150, 181, 30))]
    for z0 in range(-90, 136, 15):
        row = []
        for a0 in range(-150, 181, 30):
            k = m & (np.abs(zm - z0) < 7.5) & (np.abs(_wrap(ang - a0)) < 15)
            row.append("%5.1f" % v[k].mean() if k.sum() > 2 else "    .")
        rows.append("  %4d      " % z0 + " ".join(row))
    return chr(10).join(rows)


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
