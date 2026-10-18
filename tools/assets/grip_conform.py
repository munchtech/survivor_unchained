"""Any weapon's grip conformed to its TYPE's grip (data/grip_spec.json), nothing else touched: the type's fitted fist
(tools/anim/keyed.py WRAP, WeaponSockets' pocket for the kind) then holds every piece of the type unchanged.

    python tools/assets/grip_conform.py measure [piece ...]           every Arms.Spec row (or those named) against its type
    python tools/assets/grip_conform.py conform dagger_b --out DIR    conform one piece's grip, write DIR/<file>.glb
    python tools/assets/grip_conform.py check dagger_b DIR/daggers.glb   re-measure a conformed file (section within TOL of
                                                                      the spec; every other vertex, UV and byte as before)
    python tools/assets/grip_conform.py conform viking_sword --src a4df6f89 --seat --cylinder --roll 5 --out DIR
                                                                      a round type, made one cylinder: every ring of the
                                                                      band on the circle, its sides spaced evenly (below)
    (--src REV: read the original from git, as grip_thin.py does; default the file as it is in public/assets/weapons)

The piece is laid as Arms.Make lays it (godot/src/Actors/Arms.cs, the rows parsed from `All`): its node's meshes (Spec
Node), the principal long axis signed toward the file axis it lies nearest (Flip), its length in life (Spec.Length over
the mesh's length), the grip point its anchor_grip or Spec.Grip along the shaft. Its GRIP is then found, not typed in:
its rings along the shaft out from the grip point, until one rises past RISE over the narrowest so far (a guard, a
pommel past its neck) or its centre jumps (an axe's head). Its section: in the band's own principal frame (a flat hilt's
width and depth), the half-extents about its centre line (the rings' centres, median-smoothed). A piece that defeats
that (a wire-wrapped grip, a strap beside a bead strand) gets its own "t", "parts" or "centre" in the spec's "pieces".

Conform: the band's vertices (inside it and no further out than RISE times its widest: the guard's own faces that share
the band stay) scaled about the centre line in that frame, width and depth separately, so the widest slice comes to the
spec's (its swell kept, smaller or larger; a flat hilt keeps its flats; a round spec on a flat hilt makes it square-ish,
and the check fails it if a corner passes the circle by more than TOL). Normals by the inverse
transpose, tangents by the scale, both unit length again, their w kept. Only those rows of POSITION / NORMAL / TANGENT
change, the POSITION min/max rewritten; UVs, indices, the guard, the pommel, the blade stay byte for byte. Then an
anchor_grip node is written (or the old one replaced): the grip point as the plain mount had it (or moved to the type's
grip-from-guard, --seat), -Y toward the tip on the mount's long axis, +Z the mount's +Z (Roll kept): so the piece mounts
exactly as before, and the anchor holds the axis even though the grip's change moves the bounds' principal axis.
Last, fistfit (tools/anim/fistfit.py) is the numeric pass/fail on the conformed piece once it is in the game's files and
arms_local is re-dumped: no judge.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WEAPONS = ROOT / "public" / "assets" / "weapons"
ARMS = ROOT / "godot" / "src" / "Actors" / "Arms.cs"
SPEC = ROOT / "tools" / "anim" / "data" / "grip_spec.json"
RISE = 1.12     # a slice this much wider than the narrowest so far is the guard's or the pommel's
SMOOTH = 15.0   # mm: the centre line's median window
TOL = 0.3       # mm: a conformed section's allowance off the spec


# ------------------------------------------------------------------ the rows --
def arms_rows():
    """Arms.All, parsed: id -> dict(file, length, grip, flip, roll, node, kind, seated)."""
    s = ARMS.read_text(encoding="utf-8")
    body = s[s.index("All = new()"):]
    body = body[:body.index("};")]
    rows = {}
    for m in re.finditer(r'\["(\w+)"\]\s*=\s*new\("([^"]*)",\s*([\d.]+)f,\s*([\d.]+)f([^;]*?)\),?\s*(//[^\n]*)?\n', body):
        rest = m.group(5)
        def opt(name, pat=r"([^,)]+)"):
            k = re.search(rf"{name}:\s*{pat}", rest)
            return k.group(1).strip() if k else None
        roll = opt("Roll")
        rows[m.group(1)] = dict(
            file=m.group(2), length=float(m.group(3)), grip=float(m.group(4)),
            flip=opt("Flip") == "true", seated=opt("Seated") == "true", pistol=opt("Pistol") == "true",
            roll=np.pi if roll == "Mathf.Pi" else float(roll.rstrip("f")) if roll else 0.0,
            node=opt("Node", r'"([^"]+)"'), kind=(opt("Kind") or "WeaponKind.None").split(".")[-1],
            build="Build:" in rest)
    return rows


def spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- the glb --
class Glb:
    def __init__(self, data: bytes):
        self.b = bytearray(data)
        jl = struct.unpack("<I", self.b[12:16])[0]
        self.js = json.loads(self.b[20:20 + jl])
        self.bin0 = 20 + jl + 8

    @classmethod
    def read(cls, path: Path, rev=None):
        if rev:
            return cls(subprocess.run(["git", "show", f"{rev}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT,
                                      capture_output=True, check=True).stdout)
        return cls(path.read_bytes())

    def acc(self, i, ncomp=3):
        a = self.js["accessors"][i]; bv = self.js["bufferViews"][a["bufferView"]]
        assert a["componentType"] == 5126 and bv.get("byteStride", 4 * ncomp) == 4 * ncomp, (i, a, bv)
        off = self.bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return off, np.frombuffer(bytes(self.b[off:off + a["count"] * 4 * ncomp]), "<f4").reshape(-1, ncomp).astype(float)

    def acc_bytes(self, i):
        a = self.js["accessors"][i]; bv = self.js["bufferViews"][a["bufferView"]]
        size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]] * {5126: 4, 5125: 4, 5123: 2, 5121: 1}[a["componentType"]]
        off = self.bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return bytes(self.b[off:off + a["count"] * bv.get("byteStride", size)])

    def world(self):
        """node index -> 4x4 world matrix (glTF column-major matrices, TRS)."""
        N = self.js["nodes"]; parent = {}
        for i, n in enumerate(N):
            for c in n.get("children", []):
                parent[c] = i
        def local(n):
            if "matrix" in n:
                return np.array(n["matrix"], float).reshape(4, 4).T
            M = np.eye(4)
            if "rotation" in n:
                x, y, z, w = n["rotation"]
                M[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                             [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                             [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
            if "scale" in n:
                M[:3, :3] = M[:3, :3] * np.array(n["scale"])[None, :]
            if "translation" in n:
                M[:3, 3] = n["translation"]
            return M
        out = {}
        def w(i):
            if i not in out:
                out[i] = (w(parent[i]) if i in parent else np.eye(4)) @ local(N[i])
            return out[i]
        for i in range(len(N)):
            w(i)
        return out, parent

    def write(self, path: Path):
        jb = json.dumps(self.js, separators=(",", ":")).encode()
        jb += b" " * (-len(jb) % 4)
        out = bytearray(self.b[:12]) + struct.pack("<I4s", len(jb), b"JSON") + jb + self.b[self.bin0 - 8:]
        out[8:12] = struct.pack("<I", len(out))
        path.write_bytes(bytes(out))


def godot_name(n):
    return n.replace(".", "_")


# ----------------------------------------------------------------- the piece --
class Piece:
    """A piece laid as Arms.Make lays it: P (world points), frame (mid, lng, shrt), k (m per unit), grip point G."""

    def __init__(self, pid, glb: Glb, row):
        self.id, self.g, self.row = pid, glb, row
        W, parent = glb.world()
        N = glb.js["nodes"]
        def under(i):
            while True:
                if godot_name(N[i].get("name", "")) == row["node"]:
                    return True
                if i not in parent:
                    return False
                i = parent[i]
        self.parts = []          # (node, prim dict, world M)
        self.anchor = None
        self.node_index = next((i for i, n in enumerate(N) if row["node"] and godot_name(n.get("name", "")) == row["node"]), None)
        for i, n in enumerate(N):
            # (a file of several pieces: only the anchor under the piece's own node. NB Arms.Make takes any anchor in
            # the file today: it wants the same scoping before such a file carries one per piece)
            if n.get("name", "").startswith("anchor_grip") and (self.node_index is None or under(i)):
                self.anchor = (i, W[i])
            if "mesh" in n and (row["node"] is None or under(i)):
                for p in glb.js["meshes"][n["mesh"]]["primitives"]:
                    self.parts.append((i, p, W[i]))
        pts = []
        for _, p, M in self.parts:
            _, V = glb.acc(p["attributes"]["POSITION"])
            pts.append(V @ M[:3, :3].T + M[:3, 3])
        self.P = np.concatenate(pts)
        self.centre_by = "range"
        self.mask = np.ones(len(self.P), bool)      # the points the grip may be found in (spec "parts": those nodes')
        lng, mid = self.principal(self.P)
        if self.anchor is not None:
            lng = -self.anchor[1][:3, 1]; lng /= np.linalg.norm(lng)
            for c in (mid, lng, np.array([1.0, 0, 0]), np.array([0, 0, 1.0])):
                m = c - lng * (c @ lng)
                if m @ m > 1e-4:
                    mid = m / np.linalg.norm(m); break
        elif row["flip"]:
            lng = -lng
        shrt = np.cross(mid, lng)
        self.turn = np.array([mid, lng, shrt])                  # rows: model -> piece (X mid, Y long, Z short)
        d = self.P @ self.turn.T
        lo, hi = d.min(0), d.max(0)
        self.centre = self.turn.T @ ((lo + hi) / 2)
        if self.anchor is not None:
            f = self.turn @ self.anchor[1][:3, 2]
            if abs(f[0]) + abs(f[2]) > 1e-4:
                self.turn = ry(np.arctan2(-f[0], f[2])) @ self.turn
        elif row["roll"]:
            self.turn = ry(row["roll"]) @ self.turn
        self.k = row["length"] / (hi[1] - lo[1])                # m per model unit
        self.mm = self.k * 1000
        self.D = self.turn[1]                                    # toward the tip
        self.G = self.anchor[1][:3, 3].copy() if self.anchor is not None else \
            self.centre + self.D * ((row["grip"] - 0.5) * (hi[1] - lo[1]))

    @staticmethod
    def principal(P):
        C = np.cov((P - P.mean(0)).T, bias=True)
        w, v = np.linalg.eigh(C)
        ax = [v[:, i] for i in np.argsort(-w)]
        ax = [a if a[np.argmax(np.abs(a))] > 0 else -a for a in ax]   # signed toward the file axis nearest
        return ax[0], ax[1]

    # ---- the grip
    def local(self):
        """t (mm along D from G) and Q (model units, square to D, from the line through G) of every point."""
        dd = self.P - self.G
        t = dd @ self.D
        return t * self.mm, dd - np.outer(t, self.D)

    def sections(self, gap=0.75, width=3.0, mask=None, axes=None):
        """the rings along D: vertices grouped by t (a new ring where the next is more than `gap` mm on, or the ring
        would pass `width` mm: a dense mesh's slices), each (t mm, centre (3, model units, square to D: its points'
        mid-range in the piece's X and Z, a ring's or a hexagon's centre alike), radius mm about it, count)."""
        t, Q = self.local()
        idx = np.argsort(t) if mask is None else np.flatnonzero(mask)[np.argsort(t[mask])]
        X, Z = axes if axes is not None else (self.turn[0], self.turn[2])
        out, cur = [], [idx[0]]
        def flush(c):
            if len(c) >= 3:
                c = np.array(c); u, v = Q[c] @ X, Q[c] @ Z
                cu, cv = (u.max() + u.min()) / 2, (v.max() + v.min()) / 2     # mid-range (a ring, a hexagon)
                if self.centre_by == "axis":            # the mount's own line (an anchor on the shaft: the rule)
                    cu = cv = 0.0
                elif self.centre_by == "circle":        # least squares circle (a part-ring), unless degenerate
                    M = np.c_[2 * u, 2 * v, np.ones(len(u))]
                    k0, k1, _ = np.linalg.lstsq(M, u * u + v * v, rcond=None)[0]
                    if np.hypot(k0 - cu, k1 - cv) < 0.5 * np.hypot(u - cu, v - cv).max():
                        cu, cv = k0, k1
                ctr = X * cu + Z * cv
                out.append((float(t[c].mean()), ctr, float(np.linalg.norm(Q[c] - ctr, axis=1).max() * self.mm), len(c)))
        for i in idx[1:]:
            if t[i] - t[cur[-1]] > gap or t[i] - t[cur[0]] > width:
                flush(cur); cur = []
            cur.append(i)
        flush(cur)
        return out

    def band(self, cfg=None):
        """(t0, t1) mm: the grip's stretch either side of G (cfg: a piece's own "t" from the spec's pieces). From the
        slice at G out each way, until a slice's radius (about its own centre) rises more than RISE over the least seen
        so far that way (a guard, a pommel: a swelling grip's own shape stays in, a neck's rise to the pommel does not),
        or its centre jumps (an axe's head) more than a quarter of that radius from the last slice's."""
        if cfg and "t" in cfg:
            return tuple(cfg["t"])
        S = self.sections(mask=self.mask)
        i0 = int(np.argmin([abs(x[0]) for x in S]))
        def walk(step):
            i = i0; least = S[i0][2]
            while 0 <= i + step < len(S):
                x, prev = S[i + step], S[i]
                if x[2] > RISE * least or np.linalg.norm(x[1] - prev[1]) * self.mm > least / 4 * max(1.0, abs(x[0] - prev[0])):
                    return i, i + step
                least = min(least, x[2]); i += step
            return i, None
        def edge(i, j):          # halfway between the last slice in and the first out (a low-poly grip's long quads)
            return S[i][0] + (0.0 if j is None else (S[j][0] - S[i][0]) / 2)
        lo, lo_out = walk(-1); hi, hi_out = walk(+1)
        return float(edge(lo, lo_out)), float(edge(hi, hi_out))

    def frame(self, t0, t1, margin=2.0):
        """the band: mask of its vertices, its centre line (fitted through the rings' centres), the section frame e1 (width) and e2 (depth) square to D, t, and each point off the centre line."""
        t, Q = self.local()
        inside = (t > t0) & (t < t1) & self.mask
        inner = (t > t0 + margin) & (t < t1 - margin)
        if (inner & inside).sum() < 3:
            inner = inside
        axes = None; use = self.mask
        for _ in range(3):      # centres by the piece's X and Z, the frame from them; then centres in that frame, from
            # the band's own points (not a binding's or a guard's that share its rings): a conformed grip re-measures alike
            S = [x for x in self.sections(mask=use, axes=axes) if t0 - 4 < x[0] < t1 + 4]
            ts = np.array([x[0] for x in S]); cs = np.array([x[1] for x in S])
            # a line through them that follows a leaning or bowed haft but not a ring with a bump on one side (a
            # binding, a stud): each centre the median of those within SMOOTH mm, so the conform's scale centre is the
            # re-measure's
            cs = np.array([np.median(cs[np.abs(ts - x) <= SMOOTH], 0) for x in ts])
            def cl(tt, ts=ts, cs=cs):
                return np.stack([np.interp(tt, ts, cs[:, j]) for j in range(3)], -1)
            R = Q - cl(t)
            r = np.linalg.norm(R, axis=1) * self.mm
            m = inside & (r <= r[inner & inside].max() * RISE)
            w, v = np.linalg.eigh(np.cov(R[inner & m].T, bias=True))
            e1 = v[:, np.argmax(w)]; e1 -= self.D * (e1 @ self.D); e1 /= np.linalg.norm(e1)
            if e1 @ self.turn[0] < 0:
                e1 = -e1
            e2 = np.cross(self.D, e1)
            axes = (e1, e2); use = m
        return m, cl, e1, e2, t, R

    def section(self, t0, t1, margin=2.0):
        m, cl, e1, e2, t, R = self.frame(t0, t1, margin)
        inner = m & (t > t0 + margin) & (t < t1 - margin)
        if inner.sum() < 3:
            inner = m
        u, v = (R @ e1) * self.mm, (R @ e2) * self.mm
        hw = max(u[inner].max(), -u[inner].min()); hd = max(v[inner].max(), -v[inner].min())
        r = np.hypot(u, v)[inner].max()
        # the centre line's lean off the mount's axis (deg) and its offset from G (mm)
        d = (cl(np.array([t1]))[0] - cl(np.array([t0]))[0]) * self.mm
        lean = float(np.degrees(np.arctan2(np.linalg.norm(d), t1 - t0)))
        off = float(np.linalg.norm(cl(np.array([0.0]))[0]) * self.mm)
        return dict(half_w=float(hw), half_d=float(hd), r=float(r), t0=t0, t1=t1, n=int(m.sum()), lean=lean, off=off)


def ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def type_of(kind, sp):
    for name, t in sp["types"].items():
        if kind in t["kinds"]:
            return name, t
    return None, None


def piece_cfg(sp, row, pid):
    """a piece's own settings in the spec: by its id, else by its file (short_staff is mage_staff's file)."""
    P = sp.get("pieces", {})
    return P.get(pid) or P.get(row["file"]) or {}


def load(pid, rev=None, path=None):
    row = arms_rows()[pid]
    g = Glb.read(path or WEAPONS / f"{row['file']}.glb", rev)
    pc = Piece(pid, g, row)
    cfg = piece_cfg(spec(), row, pid)
    pc.centre_by = cfg.get("centre", "range")
    parts = cfg.get("parts")
    if parts:
        N = g.js["nodes"]; base = 0; pc.mask[:] = False
        for node, p, _ in pc.parts:
            n = g.js["accessors"][p["attributes"]["POSITION"]]["count"]
            pc.mask[base:base + n] = godot_name(N[node].get("name", "")) in parts; base += n
    return pc


def measure_piece(pc, sp):
    cfg = piece_cfg(sp, pc.row, pc.id)
    t0, t1 = pc.band(cfg)
    s = pc.section(t0, t1)
    s["mm_per_unit"] = pc.mm
    s["anchor"] = pc.anchor is not None
    return s


# ------------------------------------------------------------------ conform --
def conform(pc, sp, seat=False, anchor=True, round_=False, cylinder=False, roll=0.0, radius=None):
    tname, ty = type_of(pc.row["kind"], sp)
    assert ty, f"{pc.id}: kind {pc.row['kind']} has no grip type in {SPEC.name}"
    cfg = piece_cfg(sp, pc.row, pc.id)
    t0, t1 = pc.band(cfg)
    before = pc.section(t0, t1)
    m, cl, e1, e2, t, _ = pc.frame(t0, t1)
    hw_t, hd_t = ty["section"]["half_w"], ty["section"]["half_d"]
    hw_b, hd_b = before["half_w"], before["half_d"]     # per axis: a round spec makes a flat hilt round
    sx, sy = hw_t / hw_b, hd_t / hd_b
    rnd = (round_ or cylinder) and ty["section"]["shape"] == "round"
    cyl = cylinder and rnd
    D = pc.D
    if cyl:
        # cylinder: each RING (the band's vertices grouped along the line, as sections() groups them) drawn to the circle
        # on its own outline, so a taper, a bead or a sag between long quads all come to the type's radius: the fist
        # meets one round section along the whole band (a round spec's swell is the reference grip's: none)
        _, _, _, _, tq, R = pc.frame(t0, t1)
        idx = np.flatnonzero(m); idx = idx[np.argsort(tq[idx])]
        ring = np.zeros(len(tq), int); cur = 0; first = idx[0]
        for a, b in zip(idx[:-1], idx[1:]):
            if tq[b] - tq[a] > 0.75 or tq[b] - tq[first] > 3.0:
                cur += 1; first = b
            ring[b] = cur
        ang_all = np.arctan2(R @ e2, R @ e1); rr_all = np.linalg.norm(R, axis=1)
        tabs = {}
        for j in np.unique(ring[m]):
            sel = np.flatnonzero(m & (ring == j)); a_, r_ = ang_all[sel], rr_all[sel]
            k = ((a_ + np.pi) / (2 * np.pi) * 36).astype(int) % 36
            top = np.array(sorted([np.flatnonzero(k == q)[np.argmax(r_[k == q])] for q in np.unique(k)], key=lambda i: a_[i]))
            tabs[j] = (np.r_[a_[top] - 2 * np.pi, a_[top], a_[top] + 2 * np.pi], np.tile(r_[top], 3))
        # and its sides spaced evenly round the circle: a flat oval's vertices bunch toward its long axis, and drawn to
        # the circle as they lie its faces toward the palm span 50 degrees (a 1.2 mm flat). The angles the band's rings
        # share (the ring with the most), mapped in order onto n even steps (turned to move them least); every band
        # vertex's angle through that map (UVs stay: a wrap's texture laid as evenly as the oval's was)
        js = [j for j in np.unique(ring[m])]
        big = max(js, key=lambda j: (m & (ring == j)).sum())
        u = np.sort(ang_all[m & (ring == big)])
        u = u[np.r_[True, np.diff(u) > np.radians(0.5)]]
        if u[-1] - u[0] > 2 * np.pi - np.radians(0.5):
            u = u[1:]                       # -180 and +180 are one angle
        n_ = len(u); step = 2 * np.pi / n_
        off0 = np.angle(np.exp(1j * (u - step * np.arange(n_))).mean())
        ev = off0 + np.radians(roll) + step * np.arange(n_)
        # the corners' radius: the polygon's mean radius round its sides the spec's (an even n-gon of corner radius 1 has
        # mean (n/pi) cos(pi/n) ln tan(pi/4 + pi/2n): 0.977 for 12, so a 12-sided grip with its corners on the spec's circle
        # is 0.3 mm thin to the hand), its corners no further than TOL past the circle (check's own bound)
        mf = n_ / np.pi * np.cos(np.pi / n_) * np.log(np.tan(np.pi / 4 + np.pi / (2 * n_)))
        target = (radius or min(hw_t / mf, hw_t + TOL - 0.01)) / pc.mm
        ev = ev + 2 * np.pi * np.round((u - ev) / (2 * np.pi))    # each even angle beside its own
        def remap(th):
            xa = np.r_[u - 2 * np.pi, u, u + 2 * np.pi]; ya = np.r_[ev - 2 * np.pi, ev, ev + 2 * np.pi]
            return np.interp(th, xa, ya)
        sx = sy = float(target / rr_all[m].max())
    elif rnd:
        # round: each point's distance from the line times g(angle) = the radius / the band's outline at that angle
        # (10 degree sectors, the widest point in each at its own angle), so the outline comes to the circle, a ring's swell kept
        _, _, _, _, tq, R = pc.frame(t0, t1)
        ang = np.arctan2(R[m] @ e2, R[m] @ e1); rr = np.linalg.norm(R[m], axis=1)
        k = ((ang + np.pi) / (2 * np.pi) * 36).astype(int) % 36
        top = [np.flatnonzero(k == j)[np.argmax(rr[k == j])] for j in range(36) if (k == j).any()]
        top = np.array(sorted(top, key=lambda i: ang[i]))     # each sector's widest point, at its own angle
        xp = np.r_[ang[top] - 2 * np.pi, ang[top], ang[top] + 2 * np.pi]; fp = np.tile(rr[top], 3)
        target = hw_t / pc.mm
        def gfun(th):
            return target / np.interp(th, xp, fp)
        sx = sy = float(target / rr.max())       # (reported: the widest point's)
    S = np.eye(3) + (sx - 1) * np.outer(e1, e1) + (sy - 1) * np.outer(e2, e2)
    Sit = np.linalg.inv(S).T

    def maps(Rp, rows=None):
        """per point (world, square to D off the line): the new offset, and the normal and tangent maps."""
        if cyl:
            th = np.arctan2(Rp @ e2, Rp @ e1); out = np.linalg.norm(Rp, axis=1)
            for j, (xp_, fp_) in tabs.items():  # noqa: B007
                q = ring[rows] == j
                out[q] = np.interp(th[q], xp_, fp_)
            rad = np.linalg.norm(Rp, axis=1) * target / out
            th2 = remap(th); dth = th2 - th
            er2 = np.outer(np.cos(th2), e1) + np.outer(np.sin(th2), e2)
            c_, s_ = np.cos(dth)[:, None], np.sin(dth)[:, None]
            def turn(v):     # each row turned about D by its point's dth (Rodrigues)
                return v * c_ + np.cross(D, v) * s_ + np.outer(v @ D, D) * (1 - c_)
            def nmap(n):     # a side face (mostly radial) is the cylinder's: radial at its new angle; a cap (a guard's or
                # a pommel's face sharing the band's ring) keeps its own, turned with its point
                o = turn(n); side = np.abs(n @ D) < 0.5
                o[side] = er2[side]
                return o
            def tmap(v):     # turned with its point; then square to the new normal (Gram-Schmidt in conform's caller)
                return turn(v)
            return er2 * rad[:, None], nmap, tmap
        if not rnd:
            return Rp @ S.T, (lambda n: n @ Sit.T), (lambda v: v @ S.T)
        th = np.arctan2(Rp @ e2, Rp @ e1); gg = gfun(th)
        dg = (gfun(th + 1e-3) - gfun(th - 1e-3)) / 2e-3
        er = np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2); et = np.cross(D, er)
        def nmap(n):     # L^-T n = (n.D) D + n_perp / g - g'/g^2 (n.e_r) e_theta
            nd = n @ D; npp = n - np.outer(nd, D)
            return np.outer(nd, D) + npp / gg[:, None] - ((dg / gg ** 2) * (n * er).sum(1))[:, None] * et
        def tmap(v):     # L v = (v.D) D + g v_perp + g' (v.e_theta) e_r
            vd = v @ D; vp = v - np.outer(vd, D)
            return np.outer(vd, D) + vp * gg[:, None] + (dg * (v * et).sum(1))[:, None] * er
        return Rp * gg[:, None], nmap, tmap

    g = pc.g; base = 0; changed = {}
    for node, p, M in pc.parts:
        A = M[:3, :3]; Ai = np.linalg.inv(A)
        po, V = g.acc(p["attributes"]["POSITION"]); n = len(V)
        mm = m[base:base + n]; base += n
        if not mm.any():
            continue
        Pw = V @ A.T + M[:3, 3]
        C = pc.G + np.outer((Pw - pc.G) @ D, D) + cl(((Pw - pc.G) @ D) * pc.mm)
        off, nmap, tmap = maps((Pw - C)[mm], np.flatnonzero(mm) + base - n)
        V2 = V.copy(); V2[mm] = (C[mm] + off - M[:3, 3]) @ Ai.T
        out = V.astype("<f4"); out[mm] = V2[mm].astype("<f4")
        g.b[po:po + out.nbytes] = out.tobytes()
        a = g.js["accessors"][p["attributes"]["POSITION"]]
        a["min"] = out.min(0).astype(float).tolist(); a["max"] = out.max(0).astype(float).tolist()
        # normals: model -> world (A's inverse transpose), the map's, back (A's transpose); tangents by A, the map, A^-1
        if "NORMAL" in p["attributes"]:
            no, Nn = g.acc(p["attributes"]["NORMAL"])
            N2 = nmap((Nn @ Ai)[mm]) @ A
            N2 /= np.linalg.norm(N2, axis=1, keepdims=True)
            o = Nn.astype("<f4"); o[mm] = N2.astype("<f4")
            g.b[no:no + o.nbytes] = o.tobytes()
        if "TANGENT" in p["attributes"]:
            to, T = g.acc(p["attributes"]["TANGENT"], 4)
            T2 = tmap((T[:, :3] @ A.T)[mm]) @ Ai.T
            if cyl and "NORMAL" in p["attributes"]:      # square to the new normal (model space: t.n is A-invariant)
                T2 = T2 - N2 * (T2 * N2).sum(1, keepdims=True)
            T2 /= np.linalg.norm(T2, axis=1, keepdims=True)
            o = T.astype("<f4"); o[mm, :3] = T2.astype("<f4")
            g.b[to:to + o.nbytes] = o.tobytes()
        changed[node] = int(mm.sum())
    # the anchor: the mount as it was (the grip point, the long axis, +Z the mount's +Z)
    G = pc.G.copy(); moved = 0.0
    if seat and "grip_from_guard" in ty:          # the grip point the type's distance below the guard's end of the grip
        moved = (t1 - ty["grip_from_guard"]); G = pc.G + pc.D * moved / pc.mm
    Y = -pc.D; Z = pc.turn[2]; X = np.cross(Y, Z)
    if anchor:
        write_anchor(g, G, np.array([X, Y, Z]).T, pc.node_index)
    return dict(type=tname, before=before, sx=sx, sy=sy, changed=changed, G=G, moved=moved, band=(t0, t1))


def write_anchor(g, G, R, under=None):
    """an anchor_grip node (world point G, axes R's columns), replacing one there was: at the scene's root, or (a file
    of several pieces) a child of the piece's own node, as a matrix in its space (the node may scale)."""
    N = g.js["nodes"]; sc = g.js["scenes"][g.js.get("scene", 0)]
    W, parent = g.world()
    for i, n in enumerate(N):
        if n.get("name", "").startswith("anchor_grip") and (under is None or _under(i, under, parent)):
            for p in N:
                if i in p.get("children", []):
                    p["children"].remove(i)
                    if not p["children"]:
                        del p["children"]
            if i in sc["nodes"]:
                sc["nodes"].remove(i)
            n.clear(); n["name"] = "unused_old_anchor"
    if under is None:
        N.append(dict(name="anchor_grip", translation=[float(x) for x in G], rotation=[float(x) for x in quat(R)]))
        sc["nodes"].append(len(N) - 1)
    else:
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = G
        L = np.linalg.inv(W[under]) @ T
        N.append(dict(name="anchor_grip", matrix=[float(x) for x in L.T.reshape(-1)]))
        N[under].setdefault("children", []).append(len(N) - 1)


def _under(i, j, parent):
    while True:
        if i == j:
            return True
        if i not in parent:
            return False
        i = parent[i]


def quat(R):
    w = np.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)


# -------------------------------------------------------------------- check --
def check(pid, out_path, rev=None, moved=0.0):
    """the conformed file against the original: its mount (axes, grip point: moved mm along the shaft by --seat, scale)
    as the original's, the section against the spec, untouched rows and every other accessor byte for byte."""
    sp = spec(); a = load(pid, rev); b = load(pid, path=out_path)
    tname, ty = type_of(a.row["kind"], sp)
    cfg = piece_cfg(sp, a.row, pid)
    t0, t1 = a.band(cfg)
    mount = dict(axes_deg=float(np.degrees(np.arccos(np.clip(np.trace(a.turn @ b.turn.T) / 2 - 0.5, -1, 1)))),
                 grip_mm=float(np.linalg.norm(b.G - (a.G + a.D * moved / a.mm)) * a.mm), scale=float(b.k / a.k - 1),
                 anchored=b.anchor is not None)
    s = b.section(t0 - moved, t1 - moved)
    tw = ty["section"]["half_w"]; td = ty["section"]["half_d"]
    ok_sec = abs(s["half_w"] - tw) <= TOL and abs(s["half_d"] - td) <= TOL
    if ty["section"]["shape"] == "round":     # and round: no corner past the circle (a flat hilt scaled square)
        ok_sec = ok_sec and s["r"] <= tw + TOL
    got = f"{2 * s['half_w']:.2f} x {2 * s['half_d']:.2f} r {s['r']:.2f} (spec {2 * tw:.2f} x {2 * td:.2f})"
    # bytes: every accessor other than POSITION/NORMAL/TANGENT of the piece's parts identical; in those, the
    # changed rows only inside the band
    mine = {p["attributes"][k] for _, p, _ in a.parts for k in ("POSITION", "NORMAL", "TANGENT") if k in p["attributes"]}
    other_same = all(a.g.acc_bytes(i) == b.g.acc_bytes(i) for i in range(len(a.g.js["accessors"])) if i not in mine)
    uv = [p["attributes"][k] for _, p, _ in a.parts for k in p["attributes"] if k.startswith("TEXCOORD")]
    uv_same = all(a.g.acc_bytes(i) == b.g.acc_bytes(i) for i in uv)
    m, *_ = a.frame(t0, t1)
    rows_out = 0; base = 0; stray = 0
    for _, p, _ in a.parts:
        n = a.g.js["accessors"][p["attributes"]["POSITION"]]["count"]; mm = m[base:base + n]; base += n
        for key, w in (("POSITION", "V12"), ("NORMAL", "V12"), ("TANGENT", "V16")):
            if key in p["attributes"]:
                ia = p["attributes"][key]
                diff = np.frombuffer(a.g.acc_bytes(ia), w) != np.frombuffer(b.g.acc_bytes(ia), w)
                stray += int((diff & ~mm).sum())
                rows_out += int(diff.sum()) if key == "POSITION" else 0
    bin_len = len(a.g.b) - a.g.bin0 == len(b.g.b) - b.g.bin0
    return dict(type=tname, section=got, ok_section=ok_sec, mount=mount, changed_rows=rows_out, stray_rows=stray,
                other_accessors_identical=other_same, uv_identical=uv_same, bin_same_length=bin_len, s=s)


# ---------------------------------------------------------------------- cli --
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure"); m.add_argument("pieces", nargs="*"); m.add_argument("--src")
    c = sub.add_parser("conform"); c.add_argument("piece"); c.add_argument("--out", required=True); c.add_argument("--src")
    c.add_argument("--seat", action="store_true", help="the grip point moved to the type's grip_from_guard")
    c.add_argument("--round", action="store_true", help="a round type: the band's outline drawn to the circle (a flat hilt made round), not scaled per axis")
    c.add_argument("--cylinder", action="store_true", help="a round type: each ring of the band drawn to the circle (a taper, beads, a sag between long quads made one cylinder)")
    c.add_argument("--roll", type=float, default=0.0, help="--cylinder: deg the even sides are turned about the line (from the least move)")
    c.add_argument("--radius", type=float, default=None, help="--cylinder: mm, the corners' radius (default: the polygon's mean radius the spec's, within TOL)")
    c.add_argument("--no-anchor", action="store_true", help="no anchor_grip written (the mount stays on the bounds)")
    k = sub.add_parser("check"); k.add_argument("piece"); k.add_argument("file"); k.add_argument("--src")
    k.add_argument("--moved", type=float, default=0.0, help="mm the grip point was moved (--seat's)")
    a = ap.parse_args(argv)
    sp = spec(); rows = arms_rows()
    if a.cmd == "measure":
        print(f"{'piece':16s} {'kind':9s} {'type':8s} {'band mm':>13s} {'W x D mm':>13s} {'r mm':>6s}  spec W x D / r       off")
        for pid in a.pieces or rows:
            row = rows[pid]
            if row["build"] or row["pistol"] or row["kind"] == "Shield":
                print(f"{pid:16s} {row['kind']:9s} (made in code, pistol-held or strapped: no grip section)"); continue
            pc = load(pid, a.src); s = measure_piece(pc, sp)
            tname, ty = type_of(row["kind"], sp)
            line = (f"{pid:16s} {row['kind']:9s} {tname or '-':8s} {s['t0']:+6.1f}..{s['t1']:+5.1f} "
                    f"{2 * s['half_w']:6.2f} x{2 * s['half_d']:6.2f} {s['r']:6.2f}")
            if ty:
                q = ty["section"]
                if q["shape"] == "round":
                    line += f"  r {q['half_w']:.2f}{'':13s} {s['r'] - q['half_w']:+.2f} mm"
                else:
                    line += (f"  {2 * q['half_w']:.2f} x {2 * q['half_d']:.2f}{'':6s} "
                             f"{2 * (s['half_w'] - q['half_w']):+.2f} / {2 * (s['half_d'] - q['half_d']):+.2f} mm")
            print(line + ("  (anchor)" if s["anchor"] else ""))
    elif a.cmd == "conform":
        pc = load(a.piece, a.src)
        r = conform(pc, sp, a.seat, not a.no_anchor, a.round, a.cylinder, a.roll, a.radius)
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        assert out.resolve() != WEAPONS.resolve() and (ROOT / "godot").resolve() not in out.resolve().parents,             "a conformed piece goes to a scratch folder first; it replaces the game's file only after check and fistfit"
        f = out / f"{pc.row['file']}.glb"; pc.g.write(f)
        b = r["before"]
        print(f"{a.piece} -> {r['type']}: before {2 * b['half_w']:.2f} x {2 * b['half_d']:.2f} mm (r {b['r']:.2f}), "
              f"band {r['band'][0]:+.1f}..{r['band'][1]:+.1f} mm, scale width {r['sx']:.4f} depth {r['sy']:.4f}; "
              f"{sum(r['changed'].values())} vertices; grip point moved {r['moved']:+.1f} mm; written {f}")
        k = check(a.piece, f, a.src, r["moved"])
        print(json.dumps({x: y for x, y in k.items() if x != "s"}))
    else:
        k = check(a.piece, Path(a.file), a.src, a.moved)
        print(json.dumps({x: y for x, y in k.items() if x != "s"}))


if __name__ == "__main__":
    main()
