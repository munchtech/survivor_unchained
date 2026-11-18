"""scan.py SHOTDIR NLEGS: the round-11 judge's motion scan, repo-relative. Runs ana10.py per leg (-10..59) on SHOTDIR/views.log and flags
T3 (screen-angle step > 25 unless blade hidden/short on both frames), dshown, SPIKE shown/tilt/pitch, T1' canes, plus
STOP (leg +36..+44: |dpitch| > 8 deg or |dgripH| > 0.03 m per frame) and TILTFLIP (tilt sign change, both |tilt| >= 5). Ends with per-flag counts."""
import subprocess, re, os, sys, collections
F = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1]; n = int(sys.argv[2])
pat = re.compile(r"hd\s+(\S+)\s+([+-]\d+) yaw\s+(\S+) mov (\S+) w (\S+) a\s+(\S+) under\s+(\S+)px shown (\S+) pitch\s+(\S+) \(clip\s+(\S+)\).*gripH\s+(\S+).*tilt\s+(\S+) inw\s+(\S+)")
rows = {}
for L in range(n):
    out = subprocess.run([sys.executable, os.path.join(F, "ana10.py"), str(L), "-10", "59"], cwd=F, env=dict(os.environ, LOG=os.path.abspath(tag)), capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
    for line in out.splitlines():
        m = pat.search(line)
        if not m: continue
        v = [float(x) for x in m.groups()]
        k = 60 + 60 * L + int(v[1]); rows[k] = dict(hd=v[0], yaw=v[2], mov=v[3], w=v[4], a=v[5], under=v[6], shown=v[7], pitch=v[8], clip=v[9], gripH=v[10], tilt=v[11], inw=v[12])
ks = sorted(rows)
def rel(k):
    L = (k - 60) // 60; return f"L{L}{k-60-60*L:+d}(f{k})"
out = []; cnt = collections.Counter()
for k in ks:
    if k - 1 not in rows: continue
    p, c = rows[k - 1], rows[k]
    da = abs((c["a"] - p["a"] + 180) % 360 - 180); ds = c["shown"] - p["shown"]
    tags = []
    def add(name, s): tags.append(s); cnt[name] += 1
    if da > 25 and not (p["shown"] <= 0.5 and c["shown"] <= 0.5): add("T3", f"T3 {da:.0f}")
    if abs(ds) >= 0.25 and max(p["shown"], c["shown"]) > 0.5: add("dshown", f"dshown {ds:+.2f}")
    if k + 1 in rows:
        n_ = rows[k + 1]; d1 = c["shown"] - p["shown"]; d2 = c["shown"] - n_["shown"]
        if d1 * d2 > 0 and min(abs(d1), abs(d2)) >= 0.2: add("SPIKE_shown", f"SPIKE shown {p['shown']:.2f}>{c['shown']:.2f}>{n_['shown']:.2f}")
        t1 = c["tilt"] - p["tilt"]; t2 = c["tilt"] - n_["tilt"]
        if t1 * t2 > 0 and min(abs(t1), abs(t2)) >= 15: add("SPIKE_tilt", f"SPIKE tilt {p['tilt']:.0f}>{c['tilt']:.0f}>{n_['tilt']:.0f}")
        q1 = c["pitch"] - p["pitch"]; q2 = c["pitch"] - n_["pitch"]
        if q1 * q2 > 0 and min(abs(q1), abs(q2)) >= 10: add("SPIKE_pitch", f"SPIKE pitch {p['pitch']:.0f}>{c['pitch']:.0f}>{n_['pitch']:.0f}")
    if c["shown"] >= 0.6 and c["under"] > 8 and abs(c["a"]) < 28: add("cane", f"T1' a{c['a']:.0f} s{c['shown']:.2f} u{c['under']:.0f}")
    r = (k - 60) % 60
    if 36 <= r <= 44:
        dp = c["pitch"] - p["pitch"]; dg = round(c["gripH"] - p["gripH"], 3)
        if abs(dp) > 8 or abs(dg) > 0.03: add("STOP", f"STOP dpitch {dp:+.1f} dgripH {dg:+.3f}")
    if p["tilt"] * c["tilt"] < 0 and abs(p["tilt"]) >= 5 and abs(c["tilt"]) >= 5: add("TILTFLIP", f"TILTFLIP {p['tilt']:.0f}>{c['tilt']:.0f}")
    if tags: out.append(f"{rel(k):16s} w{c['w']:.2f} mov{c['mov']:.0f} a{c['a']:7.1f} sh{c['shown']:.2f} u{c['under']:4.0f} | " + "; ".join(tags))
print("\n".join(out))
print("SUMMARY " + " ".join(f"{k}={cnt[k]}" for k in ["T3", "dshown", "SPIKE_shown", "SPIKE_tilt", "SPIKE_pitch", "cane", "STOP", "TILTFLIP"]))
