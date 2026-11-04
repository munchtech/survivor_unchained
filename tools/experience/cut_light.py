"""The cut light check (H4): the picture's brightness must not jump across a hand-back.

    python tools/experience/cut_light.py LOG SHOTSDIR [--limit 0.08]

For each `saved ...<name>_ho_<cine>_<NNN>_1.png` line in LOG (a picture run), in order, takes that image from
SHOTSDIR (by file name) and the CUTLOG line printed just before it (its phase and shot). Brightness of a frame
pair: both to grayscale, downscaled by 8, letterbox rows (row mean < 4 in either frame) dropped from both, the
mean of what is left. Change = |b2 - b1| / max(12, (b1 + b2) / 2). A pair that is a film cut is not counted
(listed as `cut`): both CUTLOG phases cine and the shot differs, or the <cine> part of the name changes
(c03 -> c04a), or no CUTLOG line for a pair and the grayscale correlation of the two frames is under 0.6.
Frames are grouped by the run's cut (a chain c03 -> c04a is one group). Exit 1 if any group FAILS
(a counted pair over the limit, default 0.08).
"""
import os, re, sys
from PIL import Image

SAVED = re.compile(r"saved \S*?([^/\\\s]*_ho_(\w+?)_(\d+)_1\.png)")
LOGL = re.compile(r"CUTLOG (\S+) t=(\S+) dt=(\S+) phase=(\w+) (?:shot=(-?\d+) )?")


def gray(path):
    im = Image.open(path).convert("L")
    return im.resize((max(1, im.width // 8), max(1, im.height // 8)), Image.BILINEAR)


def rows(im):
    w, h = im.size; px = list(im.getdata())
    return [px[y * w:(y + 1) * w] for y in range(h)]


def compare(ga, gb):
    ra, rb = rows(ga), rows(gb)
    n = min(len(ra), len(rb)); ra, rb = ra[:n], rb[:n]
    keep = [i for i in range(n) if sum(ra[i]) / max(1, len(ra[i])) >= 4 and sum(rb[i]) / max(1, len(rb[i])) >= 4]
    if not keep: keep = list(range(n))
    fa = [v for i in keep for v in ra[i]]; fb = [v for i in keep for v in rb[i]]
    b1, b2 = sum(fa) / len(fa), sum(fb) / len(fb)
    change = abs(b2 - b1) / max(12.0, (b1 + b2) / 2)
    if len(fa) == len(fb):
        da = [v - b1 for v in fa]; db = [v - b2 for v in fb]
        den = (sum(x * x for x in da) * sum(x * x for x in db)) ** 0.5
        corr = sum(x * y for x, y in zip(da, db)) / den if den > 1e-9 else 1.0
    else: corr = 0.0
    return b1, b2, change, corr


def chain(a, b):
    """c03 -> c04a (or the same id): one run's cut."""
    ma, mb = re.match(r"(\D*)(\d+)", a), re.match(r"(\D*)(\d+)", b)
    return bool(ma and mb and ma[1] == mb[1] and int(mb[2]) - int(ma[2]) in (0, 1))


def main():
    args = sys.argv[1:]; limit = 0.08
    if "--limit" in args: i = args.index("--limit"); limit = float(args[i + 1]); del args[i:i + 2]
    log, shots = args[0], args[1]
    frames, last = [], None
    for raw in open(log, encoding="utf-8", errors="replace"):
        m = LOGL.search(raw)
        if m: last = (m[4], int(m[5]) if m[5] else -1); continue
        m = SAVED.search(raw)
        if m:
            path = os.path.join(shots, m[1])
            if os.path.exists(path): frames.append(dict(name=os.path.splitext(m[1])[0], cine=m[2], path=path, cl=last))
            last = None
    if len(frames) < 2: print("cut_light: fewer than 2 frames found"); sys.exit(0)
    groups, cur = [], [frames[0]]
    for a, b in zip(frames, frames[1:]):
        if chain(a["cine"], b["cine"]): cur.append(b)
        else: groups.append(cur); cur = [b]
    groups.append(cur)
    imgs = {x["name"]: gray(x["path"]) for x in frames}
    allok = True; series = []
    ph = lambda x: f"{x['cl'][0]}/{x['cl'][1]}" if x["cl"] else "?"
    for g in groups:
        pairs = []
        for a, b in zip(g, g[1:]):
            b1, b2, ch, corr = compare(imgs[a["name"]], imgs[b["name"]])
            ca, cb = a["cl"], b["cl"]
            if ca and cb: cut = ca[0] == "cine" and cb[0] == "cine" and ca[1] != cb[1]
            else: cut = corr < 0.6
            if a["cine"] != b["cine"]: cut = True
            pairs.append((a, b, b1, b2, ch, cut)); series.append("cut" if cut else "%.1f" % (ch * 100))
        counted = [p for p in pairs if not p[5]]
        bad = [p for p in counted if p[4] > limit]
        ok = not bad; allok &= ok
        w = max(counted, key=lambda p: p[4], default=None)
        print(f"{'PASS' if ok else 'FAIL'} {g[0]['name']}..{g[-1]['name']} frames={len(g)} worst change "
              + (f"{w[4]*100:.1f}% at {w[0]['name']}->{w[1]['name']} ({w[2]:.0f} -> {w[3]:.0f})" if w else "- (no counted pairs)")
              + f"; cuts listed {len(pairs) - len(counted)}")
        for p in pairs:
            if p[5]: print(f"  cut {p[0]['name']}->{p[1]['name']} {p[4]*100:.1f}% ({p[2]:.0f} -> {p[3]:.0f})")
        for p in bad:
            print(f"  - {p[0]['name']}->{p[1]['name']} {p[4]*100:.1f}% ({p[2]:.0f} -> {p[3]:.0f}) {ph(p[0])} {ph(p[1])}")
    print("changes %: " + " ".join(series))
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
