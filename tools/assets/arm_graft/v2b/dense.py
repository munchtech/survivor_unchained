# Body 2 B step 1: both arms of her ORIGINAL mesh densified with her own UVs (no bake).
#   python dense.py <her.npz (b_dump of heroine_built.blend)> <out dense.npz> [split thr m, default 0.0075]
# Region per side: skin faces whose every vertex is on that side, carries arm weight (upperarm+lowerarm > 0.003) or
# clavicle (> 0.15, |x| > 7.5 cm), hand < 0.3, and is not on the neck graft. Inside it: long edges split (midpoints of
# her edges lie on her surface), Delaunay flips inside each UV island, tangential relax with every moved vertex
# located again on ITS island of her original surface; island seams, sharp edges and the region border are locked.
# Corner UVs and weights are then read off her original surface at each vertex's exact location (barycentric).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
from lib import load, tri_split
from remesh import islands, Ref, Work

d = load(sys.argv[1]); out = sys.argv[2]; thr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0075
P = d["P"]; nm = d["names"]; VG = d["VG"]; uv = d["uv"]; mi = d["mi"]; polys = d["polys"]; nv = len(P)
T_all, src, cidx = tri_split(polys)
sharp_e = d["ev"][d["sharp"]]
newP = P.copy(); addP = []; addVG = []; region_flag = np.zeros(nv, int)
keep_poly = np.ones(len(polys), bool); new_tris = []; new_uv = []
for sd, flag in (("r", 1), ("l", 2)):
    g = lambda n: VG[:, nm.index(n + "_" + sd)]
    side = np.sign(P[:, 0]) == (-1 if sd == "r" else 1)
    vm = side & ((g("upperarm") + g("lowerarm") > 0.003) | ((g("clavicle") > 0.15) & (np.abs(P[:, 0]) > 0.075))) & (g("hand") < 0.3) & (d["graft"] == 0)
    pin = np.array([vm[p].all() and mi[k] == 0 for k, p in enumerate(polys)])
    keep_poly &= ~pin
    tri = pin[src]; T0g = T_all[tri]; UV0 = uv[cidx[tri]]
    vid = np.unique(T0g); loc = -np.ones(nv, int); loc[vid] = np.arange(len(vid))
    T0 = loc[T0g]; V0 = P[vid]
    FI = islands(T0, UV0)
    # border: vertices also used by faces outside the region; sharp-edge vertices
    outside = np.zeros(nv, bool)
    for k in np.nonzero(~pin)[0]: outside[polys[k]] = True
    locked = outside[vid].copy()
    se = sharp_e[(loc[sharp_e] >= 0).all(1)]; locked[loc[se].ravel()] = True
    ref = Ref(V0, T0, UV0, FI)
    w = Work(V0, T0, FI, locked, ref)
    def stats(tag):
        V, T = w.V, w.T; e = np.c_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]].reshape(-1, 2); e.sort(1); e = np.unique(e, axis=0)
        L = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1) * 100
        a = []
        for i in range(3):
            u = V[T[:, (i + 1) % 3]] - V[T[:, i]]; v = V[T[:, (i + 2) % 3]] - V[T[:, i]]
            a.append(np.degrees(np.arctan2(np.linalg.norm(np.cross(u, v), axis=1), (u * v).sum(1))))
        a = np.min(a, 0); val = np.bincount(T.ravel(), minlength=len(V))
        free = ~w.locked
        H, tw = w.edges(); bo, isl = w.seam_mask(H, tw); LH = np.linalg.norm(V[H[:, 0]] - V[H[:, 1]], axis=1) * 100
        lg = LH > 1.2; fb = np.zeros(len(T), bool); fb[(np.arange(len(H)) // 3)[bo]] = True
        print("   long>1.2cm half-edges: border %d, seam %d, on border face %d, other %d" % ((lg & bo).sum(), (lg & isl & ~bo).sum(), (lg & ~isl & fb[np.arange(len(H)) // 3]).sum(), (lg & ~isl & ~fb[np.arange(len(H)) // 3]).sum()))
        print("%s %s: verts %d faces %d | edge cm p50 %.2f p95 %.2f max %.2f | min angle p5 %.1f p50 %.1f, <15 deg %d | valence6 %.0f%% (free)"
              % (sd, tag, len(V), len(T), np.median(L), np.percentile(L, 95), L.max(), np.percentile(a, 5), np.median(a), (a < 15).sum(), 100 * (val[free] == 6).mean()))
    print(sd, "islands", len(np.unique(FI)), "locked", int(locked.sum()), "of", len(V0))
    stats("her")
    for it in range(8):
        ns = w.split(thr); nf = w.flip(); w.relax(4)
        print("  pass", it, "split", ns, "flips", nf)
        if ns == 0: break
    w.flip(); w.relax(15, lam=0.4); w.flip(); w.relax(10, lam=0.4)
    stats("dense")
    cuv, cd = w.corner_uv(); fi, bar, dist = w.vertex_anchor()
    print("  locate dist mm: corners max %.4f, vertices max %.4f" % (cd.max() * 1e3, dist.max() * 1e3))
    # weights at each working vertex from her surface (barycentric over her vertex weights)
    Wv = (VG[vid][T0[fi]] * bar[:, :, None]).sum(1)
    n0 = len(V0)
    # global ids: first n0 are her vertices (moved by relax, locked ones in place), the rest new
    gid = np.r_[vid, nv + len(addP) + np.arange(len(w.V) - n0)] if False else None
    base = nv + sum(len(x) for x in addP)
    gid = np.r_[vid, base + np.arange(len(w.V) - n0)]
    newP[vid] = w.V[:n0]; addP.append(w.V[n0:])
    VGn = VG.copy() if not addVG else None
    addVG.append(Wv[n0:])
    VG = VG.copy(); VG[vid] = Wv[:n0]  # (her own rows return unchanged where the vertex did not move)
    region_flag[vid] = flag
    region_flag = np.r_[region_flag, np.full(len(w.V) - n0, flag)]
    new_tris.append(gid[w.T]); new_uv.append(cuv)
P2 = np.vstack([newP] + addP); VG2 = np.vstack([VG] + addVG).astype(np.float32)
# assemble polys: kept polys, then the region triangles
kp = np.nonzero(keep_poly)[0]
fl = [len(polys[k]) for k in kp]; fv = [polys[k] for k in kp]
lsum = np.r_[0, np.cumsum(d["lt"])[:-1]]
uv_k = [uv[lsum[k]:lsum[k] + d["lt"][k]] for k in kp]; cn_k = [d["cn"][lsum[k]:lsum[k] + d["lt"][k]] for k in kp]
NT = np.vstack(new_tris); NU = np.vstack(new_uv)
fl += [3] * len(NT); fv += list(NT)
UVo = np.vstack(uv_k + [NU.reshape(-1, 2)]); CNo = np.vstack(cn_k + [np.zeros((3 * len(NT), 3))])
mat = np.r_[mi[kp], np.zeros(len(NT), int)]
graft = np.r_[d["graft"], np.zeros(len(P2) - nv, int)]
auto = np.r_[region_flag > 0]
fvv = np.concatenate(fv)
# sharp edges still present
E = set()
for p in fv:
    for i in range(len(p)): E.add((min(p[i], p[(i + 1) % len(p)]), max(p[i], p[(i + 1) % len(p)])))
sh = [tuple(sorted(e)) for e in sharp_e.tolist() if tuple(sorted(e)) in E]
np.savez(out, V=P2, fl=np.array(fl), fv=fvv, uv=UVo, cn=CNo, mat=mat, graft=graft, sharp=np.array(sh).reshape(-1, 2),
         W=VG2, names=np.array(nm), region=region_flag, nv0=nv, bn=np.array(d["bn"]), bh=d["bh"], bt=d["bt"])
print("WROTE", out, "verts", len(P2), "(+%d)" % (len(P2) - nv), "faces", len(fl), "sharp kept", len(sh), "of", len(sharp_e))
