"""ev13.py OPTS [STYLES] [v]: get_up, the replica at HEAD vs with OPTS (a dict; 'ridge' turns the capsules on): offline
HAIRCLEAR segments 4-7 worst per frame k40-52 (cm) against the warden (mw) and reaver (mr) meshes, the deepest any link
goes into her neck balls (nk, cm, >0 inside) over k40-52, and the largest move of a point in her neck's frame k40-60."""
from hs13 import *
def neckf(d):
    at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up)
    return neck, np.c_[np.cross(up, bk), up, bk]
def report(st, o, V=False, K0=40, K1=52):
    fr, xs, m, res = evalc(st, o, K0, K1)
    out = []
    for md in ("mw", "mr"):
        w = [min(res[md][k][3:]) for k in range(K0, K1 + 1)]
        out.append((md, min(w), w))
    nk = -99; nkk = 0
    for k in range(K0, K1 + 1):
        d = fr[k]; x = xs[k]
        for j in range(2, 8):
            for t in np.linspace(0, 1, 9):
                q = x[j - 1] + (x[j] - x[j - 1]) * t
                for b in (1, 2):
                    v = (d["r"][b] * 1.04 - np.linalg.norm(q - d["at"][b])) * 100
                    if v > nk: nk, nkk = v, k
    mv = 0; mvk = 0
    for k in range(K0 + 1, 61):
        n0, R0 = neckf(fr[k - 1]); n1, R1 = neckf(fr[k])
        a = (xs[k - 1] - n0) @ R0; b = (xs[k] - n1) @ R1; v = np.linalg.norm(a - b, axis=1).max() * 100
        if v > mv: mv, mvk = v, k
    return out, (nk, nkk), (mv, mvk), m
if __name__ == "__main__":
    o = eval(sys.argv[1]); sts = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] != "v" else ["ponytail", "braid"]
    V = "v" in sys.argv[2:]
    for st in sts:
        for name, oo in (("HEAD", {}), ("NEW", o)):
            if name == "HEAD" and "nohead" in sys.argv: continue
            out, nk, mv, m = report(st, oo)
            for md, wst, w in out:
                print("%-8s %-4s %s worst %5.1f |" % (st, name, md, wst), " ".join("%d:%.1f" % (k, v) for k, v in zip(range(40, 53), w)),
                      ("| neck %.1f (k%d) move %.1f (k%d)" % (nk + mv) if md == "mw" else ""))
            if V and name == "NEW":
                for k in range(40, 53): print("    k%d %s cap%d" % (k, "".join("1" if r else "." for r in m.rlog[k]), m.caplog[k]))
