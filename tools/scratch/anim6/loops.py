"""Fold-over loops in her skin at a bend: her posed skin cut by planes square
to the hinge every 2 mm across the joint. Each cut's outline is chained
into lines; wherever a line crosses itself the skin has turned over on
itself (a swallowtail at a fold's tip: what shows as the tick at the end of
the knee's crease), and the loop it closes is measured: its area (mm^2) and
how far it reaches from the crossing (mm). Summed over the cuts as the
volume of skin turned over (mm^3) and the largest loop's reach; a strip
draws each cut's largest reach (one character a cut, '.' none, '1' up to
1 mm, ... '9' 9 mm or more), her lateral side to the right.

    python -u loops.py <variant> ... [--joint knee|elbow] [--poses 120,145]
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import tick  # noqa: E402
from sweep import pose, knee, elbow, FRONT  # noqa: E402
from rigtest import thigh_forward  # noqa: E402

STEP = 0.2      # cm between cuts


def chains(segs, keys):
    """Segments [n, 2, 2] with their end keys (the mesh edge each end lies
    on) chained into lines: lists of segment indices in order."""
    at = defaultdict(list)
    for i, (k0, k1) in enumerate(keys):
        at[k0].append(i)
        at[k1].append(i)
    seen = np.zeros(len(segs), bool)
    lines = []
    for s0 in range(len(segs)):
        if seen[s0]:
            continue
        seen[s0] = True
        line = [(s0, False)]
        for direction in (1, 0):
            cur, flip = s0, False
            while True:
                end = keys[cur][1 if (direction == 1) != flip else 0]
                nxt = [i for i in at[end] if i != cur and not seen[i]]
                if not nxt:
                    break
                n = nxt[0]
                seen[n] = True
                nflip = keys[n][1] == end
                if direction == 1:
                    line.append((n, nflip))
                else:
                    line.insert(0, (n, not nflip))
                cur, flip = n, nflip if direction == 1 else not nflip
                if direction == 0:
                    flip = nflip
        lines.append(line)
    return lines


def polyline(segs, line):
    pts = []
    for i, fl in line:
        a, b = (segs[i][1], segs[i][0]) if fl else (segs[i][0], segs[i][1])
        if not pts:
            pts.append(a)
        pts.append(b)
    return np.array(pts)


def self_loops(pl):
    """A line's self-crossings: (area mm^2, reach mm) of the loop each closes."""
    n = len(pl) - 1
    if n < 3:
        return []
    closed = np.linalg.norm(pl[0] - pl[-1]) < 1e-6
    A, B = pl[:-1], pl[1:]
    i, j = np.triu_indices(n, 2)

    def cr(o, p, q):
        return (p[:, 0] - o[:, 0]) * (q[:, 1] - o[:, 1]) - (p[:, 1] - o[:, 1]) * (q[:, 0] - o[:, 0])
    a, b, c, d = A[i], B[i], A[j], B[j]
    hit = (cr(a, b, c) * cr(a, b, d) < 0) & (cr(c, d, a) * cr(c, d, b) < 0)
    out = []
    for k in np.nonzero(hit)[0]:
        ii, jj = i[k], j[k]
        p, r = A[ii], B[ii] - A[ii]
        q, s = A[jj], B[jj] - A[jj]
        den = r[0] * s[1] - r[1] * s[0]
        if abs(den) < 1e-12:
            continue
        t = ((q - p)[0] * s[1] - (q - p)[1] * s[0]) / den
        x = p + t * r

        def size(loop):
            area = 0.5 * abs(np.dot(loop[:-1, 0], loop[1:, 1]) - np.dot(loop[1:, 0], loop[:-1, 1]))
            return area, np.linalg.norm(loop - x, axis=1).max()
        area, reach = size(np.vstack([x, pl[ii + 1:jj + 1], x]))
        if closed:
            # a closed outline: the fold's loop is the smaller of the two parts
            a2, r2 = size(np.vstack([x, pl[jj + 1:], pl[1:ii + 1], x]))
            if a2 < area:
                area, reach = a2, r2
        out.append((area * 100, reach * 10))          # cm^2 -> mm^2, cm -> mm
    return out


def cuts(b, G, joint, side="l", reach=9.0):
    I = b.sk.index
    top, low = ("thigh", "calf") if joint == "knee" else ("upperarm", "lowerarm")
    j = I[f"{low}_{side}"]
    c = G[j][:3, 3]
    # the hinge: across the bone above and her front (elbow) or back (knee), as the poses turn it
    u = G[j][:3, 3] - G[I[f"{top}_{side}"]][:3, 3]
    u /= np.linalg.norm(u)
    h = np.cross(u, -FRONT if joint == "knee" else FRONT)
    h /= np.linalg.norm(h)
    e1 = u
    e2 = np.cross(h, e1)
    P = (b.pose(G) - c) * 100
    near = np.linalg.norm(P, axis=1) < reach * 1.5
    T = b.T[near[b.T].all(1)]
    d0 = P @ h
    q = np.stack([P @ e1, P @ e2], 1)
    out = []
    lo, hi = d0[near].min(), d0[near].max()
    for x0 in np.arange(np.floor(lo / STEP) * STEP + STEP / 2, hi, STEP):
        d = d0 - x0
        sa = d[T] > 0
        m = (sa[:, 0] != sa[:, 1]).astype(int) + (sa[:, 1] != sa[:, 2]) + (sa[:, 2] != sa[:, 0])
        Tc = T[m == 2]
        segs, keys = [], []
        for t in Tc:
            pts, ks = [], []
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if (d[a_] > 0) != (d[b_] > 0):
                    s = d[a_] / (d[a_] - d[b_])
                    pts.append(q[a_] + s * (q[b_] - q[a_]))
                    ks.append((min(a_, b_), max(a_, b_)))
            segs.append(pts)
            keys.append(ks)
        res = []
        if segs:
            segs = np.array(segs)
            # (seam points split in the mesh: chain by position, not index)
            pk = lambda e: tuple(np.round(b.P[list(e)].sum(0) / 1e-6).astype(np.int64))  # noqa: E731
            keys = [(pk(k0), pk(k1)) for k0, k1 in keys]
            for line in chains(segs, keys):
                pl = polyline(segs, line)
                if len(pl) < 4:
                    continue
                for area, rch in self_loops(pl):
                    # only loops whose crossing is within reach of the joint
                    res.append((area, rch))
        out.append((x0, res))
    return out


def poses_for(joint, which):
    out = {}
    for p in which:
        if joint == "knee":
            if p == "hip110":
                out["hip110 k135"] = [thigh_forward("l", 110), thigh_forward("r", 110), knee("l", 135), knee("r", 135)]
            else:
                out[f"knee {p}"] = [knee("l", int(p)), knee("r", int(p))]
        else:
            out[f"elbow {p}"] = [elbow("l", int(p)), elbow("r", int(p))]
    return out


def main():
    args = sys.argv[1:]
    opts = {"--joint": "knee", "--poses": "120,145", "--min": "0.5"}
    variants = []
    i = 0
    while i < len(args):
        if args[i] in opts:
            opts[args[i]] = args[i + 1]
            i += 2
        else:
            variants.append(args[i])
            i += 1
    import copy
    import helpers as hp
    spec0 = copy.deepcopy(hp.SPEC)
    joint = opts["--joint"]
    mn = float(opts["--min"])
    poses = poses_for(joint, opts["--poses"].split(","))
    for v in variants:
        hp.SPEC.clear()
        hp.SPEC.update(copy.deepcopy(spec0))
        b = tick.variant_body(v)
        tv = 0.0
        for pname, edits in poses.items():
            G = pose(b, edits)
            rows = cuts(b, G, joint)
            strip, vol, big = "", 0.0, (0.0, 0.0)
            for x0, res in rows:
                res = [r for r in res if r[1] >= mn]
                vol += sum(a for a, _ in res) * STEP * 10
                top = max((r for r in res), key=lambda r: r[1], default=None)
                if top and top[1] > big[0]:
                    big = (top[1], x0)
                strip += "." if not top else str(min(9, max(1, int(np.ceil(top[1])))))
            tv += vol
            print(f"{v:44s} {pname:12s} turned over {vol:6.1f} mm3, largest loop {big[0]:4.1f} mm at x {big[1]:+.1f}  {strip}", flush=True)
        print(f"{v:44s} TOTAL {tv:7.1f} mm3", flush=True)


if __name__ == "__main__":
    main()
