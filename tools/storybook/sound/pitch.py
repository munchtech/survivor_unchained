"""YIN pitch tracker (de Cheveigne and Kawahara 2002), numpy only.

Used to read the motif off the Warden's sung take, and to check the render's
solo is in tune. Prints a frame table or, with --notes, the segmented notes.
"""
import argparse, json, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

D3 = 146.83
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def yin(x, sr, fmin=60, fmax=500, frame=2048, hop=256, thresh=0.15):
    """Returns times, f0 (0 where unvoiced), aperiodicity and rms per frame."""
    tmax = int(sr / fmin); tmin = int(sr / fmax)
    n = (len(x) - frame - tmax) // hop
    ts, fs, ap, rms = [], [], [], []
    for i in range(max(0, n)):
        s = i * hop
        w = x[s:s + frame + tmax]
        a = w[:frame]
        # difference function via direct sums (frames are short, clarity over speed)
        d = np.array([np.sum((a - w[t:t + frame]) ** 2) for t in range(tmax + 1)])
        cm = np.ones_like(d)
        cs = np.cumsum(d[1:])
        cm[1:] = d[1:] * np.arange(1, tmax + 1) / np.maximum(cs, 1e-12)
        tau = None
        for t in range(tmin, tmax):
            if cm[t] < thresh:
                while t + 1 < tmax and cm[t + 1] < cm[t]:
                    t += 1
                tau = t; break
        if tau is None:
            tau = tmin + int(np.argmin(cm[tmin:tmax])); voiced = cm[tau] < 0.35
        else:
            voiced = True
        # parabolic refinement of the dip
        if 0 < tau < tmax:
            y0, y1, y2 = cm[tau - 1], cm[tau], cm[tau + 1]
            den = y0 - 2 * y1 + y2
            ft = tau + (0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0)
        else:
            ft = tau
        ts.append((s + frame / 2) / sr)
        fs.append(sr / ft if voiced else 0.0)
        ap.append(float(cm[tau]))
        rms.append(float(np.sqrt(np.mean(a ** 2))))
    return np.array(ts), np.array(fs), np.array(ap), np.array(rms)


def midi(f):
    return 69 + 12 * np.log2(f / 440.0)


def name(m):
    m = int(round(m)); return f"{NAMES[m % 12]}{m // 12 - 1}"


def load(path, sr=16000, start=0.0, end=None, chan=None):
    x, r = sf.read(path, always_2d=True)
    x = x.mean(1) if chan is None else x[:, chan]
    x = x[int(start * r): int(end * r) if end else None]
    if r != sr:
        g = np.gcd(int(r), sr); x = resample_poly(x, sr // g, int(r) // g)
    return x.astype(np.float64), sr


def notes(ts, fs, rms, min_len=0.12, jump=0.6):
    """Groups voiced frames into notes: a new note when pitch moves > jump semitones."""
    out, cur = [], []
    floor = 0.1 * rms.max()
    for t, f, r in zip(ts, fs, rms):
        ok = f > 0 and r > floor
        if ok and cur and abs(midi(f) - np.median([midi(c[1]) for c in cur[-4:]])) > jump:
            out.append(cur); cur = []
        if ok:
            cur.append((t, f))
        elif cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for c in out:
        if c[-1][0] - c[0][0] + 0.016 < min_len: continue
        m = float(np.median([midi(f) for _, f in c]))
        res.append({"t0": round(c[0][0], 3), "t1": round(c[-1][0], 3), "midi": round(m, 2),
                    "note": name(m), "cents_off": round((m - round(m)) * 100, 1)})
    return res


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("path"); p.add_argument("--start", type=float, default=0); p.add_argument("--end", type=float)
    p.add_argument("--fmin", type=float, default=60); p.add_argument("--fmax", type=float, default=500)
    p.add_argument("--notes", action="store_true"); p.add_argument("--chan", type=int)
    a = p.parse_args()
    x, sr = load(a.path, start=a.start, end=a.end, chan=a.chan)
    ts, fs, ap, rms = yin(x, sr, a.fmin, a.fmax)
    ts = ts + a.start
    if a.notes:
        print(json.dumps(notes(ts, fs, rms), indent=1))
    else:
        for t, f, q, r in zip(ts, fs, ap, rms):
            if r > 0.02 * rms.max():
                print(f"{t:6.2f} {f:7.1f} {name(midi(f)) if f else '-':>4} ap={q:.2f} rms={r:.3f}")
