"""ev14.py OPTS [STYLES] [v]: get_up (review dump), HEAD vs OPTS: offline HAIRCLEAR segments 4-7 worst k40-52 against the
warden (mw) and reaver (mr), all segments' worst, when the carry ends, the largest point move between frames in neck_01's
frame as Godot's HAIRMOVE (k40-60, the chain Godot reports: the drape while held, else the swing), and the largest change
from HEAD over k0-27 (cm). v: per frame the carried flags and segments."""
from hs14 import *
DUMP = dict(ponytail="hc/s11_ponytail_review", braid="hc/s11_braid_review")


def nframe(d):
    at = d["at"]; e1 = nz(d["back"][1]); v = at[2] - at[1]; e2 = nz(v - e1 * (v @ e1)); e3 = np.cross(e1, e2)
    return at[1], np.c_[e1, e2, e3]


def gx(xs, m):
    return [xs[k] if m.wlog[k] >= 1 - 1e-4 else m.swing[k] for k in range(len(xs))]


def gmove(fr, g, K0=40, K1=60, sc=1.04):
    best = (0, 0, 0); out = {}
    for k in range(K0, min(K1, len(g) - 1) + 1):
        o0, R0 = nframe(fr[k - 1]); o1, R1 = nframe(fr[k])
        a = (g[k - 1] - o0) @ R0; b = (g[k] - o1) @ R1; dd = np.linalg.norm(a - b, axis=1)[1:] / sc * 100
        out[k] = dd.max()
        if dd.max() > best[0]: best = (dd.max(), k, int(dd.argmax()) + 1)
    return best, out


def run14(st, o, log=None):
    fr = lg(*(log or DUMP[st]).split("/")); xs, m = run12(fr, st, **o); return fr, xs, m


def report(st, o, K0=40, K1=52):
    fr, xs, m = run14(st, o)
    res = {md: {k: clear(xs[k], "s12/" + md, k) for k in range(K0, K1 + 1)} for md in ("mw", "mr")}
    w47 = {md: min(min(res[md][k][3:]) for k in range(K0, K1 + 1)) for md in res}
    wall = {md: min(min(res[md][k]) for k in range(K0, K1 + 1)) for md in res}
    end = max((k for k in range(len(m.rlog)) if m.rlog[k].any()), default=-2) + 1
    mv, mvk = gmove(fr, gx(xs, m))
    return dict(fr=fr, xs=xs, m=m, res=res, w47=w47, wall=wall, end=end, mv=mv, mvk=mvk)


_HEAD = {}


def head(st):
    if st not in _HEAD: _HEAD[st] = report(st, {})
    return _HEAD[st]


def line(st, o, name="NEW"):
    r = report(st, o); h = head(st)
    d027 = max(np.linalg.norm(r["xs"][k] - h["xs"][k], axis=1).max() for k in range(0, 28)) * 100
    return r, "%-8s %-5s seg4-7 mw %5.1f mr %5.1f | all mw %5.1f mr %5.1f | carry ends k%d | move %.1f k%d p%d | k0-27 %.2f" % (
        st, name, r["w47"]["mw"], r["w47"]["mr"], r["wall"]["mw"], r["wall"]["mr"], r["end"], r["mv"][0], r["mv"][1], r["mv"][2], d027)


if __name__ == "__main__":
    o = eval(sys.argv[1]); sts = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] != "v" else ["ponytail", "braid"]
    V = "v" in sys.argv[2:]
    for st in sts:
        h = head(st)
        print("%-8s HEAD  seg4-7 mw %5.1f mr %5.1f | all mw %5.1f mr %5.1f | carry ends k%d | move %.1f k%d p%d" % (
            st, h["w47"]["mw"], h["w47"]["mr"], h["wall"]["mw"], h["wall"]["mr"], h["end"], h["mv"][0], h["mv"][1], h["mv"][2]))
        r, s_ = line(st, o); print(s_)
        if V:
            for k in range(40, 53):
                print("    k%d %s c%d | mw %s | mr %s | mv %.1f" % (k, "".join("1" if q else "." for q in r["m"].rlog[k]), r["m"].caplog[k],
                      " ".join("%5.1f" % v for v in r["res"]["mw"][k]), " ".join("%5.1f" % v for v in r["res"]["mr"][k]), r["mvk"].get(k, 0)))
