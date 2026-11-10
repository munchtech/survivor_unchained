"""region_shape: the SHAPE half of the shoulder target's gate (WIP, T2 solver for lead 14): does a surface keep her shape?

    python tools/body/region_shape.py shift --provider pub|target|lbs_base|a [--poses a,b | --only train,held,extreme | --clip NAME]
    python tools/body/region_shape.py pops  --provider ... --clips run_warden,sword_heavy,p4:bladestorm_loop
    python tools/body/region_shape.py silhouette --provider P [--poses a,b | --only ...] [--views front,back,side,top,game_front,game_back]
    python tools/body/region_shape.py sheets --provider P --poses a,b,c [--views front34,back34,top34,under] [--gate]
    python tools/body/region_shape.py edges --provider carried [--poses a,b] [--over 2.5]     (why edges stretch: cmd_edges,
        classify_edges; the poses and sides of poses.npz, the target of target_a.npz; out edges_carried.json)

Pose names: rest[:s] | x:<extreme>[:s] | <clip>@<frame>[:s] (p4:<clip>@f too); side l by default. Out: tools/body/out/shoulder.
Providers (pose -> whole-body B vertices): pub = published B; target = region_target live (full_target), or target.npz +
  region.npz when the pose is in it; lbs_base = the target's base LBS blended by beta; a = A's own surface (test: 0);
  carried = target_a.npz only (same layout as target.npz; a pose not in the file is an ERROR, never the live target);
  a_self (silhouette, sheets) = the transferred A itself (test: silhouette all 0).
A in the same pose: library clips = A's own dump frame; extremes and p4 clips = A posed by B's driven bone turns from rest
  (A spine_01/02/03 <- B spine_02/03/05, the rest by name).
shift: per band point, the signed distance (mm, + outward) to A's posed surface along A's interpolated normal, minus the
  same at rest. A is brought to B per band by the band's ANCHOR bone (D_B D_A^-1, D = posed global x rest^-1), so a skeleton
  difference (B's girdle law against A's keyed clavicle) is not read as shape. The closest point is searched only on the A
  triangles within RAD 50 mm of the point at rest whose rest normal faces the same way (no jump across the armpit).
Bands (B rest, left topology points inside the region; the right = the twins; disjoint, in this priority):
  fold_front / fold_back  within 3 rows of the seam between the arm class and the torso class (region_target's armv), more
                          than 20 mm below the joint, not on the arm's outer side (lateral < 20 mm), 10 mm in front of /
                          behind the joint: the pectoral edge and the lat edge
  deltoid_cap             within 0.12 m of the shoulder joint, lateral of it, rest normal not facing down (n.up > -0.3)
  trap_line               outside that ball, 30 mm from the midline to the joint, above the joint - 30 mm, n.up > 0.6
  breast_edge             region points within 7 rows (the border ring 3 + blend 4) of the left breast part
silhouette: does the provider keep A's outline? A is ALWAYS A posed by B's bone turns (a_from_B: same bone pose, only shape
  differs), brought onto B at the chest. Binary masks of both in one orthographic window about B's posed shoulder joint
  (SIL: +-0.20 m, 1000 px/m; the camera turns with B's chest). Per outline pixel of the provider's mask inside the window:
  the distance (mm) to the nearest outline pixel of A's mask, + where the pixel lies outside A's mask, - inside. Both masks
  are rendered SIL["margin"] wider than the window so A's nearest outline is never cut by the window's edge. Columns
  p05 / p50 / p95 / min / max; "reg" = the same over the outline pixels whose B triangle touches the shoulder region (the
  whole-window numbers also see the neck, jaw, breast and whatever hand or forearm crosses the window). The REST row (B
  published at rest against A at rest) is printed beside each pose: B's rest outline is not A's, subtract by eye.
  Out: silhouette_<provider>.json {rest, poses, summary}.
sheets: clay pictures, B published | the provider | A (transferred, aligned at the chest), one PNG a pose (rows = views) in
  out/shoulder/sheets plus _half.jpg; --gate adds gate_<provider>_half.jpg (rows = poses, front34 only, 260 px panels).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bends  # noqa: E402
import deform_audit as da  # noqa: E402
import ray  # noqa: E402
import region_target as rt  # noqa: E402
from surfdist import closest_on_tris  # noqa: E402

OUT = rt.OUT
BANDS = ["fold_front", "fold_back", "deltoid_cap", "trap_line", "breast_edge"]
ANCHOR = {"fold_front": "chest", "fold_back": "chest", "deltoid_cap": "upperarm", "trap_line": "clavicle", "breast_edge": "chest"}
RAD, K = 0.05, 64
SPINE = {"spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_05"}
# Her-only choices of silhouette and sheets (the next job moves these to a config). Views are in body coords: (lateral, away
# from the midline on the pose's side; up; front), the direction the camera sits in.
SIL = {"half": 0.20, "px": 1000, "margin": 0.06, "anchor": "chest", "center": "upperarm",
       "views": {"front": (0, 0, 1), "back": (0, 0, -1), "side": (1, 0, 0), "top": (0, 1, 0),
                 "game_front": (0, 0.77, 0.64), "game_back": (0, 0.77, -0.64)}}
SHEET = {"half": 0.20, "panel": 520, "gate_panel": 260, "gate_view": "front34", "default": ["front34", "back34"], "jpg": 88,
         "views": {"front34": (0.5, 0.2, 0.8), "back34": (0.5, 0.3, -0.8), "top34": (0.3, 0.85, 0.4), "under": (0.6, -0.5, 0.6)}}
A_KINDS = ("a", "a_self")
turn = lambda G, R0, j: da.ortho(G[j][:3, :3] @ np.linalg.inv(R0[j][:3, :3]))


class Near:
    """Signed distance of points to a posed mesh, each point against the triangles near it at rest."""

    def __init__(self, P0, N0, bd):
        self.bd, T = bd, bd.T
        c = bd.V0[T].mean(1)
        fn = da.unit(np.cross(bd.V0[T[:, 1]] - bd.V0[T[:, 0]], bd.V0[T[:, 2]] - bd.V0[T[:, 0]]))
        d, i = cKDTree(c).query(P0, k=K, distance_upper_bound=RAD)
        ok = np.isfinite(d)
        i = np.where(ok, i, 0)
        self.ok = ok & (np.einsum("nkj,nj->nk", fn[i], N0) > 0)
        self.tri = T[i]

    def signed(self, P, V):
        """(signed distance [n] m, closest point [n, 3]) of P against the mesh at V."""
        n, k = self.ok.shape
        a, b, c = (V[self.tri[..., j]].reshape(-1, 3) for j in range(3))
        p = np.repeat(P, k, 0)
        q = closest_on_tris(p, a, b, c)
        d = np.where(self.ok.ravel(), np.linalg.norm(p - q, axis=1), np.inf).reshape(n, k)
        j = d.argmin(1) + np.arange(n) * k
        q, t = q[j], self.tri.reshape(-1, 3)[j]
        A_, B_, C_ = V[t[:, 0]], V[t[:, 1]], V[t[:, 2]]
        nt = np.cross(B_ - A_, C_ - A_)
        ar = np.maximum((nt ** 2).sum(1), 1e-30)
        bw = np.stack([np.einsum("ij,ij->i", np.cross(C_ - B_, q - B_), nt), np.einsum("ij,ij->i", np.cross(A_ - C_, q - C_), nt),
                       np.einsum("ij,ij->i", np.cross(B_ - A_, q - A_), nt)], 1) / ar[:, None]
        N = self.bd._normals(V)
        nq = (np.clip(bw, 0, 1)[:, :, None] * N[t]).sum(1)
        nq /= np.maximum(np.linalg.norm(nq, axis=1, keepdims=True), 1e-12)
        sd = np.einsum("ij,ij->i", P - q, nq)
        sd[~self.ok.any(1)] = np.nan
        return sd, q


class Ctx:
    def __init__(self):
        self.B, self.A = da.body("B"), da.body("A")
        self.B.set_layer("full")
        self.A.set_layer("full")
        self.md = md = rt.Model(self.B.p)
        B, A = self.B, self.A
        self.sg = {"l": 1, "r": -1}
        cl = lambda bd, s: bd.p.names[bd.p.parent[bd.p.index[bd.role("upperarm", s)]]]
        self.anch = {s: {"upperarm": (B.role("upperarm", s), A.role("upperarm", s)), "clavicle": (cl(B, s), cl(A, s)),
                         "chest": tuple(bd.p.names[bd.p.parent[bd.p.index[cl(bd, s)]]] for bd in (B, A))} for s in "lr"}
        self.bands = self._bands()
        N0 = B._normals(B.V0)
        self.near, self.sd0, self.q0 = {}, {}, {}
        for s in "lr":
            for b in BANDS:
                v = md.first[self.bands[b][s]]
                nr = self.near[b, s] = Near(B.V0[v], N0[v], A)
                self.sd0[b, s], self.q0[b, s] = nr.signed(B.V0[v], A.V0)
        self._tz = self._cz = self._regtri = None
        self._pub = (None, None)

    def _bands(self):
        B, md = self.B, self.md
        fr, sd = B.frame, md.S["l"]
        ids, n = sd["ids"], md.n
        H = B.head("upperarm_l")
        r = md.V0 - H
        N = B._normals(B.V0)[md.first]
        inr = np.zeros(n, bool)
        inr[ids] = True
        arm = np.zeros(n, bool)
        arm[ids[sd["armv"]]] = True

        def grow(m, rows):
            for _ in range(rows):
                m = m | (md.adj @ m > 0)
            return m
        seam = grow(arm, 1) & grow(inr & ~arm, 1) & inr
        fold = grow(seam, 3) & inr & (r @ fr.up < -0.02) & (r @ fr.lat < 0.02)
        ball = np.linalg.norm(r, axis=1) < 0.12
        topo = np.load(rt.HERE / "out/topo/close.npz", allow_pickle=True)
        breast = (topo["part"] == list(topo["parts"]).index("breast")) & (topo["side"] == 1)
        m = {"fold_front": fold & (r @ fr.front > 0.01), "fold_back": fold & (r @ fr.front < -0.01),
             "deltoid_cap": inr & ball & (r @ fr.lat > 0) & (N @ fr.up > -0.3),
             "trap_line": inr & ~ball & (md.V0 @ fr.lat > 0.03) & (r @ fr.lat < 0) & (r @ fr.up > -0.03) & (N @ fr.up > 0.6),
             "breast_edge": inr & grow(breast, 7)}
        used, out = np.zeros(n, bool), {}
        for b in BANDS:
            l = np.nonzero(m[b] & ~used)[0]
            used[l] = True
            out[b] = {"l": l, "r": md.tw[l]}
        OUT.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(OUT / "bands.npz", **{f"{b}_{s}": v[s] for b, v in out.items() for s in "lr"},
                            **{f"{b}_v{s}": md.first[v[s]] for b, v in out.items() for s in "lr"})
        return out

    # ------------------------------------------------------------------ poses --
    def a_from_B(self, G):
        """A posed by B's driven bone turns from rest."""
        B, A = self.B, self.A
        want = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01"] + [f"{b}_{s}" for s in "lr" for b in ("clavicle", "upperarm", "lowerarm", "hand")]
        turns, done = [], {}
        for an in want:
            bn = SPINE.get(an, an)
            if an not in A.p.index or bn not in B.p.index:
                continue
            Rb = turn(G, B.p.rest, B.p.index[bn])
            k, Rp = A.p.parent[A.p.index[an]], np.eye(3)
            while k >= 0 and k not in done:
                k = A.p.parent[k]
            if k >= 0:
                Rp = done[k]
            turns.append((an, Rb @ Rp.T))
            done[A.p.index[an]] = Rb
        return A.pose_turns(turns)

    def poses(self, names):
        """Yield {name, side, G, A: (V, G)} for pose names (grouped by clip)."""
        B, A, by = self.B, self.A, {}
        for nm in names:
            core, s = (nm[:-2], nm[-1]) if nm[-2:] in (":l", ":r") else (nm, "l")
            if core == "rest":
                yield {"name": nm, "side": s, "G": B.G0, "A": (A.V0, A.G0)}
            elif core.startswith("x:"):
                G = rt.extreme_G(B, core[2:])[0]
                G = G if s == "l" else B.rd.drive(B.p, self.md.mirror_G(G), B.rig)[0]
                yield {"name": nm, "side": s, "G": G, "A": self.a_from_B(G)}
            else:
                c, f = core.rsplit("@", 1)
                by.setdefault(c, {}).setdefault(int(f), []).append((nm, s))
        for c, fs in by.items():
            Gs = {f: G for f, _, G in B.clip_frames(da.load_clip(c), 1) if f in fs}
            Af = {} if c.startswith("p4:") else rt.a_frames(A, c, set(fs))
            for f, lst in fs.items():
                for nm, s in lst:
                    yield {"name": nm, "side": s, "G": Gs[f], "A": Af[f] if f in Af else self.a_from_B(Gs[f])}

    # -------------------------------------------------------------- providers --
    def surface(self, kind, pose):
        B, md, G, s = self.B, self.md, pose["G"], pose["side"]
        if self._pub[0] is not G:
            self._pub = (G, rt.published(B, G))
        Vp = self._pub[1]
        if kind == "pub":
            return Vp
        sd = md.S[s]
        nr = len(sd["ids"])
        if kind == "lbs_base":
            X = md.beta[:, None] * md._lbs(sd, G)[:nr] + (1 - md.beta[:, None]) * Vp[md.first[sd["ids"]]]
        elif kind == "target":
            if self._tz is None:
                self._tz = dict(np.load(OUT / "target.npz")) if (OUT / "target.npz").exists() else {}
                self._ti = {str(n): i for i, n in enumerate(self._tz.get("name", []))}
            i = self._ti.get(pose["name"] if pose["name"][-2:] in (":l", ":r") else pose["name"] + ":l")
            X = self._tz["X"][i] if i is not None and self._tz["X"].shape[1] == nr else md.target(G, Vp[md.first], s)
        elif kind == "carried":
            X = self._carried(pose, nr)
        else:
            raise KeyError(kind)
        g = np.nonzero(sd["loc"][md.src] >= 0)[0]
        g = g[sd["loc"][md.src[g]] < nr]
        V = Vp.copy()
        V[g] = X[sd["loc"][md.src[g]]]
        return V

    def _carried(self, pose, nr):
        """The carried target of a pose from target_a.npz; no fallback."""
        f = OUT / "target_a.npz"
        if self._cz is None:
            if not f.exists():
                raise FileNotFoundError(f"provider carried: {f} does not exist")
            z = np.load(f)
            self._cz = (z["X"], {str(n): i for i, n in enumerate(z["name"])})
        X, ix = self._cz
        nm = pose["name"] if pose["name"][-2:] in (":l", ":r") else pose["name"] + ":l"
        if nm not in ix:
            raise KeyError(f"provider carried: pose {nm!r} is not in {f.name} ({len(ix)} poses); there is no live fallback")
        if X.shape[1] != nr:
            raise ValueError(f"provider carried: {f.name} has {X.shape[1]} points a pose, the region has {nr}")
        return X[ix[nm]]

    # ------------------------------------------------- silhouette and sheets --
    def a_on_B(self, pose):
        """A posed by B's bone turns of this pose, brought onto B's skeleton at the chest: [n, 3]."""
        Va, Ga = self.a_from_B(pose["G"])
        M = self.align({**pose, "A": (Va, Ga)}, SIL["anchor"])
        return Va @ M[:3, :3].T + M[:3, 3]

    def mesh(self, kind, pose, Va):
        """(V, T) of a provider's whole surface; Va = a_on_B(pose) for the A kinds."""
        return (Va, self.A.T) if kind in A_KINDS else (self.surface(kind, pose), self.B.T)

    def view(self, pose, v, half, px):
        """The orthographic window about B's posed shoulder joint, camera direction v (body coords) turned with the chest."""
        B, fr, G, s = self.B, self.B.frame, pose["G"], pose["side"]
        R = turn(G, B.p.rest, B.p.index[self.anch[s][SIL["anchor"]][0]])
        c = np.asarray(G[B.p.index[B.role(SIL["center"], s)]])[:3, 3]
        return chest_view(c, R, self.sg[s] * np.asarray(fr.lat), np.asarray(fr.up), np.asarray(fr.front), v, half, px)

    def regtri(self, s):
        """[B triangles] bool: touches the side's shoulder region."""
        if self._regtri is None:
            self._regtri = {}
            for k in "lr":
                loc = self.md.S[k]["loc"][self.md.src]
                g = np.zeros(len(self.B.V0), bool)          # the full layer has points past the body's (md.src)
                g[:len(loc)] = (loc >= 0) & (loc < len(self.md.S[k]["ids"]))
                self._regtri[k] = g[self.B.T].any(1)
        return self._regtri[s]

    def silhouette(self, kind, pose, views):
        """{view: {"all": [p05, p50, p95, min, max] mm, "reg": the same on the region's outline or None, "n": pixels}}."""
        Va = self.a_on_B(pose)
        V, T = self.mesh(kind, pose, Va)
        sp, sa = ray.scene(V, T), ray.scene(Va, self.A.T)
        px, k, out = SIL["px"], int(round(SIL["margin"] * SIL["px"])), {}
        for vn in views:
            vw = self.view(pose, SIL["views"][vn], SIL["half"] + SIL["margin"], px)
            pid = vw.cast(sp)[0]
            d = outline_signed(pid >= 0, vw.cast(sa)[0] >= 0) * 1000.0 / px
            ok = np.zeros(d.shape, bool)
            ok[k:-k, k:-k] = True
            ok &= np.isfinite(d)
            reg = ok & self.regtri(pose["side"])[np.maximum(pid, 0)] if T is self.B.T else None
            out[vn] = {"all": sil_stats(d[ok]), "reg": None if reg is None else sil_stats(d[reg]), "n": int(ok.sum())}
        return out

    def panels(self, kind, pose, views):
        """{view: [B published, the provider, A] clay panels (uint8 [h, w, 3])}, one window and light for the three."""
        Va = self.a_on_B(pose)
        cols = [(self.surface("pub", pose), self.B.T), None if kind == "pub" else self.mesh(kind, pose, Va), (Va, self.A.T)]
        out = {}
        for vn in views:
            vw = self.view(pose, SHEET["views"][vn], SHEET["half"], SHEET["panel"] / (2 * SHEET["half"]))
            im = [None if c is None else clay_rgb(c[0], c[1], vw) for c in cols]
            out[vn] = [im[0], im[0] if im[1] is None else im[1], im[2]]
        return out

    def align(self, pose, anchor):
        """4x4 taking A's posed surface onto B's by the anchor bone."""
        bn, an = self.anch[pose["side"]][anchor]
        jb, ja = self.B.p.index[bn], self.A.p.index[an]
        Ga = np.asarray(pose["A"][1])
        M = pose["G"][jb] @ np.linalg.inv(self.B.p.rest[jb]) @ np.asarray(self.A.G0)[ja] @ np.linalg.inv(Ga[ja])
        M[:3, :3] = da.ortho(M[:3, :3])
        return M

    def shift(self, kind, pose, V=None):
        """{band: per-point shift (m)} of a provider's surface against A, the rest offset removed."""
        s, out = pose["side"], {}
        Va = pose["A"][0]
        if V is None and kind != "a":
            V = self.surface(kind, pose)
        for b in BANDS:
            nr, M = self.near[b, s], self.align(pose, ANCHOR[b])
            if kind == "a":
                P, d0 = self._carry(nr, self.q0[b, s], Va), 0.0         # A's own points, carried by A
            else:
                P, d0 = (V[self.md.first[self.bands[b][s]]] - M[:3, 3]) @ M[:3, :3], self.sd0[b, s]
            out[b] = nr.signed(P, Va)[0] - d0
        return out

    def _carry(self, nr, q0, Va):
        """Points on A's rest surface (q0) carried to A's posed surface by their triangle's barycentrics."""
        A0 = self.A.V0
        n, k = nr.ok.shape
        tri = nr.tri.reshape(-1, 3)
        a, b, c = (A0[tri[:, j]] for j in range(3))
        p = np.repeat(q0, k, 0)
        d = np.where(nr.ok.ravel(), np.linalg.norm(p - closest_on_tris(p, a, b, c), axis=1), np.inf).reshape(n, k)
        t = tri[d.argmin(1) + np.arange(n) * k]
        w = np.linalg.solve(np.swapaxes(A0[t], 1, 2) + 1e-12 * np.eye(3), q0[:, :, None])[:, :, 0]
        return np.einsum("nk,nkj->nj", w / w.sum(1, keepdims=True), Va[t])


def stats(x):
    x = x[np.isfinite(x)] * 1000
    return [round(float(v), 2) for v in (np.median(x), max(-np.percentile(x, 5), 0), max(-x.min(), 0), max(x.max(), 0))]


# ------------------------------------------------------ measuring, on arrays --
def chest_view(center, R, lat, up, front, v, half, px):
    """ray.View of a square window (+-half m, px pixels a metre) about `center`; the camera sits along v = (lat, up, front)
    in the body's rest axes turned by R (the chest's turn from rest). Image up = the body's up, or its front seen from
    straight above or below; image x = up x camera, so the picture is never mirrored."""
    d = np.asarray(v, float)
    cw = R @ da.unit(d[0] * lat + d[1] * up + d[2] * front)
    u = R @ up
    ey = bends.perp(u if abs(u @ cw) < 0.95 else R @ front, cw)
    return ray.View(center, np.cross(ey, cw), ey, cw, px, -half, half, -half, half)


def outline(m):
    """The mask's own edge pixels (4-neighbour); where the mask runs off the image is not an edge."""
    p = np.pad(m, 1, mode="edge")
    return m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])


def outline_signed(mp, ma):
    """[h, w] px: at each outline pixel of mask mp, the distance to the nearest outline pixel of mask ma, + outside ma and
    - inside it (identical masks: 0); nan off mp's outline, or everywhere when ma has no outline."""
    oa = outline(ma)
    if not oa.any():
        return np.full(ma.shape, np.nan)
    d = distance_transform_edt(~oa)
    return np.where(outline(mp), np.where(ma, -d, d), np.nan)


def sil_stats(x):
    """[p05, p50, p95, min, max] or None."""
    return [round(float(v), 2) + 0.0 for v in (*np.percentile(x, [5, 50, 95]), x.min(), x.max())] if len(x) else None


def clay_rgb(V, T, view):
    img, _ = bends.clay(V, T, view)
    return np.repeat((np.clip(img, 0, 1) * 255).astype(np.uint8)[..., None], 3, 2)


def sheet(rows, labels, panel):
    """PIL image: rows of square panels (resized to `panel` px), one line of small text under each."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("arial.ttf", 13 if panel >= 400 else 11)
    except OSError:
        font = ImageFont.load_default()
    gap, txt, nc = 4, 20 if panel >= 400 else 16, max(len(r) for r in rows)
    im = Image.new("RGB", (nc * panel + (nc - 1) * gap, len(rows) * (panel + txt)), (120, 120, 120))
    dr = ImageDraw.Draw(im)
    for i, (row, lab) in enumerate(zip(rows, labels)):
        for j, (g, t) in enumerate(zip(row, lab)):
            x, y = j * (panel + gap), i * (panel + txt)
            g = Image.fromarray(g)
            im.paste(g if g.size == (panel, panel) else g.resize((panel, panel), Image.LANCZOS), (x, y))
            dr.rectangle([x, y + panel, x + panel - 1, y + panel + txt - 1], fill=(255, 255, 255))
            dr.text((x + 4, y + panel + 2), t, fill=(0, 0, 0), font=font)
    return im


def save_half(im, path):
    from PIL import Image
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(path, quality=SHEET["jpg"])


def pose_names(a):
    if a.poses:
        return a.poses.split(",")
    if a.clip:
        n = da.load_clip(a.clip)["frames"]
        return [f"{a.clip}@{f}:{s}" for f in range(n) for s in "lr"]
    z = np.load(OUT / "poses.npz")
    return [str(n) for n, k in zip(z["name"], z["kind"]) if str(k) in a.only.split(",")]


def cmd_silhouette(cx, a):
    kind, views = a.provider, (a.views or ",".join(SIL["views"])).split(",")
    names, rk = pose_names(a), a.provider if a.provider in A_KINDS else "pub"
    fmt = lambda v: "-" if v is None else "/".join(f"{x:.1f}" for x in v)
    print(f"silhouette {kind} against A (B's bone turns, chest-aligned): mm, + outside A's outline, - inside; "
          f"p05/p50/p95/min/max | reg = on the shoulder region | rest = {rk} at rest")
    rest, rows = {}, {}
    for pose in cx.poses(names):
        s = pose["side"]
        if s not in rest:
            rest[s] = cx.silhouette(rk, {"name": f"rest:{s}", "side": s, "G": cx.B.G0}, views)
        rows[pose["name"]] = r = cx.silhouette(kind, pose, views)
        if len(names) <= 40:
            for vn in views:
                print(f"{pose['name']:26s} {vn:10s} {fmt(r[vn]['all']):32s} reg {fmt(r[vn]['reg']):32s} | rest {fmt(rest[s][vn]['all']):30s}"
                      f" reg {fmt(rest[s][vn]['reg'])}", flush=True)
    summ = {}
    print(f"{kind}: {len(rows)} poses. view: worst p95 (pose) / worst min (pose) / worst max (pose), whole window then region"
          f" | rest {sorted(rest)[0] if rest else ''} p05/p50/p95/min/max")
    for vn in views:
        summ[vn] = {}
        for key in ("all", "reg"):
            v = [(n, r[vn][key]) for n, r in rows.items() if r[vn][key] is not None]
            if not v:
                continue
            p95, mn, mx = (f(v, key=lambda e: e[1][i]) for f, i in ((max, 2), (min, 3), (max, 4)))
            summ[vn][key] = {"p95": [p95[1][2], p95[0]], "min": [mn[1][3], mn[0]], "max": [mx[1][4], mx[0]]}
        line = " || ".join(f"{k}: " + " / ".join(f"{e[0]:.1f} ({e[1]})" for e in d.values()) for k, d in summ[vn].items())
        print(f"  {vn:10s} {line} | rest {fmt(rest[sorted(rest)[0]][vn]['all']) if rest else '-'}")
    (OUT / f"silhouette_{kind}.json").write_text(json.dumps({"provider": kind, "window": {k: SIL[k] for k in ("half", "px", "margin")},
                                                             "cols": ["p05", "p50", "p95", "min", "max"], "rest": rest, "poses": rows, "summary": summ}))
    print("wrote", OUT / f"silhouette_{kind}.json")


def cmd_sheets(cx, a):
    if not a.poses:
        raise SystemExit("sheets needs --poses")
    kind, views = a.provider, a.views.split(",") if a.views else SHEET["default"]
    gv, col = SHEET["gate_view"], ["B published", a.provider, "A (B's bone turns)"]
    out = OUT / "sheets"
    out.mkdir(parents=True, exist_ok=True)
    gate = []
    for pose in cx.poses(a.poses.split(",")):
        nm = pose["name"]
        P = cx.panels(kind, pose, views + ([gv] if a.gate and gv not in views else []))
        im = sheet([P[vn] for vn in views], [[f"{c} | {nm} | {vn}" for c in col] for vn in views], SHEET["panel"])
        f = out / f"{kind}_{nm.replace(':', '_').replace('@', '_f')}.png"
        im.save(f)
        save_half(im, f.with_name(f.stem + "_half.jpg"))
        print("wrote", f, "+ _half.jpg", flush=True)
        if a.gate:
            gate.append((nm, P[gv]))
    if a.gate:
        order = {n: i for i, n in enumerate(a.poses.split(","))}
        gate.sort(key=lambda e: order[e[0]])
        im = sheet([p for _, p in gate], [[f"{c} | {n}" for c in col] for n, _ in gate], SHEET["gate_panel"])
        f = out / f"gate_{kind}_half.jpg"
        im.save(f, quality=SHEET["jpg"])
        print("wrote", f)


def cmd_shift(cx, a):
    names = pose_names(a)
    print("bands:", {b: len(v["l"]) for b, v in cx.bands.items()}, "| cols per band: p50 / in95 / inmax / outmax mm (+ outward)")
    rows = {}
    for pose in cx.poses(names):
        rows[pose["name"]] = r = {b: stats(v) for b, v in cx.shift(a.provider, pose).items()}
        if len(names) <= 40:
            print(f"{pose['name']:28s}" + "  ".join(f"{b[:6]} {'/'.join(f'{x:.1f}' for x in r[b])}" for b in BANDS), flush=True)
    (OUT / f"shift_{a.provider}.json").write_text(json.dumps(rows))
    print(f"{a.provider}: {len(rows)} poses. band: worst in95 / worst inmax (pose) / worst outmax | median p50 / in95 / inmax")
    for b in BANDS:
        v = np.array([r[b] for r in rows.values()])
        w = list(rows)[int(v[:, 2].argmax())]
        print(f"  {b:12s} {v[:, 1].max():.1f} / {v[:, 2].max():.1f} ({w}) / {v[:, 3].max():.1f} | "
              f"{np.median(v[:, 0]):.1f} / {np.median(v[:, 1]):.1f} / {np.median(v[:, 2]):.1f}")


def cmd_pops(cx, a):
    """The audit's pop (run_clip): the second difference in time of each shoulder region in its own rigid fit, mm."""
    B, A, res = cx.B, cx.A, {}
    regs = [r.replace("{s}", s) for s in "lr" for r in da.JOINTS["shoulder"]]
    for c in a.clips.split(","):
        d = da.load_clip(c)
        hist, best = {}, {}
        ait = None if c.startswith("p4:") else A.clip_frames(d, 1)
        for f, Vb, G in B.clip_frames(d, 1):
            cols = {"B": (B, Vb), "A": (A, cx.a_from_B(G)[0] if ait is None else next(ait)[1])}
            if a.provider != "pub":
                V = Vb
                for s in "lr":
                    Vs = cx.surface(a.provider, {"name": f"{c}@{f}:{s}", "side": s, "G": G})
                    g = np.abs(Vs - Vb).max(1) > 0
                    V = np.where(g[:, None], Vs, V)
                cols["P"] = (B, V)
            for col, (bd, V) in cols.items():
                for r in regs:
                    v = bd.reg[r]["v"]
                    R, t = da.kabsch(bd.V0[v], V[v])
                    h = hist.setdefault((col, r), [])
                    h.append((V[v] - t) @ R)
                    if len(h) == 3:
                        x = np.linalg.norm(h[2] - 2 * h[1] + h[0], axis=1) * 1000
                        e = best.setdefault((col, r), [0.0, 0.0, -1])
                        if x.max() > e[1]:
                            e[2] = f - 1
                        e[0], e[1] = max(e[0], float(np.percentile(x, 99))), max(e[1], float(x.max()))
                        h.pop(0)
        res[c] = {f"{col}.{r}": [round(e[0], 2), round(e[1], 2), e[2]] for (col, r), e in best.items()}
        print(f"{c}: pop99 / popmax mm @frame, " + " | ".join(sorted({k[0] for k in best})))
        for r in regs:
            print(f"  {r:20s}" + " | ".join("{:.2f} / {:.2f} @{}".format(*best[col, r]) for col in sorted({k[0] for k in best})), flush=True)
    (OUT / f"pops_{a.provider}.json").write_text(json.dumps(res))


# ---------------------------------------------------------------------- edges --
EDGE_CLASSES = ["pocket", "published", "A's own", "border blend", "bridge", "carrier"]
EDGE = {"tol": 0.15, "bridge": 2.0, "tiny": 0.25, "geo_rad": 0.15, "turns": ["spine_05", "neck_01", "neck_02", "head", "clavicle_{s}", "upperarm_{s}"]}


def edge_len(X, ei, ej):
    return np.linalg.norm(X[ei] - X[ej], axis=1)


def tri_stretch(V0, V, tri):
    """The largest principal stretch rest -> posed of the triangles tri [m, 3]."""
    U, W = (np.stack([x[tri[:, 1]] - x[tri[:, 0]], x[tri[:, 2]] - x[tri[:, 0]]], 2) for x in (V0, V))
    return np.linalg.svd(W @ np.linalg.pinv(U), compute_uv=False)[:, 0]


def classify_edges(t, p, c, a, inp, bmin, bmax, bridge, over, tol=EDGE["tol"]):
    """One class (index into EDGE_CLASSES) per edge whose target ratio t is over `over`, -1 for the others. All inputs
    per edge, read at the edge's worst pose: t / p / c / a = the ratio of the target, the published surface, the carried
    surface before the border blend, the reference's own; inp = an end in the pocket; bmin / bmax = the ends' border
    share; bridge = the rest bridge measure fails. The first rule that holds, in this order:
      pocket        an end in the pocket
      published     both ends at share 0 (the target IS the published surface there)
      A's own       the carried ratio explains the target (c >= (1 - tol) t) and the reference stretches as much at the
                    same place (a >= (1 - tol) c)
      border blend  an end with share < 1, and neither the carried nor the published ratio reaches (1 - tol) t
      bridge        the ends' matched reference points lie over EDGE["bridge"] x apart along the reference's rest surface,
                    measured against the longer of the edge's rest length and the matched points' straight gap
      carrier       none of the above (carrier_note says what it looks like)"""
    lab = np.full(len(t), -1)
    cls = np.select([inp, bmax <= 0, (c >= (1 - tol) * t) & (a >= (1 - tol) * c), (bmin < 1) & (np.maximum(c, p) < (1 - tol) * t), bridge],
                    [0, 1, 2, 3, 4], 5)
    lab[t > over] = cls[t > over]
    return lab


def carrier_note(t, p, c, a, bmin, tol=EDGE["tol"]):
    """What a `carrier` edge looks like: the carry stretches where the reference does not (offset turn), the published
    surface's own stretch on a blend row, or neither surface explains it at full share."""
    return np.select([(c >= (1 - tol) * t) & (a < (1 - tol) * c), (bmin < 1) & (p >= (1 - tol) * t)],
                     ["carry over A (offsets / frames)", "published-led blend row"], "unexplained")


class EdgeProbe:
    """Edges (ei, ej) of rest points P0 against their match (tri [n, 3], bary [n, 3]) on a reference mesh at rest ref_V0."""

    def __init__(self, P0, ei, ej, tri, bary, ref_V0, tiny=EDGE["tiny"]):
        self.ei, self.ej, self.tri, self.bary, self.V0 = ei, ej, tri, bary, np.asarray(ref_V0, float)
        self.l0 = np.maximum(edge_len(P0, ei, ej), 1e-12)
        self.q0 = np.einsum("nk,nkj->nj", bary, self.V0[tri])
        self.g0 = edge_len(self.q0, ei, ej)
        self.small = self.g0 < tiny * self.l0

    def ratio(self, X):
        return edge_len(X, self.ei, self.ej) / self.l0

    def own(self, ref_V):
        """The reference's own ratio at each edge: the matched points' posed distance over their rest distance; where
        the rest distance is tiny (under `tiny` of the edge), the larger principal stretch of the two matched triangles."""
        r = edge_len(np.einsum("nk,nkj->nj", self.bary, ref_V[self.tri]), self.ei, self.ej) / np.maximum(self.g0, 1e-12)
        k = np.nonzero(self.small)[0]
        if len(k):
            r[k] = np.maximum(tri_stretch(self.V0, ref_V, self.tri[self.ei[k]]), tri_stretch(self.V0, ref_V, self.tri[self.ej[k]]))
        return r

    def along(self, T, sel, rad=EDGE["geo_rad"], weld=1e-6):
        """[len(sel)] m: the matched points' distance along the reference's rest surface for the edges sel (paths over
        the welded vertex graph, corner to corner; faces that share an edge or are one: the straight gap; `rad` = cap)."""
        from scipy.sparse.csgraph import dijkstra
        import scipy.sparse as sp
        V0 = self.V0
        _, grp = np.unique(np.round(V0 / weld).astype(np.int64), axis=0, return_inverse=True)
        grp = np.asarray(grp).ravel()
        n = int(grp.max()) + 1
        rep = np.zeros(n, np.int64)
        rep[grp] = np.arange(len(V0))
        E = np.unique(np.sort(grp[np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])], 1), axis=0)
        E = E[E[:, 0] != E[:, 1]]
        Gr = sp.coo_matrix((np.linalg.norm(V0[rep[E[:, 0]]] - V0[rep[E[:, 1]]], axis=1), (E[:, 0], E[:, 1])), (n, n)).tocsr()
        out = np.empty(len(sel))
        for a in range(0, len(sel), 96):
            k = sel[a:a + 96]
            ti, tj = self.tri[self.ei[k]], self.tri[self.ej[k]]
            src, inv = np.unique(grp[ti], return_inverse=True)
            D = dijkstra(Gr, directed=False, indices=src, limit=rad)[np.asarray(inv).reshape(ti.shape)]         # [m, 3, n]
            d = np.take_along_axis(D, np.broadcast_to(grp[tj][:, None, :], (len(k), 3, 3)), 2)
            da_, db_ = (np.linalg.norm(self.q0[e][:, None] - V0[t], axis=2) for e, t in ((self.ei[k], ti), (self.ej[k], tj)))
            path = np.minimum((da_[:, :, None] + d + db_[:, None, :]).reshape(len(k), 9).min(1), rad)
            share = (grp[ti][:, :, None] == grp[tj][:, None, :]).any(2).sum(1)
            out[a:a + 96] = np.where(share >= 2, self.g0[k], np.maximum(path, self.g0[k]))
        return out


def edge_zones(h):
    """A zone name per region point (local index, the left side's; the right = the twins): the named band, else for
    the border rows (share < 1) what bounds them (why_names of the nearest outside point) + top / front / back by the
    rest normal, else inner + top / front / back."""
    md, fr, sd = h.md, h.bd.frame, h.md.S["l"]
    ids = sd["ids"]
    N = h.N0[md.first[ids]]
    fbt = np.where(N @ np.asarray(fr.up) > 0.6, "top", np.where(N @ np.asarray(fr.front) > 0, "front", "back"))
    out = np.nonzero(md.why >= 0)[0]
    why = md.why[out[cKDTree(md.V0[out]).query(md.V0[ids])[1]]]
    z = np.array([f"{'border ' + md.why_names[w] if b < 1 else 'inner'} {f}" for w, b, f in zip(why, md.beta, fbt)], object)
    bz = np.load(OUT / "bands.npz")
    for b in BANDS[::-1]:
        z[sd["loc"][bz[f"{b}_l"]]] = b
    return z


def edge_rows(h, pr, G, s, X=None):
    """One pose and side: {t, p, c, a: ratio per edge of the target (X, or the live blend), the published surface, the
    carried surface before the blend, A's own; dis: per point |carried - published| m; stale: max |X - live blend| m}."""
    md = h.md
    MC, _, VaM = h.carried(G, s)
    Vp = h.rt.published(h.bd, G)[md.first[md.S[s]["ids"]]]
    b = md.blend(G, s)[:, None]
    oth = h.last.get("others", 0.0)      # the deltas of the regions that touch this one (the neck): added whole
    live = b * MC + (1 - b) * Vp + oth
    X = live if X is None else X
    return {"t": pr.ratio(X), "p": pr.ratio(Vp), "c": pr.ratio(MC + oth), "a": pr.own(VaM), "dis": np.linalg.norm(MC - Vp, axis=1),
            "stale": float(np.abs(X - live).max())}


def edge_probe(h, s):
    car = h.car[s]
    return EdgeProbe(h.md.V0[h.md.S[s]["ids"]], *h.edges[s], car.tri, car.bary, h.Ab.V0)


def cmd_edges(a):
    """edges: why is the carried target stretched? Per pose and side, per region edge: the ratio (posed / rest length) of
    the target (target_a.npz), the published surface, the carried surface before the border blend, A's own at the same
    place, and at rest the matched A points' distance along A's surface. Every edge over --over in some pose gets one
    class at its worst pose (classify_edges states the rule). Table zone x class; out: edges_<provider>.json."""
    import carried_target as ct
    if a.provider != "carried":
        raise SystemExit("edges: --provider carried only")
    h = ct.Her(verbose=False)
    md, bd, over = h.md, h.bd, a.over
    z, tz = np.load(OUT / "poses.npz"), np.load(OUT / "target_a.npz")
    names, tix = [str(x) for x in z["name"]], {str(n): i for i, n in enumerate(tz["name"])}
    sel = [names.index(p) for p in a.poses.split(",")] if a.poses else list(range(len(names)))
    zone, beta = edge_zones(h), md.beta
    pr = {s: edge_probe(h, s) for s in "lr"}
    acc = {s: {k: [] for k in ("t", "p", "c", "a", "dis", "name", "i")} for s in "lr"}
    stale = 0.0
    for i in sel:
        s = str(z["side"][i])
        r = edge_rows(h, pr[s], z["G"][i], s, tz["X"][tix[names[i]]])
        stale = max(stale, r["stale"])
        for k in ("t", "p", "c", "a", "dis"):
            acc[s][k].append(r[k])
        acc[s]["name"].append(names[i])
        acc[s]["i"].append(i)
    print(f"edges {a.provider}: {len(sel)} poses, over {over:g}; target_a.npz against the live blend: max {stale * 1000:.3f} mm"
          f" | A rest edge p50 {np.median(edge_len(h.Ab.V0, h.Ab.T[:, 0], h.Ab.T[:, 1])) * 1000:.1f} mm, B region edge p50 {np.median(pr['l'].l0) * 1000:.1f} mm")
    rows, cells, zworst = [], {}, {}
    for s in "lr":
        if not acc[s]["t"]:
            continue
        R = {k: np.array(acc[s][k]) for k in ("t", "p", "c", "a", "dis")}
        nm, p_, (ei, ej) = acc[s]["name"], pr[s], h.edges[s]
        w = R["t"].argmax(0)
        t, p, c, av = (R[k][w, np.arange(len(w))] for k in ("t", "p", "c", "a"))
        inp = np.zeros(len(beta), bool)
        if h.car[s].pocket is not None:
            inp[h.car[s].pocket.p] = True
        ov = np.nonzero(t > over)[0]
        geo = np.full(len(t), np.nan)
        geo[ov] = p_.along(h.Ab.T, ov)
        bmin, bmax = np.minimum(beta[ei], beta[ej]), np.maximum(beta[ei], beta[ej])
        bridge = geo > EDGE["bridge"] * np.maximum(p_.l0, p_.g0)
        lab = classify_edges(t, p, c, av, inp[ei] | inp[ej], bmin, bmax, bridge, over)
        note = carrier_note(t, p, c, av, bmin)
        ez = zone[np.where(beta[ei] <= beta[ej], ei, ej)]
        dis = np.maximum(R["dis"][w, ei], R["dis"][w, ej])
        need = np.minimum(dis / np.maximum((over - np.maximum(c, p)) * p_.l0, 1e-9), 99.0)
        mid = (md.V0[md.S[s]["ids"]][ei] + md.V0[md.S[s]["ids"]][ej]) * 500
        for e in ov:
            cl = EDGE_CLASSES[lab[e]]
            rows.append({"side": s, "edge": [int(ei[e]), int(ej[e])], "zone": ez[e], "class": cl, "note": str(note[e]) if cl == "carrier" else "",
                         "pose": nm[w[e]], "t": round(float(t[e]), 3), "p": round(float(p[e]), 3), "c": round(float(c[e]), 3), "a": round(float(av[e]), 3),
                         "along_over_l0": round(float(geo[e] / p_.l0[e]), 2), "gap_over_l0": round(float(p_.g0[e] / p_.l0[e]), 2),
                         "beta": [round(float(beta[ei[e]]), 2), round(float(beta[ej[e]]), 2)], "l0_mm": round(float(p_.l0[e] * 1000), 2),
                         "dis_mm": round(float(dis[e] * 1000), 1), "rows_need": round(float(need[e]), 1), "poses_over": int((R["t"][:, e] > over).sum()),
                         "rest_mm": [round(float(x), 1) for x in mid[e]]})
            cells.setdefault((ez[e], cl), {"l": 0, "r": 0, "worst": 0.0, "pose": "", "poses": set(), "rest_mm": None, "dis": [], "need": [], "l0": [], "notes": {}})
            ce = cells[ez[e], cl]
            ce[s] += 1
            ce["poses"] |= {nm[k] for k in np.nonzero(R["t"][:, e] > over)[0]}
            ce["dis"].append(dis[e] * 1000), ce["need"].append(need[e]), ce["l0"].append(p_.l0[e] * 1000)
            if cl == "carrier":
                ce["notes"][str(note[e])] = ce["notes"].get(str(note[e]), 0) + 1
            if t[e] > ce["worst"]:
                ce["worst"], ce["pose"], ce["rest_mm"] = float(t[e]), nm[w[e]], rows[-1]["rest_mm"]
        for zn in set(ez[ov]):
            m = ov[ez[ov] == zn]
            for k in range(len(nm)):
                v = float(R["t"][k, m].max())
                if v > over:
                    zworst.setdefault(zn, []).append((v, nm[k], acc[s]["i"][k], int((R["t"][k, m] > over).sum())))
    P, rest = bd.p, bd.p.rest

    def turns(i):
        G, s, o = z["G"][i], str(z["side"][i]), {}
        for b in EDGE["turns"]:
            b = b.replace("{s}", s)
            if b in P.index:
                j = P.index[b]
                Rl = turn(G, rest, j) @ (turn(G, rest, P.parent[j]).T if P.parent[j] >= 0 else np.eye(3))
                o[b] = round(float(np.degrees(np.arccos(np.clip((np.trace(Rl) - 1) / 2, -1, 1)))), 1)
        return o
    print(f"{'zone':34s} {'class':13s} edges l/r   worst  pose                        poses  rest mm (x, y, z)     blend: dis mm p50/max, rows p50/max")
    table = []
    for (zn, cl), ce in sorted(cells.items(), key=lambda e: (e[0][0], EDGE_CLASSES.index(e[0][1]))):
        d = {"zone": zn, "class": cl, "edges_l": ce["l"], "edges_r": ce["r"], "worst": round(ce["worst"], 2), "worst_pose": ce["pose"], "poses_over": len(ce["poses"]),
             "rest_mm": ce["rest_mm"], "dis_mm": [round(float(np.median(ce["dis"])), 1), round(float(np.max(ce["dis"])), 1)],
             "rows_need": [round(float(np.median(ce["need"])), 1), round(float(np.max(ce["need"])), 1)], "l0_mm_p50": round(float(np.median(ce["l0"])), 2), "notes": ce["notes"]}
        table.append(d)
        ex = f"{d['dis_mm'][0]:.1f}/{d['dis_mm'][1]:.1f}, {d['rows_need'][0]:.1f}/{d['rows_need'][1]:.1f}" if cl == "border blend" else " ".join(f"{k}: {v}" for k, v in ce["notes"].items())
        print(f"{zn:34s} {cl:13s} {ce['l']:4d} /{ce['r']:4d}  {ce['worst']:5.2f}  {ce['pose']:27s} {len(ce['poses']):4d}   {str(ce['rest_mm']):22s} {ex}")
    worst = {}
    print("the five worst poses per zone: ratio pose (edges over) | local turns from rest, deg")
    for zn, v in sorted(zworst.items()):
        worst[zn] = [{"ratio": round(r, 2), "pose": n, "edges_over": k, "turns_deg": turns(i)} for r, n, i, k in sorted(v, reverse=True)[:5]]
        for e in worst[zn]:
            print(f"  {zn:34s} {e['ratio']:5.2f} {e['pose']:27s} ({e['edges_over']:3d}) | " + " ".join(f"{k} {x:.0f}" for k, x in e["turns_deg"].items()))
    tot = {c: sum(1 for r in rows if r["class"] == c) for c in EDGE_CLASSES}
    print("classes:", tot, "of", len(rows), "edges over")
    f = OUT / f"edges_{a.provider}.json"
    f.write_text(json.dumps({"provider": a.provider, "over": over, "params": EDGE, "classes": EDGE_CLASSES, "poses": len(sel), "stale_mm": stale * 1000,
                             "totals": tot, "table": table, "worst_poses": worst, "edges": rows}))
    print("wrote", f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["shift", "pops", "silhouette", "sheets", "edges"])
    ap.add_argument("--over", type=float, default=2.5)
    ap.add_argument("--provider", default="pub")
    ap.add_argument("--poses", default="")
    ap.add_argument("--only", default="train,held,extreme")
    ap.add_argument("--clip", default="")
    ap.add_argument("--clips", default="run_warden,sword_heavy,p4:bladestorm_loop")
    ap.add_argument("--views", default="")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    if a.cmd == "edges":
        return cmd_edges(a)
    {"shift": cmd_shift, "pops": cmd_pops, "silhouette": cmd_silhouette, "sheets": cmd_sheets}[a.cmd](Ctx(), a)


if __name__ == "__main__":
    main()
