"""Layer a 2-5 kHz crack into every hit take whose first 60 ms is >6 dB under the set median (1-6 kHz).
Reads tools/audio/raw_takes/ (seeded from git HEAD on first run), writes godot/art/sound/. Rerunnable, idempotent."""
import glob, os, re, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "tools", "audio", "raw_takes")
OUT = os.path.join(ROOT, "godot", "art", "sound")
TABLE = r"C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_feel_f1\lead20\crack_table.txt"
PAT = re.compile(r"^hit_(flesh|hide|bone)(_crit)?_\d+\.wav$")

def seed():
    os.makedirs(RAW, exist_ok=True)
    names = subprocess.check_output(["git", "-C", ROOT, "ls-tree", "--name-only", "HEAD", "godot/art/sound/"], text=True).split()
    for n in names:
        b = os.path.basename(n)
        dst = os.path.join(RAW, b)
        if PAT.match(b) and not os.path.exists(dst):
            open(dst, "wb").write(subprocess.check_output(["git", "-C", ROOT, "show", "HEAD:" + n]))

def mono(x): return x if x.ndim == 1 else x.mean(axis=1)
def onset(m): return int(np.argmax(np.abs(m) >= 0.1 * np.abs(m).max()))
def band(m, lo, hi, sr, zp=False):
    sos = signal.butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, m) if zp else signal.sosfilt(sos, m)
def energy(m, sr, on):
    seg = band(m, 1000, 6000, sr)[on:on + int(0.06 * sr)]
    return 10 * np.log10(np.mean(seg ** 2) + 1e-20)
def env(n):
    e = np.zeros(n); r = max(1, int(0.001 * n / 40 * 1000 / 1000 * 1)) if False else None
    return e

CRACK_MS = float(os.environ.get("CRACK_MS", "40"))

def limit(y, sr, ceil_db=-1.0, look=0.002, rel=0.020):
    """Sample-wise lookahead limiter (2 ms attack, 20 ms release); gain 1.0 away from overs. Returns (y, gain)."""
    from numpy.lib.stride_tricks import sliding_window_view as win
    ceil = 10 ** (ceil_db / 20); L = max(1, int(look * sr))
    a = np.abs(y) if y.ndim == 1 else np.abs(y).max(axis=1)
    gr = np.minimum(1.0, ceil / np.maximum(a, 1e-12)); n = len(gr)
    m = win(np.concatenate([gr, np.ones(L)]), L + 1).min(axis=1)          # m[k] = min gr[k..k+L]
    sm = win(np.concatenate([np.full(L, m[0]), m]), L + 1).mean(axis=1)         # mean m[k-L..k] <= gr[k]
    al = np.exp(-1 / (rel * sr)); g = np.empty(n); prev = 1.0
    for i in range(n):
        prev = min(sm[i], prev * al + (1 - al)); g[i] = prev
    return (y * g if y.ndim == 1 else y * g[:, None]), g

def envelope(sr):
    n = int(CRACK_MS / 1000 * sr); r = max(1, int(0.001 * sr)); e = np.ones(n)
    e[:r] = np.linspace(0, 1, r, endpoint=False)
    f = n - r
    e[r:] = 0.5 * (1 + np.cos(np.pi * np.arange(f + 0) / f))[:n - r]
    return e

def main():
    seed()
    files = sorted(f for f in os.listdir(RAW) if PAT.match(f))
    data = {}
    for f in files:
        x, sr = sf.read(os.path.join(RAW, f), dtype="float64", always_2d=False)
        info = sf.info(os.path.join(RAW, f))
        m = mono(x); on = onset(m)
        data[f] = dict(x=x, sr=sr, sub=info.subtype, m=m, on=on, E=energy(m, sr, on), mat=PAT.match(f).group(1))
    M = float(np.median([d["E"] for d in data.values()]))
    rows = []
    for f in files:
        d = data[f]; x = d["x"]; sr = d["sr"]; gain = None; out = x
        if d["E"] < M - 6:
            pool = [g for g in files if data[g]["mat"] == d["mat"] and g != f]
            best = max(pool, key=lambda g: data[g]["E"])
            n = int(CRACK_MS / 1000 * sr); env_ = envelope(sr)
            if data[best]["E"] >= M - 3:
                s = data[best]; seg = s["m"][s["on"]:s["on"] + n]
                if len(seg) < n: seg = np.pad(seg, (0, n - len(seg)))
                crack = band(seg, 2000, 5000, s["sr"], zp=True) * env_
            else:
                rng = np.random.default_rng(1234)
                crack = band(rng.standard_normal(n * 4), 2000, 5000, sr, zp=True)[n:2 * n] * env_
            crack = crack / (np.abs(crack).max() + 1e-12)
            def mix(g):
                y = x.copy(); on = d["on"]; k = min(n, len(y) - on)
                add = (g * crack[:k]); 
                if y.ndim == 1: y[on:on + k] += add
                else: y[on:on + k] += add[:, None]
                return y
            guard = lambda y: limit(y, sr)[0]
            target = M - 2.6; lo, hi = 0.0, 40.0
            for _ in range(60):
                g = (lo + hi) / 2
                if energy(mono(guard(mix(g))), sr, d["on"]) < target: lo = g
                else: hi = g
            gain = g; out = mix(g)
        note = ""; grdb = 0.0; rms = 0.0
        if gain is not None:
            out, gg = limit(out, sr); grdb = -20 * np.log10(gg.min())
        if gain is None:
            open(os.path.join(OUT, f), "wb").write(open(os.path.join(RAW, f), "rb").read())
        else:
            sf.write(os.path.join(OUT, f), np.clip(out, -1, 1), sr, subtype=d["sub"])
        o = sf.read(os.path.join(OUT, f), dtype="float64")[0]
        Ea = energy(mono(o), sr, d["on"]); pa = 20 * np.log10(np.abs(o).max() + 1e-12)
        on = d["on"]; w = slice(on, on + int(0.15 * sr))
        rb = 20 * np.log10(np.sqrt(np.mean(mono(x)[w] ** 2)) + 1e-12); ra = 20 * np.log10(np.sqrt(np.mean(mono(o)[w] ** 2)) + 1e-12)
        if gain is not None: note = f"  rms150 {rb:.1f}->{ra:.1f}  maxGR {grdb:.2f} dB"
        rows.append(f"{f:24s} before {d['E']:7.2f}  after {Ea:7.2f}  M {M:7.2f}  gain {('%.4f' % gain) if gain is not None else '-':>8s}  peak {pa:6.2f} dBFS{note}")
    txt = "\n".join(rows) + f"\nchanged {sum('-' != r.split('gain')[1].split()[0] for r in rows)} of {len(rows)}; M {M:.2f} dB\n"
    os.makedirs(os.path.dirname(TABLE), exist_ok=True)
    open(TABLE, "w").write(txt); print(txt)

if __name__ == "__main__": main()
